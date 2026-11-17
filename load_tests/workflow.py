"""A session of independent players, a real host, and frontend-style timers."""
from __future__ import annotations

import hashlib
import csv
import json
import logging
import random
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone

import gevent
from gevent.event import Event
from gevent.lock import Semaphore
from gevent.pool import Group
from gevent import subprocess
from locust import HttpUser, task, __version__ as locust_version
from locust.exception import StopUser
from locust.stats import StatsCSV, StatsCSVFileWriter, PERCENTILES_TO_REPORT
from locust.html import get_html_report

from model import (ALL_ENDPOINTS, ARM_ROUNDS, FRONTEND, GOLF_ROUNDS, ROOT,
                   delay, dice_payload, host_plays_dice, inside, reasoning,
                   registration, settings)

LOG = logging.getLogger(__name__)


class WorkflowError(RuntimeError):
    pass


POLL_CYCLE_TIMEOUT = 20.0  # Frontend startPolling timeout; never scaled by human speed.


class PollCancelled(BaseException):
    """Interrupt a read-only poll without treating cleanup as a failed game write."""


def response_diagnostics(response):
    """Capture bounded failure details without another request or a full body dump."""
    content=response.content or b""
    details={"timestamp_utc":datetime.now(timezone.utc).isoformat(),
             "http_status":response.status_code,"response_bytes":len(content),
             "body_preview":content[:1024].decode("utf-8",errors="replace"),
             "body_preview_truncated":len(content)>1024,
             "response_headers":{name:response.headers[name] for name in (
                 "Content-Type","Content-Length","Connection",
                 "Access-Control-Allow-Origin","Access-Control-Allow-Methods",
                 "Access-Control-Allow-Headers","Access-Control-Max-Age")
                 if name in response.headers}}
    error=getattr(response,"error",None)
    if error is not None:
        details["transport_error_type"]=type(error).__name__
        details["transport_error"]=repr(error)[:4096]
        chain=[]
        seen=set()
        while error is not None and id(error) not in seen and len(chain)<8:
            seen.add(id(error))
            chain.append({"type":type(error).__name__,"message":str(error)[:4096]})
            error=error.__cause__ or error.__context__
        details["exception_chain"]=chain
    return details


class Simulation:
    def __init__(self, output):
        self.lock = Semaphore()
        self.errors = (output / "simulation-stderr.log").open("w", encoding="utf-8")
        node = shutil.which("node")
        if not node:
            self.errors.close()
            raise WorkflowError("Node.js is required to reuse the real frontend simulations")
        self.process = subprocess.Popen(
            [node, str(ROOT / "simulation_bridge.cjs"), str(FRONTEND)],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.errors, text=True, encoding="utf-8", bufsize=1,
        )
        try:
            self.meta = self.call(kind="metadata", seed=0)
        except BaseException:
            self.close()
            raise
        expected={"WaitRoom":0,"PracticeHArchPro":1,"PracticeHArchAmateur":2,
                  "PracticeHArchAll":3,"Experimental":4,"ExperimentalSurvey":5,
                  "TournamentStage1":6,"TournamentStage2":7,"TournamentStage3":8,
                  "TournamentStage4":9,"FinalResults":10,"ArmExperiment":11,
                  "ArmGame1":12,"ArmGame2":13,"ArmGame3":14,"ArmGame4":15,"ArmFinalResults":16}
        if any(self.meta["rounds"].get(k)!=v for k,v in expected.items()):
            self.close()
            raise WorkflowError("Frontend round mapping changed; update the workflow before testing")

    def call(self, **message):
        with self.lock:
            try:
                with gevent.Timeout(15, WorkflowError("Frontend simulation timed out")):
                    self.process.stdin.write(json.dumps(message)+"\n")
                    self.process.stdin.flush()
                    line=self.process.stdout.readline()
                if not line:
                    raise WorkflowError("Simulation bridge stopped; inspect simulation-stderr.log")
                response=json.loads(line)
                if not response.get("ok"):
                    raise WorkflowError(response.get("error", "Simulation failed"))
                return response["result"]
            except (OSError, ValueError) as exc:
                raise WorkflowError(f"Simulation bridge failed: {exc}") from exc

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.errors.close()
        self.process.stdin.close()
        self.process.stdout.close()


class Session:
    def __init__(self, environment):
        self.env=environment
        opts=environment.parsed_options
        self.config=settings(opts.game_config, speed=opts.speed,
                             scale_polling=opts.scale_polling, seed=opts.seed,
                             poll_seconds=opts.poll_seconds)
        self.scenario=opts.scenario
        self.expected=opts.players
        if self.expected < (3 if self.scenario=="departures" else 2):
            raise WorkflowError("Use at least 2 players (3 for departures), including the host")
        self.id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")+f"-{self.config['seed']}"
        self.output=inside(opts.output or ROOT/"results"/self.id)
        if environment.web_ui:
            self.output=self.output/(self.scenario+"-"+self.id)
        self.output.mkdir(parents=True,exist_ok=True)
        self.closed=False
        self.csv_writer=None
        self.csv_greenlet=None
        self.created=Event()
        self.roster={}
        self.claimed=0
        self.join_code=None
        self.failed=None
        self.completed=set()
        self.retired=set()
        self.done=set()
        self.coverage=Counter()
        self.phase_calls=Counter()
        self.metrics=Counter()
        self.transitions=[]
        self.started=time.monotonic()
        self.end_sent=False
        self.quit_scheduled=False
        self.engine=Simulation(self.output)
        self.trace=(self.output/"journey.jsonl").open("w",encoding="utf-8",buffering=1)
        fingerprints={}
        for p in list((FRONTEND/"src").rglob("*.tsx"))+list((FRONTEND/"src/Utils").glob("*.ts"))+list((FRONTEND/"src/Utils").glob("*.js")):
            fingerprints[str(p.relative_to(FRONTEND))]=hashlib.sha256(p.read_bytes()).hexdigest()
        (self.output/"manifest.json").write_text(json.dumps({"run_id":self.id,
            "error_reporting_version":2,
            "polling_model":{"version":2,"overlap":False,
                             "cycle_timeout_seconds":POLL_CYCLE_TIMEOUT,
                             "round_change_skips_previous_results":True},
            "load_test_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                for name in ("workflow.py","model.py","config.json","locustfile.py",
                                             "run.py","simulation_bridge.cjs","requirements.txt",
                                             "requirements-windows.lock.txt")},
            "scenario":self.scenario,"players_including_host":self.expected,
            "host":environment.host,"configuration":self.config,
            "runtimes":{"python":sys.version,"locust":locust_version,
                        "node":self.engine.meta["nodeVersion"],"typescript":self.engine.meta["typescriptVersion"]},
            "backend_sha256":{name:hashlib.sha256((ROOT.parent/name).read_bytes()).hexdigest()
                              for name in ("app.py","users.py","session.py","requirements.txt",
                                           "databaseStructure.sql","armDatabaseStructure.sql")},
            "frontend_sha256":fingerprints},indent=2),encoding="utf-8")
        self.watchdog=gevent.spawn_later(self.config["max_session_seconds"],self.abort,
            "Session exceeded max_session_seconds (real wall-clock limit)")
        if environment.web_ui:
            self.csv_writer=StatsCSVFileWriter(environment,PERCENTILES_TO_REPORT,str(self.output/"requests"),full_history=True)
            self.csv_greenlet=gevent.spawn(self.csv_writer.stats_writer)

    def record(self, event, **values):
        self.trace.write(json.dumps({"elapsed":round(time.monotonic()-self.started,4),
                                     "event":event,**values})+"\n")

    def abort(self, message):
        if self.failed:
            return
        self.failed=message
        self.record("abort",message=message)
        LOG.error(message)
        self.env.process_exit_code=1
        self.quit()

    def quit(self):
        if not self.quit_scheduled:
            self.quit_scheduled=True
            gevent.spawn(self.env.runner.stop if self.env.web_ui else self.env.runner.quit)

    def finish(self, index):
        self.completed.add(index)
        if len(self.completed)==self.expected:
            self.quit()

    def summary(self):
        expected=set(ALL_ENDPOINTS)
        if self.scenario!="departures":
            expected.discard("player/remove")
        if self.scenario!="arm-only":
            expected.discard("session/jumptoarmmission")
        else:
            expected-={"player/roundResult","player/freeRoamResult","player/freeRoamSurvey",
                       "session/roundresults","session/finalresults","session/surveyssubmitted"}
        if self.scenario=="golf-only":
            expected-={"player/armRoundResult","session/armroundresults","session/armfinalresults"}
        return {"run_id":self.id,"scenario":self.scenario,"session_id":self.join_code,
                "elapsed_seconds":time.monotonic()-self.started,"players":self.expected,
                "completed":len(self.completed),"retired":sorted(self.retired),
                "failure":self.failed,"endpoint_calls":dict(self.coverage),
                "phase_endpoint_calls":dict(self.phase_calls),
                "expected_endpoints":sorted(expected),"missing_endpoints":sorted(expected-set(self.coverage)),
                "metrics":dict(self.metrics),"transitions":self.transitions,
                "player_ids":{str(i):p.player_id for i,p in self.roster.items()}}

    def close(self):
        if self.closed:
            return
        self.closed=True
        self.watchdog.kill()
        result=self.summary()
        if len(self.completed)!=self.expected or result["missing_endpoints"]:
            self.env.process_exit_code=1
        if self.env.stats.total.num_failures:
            self.env.process_exit_code=1
        if self.metrics["poll_timeouts"]:
            self.env.process_exit_code=1
        (self.output/"summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        if self.csv_writer:
            self.csv_greenlet.kill()
            self.csv_writer.close_files()
            exporter=StatsCSV(self.env,PERCENTILES_TO_REPORT)
            for suffix,write in (("stats",exporter.requests_csv),("failures",exporter.failures_csv),("exceptions",exporter.exceptions_csv)):
                with (self.output/f"requests_{suffix}.csv").open("w",newline="",encoding="utf-8") as target:
                    write(csv.writer(target))
            (self.output/"report.html").write_text(get_html_report(self.env,show_download_link=False),encoding="utf-8")
        self.trace.close()
        self.engine.close()
        self.env.game_start_requested=False


class GameUser(HttpUser):
    """One finite journey, not a random list of disconnected endpoint tasks."""
    abstract=False

    def on_start(self):
        self.session=self.environment.game_session
        self.index=self.session.claimed
        self.session.claimed+=1
        if self.index>=self.session.expected:
            self.session.abort("More Locust users than --players; do not resize a running session")
            raise StopUser()
        self.is_host=self.index==0
        self.rng=random.Random(self.session.config["seed"]+self.index*104729)
        self.pace=min(1.35,max(0.75,self.rng.lognormvariate(0,0.16)))
        self.player_id=None
        self.round=0
        self.ended=False
        self.onboarded=False
        self.finished_rounds=set()
        self.saved_scores={}
        self.actions_done=set()
        self.final_golf=[]
        self.visible_results={}
        self.players=[]
        self.survey_counts=(None,None)
        self.survey_version=0
        self.controller_version=0
        self.golf_result_count=0
        self.preflight_cache={}
        self.removal_requested=False
        self.removed=False
        self.stop_timers=False
        self.active_poll_cycles=0
        self.pending=Group()
        self.schedulers=Group()
        self.next_advance=None
        self.lobby_ready_at=None

    def sleep(self, key):
        gevent.sleep(delay(self.session.config,self.rng,key,self.pace))

    def note(self, event, **values):
        self.session.record(event,player=self.index,round=self.round,**values)

    def request(self, endpoint, payload=None, *, get=False, critical=False, expected_removal=False, validator=None):
        # Preserve the frontend's leading slash callers, producing //session/...
        double=endpoint in {"session/roundresults","session/finalresults",
                           "session/armroundresults","session/armfinalresults"}
        url=("//" if double else "/")+endpoint
        # Absolute URL avoids requests interpreting //path as another host.
        target=self.host.rstrip("/")+url
        if not get and self.session.config.get("origin"):
            if not self.preflight(endpoint,target,critical):
                return None
        self.session.coverage[endpoint]+=1
        self.session.phase_calls[f"round {self.round}: {'GET' if get else 'POST'} /{endpoint}"]+=1
        error=None
        failure_kind=None
        diagnostics=None
        data=None
        if hasattr(gevent.getcurrent(),"poll_kind"):
            gevent.getcurrent().poll_request={"method":"GET" if get else "POST","endpoint":endpoint}
        with self.client.request("GET" if get else "POST",target,
                json=None if get else payload,name="/"+endpoint,catch_response=True,
                timeout=self.session.config["request_timeout"],
                headers={"Origin":self.session.config["origin"]} if self.session.config.get("origin") else {},
                context={"player":self.index,"round":self.round,"session":self.session.join_code}) as response:
            transport_error=getattr(response,"error",None)
            if transport_error is not None:
                error=f"Transport error ({type(transport_error).__name__}): {transport_error}"
                failure_kind="transport"
            else:
                try:
                    data=response.json()
                    if not isinstance(data,dict):
                        error="Expected a JSON object"
                        failure_kind="contract"
                    elif expected_removal and data.get("error")=="Player not in session":
                        self.removed=True
                        self.session.retired.add(self.index)
                        response.success()
                    elif not 200<=response.status_code<300:
                        error=f"HTTP {response.status_code}"
                        failure_kind="http"
                    elif data.get("error"):
                        error=str(data["error"])
                        failure_kind="application"
                    elif endpoint!="player/allResults" and data.get("success") is not True:
                        error="Missing success:true"
                        failure_kind="contract"
                    elif validator:
                        error=validator(data)
                        failure_kind="contract" if error else None
                    self.session.metrics["redirects"]+=len(response.history)
                except (ValueError,TypeError,KeyError) as exc:
                    if not 200<=response.status_code<300:
                        error=f"HTTP {response.status_code}: invalid JSON contract: {exc}"
                        failure_kind="http"
                    else:
                        error=f"Invalid JSON contract: {exc}"
                        failure_kind="json"
            if error:
                # Preserve Locust's original network exception in its native reports.
                response.failure(transport_error if transport_error is not None else error)
                diagnostics=response_diagnostics(response)
        if error:
            self.note("request_error",endpoint=endpoint,method="GET" if get else "POST",
                      message=error,failure_kind=failure_kind,**diagnostics)
            if critical:
                raise WorkflowError(f"{endpoint}: {error}; write requests are never automatically retried")
            return None
        return data

    def preflight(self, endpoint, target, critical):
        if time.monotonic()<self.preflight_cache.get(endpoint,0):
            return True
        origin=self.session.config["origin"]
        error=None
        failure_kind=None
        diagnostics=None
        if hasattr(gevent.getcurrent(),"poll_kind"):
            gevent.getcurrent().poll_request={"method":"OPTIONS","endpoint":endpoint}
        with self.client.options(target,name="OPTIONS /"+endpoint,catch_response=True,
                timeout=self.session.config["request_timeout"],
                headers={"Origin":origin,"Access-Control-Request-Method":"POST",
                         "Access-Control-Request-Headers":"content-type"}) as response:
            headers=response.headers
            transport_error=getattr(response,"error",None)
            if transport_error is not None:
                error=f"Transport error ({type(transport_error).__name__}): {transport_error}"
                failure_kind="transport"
            elif not 200<=response.status_code<300:
                error=f"HTTP {response.status_code} during CORS preflight"
                failure_kind="http"
            elif headers.get("Access-Control-Allow-Origin") not in (origin,"*") or "POST" not in headers.get("Access-Control-Allow-Methods","").upper() or "content-type" not in headers.get("Access-Control-Allow-Headers","").lower():
                error="CORS preflight would block the browser request"
                failure_kind="cors"
            if error:
                response.failure(transport_error if transport_error is not None else error)
                diagnostics=response_diagnostics(response)
            try:
                age=min(7200,max(0,int(headers.get("Access-Control-Max-Age","5"))))
            except ValueError:
                age=5
            self.preflight_cache[endpoint]=time.monotonic()+age
            self.session.metrics["preflight_requests"]+=1
        if error:
            self.note("request_error",endpoint=endpoint,method="OPTIONS",message=error,
                      failure_kind=failure_kind,**diagnostics)
            if critical:
                raise WorkflowError(f"OPTIONS /{endpoint}: {error}")
        return error is None

    def post(self, endpoint, **values):
        return self.request(endpoint,values,critical=True)

    def calculate(self, kind, **values):
        start=time.monotonic()
        result=self.session.engine.call(kind=kind,seed=self.rng.randrange(2**32),
                                        playerId=self.player_id,**values)
        self.session.metrics["simulation_calls"]+=1
        self.session.metrics["simulation_wall_ms"]+=round((time.monotonic()-start)*1000)
        return result

    def timer(self, kind):
        interval=self.session.config["poll_seconds"]
        if self.session.config["scale_polling"]:
            interval/=self.session.config["speed"]
        due=None
        version=-1
        running=None
        try:
            while not self.stop_timers:
                active=(kind=="controller" and not self.ended or
                        kind=="lobby" and (self.round==0 or not self.onboarded) or
                        kind=="survey" and self.round==5 and
                        (not self.survey_counts[0] or not self.survey_counts[1] or self.survey_counts[1]<self.survey_counts[0]))
                current_version=self.survey_version if kind=="survey" else self.controller_version if kind=="controller" else 0
                if not active or version!=current_version:
                    if running is not None and not running.ready():
                        running.kill(PollCancelled("effect_cleanup"),block=False)
                    due=None
                    version=current_version
                if not active:
                    gevent.sleep(min(interval,0.02))
                    continue
                if due is None:
                    due=time.monotonic()+interval
                if time.monotonic()<due:
                    gevent.sleep(min(0.02,due-time.monotonic()))
                    continue
                due+=interval
                self.session.metrics["scheduled_polls"]+=1
                if running is not None and not running.ready():
                    self.session.metrics["skipped_busy_polls"]+=1
                    continue
                if len(self.pending)>=self.session.config["max_pending_polls"]:
                    self.session.metrics["poll_overflow"]+=1
                    self.session.abort("Outstanding requests hit max_pending_polls; offered load was capped, run failed")
                    return
                running=self.pending.spawn(self.poll_cycle,kind)
        finally:
            if running is not None and not running.ready():
                running.kill(PollCancelled("effect_cleanup"),block=False)

    def poll_cycle(self, kind):
        current=gevent.getcurrent()
        current.poll_kind=kind
        self.active_poll_cycles+=1
        self.session.metrics["peak_active_poll_cycles"]=max(
            self.session.metrics["peak_active_poll_cycles"],self.active_poll_cycles)
        try:
            with gevent.Timeout(POLL_CYCLE_TIMEOUT,PollCancelled("timeout")):
                self.tick(kind)
        except PollCancelled as exc:
            reason=str(exc)
            self.session.metrics["poll_timeouts" if reason=="timeout" else "cancelled_polls"]+=1
            self.note("poll_cancelled",kind=kind,reason=reason,
                      request=getattr(current,"poll_request",None))
        finally:
            self.active_poll_cycles-=1
            del current.poll_kind
            if hasattr(current,"poll_request"):
                del current.poll_request

    def tick(self, kind):
        self.session.metrics["started_polls"]+=1
        self.session.metrics["peak_pending_polls"]=max(self.session.metrics["peak_pending_polls"],len(self.pending))
        try:
            if kind=="lobby":
                r=self.request("session/players",{"sessionId":self.session.join_code},
                               validator=lambda d:None if isinstance(d.get("players"),list) else "Missing players list")
                if r:
                    self.players=r["players"]
                return
            if kind=="survey":
                r=self.request("session/surveyssubmitted",{"sessionId":self.session.join_code},
                               validator=lambda d:None if isinstance(d.get("totalPlayers"),int) and isinstance(d.get("surveysSubmitted"),int) else "Invalid survey counts")
                if r:
                    counts=(r["totalPlayers"],r["surveysSubmitted"])
                    if counts!=self.survey_counts:
                        self.survey_version+=1
                    self.survey_counts=counts
                return
            old_round=self.round
            r=self.request("session/status",{"sessionId":self.session.join_code,"playerId":self.player_id},
                           expected_removal=self.removal_requested,
                           validator=lambda d:None if isinstance(d.get("session"),dict) and isinstance(d.get("session").get("round"),int) and 0<=d["session"]["round"]<=16 else "Invalid session round")
            if not r or r.get("error"):
                return
            new_round=r["session"]["round"]
            if new_round!=self.round:
                self.note("observed_round",new_round=new_round)
                self.round=new_round
                self.golf_result_count=0
                self.controller_version+=1
            if r["session"].get("endDate"):
                self.ended=True
            elif new_round!=old_round:
                # New GameController returns before requesting the old round's results.
                return
            endpoint=None
            payload={"sessionId":self.session.join_code}
            if old_round in GOLF_ROUNDS and old_round in self.finished_rounds:
                endpoint="session/roundresults"
                payload["round"]=old_round
            elif old_round==10 and not self.final_golf:
                endpoint="session/finalresults"
            elif old_round in ARM_ROUNDS and old_round in self.finished_rounds:
                endpoint="session/armroundresults"
                payload["round"]=old_round
            if endpoint:
                r=self.request(endpoint,payload,validator=(self.final_contract if old_round==10 else lambda d:self.score_contract(d,old_round)))
                if r:
                    if endpoint=="session/finalresults":
                        if len(self.final_golf)!=len(r["results"]):
                            self.controller_version+=1
                        self.final_golf=r["results"]
                    else:
                        self.visible_results[old_round]=r["results"]
                        if endpoint=="session/roundresults" and self.golf_result_count!=len(r["results"]):
                            self.golf_result_count=len(r["results"])
                            self.controller_version+=1
        except Exception as exc:
            self.session.abort(f"Polling failed unexpectedly: {exc}")
        finally:
            self.session.metrics["completed_polls"]+=1

    @staticmethod
    def result_contract(data):
        rows=data.get("results")
        if not isinstance(rows,list) or not all(isinstance(row,dict) and "id" in row for row in rows):
            return "Invalid result list"
        if len({row["id"] for row in rows})!=len(rows):
            return "Duplicate players in results"
        return None

    def score_contract(self, data, stage):
        error=self.result_contract(data)
        if error:
            return error
        expected=self.saved_scores.get(stage)
        if not expected:
            return None
        own=next((row for row in data["results"] if row["id"]==self.player_id),None)
        if own is None:
            return "Saved player missing from round results"
        fields=("shots","cost","score") if stage in GOLF_ROUNDS else ("weight","cost","score")
        for field in fields:
            value=expected[field]
            if field=="score" and value is None:
                value=-1  # users.roundResult normalizes unscored practice to -1.
            if own.get(field)!=value:
                return f"Saved {field} differs from round {stage} response"
        return None

    def final_contract(self, data, arm=False):
        error=self.result_contract(data)
        if error:
            return error
        own=next((row for row in data["results"] if row["id"]==self.player_id),None)
        if own is None or not isinstance(own.get("scores"),list):
            return "Player/scores missing from final results"
        stages=ARM_ROUNDS if arm else set(range(6,10))
        if {row.get("round") for row in own["scores"]}!=stages or len(own["scores"])!=len(stages):
            return "Incomplete or duplicate final round scores"
        for row in own["scores"]:
            expected=self.saved_scores.get(row["round"])
            if expected and row.get("score")!=expected["score"]:
                return "Final score differs from submitted score"
        return None

    def dice(self, onboarding):
        # Only hosts have an explicit flag. Undefined joiner flag skips onboarding
        # in WaitRoom, but does NOT satisfy `=== false` in DiceSelectGame.
        eligible=host_plays_dice(self.player_id) if self.is_host else not onboarding
        if not eligible:
            return
        self.sleep("dice_choice")
        self.sleep("dice_reason")
        payload=dice_payload(self.rng,self.player_id,onboarding)
        self.request("player/diceResult",payload,critical=True)
        if not onboarding:
            self.sleep("offboarding_questions")
            payload.update({key:reasoning(self.rng) for key in
                            ("finalReasoning","reasoning2","reasoning3","reasoning4","reasoning5")})
            # This second INSERT is what the current second-modal Continue does.
            # That click unmounts the modal without awaiting saveAndContinue().
            self.pending.spawn(self.save_background,"player/diceResult",payload)

    def golf(self, round_number):
        self.sleep("practice" if round_number in (1,3) else "golf_choice")
        self.sleep("animation")
        architecture="h" if round_number in (1,3) else self.rng.choice(["h","lp","ds","dap"])
        count={"h":1,"lp":2,"ds":2,"dap":3}[architecture]
        solvers=[1] if round_number==1 else [self.rng.randint(1,3) for _ in range(count)]
        weight=self.rng.randint(20,80)/100 if round_number==9 else 0.5
        data=self.calculate("golf",round=round_number,architecture=architecture,
                            solvers=solvers,weight=weight,reasoning=reasoning(self.rng))
        self.request("player/roundResult",data,critical=True)
        self.saved_scores[round_number]=data
        self.finished_rounds.add(round_number)

    def arm(self, round_number):
        self.sleep("arm_choice")
        arch=self.rng.choice(self.session.engine.meta["architectures"])
        solvers=[self.rng.randint(1,5) for _ in arch["components"]]
        weight=self.rng.randint(20,80)/100 if round_number==15 else 0.5
        data=self.calculate("arm",round=round_number,architecture=arch["name"],solvers=solvers,weight=weight)
        self.request("player/armRoundResult",data,critical=True)
        self.saved_scores[round_number]=data
        self.finished_rounds.add(round_number)

    def explore(self, arm=False):
        duration=delay(self.session.config,self.rng,"arm_exploration" if arm else "golf_exploration",self.pace)
        until=time.monotonic()+duration
        modules=list(range(1,7))
        self.rng.shuffle(modules)
        first=True
        while first or time.monotonic()<until:
            first=False
            self.sleep("exploration_attempt")
            if arm:
                arch=self.rng.choice(self.session.engine.meta["architectures"])
                self.calculate("arm-experiment",solver=self.rng.randint(1,5),component=self.rng.choice(arch["components"]))
            else:
                module=modules.pop() if modules else self.rng.randint(1,6)
                data=self.calculate("free",module=module,solver=self.rng.randint(1,3))
                # Frontend saveFreeRoamResult is fire-and-forget.
                self.pending.spawn(self.save_background,"player/freeRoamResult",data)

    def save_background(self, endpoint, data):
        try:
            self.request(endpoint,data,critical=True)
        except Exception as exc:
            self.session.abort(str(exc))

    def action(self, round_number):
        if round_number==0:
            self.dice(True)
            self.onboarded=True
        elif round_number in GOLF_ROUNDS:
            self.golf(round_number)
        elif round_number==2:
            # AmateurOnly has no player/roundResult call.
            self.sleep("amateur_experiment")
        elif round_number==4:
            self.explore()
        elif round_number==5:
            self.sleep("survey")
            self.post("player/freeRoamSurvey",playerId=self.player_id,
                      **{key:self.rng.randint(0,7) for key in ("drive","long","fairway","short","putt","entireHole")})
        elif round_number==10:
            self.dice(False)
            self.sleep("final_review")
        elif round_number==11:
            self.explore(arm=True)
        elif round_number in ARM_ROUNDS:
            self.arm(round_number)
        elif round_number==16:
            r=self.request("session/armfinalresults",{"sessionId":self.session.join_code},
                           critical=True,validator=lambda d:self.final_contract(d,arm=True))
            if self.is_host:
                self.post("session/end",sessionId=self.session.join_code)
                self.session.end_sent=True
            # ArmFinalResults remounts dice even after golf offboarding.
            self.dice(False)
            self.sleep("final_review")
        self.actions_done.add(round_number)
        self.session.done.add((self.index,round_number))
        self.note("action_complete",completed_round=round_number)

    def host_control(self):
        stage=self.round
        if stage==16 or self.session.end_sent:
            return
        if stage==0:
            ready=len(self.session.roster)==self.session.expected and all(
                p.onboarded or i in self.session.retired for i,p in self.session.roster.items())
            if self.session.scenario=="departures":
                # One self-exit and one host removal, both through real UI routes.
                target=self.session.roster.get(self.session.expected-2)
                if target and target.onboarded and not target.removal_requested:
                    target.removal_requested=True
                    self.request("player/remove",{"playerId":target.player_id},critical=True)
                    self.note("host_kick",target=target.index)
                ready=ready and {self.session.expected-1,self.session.expected-2}<=self.session.retired
        elif stage in GOLF_ROUNDS|ARM_ROUNDS:
            rows=self.visible_results.get(stage,[])
            field="shots" if stage in GOLF_ROUNDS else "weight"
            expected={p.player_id for i,p in self.session.roster.items() if i not in self.session.retired}
            ready=bool(expected) and expected<={r["id"] for r in rows if r.get(field)}
        elif stage==5:
            total,submitted=self.survey_counts
            ready=bool(total) and submitted==total and stage in self.actions_done
        else:
            ready=all((i,stage) in self.session.done for i in self.session.roster if i not in self.session.retired)
            if stage==10:
                ready=ready and bool(self.final_golf)
        if not ready or self.next_advance==stage:
            return
        self.next_advance=stage
        self.sleep("lobby" if stage==0 else "results_review")
        if self.session.scenario=="golf-only" and stage==10:
            self.post("session/end",sessionId=self.session.join_code)
            self.session.end_sent=True
            return
        if self.session.scenario=="arm-only" and stage==0:
            self.post("session/jumptoarmmission",sessionId=self.session.join_code)
            expected=11  # Handler returns 1 here; frontend ignores that value.
        else:
            self.post("session/advance",sessionId=self.session.join_code)
            expected=stage+1
        self.session.transitions.append({"from":stage,"to":expected,"elapsed":time.monotonic()-self.session.started})
        self.note("host_advance",expected_round=expected)

    @task
    def journey(self):
        try:
            self.sleep("registration")
            if not self.is_host:
                self.session.created.wait()
            payload=registration(self.rng,self.session.id,self.index)
            if not self.is_host:
                payload["joinCode"]=str(self.session.join_code)
            endpoint="player/host" if self.is_host else "player/join"
            r=self.request(endpoint,payload,critical=True,
                           validator=lambda d:None if isinstance(d.get("playerId"),str) and
                           (not self.is_host or isinstance(d.get("joinCode"),int)) else "Missing player ID / join code")
            self.player_id=r["playerId"]
            if self.is_host:
                self.session.join_code=r["joinCode"]
                self.session.created.set()
            self.session.roster[self.index]=self
            self.note("registered",player_id=self.player_id)
            for kind in ("controller","lobby","survey"):
                self.schedulers.spawn(self.timer,kind)
            while not self.removed:
                stage=self.round
                if stage not in self.actions_done:
                    self.action(stage)
                if self.session.scenario=="departures" and self.index==self.session.expected-1 and not self.removal_requested:
                    self.sleep("results_review")
                    self.request("player/remove",{"playerId":self.player_id},critical=True)
                    self.removal_requested=True
                    self.removed=True
                    self.session.retired.add(self.index)
                    self.note("self_exit")
                    break
                if self.is_host:
                    self.host_control()
                final=10 if self.session.scenario=="golf-only" else 16
                if self.ended and final in self.actions_done:
                    if self.is_host or self.rng.random()<self.session.config["archive_probability"]:
                        self.request("player/allResults",get=True,critical=True,
                                     validator=lambda d:None if isinstance(d.get("results"),list) else "Missing archive results")
                        self.sleep("historical_results")
                    break
                gevent.sleep(0.02)
            self.stop_timers=True
            self.schedulers.kill()
            self.pending.join(timeout=self.session.config["request_timeout"]+1)
            if self.pending:
                raise WorkflowError("Pending requests did not drain")
            self.session.finish(self.index)
        except Exception as exc:
            self.session.abort(f"Player {self.index}: {exc}")
        finally:
            self.stop_timers=True
            self.schedulers.kill()
            self.pending.kill()
        # Finite users remain parked so Locust does not respawn a new session.
        while True:
            gevent.sleep(60)

    def on_stop(self):
        self.stop_timers=True
        if hasattr(self,"schedulers"):
            self.schedulers.kill()
            self.pending.kill()
