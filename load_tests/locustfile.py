"""Run through run.py to keep environment, caches, and reports in this folder."""
import logging
from locust import events
from locust.runners import MasterRunner, WorkerRunner, STATE_INIT, STATE_STOPPED

from model import PROFILES, ROOT, inside
from workflow import GameUser, Session


@events.init_command_line_parser.add_listener
def arguments(parser, **_):
    parser.add_argument("--players", type=int, default=100, include_in_web_ui=False, help="Total participants, INCLUDING one host; must equal --users in headless mode")
    parser.add_argument("--scenario", choices=PROFILES, default="full")
    parser.add_argument("--speed", type=float, default=None, help="Human-time multiplier: 10 is ten times faster")
    parser.add_argument("--scale-polling", action="store_true", default=None, include_in_web_ui=False, help="Also divide 2.5s polling by --speed")
    parser.add_argument("--poll-seconds", type=float, default=None, include_in_web_ui=False)
    parser.add_argument("--seed", type=int, default=None, include_in_web_ui=False)
    parser.add_argument("--game-config", default=None, include_in_web_ui=False, help="JSON overrides; config.json supplies defaults")
    parser.add_argument("--output", default=None, include_in_web_ui=False, help="Output directory, constrained to load_tests")
    parser.add_argument("--no-connection-monitor", action="store_true", include_in_web_ui=False,
                        help="Disable automatic local server TCP connection sampling")


@events.init.add_listener
def guard_web_changes(environment, **_):
    if not environment.web_ui:
        return
    from flask import request, jsonify, g

    @environment.web_ui.app.before_request
    def validate_start():
        if request.path=="/stop" and request.method=="POST":
            environment.game_start_requested=False
            return None
        if request.path!="/swarm" or request.method!="POST":
            return None
        session=getattr(environment,"game_session",None)
        starting=getattr(environment.web_ui,"_swarm_greenlet",None)
        if (getattr(environment,"game_start_requested",False) or session and not session.closed or
                environment.runner.state not in (STATE_INIT,STATE_STOPPED) or
                starting is not None and not starting.ready()):
            return jsonify(success=False,message="Stop or finish the current game before starting another; resizing an active classroom is unsupported"),400
        try:
            count=int(request.form.get("user_count","0"))
            scenario=request.form.get("scenario",environment.parsed_options.scenario)
            if scenario not in PROFILES:
                raise ValueError("Choose a supported game scenario")
            minimum=3 if scenario=="departures" else 2
            if count<minimum:
                raise ValueError(f"This scenario needs at least {minimum} users, including one host")
            raw=request.form.get("speed")
            if raw not in (None,"","None","null"):
                from model import settings
                settings(speed=float(raw))
        except (TypeError,ValueError) as exc:
            return jsonify(success=False,message=str(exc)),400
        environment.game_start_requested=True
        g.game_start_request=True
        return None

    @environment.web_ui.app.after_request
    def reset_rejected_start(response):
        if getattr(g,"game_start_request",False):
            data=response.get_json(silent=True)
            if not data or not data.get("success"):
                environment.game_start_requested=False
        return response


@events.test_start.add_listener
def start(environment, **_):
    try:
        opts=environment.parsed_options
        if isinstance(environment.runner,(MasterRunner,WorkerRunner)) or getattr(opts,"processes",None):
            raise ValueError("This coordinated session uses one Locust process; distributed execution is explicitly unsupported")
        if environment.web_ui:
            opts.players=int(opts.num_users or 0)
            # Nullable custom values submitted by Locust's form arrive as strings.
            if opts.speed in (None,"","None","null"):
                opts.speed=None
            else:
                opts.speed=float(opts.speed)
        if int(opts.num_users or 0)!=opts.players:
            raise ValueError("--users must equal --players, including the host")
        for name in ("html_file","csv_prefix","logfile"):
            value=getattr(opts,name,None)
            if value:
                inside(value)
        environment.process_exit_code=None
        environment.game_session=Session(environment)
        logging.info("Game workflow started: %s",environment.game_session.output)
    except Exception as exc:
        environment.game_start_requested=False
        logging.exception("Cannot start game workflow: %s",exc)
        environment.process_exit_code=1
        import gevent
        gevent.spawn(environment.runner.stop if environment.web_ui else environment.runner.quit)


@events.test_stop.add_listener
def stop(environment, **_):
    session=getattr(environment,"game_session",None)
    if session:
        session.close()
