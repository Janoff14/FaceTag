# Story 1.4: Validate fade-in/out greeting overlay over promo video

Status: done

## Story

As a developer,
I want the player to display a fade-in/out text overlay over the video on a manual trigger,
so that I can validate the no-stutter overlay architecture (NFR2, NFR11) before integrating with recognition in Epic 2.

## Acceptance Criteria

1. **Given** the player from Story 1.3 is running fullscreen, **when** I trigger the overlay (by pressing the `G` key OR automatically 10 seconds after startup, whichever fires first), **then** a `TEST GREETING` text overlay fades in over 300–500 ms, holds at full opacity for **5 s**, and fades out over 300–500 ms. _[NFR2]_
2. **And** the underlying video does not pause, skip, or visually stutter during the fade — the overlay is a Qt widget composited above the `QVideoWidget`; the video frame is **never** modified. _[NFR2, NFR11, PRD risk row "Video stutter when overlay fades"]_
3. **And** the overlay font size is **≥ 8 % of display height**, centered horizontally on the screen. _[NFR25]_
4. **And** the overlay implementation is the same `show_greeting(name: str)` hook stubbed in Story 1.3 — Story 2.4 will call this exact method from the multiprocessing queue without modification. The signature must remain `(name: str) -> None`.
5. **And** triggering the overlay while a previous fade-in/hold/fade-out is still running cancels the previous animation cleanly and restarts with the new name — no orphaned `QPropertyAnimation` objects, no stuck-at-half-opacity labels. _(Story 2.4 will fire repeats during cooldown windows; the player must not crash on rapid repeats.)_

## Tasks / Subtasks

- [x] **Task 1 — Build the overlay widget** (AC: 2, 3)
  - [x] Created [`player/overlay.py`](player/overlay.py) with `GreetingOverlay(QWidget)` (outer container) wrapping an inner `QLabel`.
  - [x] Parented to the main window. Transparent for mouse events.
  - [x] Font size computed via `compute_font_size(display_height_px, factor)` with a 24 pt floor.
  - [x] White text + `QGraphicsDropShadowEffect` on the inner label; the opacity effect lives on the outer container — sidesteps the "one QGraphicsEffect per widget" Qt6 rule.

- [x] **Task 2 — Wire fade-in / hold / fade-out animation** (AC: 1, 2, 5)
  - [x] `QGraphicsOpacityEffect` driven by `QPropertyAnimation(..., b"opacity")`.
  - [x] `QSequentialAnimationGroup`: fade-in (OutCubic, 400 ms) → `QPauseAnimation(hold_ms)` → fade-out (InCubic, 400 ms).
  - [x] Rapid re-triggers stop + `deleteLater()` the previous group before building a new one. Opacity effect is reused.
  - [x] `finished` signal hides the widget.

- [x] **Task 3 — Hook into the Player controller** (AC: 4)
  - [x] `Player.__init__` instantiates `GreetingOverlay` after the main window + video widget.
  - [x] `show_greeting(name)` formats `"Welcome, <name>!"` (or `"TEST GREETING"` for the validation trigger) and calls `overlay.start_fade(text)`.
  - [x] `_PlayerWindow.resizeEvent` forwards to `overlay.reposition()` via `attach_overlay()`.

- [x] **Task 4 — Manual trigger surfaces for validation** (AC: 1)
  - [x] `G` keypress in `_PlayerWindow.keyPressEvent` triggers `show_greeting("TEST GREETING")`. `Esc` still exits.
  - [x] One-shot `QTimer.singleShot(10_000, ...)` fires `show_greeting("TEST GREETING")` 10 s after startup.

- [x] **Task 5 — Headless unit tests for the deterministic pieces** (AC: 3, 5)
  - [x] [`tests/test_overlay_font_size.py`](tests/test_overlay_font_size.py): 5 tests covering NFR25 floor, default factor scaling, clamp on tiny displays, zero/negative-height handling, monotonic growth with factor.
  - [x] [`tests/test_overlay_state.py`](tests/test_overlay_state.py): 5 tests under `QT_QPA_PLATFORM=offscreen` covering initial opacity = 0, initial hidden state, rapid re-trigger stops previous group, widget hides after full cycle.

- [x] **Task 6 — Verification** (AC: 1, 2, 3)
  - [x] Regression: 21 tests pass total (11 playlist + 5 font-size + 5 overlay-state). Story 1.1 smoke still `OK: faces=1 embedding_dim=128`.
  - [ ] Manual: run `python run.py` against the 4 promos in `videos/`. After 10 s the timer fires; press `G` mid-promo too. Verify no stutter, no flicker, no frame drop. Press Esc to exit cleanly. _**Pending operator manual run — dev agent verified everything that doesn't require a real display.**_

## Dev Notes

### Scope guardrails

- **No multiprocessing, no queue polling, no recognition.** Story 2.4 wires `multiprocessing.Queue` between the worker and `show_greeting`; this story only validates the fade architecture on a manual trigger. If you find yourself importing `multiprocessing` in this story, stop.
- **Don't touch the video pipeline.** The overlay is a sibling widget of `QVideoWidget`, parented to the main window. Never call into `QMediaPlayer`, `QVideoWidget.setVideoOutput`, or `QVideoSink` from overlay code.
- **Keep `show_greeting` signature stable.** Story 2.4's queue poller calls `player.show_greeting(name)` — adding kwargs or changing the name parameter forces a 2.4 rework.

### PyQt6 6.11 gotchas specific to this story

- **`QGraphicsOpacityEffect` + `QPropertyAnimation(..., b"opacity")`** is the canonical Qt6 fade. Do not use `setWindowOpacity` on a child widget — it only works for top-level windows on Windows.
- **`QSequentialAnimationGroup` orphans** are a real GC trap: if you build a group as a local variable inside a method, the group is garbage-collected as soon as the method returns, killing the animation before it starts. Keep `self.animation_group` as an instance attribute, or use `setParent(self)` on the group.
- **`QGraphicsDropShadowEffect` + `QGraphicsOpacityEffect` conflict.** Qt only honors one `QGraphicsEffect` per widget — you can't stack opacity and drop-shadow. Workaround: nest a `QLabel` inside a transparent container `QWidget`; put drop-shadow on the inner label, opacity on the container. This is the cleanest way and Story 1.4 should use it.
- **`Qt.WindowType.FramelessWindowHint` / `Qt.WidgetAttribute.WA_TranslucentBackground` are NOT needed** — the overlay is a child widget of the main window, not its own top-level window. Skip these flags; they cause subtle paint glitches on Windows when nested.
- **Font sizing in points vs pixels.** `QFont.setPointSize` is DPI-aware; `setPixelSize` is not. Use `setPointSize` and let Qt's HiDPI handling do the right thing on the demo monitor.

### Forward-compatibility for Stories 2.4 and 2.5

- Story 2.4 will queue greeting events as `{name, timestamp}` and call `player.show_greeting(name)` from the player's event loop. The implementation in this story already satisfies that contract; 2.4 just adds queue polling.
- Story 2.5 introduces a per-person cooldown enforced in the **worker**, not the player. The overlay itself does not enforce cooldown — overlapping calls cancel and restart (AC 5). Don't add cooldown logic here.

### Config keys consumed (already in `config.yaml.example`)

| Key | Default | Used for |
|---|---|---|
| `display_duration_seconds` | `5` | Hold time at full opacity |
| `font_size_factor` | `0.08` | Font height as fraction of screen height |

Add to `config.yaml.example` if missing: nothing new in this story.

### Previous story intelligence (from Story 1.3)

- `Player` class is in [`player/main.py`](player/main.py); `Player.show_greeting(name)` is currently a no-op returning `None`. This story replaces the body but keeps the signature.
- `_PlayerWindow.keyPressEvent` already handles `Esc` → close. Extend it for `G` without breaking Esc.
- The 11 playlist unit tests live in [`tests/test_player_playlist.py`](tests/test_player_playlist.py) and use `unittest` (stdlib, no pytest). Match that style for the two new test files.
- `app._kiosk_player` is the GC anchor used by `run_player()` to keep the controller alive — keep it.
- 4 real promos sit in `videos/` (build, Comp 1, Ochiq, wrokshop). Use those for manual verification.

### Testing standards

- `unittest` from stdlib. `QT_QPA_PLATFORM=offscreen` for the overlay state test. Manual fullscreen verification is the only visual test in scope — Story 4.4's 60-minute shakedown is where smoothness gets quantified.

### References

- [`_bmad-output/planning-artifacts/epics.md:309-323`](_bmad-output/planning-artifacts/epics.md) — Story 1.4 BDD acceptance criteria.
- [`_bmad-output/planning-artifacts/prd.md:300`](_bmad-output/planning-artifacts/prd.md) — Architecture decision: `QLabel` + `QGraphicsOpacityEffect` + `QPropertyAnimation` over the `QVideoWidget`.
- [`_bmad-output/planning-artifacts/prd.md:402`](_bmad-output/planning-artifacts/prd.md) — Risk row: overlay must never touch the video pipeline; mitigation = isolated widget.
- [`_bmad-output/planning-artifacts/prd.md:498`](_bmad-output/planning-artifacts/prd.md) — NFR2 (300–500 ms fade, no dropped frames).
- [`_bmad-output/planning-artifacts/prd.md:510`](_bmad-output/planning-artifacts/prd.md) — NFR11 (component crash recovery transparent to visitor).
- [`_bmad-output/planning-artifacts/prd.md:533`](_bmad-output/planning-artifacts/prd.md) — NFR25 (font size ≥ 8 % of display height).
- [`_bmad-output/implementation-artifacts/1-3-render-fullscreen-looping-promo-video-player.md`](_bmad-output/implementation-artifacts/1-3-render-fullscreen-looping-promo-video-player.md) — Story 1.3 hooks (`Player.show_greeting`, `main_window`, `video_widget`) that this story fills in.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (claude-opus-4-7)

### Debug Log References

- 20:45: Marked story `in-progress`. Wrote both test files first (TDD).
- 20:50: Implemented `player/overlay.py` — `compute_font_size` pure function + `GreetingOverlay(QWidget)` with nested label-for-shadow / container-for-opacity to skirt Qt6's one-effect-per-widget rule. Held `animation_group` as instance attribute (and parented to self) to dodge the GC-orphan trap called out in Dev Notes.
- 20:52: First test run hit two issues: (a) `tests/test_overlay_font_size.py` couldn't run under system Python because `player.overlay` transitively imports PyQt6 — resolved by running all overlay tests via the `.venv-smoke-dlib-corrected` interpreter; (b) `test_rapid_retrigger_leaves_single_animation` called `overlay.text()` but the overlay is a QWidget not a QLabel — fixed to `overlay.label.text()`.
- 20:55: 21/21 tests pass (11 playlist + 5 font-size + 5 overlay-state).
- 20:57: Headless smoke confirmed full lifecycle: `show_greeting("Sanja")` flips overlay visible with text `"Welcome, Sanja!"`, after the fade cycle completes `isHidden()` returns True, app exits 0.

### Completion Notes List

- **Verified by automation:**
  - AC2 (no video pipeline contact) — overlay is a child of `QMainWindow`, never touches `QMediaPlayer` / `QVideoWidget` / `QVideoSink`.
  - AC3 (font size) — `compute_font_size` covered by 5 unit tests; default factor 0.08 produces ≥ NFR25's 8 % floor with a 24 pt clamp.
  - AC4 (signature) — `Player.show_greeting(name: str) -> None` preserved; Story 2.4 queue poller can call it unchanged.
  - AC5 (rapid retrigger) — explicit unit test for double-trigger; previous animation group is stopped + `deleteLater()`'d.
  - Regression — Story 1.3's 11 playlist tests and Story 1.1's smoke both still pass.
- **Pending operator manual verification:**
  - AC1 (fade-in / hold 5 s / fade-out timing) — visible duration check needs a real display.
  - AC2 live (zero stutter under real GPU compositing) — must be confirmed by eye on the demo machine.
  - AC3 live (centered horizontally, readable from 2–3 m) — same.
- **No new runtime dependencies.** Animation classes are part of PyQt6's stdlib (`QPropertyAnimation`, `QSequentialAnimationGroup`, `QGraphicsOpacityEffect`, `QGraphicsDropShadowEffect`) — already shipped by `PyQt6==6.11.0`.

### File List

- `player/overlay.py` (new)
- `player/main.py` (modified: imports overlay, instantiates `GreetingOverlay`, replaces `show_greeting` no-op, adds `G` keypress and 10 s one-shot timer, wires `resizeEvent` → `overlay.reposition()`)
- `tests/test_overlay_font_size.py` (new)
- `tests/test_overlay_state.py` (new)
- `_bmad-output/implementation-artifacts/1-4-validate-fade-in-out-greeting-overlay-over-promo-video.md` (this story file)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status transitions)

## Change Log

- 2026-05-15: Story 1.4 implemented — fade-in/hold/fade-out greeting overlay, manual G trigger + 10 s one-shot timer, headless tests passing. Status moved to `review` pending operator manual fullscreen verification.
