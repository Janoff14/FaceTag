# Story 5.4: Admin web UI — videos CRUD + supervisor wiring

Status: done

## Story

As a judge or onsite operator,
I want the same admin panel to also list, upload, and remove promo videos,
and I want the panel to come up automatically when `run.py` starts,
so that everything is one click away with no separate launch step.

## Acceptance Criteria

1. The right column on `/` shows registered videos with delete buttons.
2. Uploading a video via the form atomically copies it through `player.video_writer.add_video` (AR9).
3. Unsupported extensions and missing files surface as flash errors instead of stack traces.
4. `run.py` (via `ComponentSupervisor`) spawns the webapp as a subprocess alongside the bot, captures its logs to `logs/webapp.log`, and restarts it on non-zero exit within the FR30 contract.

## Tasks / Subtasks

- [x] **Task 1** — `/videos/add` and `/videos/delete` routes in `webapp.py` (already wired with 5.3's create_app).
- [x] **Task 2** — Templates already render both columns (Story 5.3's `index.html` did both halves).
- [x] **Task 3** — `tests/test_webapp_videos.py` covering: index lists videos, add happy/error paths, delete happy/error paths.
- [x] **Task 4** — Supervisor: new `WebappHandle`, `start_webapp_process`, `stop_webapp_process`; `ComponentSupervisor.start()` spawns it; `tick()` restarts on non-zero exit; `stop()` shuts it down. `webapp.log` added to `COMPONENT_LOGS` so `format_log_tail` includes it.
- [x] **Task 5** — Regression: 212/212 tests pass (was 197 after Story 5.2; +9 webapp-people + 6 webapp-videos).

## Dev Notes

### Spawn pattern

Reuses the bot's pattern verbatim — `subprocess.Popen` with stdout/stderr → `logs/webapp.log`. The webapp prints `WEBAPP_READY http://127.0.0.1:8000` on startup so an operator can grep for readiness.

### Why subprocess, not thread

Flask's dev server binds a socket and runs an event loop; running it in a thread inside the supervisor would couple shutdown semantics with the Qt main loop. Subprocess matches the bot's isolation model — supervisor restarts on crash, log capture is per-file, no shared state.

### What 5-3 already did

The webapp routes for videos (`/videos/add`, `/videos/delete`) and the template column were already in place from Story 5.3's commit. This story is really about the **supervisor integration** + **tests for the video routes**.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### File List

- `webapp.py` (already had video routes from 5.3)
- `supervisor.py` (modified — `WebappHandle`, start/stop functions, `ComponentSupervisor` integration, `COMPONENT_LOGS` includes `webapp`)
- `tests/test_webapp_videos.py` (new)
- `_bmad-output/implementation-artifacts/5-4-admin-web-ui-videos-and-supervisor-wiring.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 5.4 implemented; supervisor now spawns the webapp alongside the bot. 212/212 tests pass.
