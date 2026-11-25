"""Read-only local TCP sampling, isolated from Locust's request scheduler."""
from __future__ import annotations

import csv
import ipaddress
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit

LOG = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent


def local_target(url):
    parsed = urlsplit(url)
    host = parsed.hostname
    if host != "localhost":
        try:
            if not ipaddress.ip_address(host).is_loopback:
                return None
        except (ValueError, TypeError):
            return None
    return host, parsed.port or (443 if parsed.scheme == "https" else 80)


def summarize_connections(connections, host, port):
    """Count only server-side rows owned by matching TCP listeners."""
    def matches(address):
        if not address or address.port != port:
            return False
        ip = ipaddress.ip_address(address.ip.split("%")[0])
        return ip.is_unspecified or (ip.is_loopback if host == "localhost" else str(ip) == host)

    pids = {c.pid for c in connections if c.status == "LISTEN" and matches(c.laddr) and c.pid is not None}
    states = Counter(c.status for c in connections
                     if c.pid in pids and c.status != "LISTEN" and matches(c.laddr))
    # TIME_WAIT is a kernel-managed closed connection, not an accepted HTTP channel.
    open_count = sum(n for state, n in states.items() if state not in ("TIME_WAIT", "CLOSED", "DELETE_TCB"))
    return {"listener_pids": sorted(pids), "open_connections": open_count if pids else None,
            "established": states["ESTABLISHED"] if pids else None,
            "close_wait": states["CLOSE_WAIT"] if pids else None, "states": dict(states)}


def write_summary(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)


def sample_run(output, host, port, started_epoch, interval=1.0):
    import psutil
    summary_path = output / "connection_monitor.json"
    stop_path = output / "connection_monitor.stop"
    summary = {"status": "running", "target_host": host, "target_port": port,
               "interval_seconds": interval, "samples": 0, "successful_samples": 0,
               "sample_errors": 0, "peak_open_connections": None,
               "peak_open_timestamp_utc": None, "peak_established": None,
               "server_pids_seen": [],
               "measurement": "OS server-side TCP sockets owned by the target listener; approximate HTTP channels, not active requests or Waitress queue depth"}
    fields = ["timestamp_utc", "elapsed_seconds", "sample_duration_ms", "listener_pids",
              "open_connections", "established", "close_wait", "states", "error"]
    with (output / "connections.csv").open("w", newline="", encoding="utf-8", buffering=1) as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        try:
            while True:
                began = time.monotonic()
                now = datetime.now(timezone.utc).isoformat()
                row = {"timestamp_utc": now, "elapsed_seconds": round(time.time()-started_epoch, 3), "error": ""}
                try:
                    snapshot = summarize_connections(psutil.net_connections(kind="tcp"), host, port)
                    row.update(snapshot)
                    summary["successful_samples"] += 1
                    summary["server_pids_seen"] = sorted(set(summary["server_pids_seen"]) | set(snapshot["listener_pids"]))
                    for source, peak in (("open_connections", "peak_open_connections"), ("established", "peak_established")):
                        value = snapshot[source]
                        if value is not None and (summary[peak] is None or value > summary[peak]):
                            summary[peak] = value
                            if source == "open_connections":
                                summary["peak_open_timestamp_utc"] = now
                    summary["last_observation"] = snapshot
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"
                    summary["sample_errors"] += 1
                    summary["last_error"] = row["error"]
                row["sample_duration_ms"] = round((time.monotonic()-began)*1000, 2)
                summary["samples"] += 1
                summary["last_sample_timestamp_utc"] = now
                csv_row = dict(row)
                for key in ("listener_pids", "states"):
                    if key in csv_row:
                        csv_row[key] = json.dumps(csv_row[key])
                writer.writerow(csv_row)
                target.flush()
                write_summary(summary_path, summary)
                if stop_path.exists() or os.getppid() == 1:
                    break
                time.sleep(max(0.01, interval-(time.monotonic()-began)))
        finally:
            summary["status"] = "stopped"
            write_summary(summary_path, summary)


class ConnectionMonitor:
    def __init__(self, output, url, enabled=True):
        self.output = output
        self.process = None
        self.errors = None
        self.closed = False
        self.metadata = {"status": "not_started"}
        self.url = url
        self.enabled = enabled

    def start(self):
        target = local_target(self.url)
        if not self.enabled or target is None:
            self.metadata = {"status": "disabled" if not self.enabled else "skipped_remote_target"}
            write_summary(self.output / "connection_monitor.json", self.metadata)
            return
        try:
            self.errors = (self.output / "connection_monitor.log").open("w", encoding="utf-8")
            self.metadata = {"status": "starting", "interval_seconds": 1.0,
                             "target_host": target[0], "target_port": target[1]}
            write_summary(self.output / "connection_monitor.json", self.metadata)
            # Import gevent's cooperative wrapper only in the Locust parent.
            from gevent import subprocess as cooperative
            self.process = cooperative.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), str(self.output),
                 target[0], str(target[1]), str(time.time()), str(os.getpid())],
                stdout=subprocess.DEVNULL, stderr=self.errors,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception as exc:
            self.metadata = {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}
            write_summary(self.output / "connection_monitor.json", self.metadata)
            LOG.warning("Connection monitoring unavailable: %s", exc)
            if self.errors:
                self.errors.close()

    def report(self):
        try:
            result = json.loads((self.output / "connection_monitor.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = self.metadata
        if self.process and self.process.poll() not in (None, 0):
            result = {**result, "status": "unavailable", "exit_code": self.process.returncode,
                      "diagnostics": "connection_monitor.log"}
        return result

    def stop(self):
        if self.closed:
            return
        self.closed = True
        if self.process:
            (self.output / "connection_monitor.stop").touch()
            try:
                self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=3)
            if self.process.returncode != 0:
                LOG.warning("Connection monitor exited with code %s; see connection_monitor.log", self.process.returncode)
                write_summary(self.output / "connection_monitor.json", self.report())
            self.errors.close()
            (self.output / "connection_monitor.stop").unlink(missing_ok=True)


if __name__ == "__main__":
    # A parent-process handle detects abrupt Locust exits, including on Windows.
    import psutil
    output = Path(sys.argv[1]).resolve()
    if not output.is_relative_to(ROOT):
        raise SystemExit("Monitor output must remain inside load_tests")
    parent = psutil.Process(int(sys.argv[5]))
    import threading
    def watch_parent():
        parent.wait()
        (output / "connection_monitor.stop").touch()
    threading.Thread(target=watch_parent, daemon=True).start()
    sample_run(output, sys.argv[2], int(sys.argv[3]), float(sys.argv[4]))
