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
