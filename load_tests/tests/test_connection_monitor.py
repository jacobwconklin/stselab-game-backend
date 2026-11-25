"""Socket attribution, unknown/error handling, and real monitor lifecycle."""
import csv
import json
from pathlib import Path
import socket
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from connection_monitor import ConnectionMonitor, local_target, sample_run, summarize_connections


def connection(port, status="ESTABLISHED", pid=10, ip="127.0.0.1"):
    return SimpleNamespace(laddr=SimpleNamespace(ip=ip, port=port), status=status, pid=pid)


class ConnectionMonitorTests(unittest.TestCase):
    def test_only_local_origins_are_eligible(self):
        self.assertEqual(local_target("http://127.0.0.1:5000"), ("127.0.0.1", 5000))
        self.assertEqual(local_target("https://[::1]"), ("::1", 443))
        self.assertEqual(local_target("http://localhost"), ("localhost", 80))
        self.assertIsNone(local_target("https://example.com"))
        self.assertIsNone(local_target("http://192.168.1.5:5000"))

    def test_server_attribution_excludes_clients_other_processes_and_time_wait(self):
        rows = [connection(5000, "LISTEN", ip="0.0.0.0"), connection(5000),
                connection(5000, "CLOSE_WAIT"), connection(5000, "TIME_WAIT"),
                connection(5000, pid=99), connection(5001), connection(55000),
                connection(5000, ip="127.0.0.2")]
        result = summarize_connections(rows, "127.0.0.1", 5000)
        self.assertEqual(result["open_connections"], 2)
        self.assertEqual(result["established"], 1)
        self.assertEqual(result["close_wait"], 1)
        self.assertEqual(result["states"]["TIME_WAIT"], 1)

    def test_missing_listener_is_unknown_not_zero(self):
        self.assertIsNone(summarize_connections([connection(5000)], "127.0.0.1", 5000)["open_connections"])

    def test_ipv6_and_listener_pid_changes(self):
        rows = [connection(5000, "LISTEN", 20, "::"), connection(5000, pid=20, ip="::1")]
        self.assertEqual(summarize_connections(rows, "::1", 5000)["listener_pids"], [20])
        self.assertEqual(summarize_connections(rows, "localhost", 5000)["open_connections"], 1)

    def test_remote_and_disabled_runs_save_explicit_status_without_process(self):
        with tempfile.TemporaryDirectory(dir=ROOT/".tmp") as directory:
            for url, enabled, status in [("https://example.com", True, "skipped_remote_target"),
                                         ("http://localhost:5000", False, "disabled")]:
                monitor = ConnectionMonitor(Path(directory), url, enabled)
                monitor.start()
                self.assertIsNone(monitor.process)
                self.assertEqual(monitor.report()["status"], status)
                monitor.stop()
                monitor.stop()

    def test_sample_error_is_saved_without_fabricating_a_count(self):
        with tempfile.TemporaryDirectory(dir=ROOT/".tmp") as directory:
            output = Path(directory)
            (output/"connection_monitor.stop").touch()
            with patch("psutil.net_connections", side_effect=PermissionError("test denial")):
                sample_run(output, "127.0.0.1", 5000, time.time())
            report = json.loads((output/"connection_monitor.json").read_text())
            self.assertEqual(report["sample_errors"], 1)
            self.assertIsNone(report["peak_open_connections"])
            with (output/"connections.csv").open(newline="") as source:
                row = next(csv.DictReader(source))
            self.assertEqual(row["open_connections"], "")
            self.assertIn("PermissionError", row["error"])

    def test_live_child_counts_server_side_once_and_stops_cleanly(self):
        with tempfile.TemporaryDirectory(dir=ROOT/".tmp") as directory, socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            clients = [socket.create_connection(("127.0.0.1", port)) for _ in range(2)]
            accepted = [listener.accept()[0] for _ in clients]
            monitor = ConnectionMonitor(Path(directory), f"http://127.0.0.1:{port}")
            try:
                monitor.start()
                deadline = time.monotonic()+10
                while time.monotonic()<deadline and monitor.report().get("samples", 0)<2:
                    time.sleep(.1)
                self.assertEqual(monitor.report().get("peak_established"), 2, monitor.report())
                self.assertEqual(monitor.report()["peak_open_connections"], 2)
                monitor.stop()
                self.assertEqual(monitor.report()["status"], "stopped")
                self.assertEqual(monitor.process.returncode, 0)
                self.assertFalse((Path(directory)/"connection_monitor.stop").exists())
            finally:
                monitor.stop()
                for sock in clients+accepted:
                    sock.close()


if __name__ == "__main__":
    (ROOT/".tmp").mkdir(exist_ok=True)
    unittest.main()
