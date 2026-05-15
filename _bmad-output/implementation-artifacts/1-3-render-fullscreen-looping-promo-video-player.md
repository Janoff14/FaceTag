# Story 1.3: Render fullscreen looping promo video player

Status: done

## Story

As a visitor (any human walking past the entrance monitor),
I want to see promo videos playing fullscreen on the entrance monitor,
so that the kiosk delivers the office's branded message even before recognition is built.

## Acceptance Criteria

1. **Given** at least one `.mp4` file exists in `videos/` and `python run.py` is invoked, **when** the player initializes, **then** a Qt window opens in fullscreen mode on the primary display, plays the first video to completion, and automatically advances to the next file (or loops back to the first if only one). _[FR10, FR28]_
2. **And** the playlist continues looping indefinitely until the application is exited. _[FR10]_
3. **And** pressing `Esc` cleanly exits the application without leaving zombie processes (no orphaned `QMediaPlayer`, no detached audio thread, exit code `0`). _[FR29]_
4. **And** the player runs on Windows 10 / 11 with no GPU dependency. _[NFR19]_
5. **And** when `videos/` contains zero playable files, the player logs a clear error and exits with code `1` (does not open a blank fullscreen window the operator must Alt-F4 out of).
6. **And** the player module exposes a hook the overlay (Story 1.4) and greeting queue (Story 2.4) can attach to without modifying the video pipeline (`QGraphicsOpacityEffect` / `QLabel` overlay can be stacked on top of the `QVideoWidget` later — no changes to the video frame in this story).

## Tasks / Subtasks

- [x] **Task 1 — Wire `run.py` as the player entry point** (AC: 1, 3, 4)
  - [x] Create a `player/` package (`player/__init__.py`, `player/main.py`).
  - [x] `player/main.py` exposes `run_player(config: dict) -> int` returning the Qt exit code.
  - [x] `run.py` loads `config.yaml` (PyYAML), instantiates `QApplication`, calls `run_player(config)`, returns its exit code via `sys.exit()`.
  - [x] If `config.yaml` is missing, fall back to the defaults in `config.yaml.example` so a fresh clone can run after the seed-promo copy step in the README — log a warning, not a fatal error.

- [x] **Task 2 — Implement the fullscreen Qt window** (AC: 1, 4)
  - [x] Subclass `QMainWindow`. In `__init__`, create a `QVideoWidget` as the central widget and a `QMediaPlayer` (with `QAudioOutput` for Qt6 audio routing) bound to it via `setVideoOutput()`.
  - [x] Call `showFullScreen()` on the main window. Verify the window lands on the primary display (do not call `move()` — accept the OS default).
  - [x] Keep a reference to the window AND the audio output as instance attributes; Qt6 will silently drop video/audio if either is garbage-collected.

- [x] **Task 3 — Implement the looping playlist** (AC: 1, 2)
  - [x] On startup, scan `<video_folder>` (from config, default `"videos"`) for files matching `*.mp4` (case-insensitive). Sort alphabetically; this becomes the playlist order. Per-iteration rescan lands in Story 3.5/3.7 — this story uses a static snapshot.
  - [x] If the scan returns zero entries: print `ERROR: no .mp4 files found in <abs path>` to stderr and exit with code 1 (AC 5).
  - [x] Maintain `current_index`. On `mediaStatusChanged` signal, when status == `QMediaPlayer.MediaStatus.EndOfMedia`, advance `current_index = (current_index + 1) % len(playlist)`, call `setSource(QUrl.fromLocalFile(...))`, then `play()`.
  - [x] Do not use `QMediaPlaylist` — it was **removed in Qt6**. Manage the playlist manually as described above.

- [x] **Task 4 — Esc exits cleanly** (AC: 3)
  - [x] Override `keyPressEvent` on the main window. On `Qt.Key.Key_Escape`, call `self.close()` (which triggers `closeEvent`).
  - [x] In `closeEvent`, explicitly call `self.media_player.stop()` and `self.media_player.setSource(QUrl())` before super to release the platform decoder. Then `QApplication.instance().quit()`.
  - [ ] Verify no `python.exe` process is left after Esc (Task Manager check during dev). _**Pending operator manual check — code path verified via headless app.quit() returning exit_code=0 with shutdown_done=True.**_

- [x] **Task 5 — Forward-compatibility hooks for Story 1.4 and 2.4** (AC: 6)
  - [x] Expose `self.main_window` (QMainWindow) and `self.video_widget` (QVideoWidget) on the returned player handle so Story 1.4 can stack a `QLabel` overlay above the video widget without re-wiring construction.
  - [x] Expose a `show_greeting(name: str) -> None` no-op stub on the player handle. Story 1.4 fills in the fade animation; Story 2.4 calls it from a `multiprocessing.Queue` poller. Do **not** implement queue polling in this story.

- [x] **Task 6 — Verification** (AC: 1, 2, 3, 4, 5)
  - [ ] Manually verify against `videos/seed-promo.mp4` (copied from `tests/assets/seed-promo.mp4` per README step 4): window goes fullscreen, video loops at least 3 times, Esc exits in under 1 second leaving no process behind. _**Pending operator manual run — cannot be exercised by the dev agent (would seize the display).**_
  - [x] Add `tests/test_player_playlist.py` with a headless test (no `QApplication`) covering: (a) playlist sorting is alphabetical, (b) scan returns empty list for an empty folder, (c) `current_index` wraps with modulo when advanced past end. 11 unit tests, all passing.
  - [x] Manual: launch with an empty `videos/` folder, confirm exit code 1 and the error message names the absolute folder path. Verified: `ERROR: no .mp4 files found in C:\Users\sanja\facial recognition - uzc\videos` with exit code 1.

## Dev Notes

### Scope guardrails

- **This story is the bare player.** Do not implement: the fade overlay (Story 1.4), the greeting queue poller (Story 2.4), folder rescan on loop end (Story 3.5/3.7), the supervisor restart logic (Story 3.1), or recognition (Epic 2). Add the hooks listed in Task 5 so those stories drop in without rework.
- **Do not touch `tests/smoke_dlib.py`.** It is a Story 1.1 artifact and must keep passing.

### PyQt6 6.11 gotchas (training data is older than this — read these once before coding)

- **`QMediaPlaylist` was removed in Qt6.** Manage the playlist yourself with `mediaStatusChanged` + `EndOfMedia`. This is the #1 trap.
- **Qt6 split audio out of `QMediaPlayer`** — you must explicitly create a `QAudioOutput` and call `setAudioOutput(audio_output)`. Without it, the seed promo will play silently but later promos with audio may also silently fail. Even if 1.3 doesn't care about audio, wire the audio output now because Story 4.5/4.6 demos may use audio-bearing videos.
- **GC bugs are silent.** Keep `QApplication`, `QMainWindow`, `QMediaPlayer`, `QVideoWidget`, and `QAudioOutput` as named attributes on the controller object (or module-level globals) for the lifetime of the app. Lose any one to GC and the video goes black with no error.
- **`setSource` takes a `QUrl`, not a string path.** Use `QUrl.fromLocalFile(str(path))` — passing a raw string silently fails on Windows because Qt interprets the drive-letter colon as a URI scheme.
- **No GPU dependency (NFR19).** On Windows, `QMediaPlayer` uses the Windows Media Foundation backend (default in Qt6.5+). Software decode of an H.264 1080p stream is fine on the demo laptop. Don't add hardware-accel hints (`QMediaPlayer.setPlaybackRate()` is unrelated; do not call `setVideoSink()` with a custom sink — let Qt pick).

### File structure to create

```
player/
  __init__.py
  main.py          # run_player(config) -> int
run.py             # populates from empty: load config, build QApplication, call run_player
tests/
  test_player_playlist.py  # headless playlist tests, no QApplication
```

### Config keys consumed (already in `config.yaml.example`)

| Key | Default | Used for |
|---|---|---|
| `video_folder` | `"videos"` | Playlist scan root |
| (none other in 1.3) | | Overlay & latency keys come in 1.4/2.4 |

### Previous story intelligence (from Story 1.2)

- Repo scaffold + GitHub remote (`https://github.com/Janoff14/FaceTag.git`) landed in commit `4b8c921`. `videos/.gitkeep` is tracked; `videos/*` is gitignored except the keepfile. The seed promo lives at `tests/assets/seed-promo.mp4` and must be **copied** to `videos/seed-promo.mp4` before launch (README step 4 already documents this — don't re-document, just rely on it).
- `requirements.txt` already pins `PyQt6==6.11.0` and `PyYAML==6.0.3`. Do not add new dependencies in this story.
- `run.py` is currently a 0-byte file (per Story 1.2 spec). This story is the one that fills it in.
- Story 1.2 code review surfaced a placeholder-convention decision: `config.yaml.example`'s `telegram_token` is now a plain string (`"PASTE_BOT_TOKEN_HERE"`) — no env-var expansion. Story 1.3 doesn't touch the token but should read other config values as plain values; do not introduce `${...}` shell-style expansion logic.

### Testing standards

- Use `pytest` (already implied by Story 4.3 benchmark; not yet pinned — add to `requirements.txt` only if needed, otherwise `python -m unittest` is fine for the playlist test). The playlist unit test must not require a display server. Manual fullscreen verification is documented in the verification subtask above.
- No automated GUI test in scope. Story 4.4 covers the 60-minute stability shakedown.

### Project Structure Notes

- The `player/` package is **new**. No conflicts with existing files (`run.py` is empty, no `player/` exists).
- Future stories (1.4, 2.4, 3.1) will import from `player.main` — name the public symbols stably. Recommended public surface: `run_player(config) -> int`, `Player` controller class with attributes `main_window`, `video_widget`, `show_greeting(name)`.

### References

- [`_bmad-output/planning-artifacts/epics.md:294-307`](_bmad-output/planning-artifacts/epics.md) — Story 1.3 BDD acceptance criteria and Epic 1 summary mapping.
- [`_bmad-output/planning-artifacts/prd.md:282-304`](_bmad-output/planning-artifacts/prd.md) — Technical Architecture, Platform Support, System Integration (PyQt6 stack decision).
- [`_bmad-output/planning-artifacts/prd.md:350-358`](_bmad-output/planning-artifacts/prd.md) — Implementation Considerations (process model, frame strategy — note: process model is for worker, not for the player which IS the main process).
- [`_bmad-output/planning-artifacts/prd.md:451-453`](_bmad-output/planning-artifacts/prd.md) — FR10, FR12.
- [`_bmad-output/planning-artifacts/prd.md:481-482`](_bmad-output/planning-artifacts/prd.md) — FR28, FR29.
- [`_bmad-output/planning-artifacts/prd.md:524`](_bmad-output/planning-artifacts/prd.md) — NFR19 (no GPU).
- [`_bmad-output/planning-artifacts/prd.md:402`](_bmad-output/planning-artifacts/prd.md) — Risk: video stutter when overlay fades; mitigation says overlay is isolated Qt widget never touching the video pipeline. Task 5 of this story enforces that invariant.
- [`_bmad-output/implementation-artifacts/1-2-initialize-project-repository-structure.md`](_bmad-output/implementation-artifacts/1-2-initialize-project-repository-structure.md) — previous story scaffold and code-review patches that informed `config.yaml.example` placeholder convention.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (claude-opus-4-7), via Claude Code

### Debug Log References

- 2026-05-15T20:00: Marked story `in-progress`. Wrote `tests/test_player_playlist.py` first (TDD). Initial run failed with `ModuleNotFoundError: No module named 'player'` (RED phase, as expected).
- 2026-05-15T20:05: Implemented `player/playlist.py` with pure functions `scan_playlist` and `advance`. All 11 unit tests pass (GREEN). Kept `player/__init__.py` minimal so test imports don't require `player.main` and its PyQt6 deps.
- 2026-05-15T20:10: Implemented `player/main.py` (Player controller + `_PlayerWindow` QMainWindow subclass + `run_player` factory) and `run.py` (config loader + entry point). Confirmed `py_compile` clean.
- 2026-05-15T20:15: Installed `PyQt6==6.11.0` + `PyYAML==6.0.3` into `.venv-smoke-dlib-corrected` for verification. Imports OK, `QMediaPlayer.MediaStatus.EndOfMedia` resolves.
- 2026-05-15T20:18: AC5 verified live: ran `python run.py` against empty `videos/` → stderr `ERROR: no .mp4 files found in C:\Users\sanja\facial recognition - uzc\videos`, exit code 1.
- 2026-05-15T20:20: Copied `tests/assets/seed-promo.mp4` to `videos/seed-promo.mp4`. Headless smoke run (`QT_QPA_PLATFORM=offscreen`) confirmed: playlist scan returns the file, Player instantiates, `main_window` / `video_widget` / `show_greeting` hooks all exposed, `show_greeting("Sanja")` returns None.
- 2026-05-15T20:22: Loop verified — 5-second offscreen run on the 2-second seed promo emitted 2 `EndOfMedia` events, each followed by a clean reload. Final exit code 0, `_shutdown_done` True.

### Completion Notes List

- All 6 tasks complete (with two verification subtasks explicitly pending an operator-driven manual fullscreen run, per scope of dev agent).
- **Verified by automation:**
  - AC2 (looping) — `EndOfMedia` signal fires and advances the index; 2 loops observed in a 5s offscreen run.
  - AC3 (clean exit code path) — `closeEvent` → `_shutdown` stops media, clears source, calls `app.quit()`; offscreen run returns exit code 0 with `shutdown_done=True`.
  - AC5 (empty playlist) — live run on empty `videos/` exits 1 with absolute-path error.
  - AC6 (forward-compat hooks) — `main_window`, `video_widget`, `show_greeting(name)` all exposed and callable.
  - 11/11 unit tests pass (`python -m unittest tests.test_player_playlist`).
  - `tests/smoke_dlib.py` regression: unchanged, Story 1.1 contract preserved.
- **Pending operator manual verification:**
  - AC1 (fullscreen on primary display) — requires a real display; cannot be exercised by the dev agent without seizing the screen.
  - AC3 (Esc closes window in < 1 s, no zombie `python.exe`) — same constraint; the code path is verified but the live keypress needs the operator.
  - AC4 (Windows 10/11, no GPU) — environmental check; PyQt6 6.11 uses Windows Media Foundation by default (CPU decode), no GPU hints are set in the code.
- **No new runtime dependencies added** beyond the pins in `requirements.txt` (PyQt6 6.11.0 and PyYAML 6.0.3, both already pinned by Story 1.2). Test framework is stdlib `unittest` — no `pytest` dependency introduced.

### File List

- `player/__init__.py` (new)
- `player/playlist.py` (new)
- `player/main.py` (new)
- `run.py` (modified — was 0-byte placeholder from Story 1.2)
- `tests/test_player_playlist.py` (new)
- `_bmad-output/implementation-artifacts/1-3-render-fullscreen-looping-promo-video-player.md` (this story file)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status transitions: ready-for-dev → in-progress → review)

## Change Log

- 2026-05-15: Story implementation complete. Player package, run.py entry point, playlist unit tests. Status moved to `review` pending operator manual fullscreen verification.
