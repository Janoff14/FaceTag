# Story 5.6: Telegram recognition notifications

Status: done

## Story

As Dilnoza,
I want a Telegram message every time the kiosk recognizes someone,
so that I can quietly track who's at the entrance without watching the screen.

## Acceptance Criteria

1. Every time the recognition worker emits a greeting event, it also appends a one-line JSON record to `logs/recognitions.jsonl` with `{"name", "timestamp"}`.
2. The Telegram bot tails this file and sends `🎯 Aziza recognized at 14:32` (single line, plain language per NFR26) to every admin chat ID.
3. The bot's status counter (Story 5.5 — `greetings_count`) is incremented once per notification dispatched.
4. An admin can run `/quiet` to mute notifications and `/unquiet` to resume; the toggle is per-process (no persistence — restarts default back to ON).
5. The worker tolerates write failures on the JSONL file (e.g., directory missing) — it logs to stderr and continues; the greeting queue is the source of truth.
6. Notifications work without resending stale events on bot restart: the tailer starts from the current end-of-file, not the beginning.

## Tasks / Subtasks

- [ ] **Task 1 — `recognition/notifications.py`** with `append_recognition_event(log_dir, name, timestamp)`: atomic append (open in `"a"`, write `json.dumps({"name":…, "timestamp":…})+"\n"`, fsync optional). Creates `log_dir` if missing.
- [ ] **Task 2 — Worker integration** — call `append_recognition_event(logs/, name, now)` right after a successful `greeting_queue.put_nowait`. Failures are caught and logged to stderr.
- [ ] **Task 3 — `bot_notifier.py`** (or inline helper) with pure function `read_new_events(path, last_offset) -> (events, new_offset)` — read from `last_offset`, parse line-by-line, skip malformed lines.
- [ ] **Task 4 — Bot polling job** via `application.job_queue.run_repeating(..., interval=2)`. On each tick: read new events, for each event send a notification message to each admin chat ID if `notify_enabled` is True, increment `greetings_count`.
- [ ] **Task 5 — `/quiet` and `/unquiet` commands** (admin-only) toggle `bot_data["notify_enabled"]`. Reply with the new state.
- [ ] **Task 6 — Tests**:
  - `recognition/notifications.py`: appending writes a parseable line.
  - `read_new_events`: empty file → (`[]`, 0); single line → ([event], offset); subsequent call resumes from offset.
  - Bot `notify_enabled` flag: tests can verify the toggle through `/quiet`/`/unquiet` commands.

## Dev Notes

### Why file-based IPC?

The recognition worker is a `multiprocessing.Process`; the bot is a `subprocess.Popen(python bot.py)`. Sharing a `multiprocessing.Queue` across the subprocess boundary requires authkey juggling that we don't need at this scale. A JSONL file is durable (survives bot restart, shows up in `logs/`), trivially testable, and shows in `logs/recognitions.jsonl` for audit.

### Bot startup behavior

Start the polling job's `last_offset` at the **current file size** (not 0), so a bot restart doesn't replay yesterday's recognitions.

### JobQueue gotcha

`application.job_queue` is only present if `python-telegram-bot[job-queue]` (or `[ext]`) is installed. v22 ships it by default with the standard install we already have. Verify with a quick import check; fall back to a thread if absent (defensive only — should not trigger).

## Dev Agent Record

### Agent Model Used

_TBD_

### File List

_Expected:_

- `recognition/notifications.py` (new)
- `recognition/worker.py` (modified — call append after emit)
- `bot.py` (modified — JobQueue setup, `/quiet`, `/unquiet`, `read_new_events` helper)
- `tests/test_notifications.py` (new)
- `tests/test_bot_notify.py` (new)
- `_bmad-output/implementation-artifacts/5-6-telegram-recognition-notifications.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 5.6 created, status set to ready-for-dev.
