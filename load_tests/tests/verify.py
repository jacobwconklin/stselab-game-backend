"""Offline verification: real handler functions + in-memory SQLite adapter.

Never imports app.py/environmentSecrets and never opens a real MySQL connection.
This verifies the test driver, NOT production performance or MySQL compatibility.
"""
from gevent import monkey
monkey.patch_all()

import ast
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import random
import re
import socket
import sqlite3
import sys
import unittest
from unittest.mock import patch
import uuid
from types import SimpleNamespace

import gevent
from gevent import subprocess
from gevent.pywsgi import WSGIServer
from flask import Flask, jsonify, request
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["PYTHONPYCACHEPREFIX"]=str(ROOT/".cache/pycache")
(ROOT/".tmp").mkdir(exist_ok=True)
os.environ["TEMP"]=os.environ["TMP"]=os.environ["TMPDIR"]=str(ROOT/".tmp")
from model import (ALL_ENDPOINTS, ARM_ROUNDS, GOLF_ROUNDS, FRONTEND, delay,
                   dice_payload, host_plays_dice, inside, registration, settings)
from workflow import GameUser, Simulation
from workflow import WorkflowError
from locust.env import Environment

OUTPUT=ROOT/"results"/("verification-"+datetime.now().strftime("%Y%m%dT%H%M%S%f"))
OUTPUT.mkdir(parents=True)


class BackendAdapter:
    def __init__(self, failure=None, status_delay=0):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.calls=[]
        self.queries=[]
        self.failure=failure
        self.status_delay=status_delay
        self.counter=1
        backend=ROOT.parent
        for name in ("databaseStructure.sql","armDatabaseStructure.sql"):
            source=(backend/name).read_text(encoding="utf-8")
            source=re.sub(r"--[^\n]*","",source)
            for table in re.findall(r"CREATE TABLE\s+\w+\s*\(.*?\);",source,re.S):
                table=re.sub(r"Id int AUTO_INCREMENT PRIMARY KEY","Id INTEGER PRIMARY KEY AUTOINCREMENT",table)
                table=re.sub(r"\s*FOREIGN KEY\s*\([^)]+\)\s*REFERENCES\s*\w+\s*\([^)]+\),?","",table)
                table=re.sub(r",\s*\);", ");",table)
                self.db.executescript(table)
        # Support checkouts both before and after the TimeStamp schema correction.
        columns={row[1].lower() for row in self.db.execute("PRAGMA table_info(FreeRoamResult)")}
        if "timestamp" not in columns:
            self.db.execute("ALTER TABLE FreeRoamResult ADD COLUMN TimeStamp datetime")
        outer=self

        class Cursor:
            def __init__(self):
                self.raw=outer.db.cursor()
            def execute(self, sql, parameters=None):
                outer.queries.append((sql,parameters))
                sql=sql.replace("CURRENT_TIMESTAMP()","CURRENT_TIMESTAMP")
                if parameters is not None:
                    return self.raw.execute(sql.replace("%s","?"),parameters)
                return self.raw.execute(sql)
            def fetchone(self):
                row=self.raw.fetchone()
                return dict(row) if row else None
            def fetchall(self):
                return [dict(row) for row in self.raw.fetchall()]
            def close(self):
                self.raw.close()

        class Connection:
            def __init__(self,**_):
                pass
            def cursor(self,*_):
                return Cursor()
            def commit(self):
                outer.db.commit()
            def close(self):
                pass  # Preserve the single in-memory test database.

        def next_uuid():
            outer.counter+=1
            return uuid.UUID(int=outer.counter)

        namespace=dict(request=request,jsonify=jsonify,random=random,datetime=datetime,
                       uuid=SimpleNamespace(uuid4=next_uuid),json=json,
                       pymysql=SimpleNamespace(connections=SimpleNamespace(Connection=Connection),
                                               cursors=SimpleNamespace(DictCursor=object)))
        namespace.update({k:None for k in ("VT_MYSQL_HOST","VT_MYSQL_USER","VT_MYSQL_PASSWORD",
                                         "VT_MYSQL_STSELAB_DB","VT_MYSQL_PORT")})
        for name in ("users.py","session.py"):
            tree=ast.parse((backend/name).read_text(encoding="utf-8"))
            definitions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
            exec(compile(definitions,str(backend/name),"exec"),namespace)
        self.app=Flask(__name__)
        app_tree=ast.parse((backend/"app.py").read_text(encoding="utf-8"))
        routes=[]
        for node in ast.walk(app_tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="add_url_rule":
                route=node.args[0].value
                if route.startswith(("/player/","/session/")):
                    routes.append((route,node.args[2].id))

        def wrap(route, function):
            def endpoint():
                data=request.get_json(silent=True)
                sid=(data or {}).get("sessionId",(data or {}).get("joinCode"))
                if sid is None and (data or {}).get("playerId"):
                    player=self.db.execute("SELECT SessionId FROM PlayerBrief WHERE Id=?",(data["playerId"],)).fetchone()
                    sid=player[0] if player else None
                current=self.db.execute("SELECT Round FROM Session WHERE JoinCode=?",(sid,)).fetchone()
                self.calls.append({"endpoint":route.lstrip("/"),"body":data,
                                   "round":current[0] if current else None})
                if route=="/session/status" and self.status_delay:
                    gevent.sleep(self.status_delay)
                if route==self.failure:
                    return jsonify({"error":"Injected application failure"})
                return function()
            return endpoint

        for route,name in routes:
            self.app.add_url_rule(route,name,wrap(route,namespace[name]),methods=["GET"] if route.endswith("allResults") else ["POST"])

        @self.app.after_request
        def cors(response):
            response.headers["Access-Control-Allow-Origin"]=request.headers.get("Origin","*")
            response.headers["Access-Control-Allow-Methods"]="GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"]="Content-Type"
            return response

        self.server=WSGIServer(("127.0.0.1",0),self.app,log=None)
        self.server.start()
        self.url=f"http://127.0.0.1:{self.server.server_port}"

    def close(self):
        self.server.stop()
        gevent.sleep(self.status_delay+.02)
        self.db.close()


def run_case(name,scenario="full",**kwargs):
    adapter=BackendAdapter(failure=kwargs.get("failure"),status_delay=kwargs.get("status_delay",0))
    folder=OUTPUT/name
    configuration=OUTPUT/(name+"-config.json")
    configuration.write_text(json.dumps({"max_session_seconds":kwargs.get("deadline",45),
        "max_pending_polls":kwargs.get("max_pending",100),"archive_probability":1.0}),encoding="utf-8")
    command=[sys.executable,"-B",str(ROOT/"run.py"),"--host",adapter.url,
             "--players","6","--spawn-rate","100","--scenario",scenario,
             "--speed","1200","--poll-seconds","0.05", "--seed","12345",
             "--game-config",str(configuration),"--output",str(folder)]
    with (OUTPUT/(name+"-console.log")).open("w",encoding="utf-8") as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
        try:
            code=process.wait(timeout=80 if scenario=="coverage" else 60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            adapter.close()
            raise AssertionError(f"Driver hung; see {OUTPUT/name}")
    return code,folder,adapter


class ModelTests(unittest.TestCase):
    def test_frontend_endpoint_inventory(self):
        found=set()
        for path in (FRONTEND/"src").rglob("*"):
            if path.suffix in (".ts",".tsx",".js"):
                found.update(re.findall(r"(?:postRequest|getRequest)\(\s*['\"]/?([^'\"]+)",path.read_text(encoding="utf-8")))
        self.assertEqual(found,ALL_ENDPOINTS,"Frontend endpoint calls changed; update coverage")

    def test_timing_and_validation(self):
        normal=settings()
        fast=settings(speed=10)
        self.assertAlmostEqual(delay(normal,random.Random(1),"survey")/10,
                               delay(fast,random.Random(1),"survey"))
        self.assertEqual(normal["poll_seconds"],fast["poll_seconds"])
        self.assertFalse(fast["scale_polling"])
        for bad in (0,-1,float("inf"),float("nan")):
            with self.assertRaises(ValueError):
                settings(speed=bad)
        with self.assertRaises(ValueError):
            inside(ROOT.parent/"outside.json")

    def test_registration_and_dice(self):
        rng=random.Random(20)
        for i in range(100):
            data=registration(rng,"verification",i)
            self.assertIsInstance(data["age"],int)
            self.assertNotIn("'",data["name"])
            dice=dice_payload(rng,"player",False)
            self.assertLessEqual(sum(dice[f"d{d}"]*c for d,c in ((6,2),(8,3),(10,4),(12,5),(20,6))),8)
            self.assertGreaterEqual(sum(dice[f"d{d}"]*d for d in (6,8,10,12,20)),12)
            self.assertTrue(0<=dice["score"]<=100)
            self.assertEqual(dice["finalReasoning"],"")

    def test_poll_speed_is_independent_by_default(self):
        from gevent.pool import Group
        def count_polls(scale):
            user=object.__new__(GameUser)
            config=settings(speed=4,poll_seconds=.08,scale_polling=scale)
            user.session=SimpleNamespace(config=config,metrics=Counter(),abort=lambda message: self.fail(message))
            user.stop_timers=False
            user.ended=False
            user.round=1
            user.controller_version=0
            user.pending=Group()
            ticks=[]
            user.tick=lambda kind:ticks.append(kind)
            timer=gevent.spawn(user.timer,"controller")
            gevent.sleep(.225)
            user.stop_timers=True
            timer.join(timeout=1)
            user.pending.join()
            return len(ticks)
        normal=count_polls(False)
        scaled=count_polls(True)
        self.assertTrue(2<=normal<=3)
        self.assertGreaterEqual(scaled,normal*3)

    def test_simulation_payloads(self):
        output=OUTPUT/"simulation"
        output.mkdir()
        bridge=Simulation(output)
        try:
            for arch,n in (("h",1),("lp",2),("ds",2),("dap",3)):
                for r in sorted(GOLF_ROUNDS):
                    data=bridge.call(kind="golf",seed=12,playerId="player",round=r,
                                     architecture=arch,solvers=[2]*n,weight=.5,reasoning="Synthetic choice")
                    self.assertEqual(data["round"],r)
                    self.assertIsInstance(data["cost"],int)
                    self.assertEqual(data["customPerformanceWeight"],50)
            for module in range(1,7):
                data=bridge.call(kind="free",seed=100,playerId="player",module=module,solver=3)
                self.assertEqual(data["module"],module)
                self.assertIsInstance(data["distance"],int)
            for arch in bridge.meta["architectures"]:
                data=bridge.call(kind="arm",seed=100,playerId="player",round=15,architecture=arch["name"],solvers=[1]*len(arch["components"]),weight=.5)
                self.assertGreater(data["weight"],0)
                self.assertEqual(len([k for k in data if k.startswith("solver")]),len(arch["components"]))
        finally:
            bridge.close()


class ResponseReportingTests(unittest.TestCase):
    """Exercise Locust's real safe-mode/error events without contacting a backend."""

    def setUp(self):
        self.reports=[]
        self.records=[]
        environment=Environment(host="http://127.0.0.1:1")
        environment.events.request.add_listener(lambda **report:self.reports.append(report))
        with patch.object(GameUser,"host",environment.host):
            self.user=GameUser(environment)
            self.user.host=environment.host
        self.user.index=7
        self.user.round=0
        self.user.preflight_cache={}
        self.user.removed=False
        self.user.session=SimpleNamespace(
            config=settings(origin=""),join_code=123456,coverage=Counter(),
            phase_calls=Counter(),metrics=Counter(),retired=set(),
            record=lambda event,**values:self.records.append({"event":event,**values}))

    def tearDown(self):
        self.user.client.close()

    def response(self,status=200,body=b'{"success":true}',headers=None):
        response=requests.Response()
        response.status_code=status
        response._content=body
        response.encoding="utf-8"
        response.headers.update(headers or {"Content-Type":"application/json"})
        response.url="http://127.0.0.1:1/session/status"
        return response

    def test_post_transport_error_preserves_original_exception_and_cause(self):
        cause=ConnectionResetError(10054,"Connection reset by peer")
        error=requests.ConnectionError("Connection aborted",cause)
        error.__cause__=cause
        with patch.object(requests.Session,"request",side_effect=error) as send:
            result=self.user.request("session/status",{"sessionId":123456})
        self.assertIsNone(result)
        self.assertEqual(send.call_count,1)
        self.assertIs(self.reports[0]["exception"],error)
        record=self.records[0]
        self.assertEqual(record["failure_kind"],"transport")
        self.assertEqual(record["http_status"],0)
        self.assertEqual(record["response_bytes"],0)
        self.assertEqual(record["transport_error_type"],"ConnectionError")
        self.assertEqual(record["exception_chain"][-1]["type"],"ConnectionResetError")
        self.assertIn("10054",record["transport_error"])
        self.assertIn("timestamp_utc",record)
        self.assertNotIn("Invalid JSON",record["message"])

    def test_critical_transport_failure_still_stops_without_retry(self):
        error=requests.ReadTimeout("Response timed out")
        with patch.object(requests.Session,"request",side_effect=error) as send:
            with self.assertRaisesRegex(WorkflowError,"Transport error.*ReadTimeout"):
                self.user.post("player/roundResult",playerId="synthetic")
        self.assertEqual(send.call_count,1)
        self.assertEqual(len(self.reports),1)
        self.assertIs(self.reports[0]["exception"],error)

    def test_preflight_transport_failure_is_not_reported_as_cors(self):
        self.user.session.config["origin"]="http://localhost:3000"
        error=requests.ConnectTimeout("Connection timed out")
        with patch.object(requests.Session,"request",side_effect=error) as send:
            with self.assertRaisesRegex(WorkflowError,"OPTIONS /player/join: Transport error"):
                self.user.post("player/join",joinCode=123456)
        self.assertEqual(send.call_count,1,"Blocked preflight must not send or retry the POST")
        self.assertEqual(send.call_args.args[0],"OPTIONS")
        self.assertIs(self.reports[0]["exception"],error)
        self.assertEqual(self.records[0]["method"],"OPTIONS")
        self.assertEqual(self.records[0]["failure_kind"],"transport")

    def test_http_error_retains_status_and_bounded_body(self):
        body=b"<html>Service unavailable</html>"+b"x"*4000
        response=self.response(503,body,{"Content-Type":"text/html","Connection":"close"})
        with patch.object(requests.Session,"request",return_value=response):
            self.assertIsNone(self.user.request("session/status",{}))
        record=self.records[0]
        self.assertEqual(record["failure_kind"],"http")
        self.assertEqual(record["http_status"],503)
        self.assertEqual(record["response_bytes"],len(body))
        self.assertEqual(len(record["body_preview"]),1024)
        self.assertTrue(record["body_preview_truncated"])
        self.assertEqual(record["response_headers"]["Content-Type"],"text/html")
        self.assertIn("HTTP 503",str(self.reports[0]["exception"]))

    def test_malformed_success_response_is_still_a_json_failure(self):
        with patch.object(requests.Session,"request",return_value=self.response(body=b"not JSON")):
            self.assertIsNone(self.user.request("session/status",{}))
        self.assertEqual(self.records[0]["failure_kind"],"json")
        self.assertEqual(self.records[0]["http_status"],200)
        self.assertEqual(self.records[0]["body_preview"],"not JSON")
        self.assertIsNotNone(self.reports[0]["exception"])

    def test_preflight_distinguishes_http_errors_from_real_cors_errors(self):
        self.user.session.config["origin"]="http://localhost:3000"
        for status,kind in ((503,"http"),(200,"cors")):
            with self.subTest(status=status):
                self.user.preflight_cache.clear()
                with patch.object(requests.Session,"request",return_value=self.response(status)) as send:
                    self.assertIsNone(self.user.request("session/status",{}))
                self.assertEqual(send.call_count,1)
                self.assertEqual(self.records[-1]["failure_kind"],kind)
                self.assertEqual(self.records[-1]["http_status"],status)
                self.assertIsNotNone(self.reports[-1]["exception"])

    def test_successful_requests_keep_payload_timeout_and_preflight_cache(self):
        self.user.session.config["origin"]="http://localhost:3000"
        headers={"Access-Control-Allow-Origin":"http://localhost:3000",
                 "Access-Control-Allow-Methods":"POST, OPTIONS",
                 "Access-Control-Allow-Headers":"Content-Type"}
        payload={"sessionId":123456}
        responses=[self.response(headers=headers),self.response(),self.response()]
        with patch.object(requests.Session,"request",side_effect=responses) as send:
            for _ in range(2):
                self.assertEqual(self.user.request("session/status",payload),{"success":True})
        self.assertEqual([call.args[0] for call in send.call_args_list],["OPTIONS","POST","POST"])
        for call in send.call_args_list:
            self.assertEqual(call.kwargs["timeout"],20)
            self.assertEqual(call.kwargs["headers"]["Origin"],"http://localhost:3000")
        self.assertEqual(send.call_args_list[1].kwargs["json"],payload)
        self.assertEqual(self.records,[])
        self.assertTrue(all(report["exception"] is None for report in self.reports))

    def test_application_contract_and_expected_removal_outcomes_are_preserved(self):
        cases=[(b'{"error":"Database unavailable"}',False,"application",False),
               (b'{"success":false}',False,"contract",False),
               (b'{"error":"Player not in session"}',True,None,True)]
        for body,expected_removal,kind,success in cases:
            with self.subTest(body=body):
                self.records.clear()
                with patch.object(requests.Session,"request",return_value=self.response(body=body)):
                    self.user.request("session/status",{},expected_removal=expected_removal)
                self.assertEqual(self.reports[-1]["exception"] is None,success)
                if success:
                    self.assertTrue(self.user.removed)
                    self.assertEqual(self.records,[])
                else:
                    self.assertEqual(self.records[0]["failure_kind"],kind)


class WorkflowTests(unittest.TestCase):
    def test_web_launcher(self):
        import run
        destination=OUTPUT/"web-launcher"
        arguments=["run.py","--host","http://127.0.0.1:5000","--web","--output",str(destination)]
        with patch.object(sys,"argv",arguments),patch.object(run.subprocess,"run",return_value=SimpleNamespace(returncode=0)) as launch:
            self.assertEqual(run.main(),0)
        command=launch.call_args.args[0]
        self.assertNotIn("--headless",command)
        self.assertIn("--web-port",command)
        self.assertIn("127.0.0.1",command)
        self.assertNotIn("--csv",command)

    def test_web_dashboard_runs_again_and_preserves_reports(self):
        backend=BackendAdapter()
        folder=OUTPUT/"web-dashboard"
        folder.mkdir()
        config=OUTPUT/"web-config.json"
        config.write_text(json.dumps({"max_session_seconds":45,"archive_probability":1}),encoding="utf-8")
        with socket.socket() as bound:
            bound.bind(("127.0.0.1",0))
            port=bound.getsockname()[1]
        url=f"http://127.0.0.1:{port}"
        command=[sys.executable,"-B","-m","locust","-f",str(ROOT/"locustfile.py"),
                 "--host",backend.url,"--users","6","--players","6","--spawn-rate","100",
                 "--speed","1200","--poll-seconds","0.05","--game-config",str(config),
                 "--output",str(folder),"--web-host","127.0.0.1","--web-port",str(port),
                 "--logfile",str(folder/"locust.log")]
        with (folder/"console.log").open("w",encoding="utf-8") as log:
            process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
            try:
                with gevent.Timeout(15,AssertionError("Dashboard did not start")):
                    while True:
                        try:
                            response=requests.get(url,timeout=1)
                            if response.status_code==200:
                                break
                        except requests.RequestException:
                            pass
                        gevent.sleep(.05)
                self.assertEqual(backend.calls,[],"Dashboard must wait for Start before sending game requests")
                bad=requests.post(url+"/swarm",data={"user_count":"1","spawn_rate":"100","host":backend.url},timeout=2)
                self.assertEqual(bad.status_code,400)
                previous=set()
                for scenario,count in (("arm-only",4),("full",5)):
                    response=requests.post(url+"/swarm",data={"user_count":str(count),"spawn_rate":"100","host":backend.url,"scenario":scenario,"speed":"1200"},timeout=5)
                    self.assertEqual(response.status_code,200,response.text)
                    self.assertTrue(response.json().get("success"),response.text)
                    resize=requests.post(url+"/swarm",data={"user_count":"10","spawn_rate":"100","host":backend.url},timeout=5)
                    self.assertEqual(resize.status_code,400,resize.text)
                    with gevent.Timeout(35,AssertionError(f"Dashboard {scenario} did not finish")):
                        while True:
                            new=set(folder.glob("*/summary.json"))-previous
                            state=requests.get(url+"/stats/requests",timeout=2).json()["state"]
                            if new and state=="stopped" and all((p.parent/"report.html").exists() for p in new):
                                break
                            gevent.sleep(.05)
                    self.assertEqual(len(new),1)
                    summary_path=new.pop()
                    summary=json.loads(summary_path.read_text())
                    self.assertEqual(summary["scenario"],scenario)
                    self.assertEqual(summary["completed"],count)
                    self.assertEqual(summary["players"],count)
                    self.assertIsNone(summary["failure"])
                    self.assertEqual(summary["missing_endpoints"],[])
                    self.assertTrue((summary_path.parent/"requests_stats.csv").exists())
                    self.assertTrue((summary_path.parent/"requests_stats_history.csv").exists())
                    self.assertEqual(requests.get(url,timeout=2).status_code,200,"Dashboard should stay open after completion")
                    previous.add(summary_path)
                self.assertEqual(len(previous),2)
                self.assertIsNone(process.poll())
            finally:
                process.terminate()
                process.wait(timeout=5)
                backend.close()

    def test_all_profiles_and_persisted_flow(self):
        code,folder,backend=run_case("coverage","coverage")
        try:
            self.assertEqual(code,0,f"See {folder} and its locust.log files")
            coverage=json.loads((folder/"coverage.json").read_text())
            self.assertTrue(coverage["complete"])
            self.assertEqual(coverage["missing"],[])
            for scenario in ("full","golf-only","arm-only","departures"):
                result=json.loads((folder/scenario/"summary.json").read_text())
                self.assertEqual(result["completed"],6)
                self.assertIsNone(result["failure"])
                self.assertEqual(result["missing_endpoints"],[])
                self.assertGreater(result["metrics"]["preflight_requests"],0)
                session_id=result["session_id"]
                expected=[0,11,12,13,14,15] if scenario=="arm-only" else list(range(16 if scenario!="golf-only" else 10))
                self.assertEqual([t["from"] for t in result["transitions"]],expected)
                ids=result["player_ids"]
                for index,pid in ids.items():
                    removed=int(index) in result["retired"]
                    golf=[r[0] for r in backend.db.execute("SELECT Round FROM RoundResult WHERE PlayerId=?",(pid,))]
                    arms=[r[0] for r in backend.db.execute("SELECT Round FROM ArmRoundResult WHERE PlayerId=?",(pid,))]
                    self.assertEqual(set(golf),GOLF_ROUNDS if not removed and scenario!="arm-only" else set())
                    self.assertEqual(len(golf),len(set(golf)),"Accidental duplicate round submission")
                    self.assertEqual(set(arms),ARM_ROUNDS if not removed and scenario!="golf-only" else set())
                    dice=list(backend.db.execute("SELECT Onboarding,FinalReasoning FROM DiceResult WHERE PlayerId=?",(pid,)))
                    plays_host=host_plays_dice(pid) if int(index)==0 else False
                    self.assertEqual(sum(bool(d[0]) for d in dice),1 if plays_host else 0)
                    offboarding=not removed and (int(index)!=0 or plays_host)
                    count=(4 if scenario in ("full","departures") else 2) if offboarding else 0
                    self.assertEqual(sum(not d[0] for d in dice),count)
                    if count:
                        self.assertTrue(any(d[1] for d in dice if not d[0]))
                        calls=[c for c in backend.calls if c["endpoint"]=="player/diceResult" and c["body"]["playerId"]==pid and not c["body"]["onboarding"]]
                        expected_stages=[10,16] if scenario in ("full","departures") else [10] if scenario=="golf-only" else [16]
                        self.assertEqual(Counter(c["round"] for c in calls),Counter({stage:2 for stage in expected_stages}))
                if scenario!="golf-only":
                    host_id=ids["0"]
                    calls=backend.calls
                    end_index=next(i for i,c in enumerate(calls) if c["endpoint"]=="session/end" and c["body"]["sessionId"]==session_id)
                    host_final=next(i for i,c in enumerate(calls) if c["endpoint"]=="session/armfinalresults" and c["body"]["sessionId"]==session_id)
                    self.assertLess(host_final,end_index)
                    if host_plays_dice(host_id):
                        host_dice=next(i for i,c in enumerate(calls) if c["endpoint"]=="player/diceResult" and c["body"]["playerId"]==host_id and c["round"]==16)
                        self.assertLess(end_index,host_dice)
                end=backend.db.execute("SELECT EndDate FROM Session WHERE JoinCode=?",(session_id,)).fetchone()[0]
                self.assertIsNotNone(end)
            self.assertNotIn(2,{call["body"]["round"] for call in backend.calls if call["endpoint"]=="player/roundResult"})
        finally:
            backend.close()

    def test_http_200_application_errors_fail_run(self):
        code,folder,backend=run_case("application-error",failure="/player/roundResult")
        try:
            self.assertNotEqual(code,0)
            result=json.loads((folder/"full/summary.json").read_text())
            self.assertIn("Injected application failure",result["failure"])
        finally:
            backend.close()

    def test_slow_polls_overlap_and_cap_is_failure(self):
        code,folder,backend=run_case("overlap-cap",status_delay=.2,max_pending=2,deadline=10)
        try:
            self.assertNotEqual(code,0)
            result=json.loads((folder/"full/summary.json").read_text())
            self.assertIn("max_pending_polls",result["failure"])
            self.assertGreater(result["metrics"].get("poll_overflow",0),0)
        finally:
            backend.close()


if __name__=="__main__":
    print(f"Verification artifacts: {OUTPUT}",flush=True)
    unittest.main(verbosity=2)
