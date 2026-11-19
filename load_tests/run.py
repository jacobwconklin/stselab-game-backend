"""Folder-confined launcher. Run with load_tests/.venv/Scripts/python.exe."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["PIP_CACHE_DIR"]=str(ROOT/".cache/pip")
os.environ["PYTHONPYCACHEPREFIX"]=str(ROOT/".cache/pycache")
(ROOT/".tmp").mkdir(exist_ok=True)
os.environ["TEMP"]=os.environ["TMP"]=os.environ["TMPDIR"]=str(ROOT/".tmp")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host",required=True,help="Explicit local/staging backend URL; no production default")
    parser.add_argument("--players",type=int,default=100,help="Total participants including one host")
    parser.add_argument("--spawn-rate",type=float,default=5)
    parser.add_argument("--scenario",choices=("full","golf-only","arm-only","departures","coverage"),default="full")
    parser.add_argument("--speed",type=float,default=None)
    parser.add_argument("--scale-polling",action="store_true")
    parser.add_argument("--poll-seconds",type=float,default=None)
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--game-config",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--web",action="store_true",help="Start the browser dashboard instead of an automatic headless run")
    parser.add_argument("--web-port",type=int,default=8089)
    parser.add_argument("--no-connection-monitor",action="store_true",help="Disable automatic local TCP connection monitoring")
    args=parser.parse_args()
    from model import inside, settings
    from urllib.parse import urlparse
    url=urlparse(args.host)
    if url.scheme not in ("http","https") or not url.hostname or url.path not in ("","/") or url.query or url.fragment or url.username:
        parser.error("--host must be an HTTP(S) origin without a path, query, or embedded credentials")
    if args.players<2 or args.spawn_rate<=0:
        parser.error("Use at least two players and a positive spawn rate")
    if args.scenario in ("departures","coverage") and args.players<3:
        parser.error("Departures/coverage needs at least three players")
    if args.web and args.scenario=="coverage":
        parser.error("In the dashboard choose one scenario at a time; automatic coverage uses headless mode")
    if not 1<=args.web_port<=65535:
        parser.error("--web-port must be between 1 and 65535")
    try:
        settings(args.game_config,speed=args.speed,poll_seconds=args.poll_seconds,seed=args.seed)
        output=inside(args.output or ROOT/"results"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
    except ValueError as exc:
        parser.error(str(exc))
    if output.exists():
        parser.error("Output already exists; use a fresh directory to preserve earlier results")
    output.mkdir(parents=True)
    cases=("full","golf-only","arm-only","departures") if args.scenario=="coverage" else (args.scenario,)
    summaries=[]
    exit_code=0
    for scenario in cases:
        case=output/("dashboard" if args.web else scenario)
        case.mkdir()
        cmd=[sys.executable,"-B","-m","locust","-f",str(ROOT/"locustfile.py"),
             "--host",args.host,"--users",str(args.players),
             "--players",str(args.players),"--spawn-rate",str(args.spawn_rate),
             "--scenario",scenario,"--output",str(case),"--logfile",str(case/"locust.log")]
        if args.web:
            cmd.extend(["--web-host","127.0.0.1","--web-port",str(args.web_port)])
            print(f"Open http://127.0.0.1:{args.web_port} and click Start. Ctrl+C closes the dashboard.",flush=True)
        else:
            cmd.extend(["--headless","--csv",str(case/"requests"),"--csv-full-history","--html",str(case/"report.html")])
        for name,value in (("--speed",args.speed),("--poll-seconds",args.poll_seconds),
                           ("--seed",args.seed),("--game-config",args.game_config.resolve() if args.game_config else None)):
            if value is not None:
                cmd.extend([name,str(value)])
        if args.scale_polling:
            cmd.append("--scale-polling")
        if args.no_connection_monitor:
            cmd.append("--no-connection-monitor")
        print(f"Running {scenario}: {args.players} participants; outputs: {case}",flush=True)
        result=subprocess.run(cmd,cwd=ROOT,env=os.environ.copy(),check=False)
        exit_code=max(exit_code,0 if result.returncode==0 else 1)
        summary_paths=list(case.glob("*/summary.json")) if args.web else [case/"summary.json"]
        found=[json.loads(p.read_text(encoding="utf-8")) for p in summary_paths if p.exists()]
        summaries.extend(found)
        if not args.web and not found:
            exit_code=1
        if any(d["failure"] or d["missing_endpoints"] or d["completed"]!=d["players"] for d in found):
            exit_code=1
    if args.scenario=="coverage":
        from model import ALL_ENDPOINTS
        called={endpoint for summary in summaries for endpoint in summary["endpoint_calls"]}
        missing=sorted(ALL_ENDPOINTS-called)
        (output/"coverage.json").write_text(json.dumps({"called":sorted(called),"missing":missing,
            "complete":not missing and len(summaries)==len(cases)},indent=2),encoding="utf-8")
        if missing or len(summaries)!=len(cases):
            exit_code=1
    print(f"Finished. Reports: {output}")
    return exit_code


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
