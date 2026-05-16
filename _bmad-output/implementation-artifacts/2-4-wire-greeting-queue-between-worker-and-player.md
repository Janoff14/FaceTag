# Story 2.4: Wire greeting queue between worker and player

Status: done

## Story

As a visitor,
I want my name to appear on the screen when the camera sees me,
so that the kiosk acknowledges me personally.

## Acceptance Criteria

1. **Given** the worker and player are both running, and `people.json` contains a registered face, **when** that person enters the camera frame, **then** the worker pushes a `{name, timestamp}` event to a `multiprocessing.Queue`. _[AR7]_
2. **And** the player polls the queue from its Qt event loop and triggers the overlay with text `Welcome, <name>!`. _[FR6, FR7]_
3. **And** the greeting becomes visible on screen within 2 seconds of the face entering frame, subject to the recognition pipeline budget. _[NFR1]_
4. **And** the underlying promo video does not pause, skip, or stutter during the fade because queue polling is non-blocking and runs through `QTimer`. _[NFR2, FR12]_
5. **And** an unregistered visitor walking past produces no event and no UI change. _[FR5]_

## Tasks / Subtasks

- [x] **Task 1 - Worker event emission** - Story 2.3 already emitted `{"name": name, "timestamp": time.time()}` via optional `greeting_queue.put_nowait(...)`; added a focused assertion that the event payload is produced.
- [x] **Task 2 - Player-side queue drain** - Added `player.greeting_queue.drain_greeting_queue(...)` to consume queued events without blocking the Qt event loop.
- [x] **Task 3 - Qt poller** - Added a `QTimer` poller to `Player.start()` when a queue is provided; valid names call `Player.show_greeting(name)`.
- [x] **Task 4 - Single-command Epic 2 runtime** - Updated `run.py` to create a bounded `multiprocessing.Queue`, start `recognition.worker.run(...)` in a separate process, pass the queue to the player, and stop the worker on shutdown.
- [x] **Task 5 - Remove synthetic startup greeting** - Removed the previous automatic `TEST GREETING` timer so normal runtime shows no UI change unless recognition emits an event.
- [x] **Task 6 - Unit tests** - Added player queue-drain tests and worker queue-payload coverage.

## Dev Notes

- The queue is bounded at 8 events in `run.py`, matching Story 2.3's drop-on-saturate behavior. Recognition should never block the camera loop for UI backpressure.
- The player drains up to 32 events per poll at 100 ms intervals. Multiple immediate matches will collapse visually to the latest overlay animation, which is acceptable until Story 2.5 adds cooldown.
- The full supervisor, log capture, and restart policy remain Story 3.1 scope. In 2.4, `run.py` performs only simple worker lifecycle cleanup when the Qt app exits.
- Manual camera-to-overlay smoke remains hardware-dependent.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-15: Confirmed only the `main` worktree exists locally; story 2.1-2.3 work is present as uncommitted files on `main`.
- 2026-05-15: Implemented player queue polling and Epic 2 worker startup/shutdown in `run.py`.

### Completion Notes List

- Worker-to-player IPC is now real for `python run.py`: worker process -> `multiprocessing.Queue` -> Qt `QTimer` poller -> `Player.show_greeting`.
- Queue polling is non-blocking and ignores malformed events defensively.
- The old 10-second synthetic overlay trigger is gone from normal startup, preserving the "unknown visitor sees nothing" behavior.

### File List

- `player/greeting_queue.py` (new - pure greeting event drain helper)
- `player/main.py` (modified - `QTimer` poller)
- `run.py` (modified - starts/stops recognition worker with shared queue)
- `tests/test_player_greeting_queue.py` (new)
- `tests/test_worker.py` (modified - queue event assertion)
- `_bmad-output/implementation-artifacts/2-4-wire-greeting-queue-between-worker-and-player.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-15: Story 2.4 implemented. Greeting events now flow from the recognition worker process to the fullscreen player overlay.
