# STSE game Locust suite

All test code, configuration, environment, caches, logs, and reports belong under:

`E:\vscodeStuff\stse_game\backend\load_tests`

Nothing here changes application code, frontend code, production dependencies, or database schema. Runs use the existing public game API and create synthetic player/session/result rows. Only the offline verifier has been run during implementation; no deployed game or production database was contacted.

## What it does

- One host and the remaining players join the same newly created session. `--players 100` means **100 total**, including the host.
- A finite, ordered journey follows all game stages, with independent status/lobby/survey timers, real host advancement, and result polling while others finish.
- Normal speed models an estimated **30–45-minute full lesson**, with randomized reading, decisions, exploration, questionnaires, and review. It is an estimate; group size, slower individuals, network delay, and host waiting can extend it.
- Seeded randomness varies player pace, actions, choices, answers, and exploration attempts. A seed makes choices comparable; scheduling and server-generated UUIDs still prevent bit-identical HTTP traces.
- Node reads/transpiles the existing frontend simulation/scoring functions in memory to produce actual payloads. No simulated score tables or replacement arm model are installed in the application.
- Response validation catches application errors returned with HTTP 200. Host readiness uses the scores/survey counts it receives from the API, so missing saved results cannot be hidden by local bookkeeping.
- Completion/incomplete journeys, missing expected endpoints, timeouts, unexpected application errors, or poll-overflow produce a nonzero exit status.

See `COVERAGE.md` for the **19-endpoint inventory**, branch coverage, current frontend quirks, and fidelity limitations. This is HTTP load testing; browser rendering/assets need separate profiling.

## Prerequisites

1. Working Python **3.10+** (3.12 used for verification), Node.js on PATH, and the existing frontend dependencies already installed. The bridge reads the frontend's TypeScript and random-normal packages. If those packages are absent, the prerequisite is a normal frontend dependency installation by the project maintainer; this suite does not install or edit anything there.
2. A separately running **local or staging** backend and a disposable MySQL database with the complete current game schema. Point that backend's existing configuration at the disposable DB yourself. The suite never reads `environmentSecrets.py` or makes direct database connections.
3. The supplied Docker initialization creates databases only. Check the real schema before running: in particular `/player/freeRoamResult` requires `TimeStamp`. Updating the SQL definition does not alter an existing database table. Do not mistake schema/configuration failures for performance failures.

The backend's existing virtual environment on this machine points to an unavailable Python installation. The suite has its own independent environment and does not repair that backend environment.

## Install (PowerShell)

```powershell
Set-Location 'E:\vscodeStuff\stse_game\backend\load_tests'
.\setup.ps1
```

If `python` is not a working interpreter, pass its absolute executable:

```powershell
.\setup.ps1 -Python 'C:\Path\To\Python312\python.exe'
```

Setup creates `.venv` here and installs Locust from this folder's `requirements.txt`. It puts installer cache/temp locations here too. No environment activation is required for the commands below. This checkout already has a test-only environment installed during verification.

`requirements-windows.lock.txt` records the exact dependency versions in the verified Windows environment. To reproduce it in this test environment, install that file instead of `requirements.txt`; it contains Windows-specific packages and is not a Linux lockfile.

## Verify the driver without a game server or MySQL

```powershell
.\.venv\Scripts\python.exe -B .\tests\verify.py
```

The verifier starts its own loopback-only server with extracted handler functions and an in-memory database adapter. It runs all profiles and checks persisted round results, duplicate submissions, dice gating/two-step offboarding, host transitions, removal, CORS traffic, error handling, and overlapping polls. Artifacts stay in `results\verification-*`. This is not a capacity benchmark. See `COVERAGE.md` for adapter limitations.

For the batched session queries, also run the response-regression and constant-query-count checks:

```powershell
.\.venv\Scripts\python.exe -B .\tests\test_batched_queries.py
```

These compare 22 response cases captured before batching, check all six handlers at 1, 5, 100, and 500 players, and cover bound player IDs and case-insensitive ID matching. They also use only a disposable SQLite database.

## Run a representative session

First start your independently configured test backend. Then:

```powershell
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --players 100
```

No production URL is a default. The launcher requires an explicit target and automatically stops when all participants have finished or the session deadline fails. Do not use it against production without the service owner's authorization: it writes synthetic research records.

### Run from the browser dashboard

```powershell
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --web --players 5 --speed 10
```

Open **http://127.0.0.1:8089** in your browser. No game requests are sent until you click **Start**. On the start form:

- **Number of users:** total participants including one host. Start small (for example 5).
- **Spawn rate:** how many simulated users start each second (for example 1 or 5).
- **Host:** the backend URL, not the dashboard URL.
- **Scenario:** choose `full`, `golf-only`, `arm-only`, or `departures`.
- **Speed:** human-time multiplier; use 1 for normal pacing or 10 for ten times faster. Blank uses configuration defaults.

Live Statistics, Charts, Failures, and Downloads are provided by Locust. A completed journey automatically stops the load while **keeping the dashboard open**. You can then start another test with different users, speed, or scenario. Stop an active game before starting a new one; mid-game resizing is rejected because it breaks this workflow's classroom-completion rules. At least two users are required, or three for departures. Leave any time-limit field blank to allow the full journey; stopping early is saved as an incomplete run.

Each dashboard test gets a separate timestamped directory under `results\<launch>\dashboard\`, including HTML, CSV/history, manifest, summary, and journey logs. Previous runs are preserved. The launch-wide `locust.log` sits in the dashboard parent folder. **Ctrl+C** in the terminal closes the dashboard. Use `--web-port 8090` if 8089 is already occupied. The server binds only to the local machine.

Polling remains at the configured real interval unless the launcher was given `--scale-polling`. Advanced settings such as polling, seed, and configuration-file path are supplied on the command line. Automatic `--scenario coverage` remains headless; in the dashboard, select its four scenarios individually.

### Speed control

```powershell
# Human actions ten times faster; polling stays every 2.5 seconds.
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --players 100 --speed 10

# Half-speed human actions, leaving more time for reading/exploration.
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --players 100 --speed 0.5

# Explicitly accelerate polling as well: 2.5 / 10 = 0.25 seconds.
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --players 100 --speed 10 --scale-polling
```

`--speed` divides human/UI waits, including the simulated 2.8005-second golf animation. It does not divide actual HTTP/database latency, request deadlines, CORS cache lifetime, or the real wall-clock session deadline. `--scale-polling` deliberately increases backend pressure and is a distinct stress workload. Fixed polling and round-propagation overhead mean a 10x speed setting does not guarantee exactly one tenth the total run duration.

### Scenarios and all-endpoint coverage

```powershell
# Normal lobby → full golf → arm mission → final offboarding/history.
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --players 100 --scenario full

# All branches in four separate, sequential sessions.
.\.venv\Scripts\python.exe -B .\run.py --host http://127.0.0.1:5000 --players 10 --scenario coverage --speed 30
```

| Scenario | Behavior |
|---|---|
| `full` (default) | Complete golf and arm workflow |
| `golf-only` | End after golf final results/offboarding |
| `arm-only` | Host chooses the real lobby shortcut into the arm mission |
| `departures` | Full workflow with one self-exit and one host kick in the lobby; at least three players required |
| `coverage` | Launcher runs all four above and checks the union covers every game endpoint |

The skip-golf endpoint cannot belong to a session that also plays all golf rounds. Full endpoint coverage therefore means **the suite**, not artificial calls inserted into an incompatible normal journey. Profiles other than `departures` maintain their advertised population. Departures retains `players - 2` active participants.

### Other controls

- `--spawn-rate 5`: Locust users started per second; real registration submissions also have randomized reading/filling delay. Spawn rate is not the HTTP request rate.
- `--seed 12345`: comparable randomized choices and pacing.
- `--poll-seconds 2.5`: override the unscaled timer interval. Use lower values only when intentionally testing a different workload.
- `--game-config <path>`: JSON overrides; missing settings inherit from `config.json`. Paths are read-only inputs.
- `--output <path>`: choose a fresh output directory **inside load_tests**; outside paths and existing directories are rejected.

`config.json` contains `[minimum, mode, maximum]` seconds for each human activity. Values are triangular samples multiplied by a per-player pace factor (bounded 0.75–1.35), then divided by speed. Survey and offboarding waits are longer than simple choices. Architecture/solver choices are randomized; exploration repeats with varied choices.

Example custom overrides, saved as `quick.json` inside this folder:

```json
{
  "speed": 10,
  "archive_probability": 0.4,
  "max_session_seconds": 3600,
  "request_timeout": 20,
  "origin": "http://localhost:3000",
  "timings": {
    "survey": [60, 100, 180],
    "golf_exploration": [180, 240, 360]
  }
}
```

For staging, set `origin` to the actual frontend origin. Null disables OPTIONS/CORS emulation for API-only isolation. Default JSON preflight cache is five real seconds unless the backend supplies a max-age. No source API query is made for charts, local arm exploration, printing, or downloading results because those actions run in the browser.

## Results and interpretation

Each profile's output directory contains:

- `report.html`: Locust's interactive static report, endpoint response times and failures.
- `requests_stats.csv`, `requests_stats_history.csv`, `requests_failures.csv`, `requests_exceptions.csv`: native Locust exports, including percentile response times and throughput.
- `manifest.json`: target, effective configuration, seed, population, runtime versions, and SHA-256 fingerprints of frontend/backend sources used for the run. Error-reporting version 2 also fingerprints the load-test code, default configuration, and dependency lists.
- `summary.json`: session/player IDs, completed journeys, endpoint coverage and counts by game round, host transitions, poll counts/overflow, simulation overhead, and failure reason.
- `journey.jsonl`: chronological registration, observed stage changes, completed actions, host advances, departures, and errors.
- `locust.log`, `simulation-stderr.log`: driver and frontend-calculation diagnostics.

The coverage launcher also writes `coverage.json` with called/missing endpoints across its profiles. Failed runs retain their artifacts for inspection. It never reports a partial journey as a completed test.

Compare fixed populations in separate fresh runs (10, 25, 50, 75, 100, 150, 200), using the same timings/seed, dataset history, deployment, and polling policy. Completed throughput can drop when the server slows: inspect scheduled/started/completed polls, peak pending requests, timeouts, and overflow as well as averages. Initial registration and final-results bursts should be examined separately from steady polling. This suite does not instrument production SQL, worker queues, or browser frame times; gather those measurements alongside it.

### Error details and comparisons with earlier runs

Error-reporting version 2 checks for an underlying connection exception before validating JSON or CORS. Native Locust failure reports retain the original transport exception. Failed HTTP responses retain their status; a successful HTTP response with missing CORS permissions remains a CORS failure. Each failed POST, GET, or OPTIONS also adds a `request_error` entry to `journey.jsonl` with UTC time, method, endpoint, player, round, failure kind, HTTP status, selected response headers, response size, and a body preview limited to the first 1,024 bytes. Transport failures include the exception type and chain; HTTP status `0` is Locust's placeholder when no usable HTTP response was received, not a status sent by Flask.

Earlier reports remain useful baseline measurements of request counts, response times, failures, and journey completion. Their generic `Invalid JSON contract` and `CORS preflight would block the browser request` messages may conceal transport errors; the original exception cannot be recovered from those reports. Error categories should not be compared directly across reporting versions. A failed run measures only the stages reached, not full-game capacity, and its latency percentiles include failed requests.

This reporting correction does not change endpoint selection, payloads, pacing/randomness, polling, timeout values, preflight caching, retries, or stop conditions. It records extra details on failures, so small differences in failure-heavy runs are possible. Preserve the old reports, and repeat the unoptimized backend with the corrected test driver before making application changes for the strongest before/after comparison. Compare the same stages and population, with matching speed, polling, spawn rate, dataset, and server setup. New manifests identify the reporting version and exact load-test sources; keep that version fixed while evaluating optimizations.

There is **one coordinated room per Locust process**. Multiprocess/distributed execution is explicitly rejected. Use a separate invocation/output folder for an independent room. Do not change the number of users midway through a journey; it changes group completion semantics. The headless launcher automatically keeps `--users` equal to `--players` and parks completed users until the entire room finishes, preventing an accidental new player/session loop.

## Data retention and cleanup

Runs create new synthetic sessions and persist their results, just like real gameplay. Names are prefixed `LT-<run-id>-<index>` and IDs are recorded in the manifest/summary. There is no public API to delete a session and all child research records. `/player/remove` only clears membership; it is not database cleanup. No automatic direct-SQL cleanup or migration is performed. Use a disposable database, snapshot restoration, or an owner-approved cleanup outside this suite. Keep database size comparable when evaluating improvements.

## Source references

- Frontend controller: `E:\vscodeStuff\stse_game\frontend\src\Pages\GameController\GameController.tsx`
- API helper: `E:\vscodeStuff\stse_game\frontend\src\Utils\Api.ts`
- Round enum/scoring: `E:\vscodeStuff\stse_game\frontend\src\Utils\Utils.ts`
- Backend routing: `E:\vscodeStuff\stse_game\backend\app.py`
- Handler implementations: `E:\vscodeStuff\stse_game\backend\users.py`, `E:\vscodeStuff\stse_game\backend\session.py`
- Locust: https://docs.locust.io/en/stable/writing-a-locustfile.html
