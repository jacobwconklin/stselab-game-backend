# Verification record

Verified November 11, 2026 on Windows with Python 3.12, Node v24.12.0, the frontend's TypeScript 4.9.5, and Locust 2.47.0. The exact Python dependency versions are recorded in `requirements-windows.lock.txt`.

Command, run from `E:\vscodeStuff\stse_game\backend\load_tests`:

```powershell
.\.venv\Scripts\python.exe -B .\tests\verify.py
```

Final result: **8 tests passed**. The verification run's artifacts are in `results\verification-20261111T200433997395`.

- The source scan found all **19** frontend game API endpoints represented in the suite.
- The coverage run completed `full`, `golf-only`, `arm-only`, and `departures`, with six participants per profile, a new session per profile, and no missing expected endpoints.
- Persisted golf rounds were exactly 1, 3, 6, 7, 8, and 9 where applicable; arm rounds were 12–15. No accidental duplicate round submissions occurred.
- Onboarding followed actual host UUID parity and undefined joiner-flag behavior. Eligible offboarding produced two inserts per final-results stage, including separate golf and arm offboarding in a full game.
- Normal host transitions, the jump-to-arm shortcut, both removal paths, end-session behavior, and archive retrieval completed through HTTP calls to the existing handler definitions.
- Payload checks exercised actual frontend golf and arm calculations, unit conversions, and dice budgets/probabilities. Returned round and final scores were checked against submitted values.
- A scheduler check confirmed that increasing human speed retains the default polling interval, while explicitly scaling polling increases timer frequency.
- An injected HTTP 200 application error produced the expected nonzero test-run status.
- Deliberately slow polls overlapped; reaching the configured pending-poll cap failed the run rather than silently understating offered load.

These are functional checks of the load-test implementation. The verifier uses a local, disposable HTTP server and an in-memory SQLite adapter around extracted backend handlers. It does not import production configuration or connect to MySQL. Its schema/dialect substitutions are described in `COVERAGE.md`. It establishes neither deployed MySQL compatibility nor capacity at 100 players.

The timing defaults were also checked with an approximate human-time model across 100 synthetic 100-person cohorts: median about 41.5 minutes, sampled range about 38–45 minutes, before real request/poll-propagation overhead. This is a planning estimate, not an observed classroom duration or full-speed deployment benchmark.

Only `backend\load_tests\` was created/modified for this task. Pre-existing changes in backend SQL files and the frontend package lock were preserved. Test installation, caches, temporary files, and generated reports are confined to this folder.

## Browser dashboard verification

After adding `run.py --web`, the expanded suite passed **10 tests**. Artifacts: `results\verification-20261111T202744898042`.

The dashboard test started Locust's real loopback web server, confirmed that no game calls occurred before Start, rejected an invalid one-user session and an overlapping Start, completed an arm-only game with four participants, kept the dashboard available, and then completed a full game with five participants in the same dashboard process. Each session retained its own HTML, CSV/history, manifest, summary, and journey output. The launcher check also confirmed browser mode omits `--headless` and binds to the local machine. Existing headless coverage and error/overlap tests still pass.

Verification used HTTP requests to the dashboard's own control endpoints, not a browser rendering test or a deployed game/database.

## Error-reporting correction

On November 11, 2026, the expanded suite passed **18 tests**. Artifacts: `results\verification-20261111T214627648177`.

- Eight new diagnostic checks exercised Locust's actual safe-mode and request-event handling with injected connection resets, read/connect timeouts, HTTP 503 HTML responses, malformed HTTP 200 JSON, missing CORS permissions, and successful cached preflights. They confirmed original transport exceptions and their causes survive into native Locust reports, HTTP status/body details are retained with a bounded preview, critical failures still stop without retry, and application/contract/removal outcomes are preserved.
- Existing complete-profile coverage, persisted game data, polling/overlap checks, and repeat browser-dashboard sessions still passed. Verification used only the disposable loopback server/in-memory adapter; no real game or MySQL load test was run.
- The verifier now checks whether `TimeStamp` already exists before adding the compatibility column to its disposable SQLite database, accommodating the corrected source DDL without editing application SQL.
- An integrity check confirmed **112 existing files** were unchanged: the saved non-verification results/backend log, application-root files, workload model/configuration, launcher, frontend bridge, and dependency lists. Source comparison confirmed the existing game timers, choices, payload generation, and journey actions were unchanged. Production application files were not edited.
- New manifests set `error_reporting_version` to `2` and fingerprint eight load-test source/configuration/dependency files. The generated verification manifest's fingerprints matched the files used.

The correction changes failure classification and adds bounded diagnostic records on failures. Earlier timings, request/failure counts, and completion outcomes remain useful, but older generic JSON/CORS labels do not identify the original transport cause. For a controlled optimization comparison, retain the old reports and repeat the unoptimized application with reporting version 2 before changing the application; hold the driver, workload, data, and server setup fixed thereafter. See `README.md` for comparison guidance.

## Batched session queries — November 16, 2026

Application changes are confined to `backend/session.py`. The shared `_playerRecords` helper fetches related records for the roster in one parameterized query and groups them by the canonical player ID. It joins the roster so grouping preserves database ID comparison semantics, including case-insensitive matching. The normal populated-session query counts are:

| Handler | Before | After |
| --- | --- | --- |
| `playersInSession` | N+2 | 3 |
| `roundResults` | N+1 | 2 |
| `finalResults` | N+1 | 2 |
| `armRoundResults` | N+1 | 2 |
| `armFinalResults` | N+1 | 2 |
| `surveysSubmitted` | N+1 | 2 |

Lobby and survey queries retrieve distinct matching player IDs, counting a player once even when multiple submissions exist. Lobby completion still accepts any dice row, matching the original behavior. Golf final results still include rounds greater than five, while arm final results retain all arm rounds. Players without scores remain present; final results retain empty score arrays. Missing-session/empty-roster responses are preserved. Bulk score rows are explicitly ordered by result ID; round responses select the lowest-ID matching result when duplicate submissions exist. The old SQL did not specify an order.

Verification:

- `tests/test_batched_queries.py`: **4 tests passed**, including exact equality against **22 original response fixtures**, captured before editing the handlers. Fixtures cover empty/missing sessions, other-session/departed players, duplicate dice/survey/score records, practice and tournament filters, missing results, null/zero values, and display text.
- All six handlers used exactly 3/2 application SQL statements at **1, 5, 100, and 500 players**. Parameter-binding checks cover quoted player IDs; an explicit case-insensitive test covers canonical ID grouping.
- `tests/verify.py`: **18 tests passed** after the final changes, including all game profiles, persisted results, repeat browser-dashboard sessions, error reporting, and overlapping polls. Artifacts: `results\verification-20261116T221002551689`.
- The existing SQL fixtures were extended only to support bound parameters and count executed queries. Locust's workload/configuration, request payloads, polling, timeouts, source simulations, and dependency lists were unchanged.

All functional tests use the disposable SQLite adapter and extracted real handlers. A read-only MySQL verification was attempted only against the configured loopback host, but connection failed with code 2003; no MySQL data was changed. These checks do not establish a measured MySQL speedup or player capacity. Restart the actual backend and repeat the saved 1x/30x controls under the same server/database settings to measure those outcomes.

## Guarded frontend polling model — November 17, 2026

Backend branch `new-polling` was created from `n-plus-one-optimization`. Application handlers, database settings, the frontend, and human timing defaults were not changed. The load-test scheduler now skips busy ticks per poller, cancels reads on tracked effect changes/unmounts, applies the frontend's 20-second whole-cycle deadline, and skips old-round results after a round change. Exploration and dice background writes remain independent. New manifests identify polling-model version 2.

- `tests/test_guarded_polling.py`: **10 tests passed**. Checks cover non-overlap, independent pollers, effect replacement, unmount cancellation, deadline recovery, one deadline across sequential requests, no stale round updates, unchanged background writes, and matching frontend interval/timeout constants. A real delayed loopback HTTP response was cancelled without applying its state update.
- `tests/verify.py`: **18 tests passed**, including all profiles, saved game data, browser-dashboard reuse, diagnostic reporting and the outstanding-request cap. Final workflow artifacts: `results\verification-20261117T003451958808`.
- `tests/test_batched_queries.py`: **4 tests passed**; existing query-batching behavior remains intact.
- The timing unit check now explicitly requests speed 1 for its normal-speed reference, so changing the saved default speed does not invalidate the test.

Skipped ticks and client-aborted cycles are reported separately from completed HTTP requests. Poll timeouts invalidate a clean final run even when the journey recovers; normal effect-cleanup cancellations do not. These are local functional checks against a disposable adapter, not a MySQL or production-capacity benchmark. Use the old branch for legacy polling controls and hold backend/server/data settings fixed when comparing the changed client workload.

## Bounded game database connections — November 17, 2026

Branch `connection-pooling` starts at the `new-polling` checkpoint `a285aa4` (`changed load test polling to match new frontend changes`). All 19 game handlers now acquire connections from `database.get_game_connection()`. Existing raw SQL and all 14 explicit commit calls were checked against the parent branch and were unchanged. Nested cleanup returns connections even when cursor cleanup fails. The application dependency is pinned to SQLAlchemy 2.0.58; there are no ORM models, migrations, or database-schema changes.

Defaults: 16 connections per process, zero overflow, five-second checkout timeout, pre-ping validation, recycle on checkout after 1,800 seconds, rollback on return. Creation is lazy/thread-safe; Unix child processes receive a fresh pool without closing parent sockets. Settings and installation are documented in the backend README. New run manifests fingerprint `database.py`; the Locust workload is unchanged.

- `tests/test_connection_pool.py`: **9 tests passed** using the real SQLAlchemy QueuePool and disposable SQLite connections. They cover 100 checkouts reusing one physical connection, pool limits and timeout recovery, exclusive concurrent checkout, one engine initialization, rollback of unfinished writes, persistence of committed writes, stale connection replacement, fork reset, configuration validation, and cleanup in all 19 game handlers.
- A separate read-only check against the configured loopback MySQL used actual PyMySQL dictionary cursors and confirmed two checkouts returned the same MySQL `CONNECTION_ID()`. No user/game data was written.
- Existing suites also passed: **18 workflow tests**, **10 guarded-polling tests**, and **4 query-regression tests**; **41 tests total**. Workflow artifacts: `results\verification-20261117T010137580277`.
- The existing backend virtual environment points to an unavailable Python 3.10 interpreter in this tool environment. Tests ran with the working load-test interpreter and installed pooling test dependencies. Install the new SQLAlchemy dependency in the actual environment used to launch Waitress, then restart the backend.

This verifies behavior and reuse, not an observed performance gain. Compare the same workload, polling model, database data, HTTP server settings and explicit pool limits before drawing throughput/capacity conclusions. Optional pool-test dependencies are in `requirements-pooling.txt`; install them into the test environment before running `tests/test_connection_pool.py`.

## Automatic local TCP monitoring — November 17, 2026

All changes for monitoring are confined to `load_tests`. Local runs automatically start a separate read-only psutil sampler and persist `connections.csv`, `connection_monitor.json`, and diagnostics with the run; final summaries include the monitor report. Remote targets are skipped explicitly. `--no-connection-monitor` disables sampling. Counts describe OS server-side TCP sockets, not exact Waitress channels, HTTP request concurrency, or queue depth.

- Seven monitor tests verify local/remote eligibility, server-side attribution without double counting, TIME_WAIT exclusion, unknown versus zero, IPv6 and listener process IDs, saved permission errors, and real child-process sampling/clean shutdown with two live TCP connections.
- All 30 discovered tests passed (including those seven), and all 18 existing workflow/response/model tests passed: 48 total. Successful and aborted runs saved monitoring files automatically. Initial workflow artifacts: `results/verification-20261117T171400727967`.
- After adding persisted-monitor assertions, the four-profile coverage workflow and consecutive dashboard-run checks passed again in `results/verification-20261117T171512134403`. No sampling errors were observed. The test uses a disposable local backend adapter, not the actual game database.

One-second sampling can miss brief peaks; OS permission restrictions and local proxies can affect attribution. Monitoring overhead has not been benchmarked at large player counts. Existing historical runs have no recoverable connection snapshots.
