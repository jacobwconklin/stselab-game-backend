"""Frontend-style timer guards, cycle cancellation, and old-round suppression."""
from verify import GameUser, settings, Counter, SimpleNamespace, gevent, unittest, patch, BackendAdapter, ROOT
from gevent.pool import Group
from workflow import PollCancelled


class GuardedPollingTests(unittest.TestCase):
    def setUp(self):
        self.user=object.__new__(GameUser)
        self.records=[]
        self.user.session=SimpleNamespace(
            config=settings(poll_seconds=.025),metrics=Counter(),join_code=123,
            abort=lambda message:self.fail(message))
        self.user.stop_timers=False
        self.user.ended=False
        self.user.onboarded=False
        self.user.round=0
        self.user.index=0
        self.user.controller_version=0
        self.user.survey_version=0
        self.user.survey_counts=(None,None)
        self.user.active_poll_cycles=0
        self.user.pending=Group()
        self.user.note=lambda event,**values:self.records.append((event,values))
        self.timers=Group()

    def tearDown(self):
        self.user.stop_timers=True
        self.timers.kill()
        self.user.pending.kill()

    def test_slow_cycle_skips_busy_ticks(self):
        active=0
        maximum=0
        calls=[]
        def tick(kind):
            nonlocal active,maximum
            active+=1
            maximum=max(maximum,active)
            calls.append(kind)
            try:gevent.sleep(.11)
            finally:active-=1
        self.user.tick=tick
        self.timers.spawn(self.user.timer,"controller")
        gevent.sleep(.21)
        self.assertEqual(maximum,1)
        self.assertGreater(self.user.session.metrics["skipped_busy_polls"],0)
        self.assertEqual(len(calls),2)

    def test_frontend_timeout_and_default_interval_match(self):
        import re
        import workflow
        source=(ROOT.parent.parent/"frontend/src/Utils/Polling.ts").read_text(encoding="utf-8")
        timeout=int(re.search(r"timeoutMs\s*=\s*(\d+)",source)[1])
        interval=int(re.search(r"intervalMs\s*=\s*(\d+)",source)[1])
        self.assertEqual(workflow.POLL_CYCLE_TIMEOUT,timeout/1000)
        self.assertEqual(settings()["poll_seconds"],interval/1000)

    def test_separate_pollers_can_run_concurrently(self):
        self.user.tick=lambda kind:gevent.sleep(.12)
        for kind in ("controller","lobby"):
            self.timers.spawn(self.user.timer,kind)
        gevent.sleep(.08)
        self.assertEqual(self.user.active_poll_cycles,2)
        self.assertEqual(self.user.session.metrics["peak_active_poll_cycles"],2)

    def test_effect_change_cancels_old_cycle_before_replacement(self):
        completed=[]
        def tick(kind):
            version=self.user.controller_version
            gevent.sleep(.15)
            completed.append(version)
        self.user.tick=tick
        self.timers.spawn(self.user.timer,"controller")
        gevent.sleep(.06)
        self.user.controller_version+=1
        gevent.sleep(.21)
        self.assertNotIn(0,completed)
        self.assertEqual(completed,[1])
        self.assertGreaterEqual(self.user.session.metrics["cancelled_polls"],1)
        self.assertEqual(self.user.session.metrics["peak_active_poll_cycles"],1)

    def test_unmount_cancels_waiting_lobby_response(self):
        completed=[]
        def tick(kind):
            gevent.sleep(.15)
            completed.append(kind)
        self.user.tick=tick
        self.timers.spawn(self.user.timer,"lobby")
        gevent.sleep(.06)
        self.user.round=1
        self.user.onboarded=True
        gevent.sleep(.16)
        self.assertEqual(completed,[])
        self.assertEqual(self.user.active_poll_cycles,0)
        self.assertEqual(self.user.session.metrics["cancelled_polls"],1)

    def test_cycle_timeout_releases_lock_and_recovers(self):
        calls=[]
        def tick(kind):
            calls.append(kind)
            if len(calls)==1:gevent.sleep(1)
        self.user.tick=tick
        with patch("workflow.POLL_CYCLE_TIMEOUT",.06):
            self.timers.spawn(self.user.timer,"controller")
            gevent.sleep(.16)
        self.assertEqual(self.user.session.metrics["poll_timeouts"],1)
        self.assertGreaterEqual(len(calls),2)
        self.assertEqual(self.user.session.metrics["peak_active_poll_cycles"],1)

    def test_round_change_does_not_request_previous_results(self):
        self.user.round=1
        self.user.player_id="test-player"
        self.user.removal_requested=False
        self.user.finished_rounds={1}
        self.user.golf_result_count=0
        calls=[]
        def request(endpoint,*args,**kwargs):
            calls.append(endpoint)
            return {"session":{"round":2,"endDate":None}}
        self.user.request=request
        self.user.tick("controller")
        self.assertEqual(calls,["session/status"])
        self.assertEqual(self.user.round,2)

    def test_guard_does_not_cancel_background_writes(self):
        saved=[]
        def save():
            gevent.sleep(.13)
            saved.append(True)
        self.user.pending.spawn(save)
        self.user.tick=lambda kind:gevent.sleep(.2)
        self.timers.spawn(self.user.timer,"controller")
        gevent.sleep(.06)
        self.user.controller_version+=1
        gevent.sleep(.1)
        self.assertEqual(saved,[True])

    def test_one_timeout_budget_covers_the_whole_cycle(self):
        completed=[]
        def tick(kind):
            gevent.sleep(.04)  # First request.
            gevent.sleep(.04)  # Second request must not receive a fresh budget.
            completed.append(True)
        self.user.tick=tick
        with patch("workflow.POLL_CYCLE_TIMEOUT",.06):
            self.user.poll_cycle("controller")
        self.assertEqual(completed,[])
        self.assertEqual(self.user.session.metrics["poll_timeouts"],1)

    def test_real_delayed_http_response_is_cancelled_without_stale_update(self):
        from locust.clients import HttpSession
        from locust.event import EventHook
        backend=BackendAdapter(status_delay=.2)
        try:
            backend.db.execute("INSERT INTO Session (JoinCode,Round) VALUES (123,1)")
            backend.db.execute("INSERT INTO PlayerBrief (Id,SessionId) VALUES ('test-player',123)")
            self.user.host=backend.url
            self.user.client=HttpSession(backend.url,EventHook(),None)
            self.user.player_id="test-player"
            self.user.removal_requested=False
            self.user.session.coverage=Counter()
            self.user.session.phase_calls=Counter()
            self.user.session.config["origin"]=""
            with patch("workflow.POLL_CYCLE_TIMEOUT",.06):
                self.user.poll_cycle("controller")
            self.assertEqual(self.user.round,0)
            self.assertEqual(self.user.session.metrics["poll_timeouts"],1)
            self.assertEqual(self.records[-1][1]["request"],{
                "method":"POST","endpoint":"session/status"})
            self.user.client.close()
        finally:
            backend.close()


if __name__=="__main__":
    unittest.main(verbosity=2)
