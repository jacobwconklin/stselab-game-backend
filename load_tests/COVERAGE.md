# Frontend-to-load-test coverage

The inventory assertion in `tests/verify.py` scans all frontend literal `postRequest` / `getRequest` calls and fails if they differ from the 19 endpoints below. It includes `advanceSession`'s request inside `Api.ts`. This is game coverage, not the separate `/navydp/*` survey application, sample routes, SMTP, or health checks. There is no game call to those endpoints.

| Endpoint | Where it belongs in the modeled flow |
|---|---|
| POST `/player/host` | One host registers and creates a new session |
| POST `/player/join` | Every other participant registers using that host's code |
| POST `/session/status` | Each participant's independent 2.5-second controller timer; stops on observed end date or departure |
| POST `/session/players` | Independent lobby timer, including while onboarding |
| POST `/player/diceResult` | Eligible host onboarding; two offboarding submissions per eligible participant per final-results component |
| POST `/session/advance` | Host only, for each normal transition; never called by ordinary participants |
| POST `/player/roundResult` | Once in rounds 1, 3, 6, 7, 8, 9; never in amateur-only round 2 |
| POST `/session/roundresults` | After each participant finishes a scored golf round; follows the controller's status request |
| POST `/player/freeRoamResult` | Repeated randomized exploration attempts in round 4, fire-and-forget saves |
| POST `/player/freeRoamSurvey` | Once after completing round 5's questionnaire |
| POST `/session/surveyssubmitted` | Separate timer in round 5, for ordinary participants as well as host, until all surveys counted |
| POST `/session/finalresults` | Round 10 controller fetch, cached when nonempty; fetched even while offboarding is visible |
| POST `/session/jumptoarmmission` | Host's lobby shortcut in `arm-only`; skips golf and enters round 11 |
| POST `/player/armRoundResult` | Once in each of rounds 12–15, using the real arm calculations |
| POST `/session/armroundresults` | After completing an arm round, following status, until the host advances |
| POST `/session/armfinalresults` | Once on entering round 16; before completing offboarding |
| POST `/session/end` | After golf-only final review, or immediately after host loads arm final results |
| GET `/player/allResults` | Once for participants choosing historical results after ending; host always chooses it so coverage is deterministic |
| POST `/player/remove` | Self-exit and host removal in the separate `departures` profile |

By default JSON POSTs also reproduce cross-origin OPTIONS preflights, with an initial five-second browser-like cache and respect for the server's max-age (capped at 7,200 seconds). Set `origin` in configuration to match the frontend origin; null disables this for API-only isolation. GET historical results is a simple cross-origin request without a preflight. OPTIONS is reported separately by Locust. This is a network approximation, not a complete browser CORS/cache implementation.

## Round mapping

`0 lobby → 1 professional practice → 2 amateur-only practice → 3 solver-choice practice → 4 golf exploration → 5 survey → 6–9 golf tournament → 10 golf results/offboarding → 11 arm exploration → 12–15 arm tournament → 16 arm results/offboarding/end`.

`golf-only` ends at 10. `arm-only` uses the real shortcut from 0 to 11. `departures` follows the full sequence after two lobby departures. `coverage` in the launcher runs all four profiles sequentially, in separate sessions and report folders.

## Current behavior deliberately preserved

Source paths below are relative to `E:\vscodeStuff\stse_game\frontend\src`.

- **Dice assignment:** `Pages/Register/Register.tsx` sets `shouldPlayDiceGame` only for host registration. A joiner's flag is undefined. `WaitRoom` consequently skips joiner onboarding; `DiceSelectGame` skips offboarding only for an explicit false flag, so joiners do play offboarding. Host participation follows the returned UUID's character-sum parity. The suite uses returned IDs, never edits them to force participation.
- **Two offboarding writes:** `Pages/DiceSelectGame/DiceSelectGame.tsx` first submits the dice choice/reasoning with empty follow-up answers, then the second modal's Continue calls the same save function with completed follow-up answers. Both are INSERTs. The second click navigates without awaiting its save; the suite likewise starts that write in the background, then drains pending writes before declaring the journey complete. It does not silently convert the second write into an update or call it a retry.
- **Offboarding twice in full games:** golf final results has an offboarding component; arm final results mounts a fresh one without checking whether golf offboarding already happened. Eligible players therefore make four offboarding writes in a full game.
- **Local-only activity:** amateur practice (round 2) and arm exploration (round 11) make no result-saving API calls. They consume realistic human time while status polling continues. Arm exploration invokes the actual component calculations locally. Golf exploration saves every individual attempt; the commented-out simulate-all path is not called.
- **Units:** golf cost, golf score, custom performance weight, and exploration distance have the same multiplication/flooring as their callers; arm cost/weight remain in the existing source units while its score is multiplied by 100. Architecture spelling, including `Gripper and Maniuplator`, comes from frontend metadata.
- **Shortcut response quirk:** `session/jumptoarmmission` updates the stored round to 11 but returns old-round-plus-one. The frontend ignores the returned round and discovers 11 via status; the suite does too.
- **Final ordering:** arm-results fetch occurs when the component mounts; the host calls end immediately after its own fetch. Other clients observe the end through status, but continue their final questionnaire. The suite does not end the run just because the host sent end.
- **No automatic write retries:** the game does not make them, and its inserts are not idempotent. A failed write ends the test with a diagnostic instead of silently changing workload/data.
- **Guarded polling (model version 2):** each player has independent controller/lobby/survey clocks. A clock skips ticks while its previous complete callback is pending, including status followed by results. It does not sleep after each response. Separate pollers and background writes can still run concurrently. The outstanding-request cap remains a load-generator protection: reaching it FAILS the run and reports that offered load was capped.
- **Cleanup and deadlines:** each complete polling cycle has the frontend's unscaled 20-second deadline. A tracked effect dependency change or screen unmount interrupts the pending read and resets the timer; it does not cancel background saves. Skipped ticks, cancelled cycles and timeouts are recorded separately. Client cancellation cannot guarantee the server stops work it already accepted.
- **Controller dependencies:** timer deadlines reset on observed round changes and changes to golf/final-result list lengths; survey deadlines reset on changed count values. A changed round without an end date now returns before requesting results for the previous round, matching the updated GameController.
- **Leading slashes:** callers of round/final result endpoints pass a leading slash to an already slash-terminated base URL. The suite preserves the resulting double slash using an absolute URL and counts redirects.

## Fidelity boundaries

The goal is source-aligned API flow, payloads, concurrency, and human pacing. Locust does not execute React, DOM effects, rendering, CSS, GPU animation, asset loading, print/download actions, or local-storage refresh/reopen behavior. It does not claim bit-for-bit reproduction of React effect races or browser connection limits. Those require a real browser companion test. Effect transitions are detected by the scheduler, with up to approximately 20 ms observation delay. Polling cycles have the frontend's fixed 20-second deadline; the configurable per-request timeout remains an additional driver control for all HTTP calls, including non-polling calls that the browser does not time out.

Human timings, exploration frequency, architecture/solver preferences, and archive probability are explicit assumptions, not measured classroom behavior. There is player-to-player variation and per-action variation. Default host policy waits for all active scores/surveys and gives review time; for local-only phases it waits for participants' exploration time. This is one realistic, completion-oriented host policy, not every possible early-advance decision. Arrival is staggered by Locust spawn rate plus registration time. The suite has one session/host per process and rejects distributed/multiprocess execution rather than silently splitting one classroom across independent hosts.

The `departures` scenario deterministically selects two non-host participants for a self-exit and a kick so the optional branch is covered. The other profiles keep their full population, making baseline comparisons reproducible. Final review and archive times vary; the host always visits the archive to guarantee that endpoint without forcing every participant to do so.

## Verification boundary

The local verifier extracts real handler definitions via Python AST, supplies a disposable in-memory database adapter, and sends real HTTP requests through Locust. It never imports `environmentSecrets` or starts the deployed application. Its SQLite adapter translates timestamps/identity syntax, omits foreign-key constraints, and adds the required `FreeRoamResult.TimeStamp` column only when it is absent from the source DDL. It verifies workflow/payload/ordering behavior, not MySQL types, transactions, network topology, locks, indexes, or capacity. Those need a staging run against the actual database engine/schema.
