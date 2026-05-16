# Story 3.1: Wire supervisor for component lifecycle start/log/restart

Status: done

## Story

As the operator,
I want a single `python run.py` to spawn the player, recognition worker, and a temporary bot-process stub, capture their logs, and restart supervised background components,
so that the lifecycle contract is proven before the real Telegram bot is added.

## Acceptance Criteria

1. **Given** `run.py` exists at the project root, **when** I invoke `python run.py`, **then** the supervisor spawns the player in the main process, the recognition worker as a `multiprocessing.Process`, and a minimal `bot.py` stub subprocess that starts, writes `BOT_STUB_READY`, and stays alive until shutdown. _[FR28, FR29]_
2. **And** all three supervised components are ready within < 30 s cold boot. _[NFR3]_
3. **And** each component's stdout/stderr is captured to `logs/player.log`, `logs/worker.log`, `logs/bot.log`, and `logs/supervisor.log`. _[NFR28, FR32]_
4. **And** if the bot stub or worker process exits non-zero, the supervisor detects within 5 s and restarts that component without killing the player or the other component. _[FR30, NFR11]_
5. **And** the supervisor can print a rolling tail of all component logs to the console on demand, sufficient to identify which component crashed or degraded during a demo. _[NFR29]_
6. **And** pressing Ctrl+C on the supervisor cleanly shuts down all three components with no orphan worker or bot process.

## Tasks / Subtasks

- [x] **Task 1 - Add bot stub** - Create `bot.py` that logs `BOT_STUB_READY` and stays alive until interrupted.
- [x] **Task 2 - Add supervisor tests** - Cover bot stub launch/readiness, worker process restart on non-zero exit, bot subprocess restart on non-zero exit, log-tail formatting, and clean shutdown.
- [x] **Task 3 - Implement supervisor module** - Encapsulate worker start/stop, bot start/stop, log capture, restart checks, and rolling tail.
- [x] **Task 4 - Wire `run.py`** - Start background supervisor, run player in main process, capture player stdout/stderr, stop components on exit/Ctrl+C.
- [x] **Task 5 - Regression verification** - Run full test suite.

## Dev Notes

- Keep the player in the main process because Qt owns the event loop.
- Keep worker restart policy outside `recognition.worker`; worker remains a simple callable process target.
- Use append-mode logs under the configured `log_directory` so a crash does not erase the previous failure lines.
- The real Telegram bot arrives in Story 3.2; this story must keep the bot as a minimal stub.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-15: Created story file from `epics.md`; existing `run.py` already launched player + worker but lacked bot stub, logs, and restart policy.
- 2026-05-15: Added failing supervisor tests, implemented `supervisor.py`, `bot.py`, and rewired `run.py`.
- 2026-05-15: Verified `run.py --tail-logs`; avoided counting stdin-based multiprocessing smoke because Windows spawn cannot use `<stdin>` as `__main__`.

### Completion Notes List

- Added temporary `bot.py` stub that writes `BOT_STUB_READY` and stays alive until terminated.
- Added `supervisor.py` with worker process launch/log capture, bot subprocess launch/log capture, non-zero restart checks, clean shutdown, and rolling log tail formatting.
- Rewired `run.py` so the player remains in the main process while `ComponentSupervisor` supervises worker + bot in the background.
- Added `run.py --tail-logs --tail-lines N` for on-demand component log tails.
- Player stdout/stderr now redirects to `logs/player.log`; worker and bot stdout/stderr redirect to `logs/worker.log` and `logs/bot.log`; lifecycle events go to `logs/supervisor.log`.
- Verified `.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`: 76/76 pass.

### File List

- `bot.py` (new - temporary bot stub)
- `supervisor.py` (new - lifecycle/log/restart supervisor)
- `run.py` (modified - supervisor entry point and log tail command)
- `tests/test_supervisor.py` (new - lifecycle/log/restart tests)
- `_bmad-output/implementation-artifacts/3-1-wire-supervisor-for-component-lifecycle-start-log-restart.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-15: Story 3.1 created and started.
- 2026-05-15: Story 3.1 implemented and verified; status set to done.
