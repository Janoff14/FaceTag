# Story 2.3: Run recognition worker as separate process with camera capture

Status: done

## Story

As the operator,
I want recognition to run in its own OS process pulling frames from the USB camera,
so that the player's Qt event loop is never blocked by dlib's CPU work (AR6 — GIL avoidance).

## Acceptance Criteria

1. **Given** `config.yaml` specifies `camera_device_index` and `people.json` has at least one registered person, **when** the worker entry point is invoked, **then** it opens `cv2.VideoCapture(<index>)` and pulls frames at native rate. _[AR6]_
2. **And** each frame is downsampled to **320×240** for HOG detection (AR8), but the embedding is computed on the **native-resolution crop** at the scaled-back face bounding box. _[AR8]_
3. **And** the camera buffer is drained between iterations so the loop always sees the **latest** frame — never queues stale frames. _[AR8]_
4. **And** the worker prints `MATCH: <name>` to stdout (one line per match, flush=True) every iteration where a registered face is detected. _[FR1, FR2, FR3]_
5. **And** the worker prints nothing for unknown faces or empty frames. _[FR5]_
6. **And** an invalid camera index (`cap.isOpened()` returns False) causes the worker to log `ERROR: cannot open camera index <N>` to stderr and exit with code 1. _[NFR11 — clear failure mode]_
7. **And** the worker can be spawned via `multiprocessing.Process(target=recognition.worker.run, args=(config_dict, stop_event))` — `stop_event` is a `multiprocessing.Event`; setting it cleanly exits the loop, releases the camera, and returns. Story 3.1 (supervisor) and Story 2.4 (queue plumbing) will use this signature.
8. **And** the worker is runnable standalone via `python -m recognition.worker` for development smoke-testing — it loads `config.yaml` itself in that mode.

## Tasks / Subtasks

- [x] **Task 1 — Module + public `run()` signature** — `recognition/worker.py:run(config, stop_event=None, greeting_queue=None) -> int`. Accepts queue param now so Story 2.4 doesn't change the signature.
- [x] **Task 2 — Camera open + invalid-index path** (AC: 1, 6) — `cv2.VideoCapture(idx)` + `isOpened()` check, stderr error, exit 1, `try/finally` for `cap.release()`.
- [x] **Task 3 — Skip-if-behind frame read** (AC: 3) — `_read_latest_frame` calls `grab()` up to 5 times then `retrieve()` once. Returns None on empty buffer; caller sleeps 10 ms.
- [x] **Task 4 — Dual-resolution detect + embed** (AC: 2) — `recognize_dual` downsamples to 320-wide via `INTER_AREA`, HOG detects, picks largest, scales box back to native, embeds at native crop. Falls back to single-res `recognize` if input is already ≤320 wide.
- [x] **Task 5 — Main loop + MATCH output** (AC: 4, 5, 7) — Loop respects `stop_event`, prints `MATCH: <name>` only on match, optional `greeting_queue.put_nowait` with `queue.Full` drop-on-saturate.
- [x] **Task 6 — `__main__` entry** (AC: 8) — `python -m recognition.worker` loads `config.yaml` (or example fallback) and calls `run()`.
- [x] **Task 7 — Unit tests** — 3 dual tests (empty registry, black frame, real-face fixture) + 5 worker tests (drain buffer, empty buffer, invalid camera, stop_event clean shutdown, MATCH printing on match-then-unknown).
- [x] **Task 8 — Verification** — 55/55 pass. Operator manual smoke deferred to your hardware (needs a real camera).

## Dev Notes

### Scope guardrails

- **No greeting overlay trigger.** Story 2.4 wires `multiprocessing.Queue` between this worker and `Player.show_greeting`. This story only prints to stdout.
- **No cooldown.** Story 2.5 adds per-person cooldown logic — it lives in the worker but is out of scope for 2.3.
- **No `watchdog` hot-reload.** Story 3.5 adds `watchdog.Observer` on `people.json`. Registry is loaded once at worker startup in this story.
- **No supervisor.** Story 3.1 wires the supervisor that respawns crashed workers. In this story the worker is callable but not auto-restarted.

### Multiprocessing model

- `multiprocessing.Process(target=run, args=(config, stop_event, greeting_queue))` — Story 3.1 will own the construction. This story's job is the `run` function and a `__main__` entry for standalone testing.
- Do **not** `fork()` on Windows — Python `multiprocessing` defaults to `spawn` on Windows anyway; just don't add code that assumes fork semantics (no module-level state mutation, no shared imports of camera handles).
- The worker should not import PyQt6 — the player owns Qt, the worker owns OpenCV + dlib. Importing PyQt6 in the worker process would re-initialize Qt and waste 100+ MB.

### OpenCV / cv2 specifics

- `cv2.VideoCapture(N)` on Windows uses MSMF by default in OpenCV 4.x. Indices can shift when peripherals plug/unplug — that's why the index is config-driven (NFR-ish operator concern).
- `cap.read()` is `grab()` + `retrieve()`. To drain stale frames cheaply, call `grab()` repeatedly (no decode) and `retrieve()` once. 5 grabs is plenty for a 30 fps camera.
- `cv2.cvtColor(BGR → RGB)` is required before passing to `face_recognition` (already established by Story 1.1 + Story 2.1).
- `cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)` is the right downscale filter (keeps edges sharp for HOG).

### `face_recognition` specifics (recap from Story 2.1)

- `face_locations(rgb, model="hog")` — HOG only, no GPU.
- Box order is `(top, right, bottom, left)` — Pillow/PIL convention, not OpenCV.
- To scale a box from downsampled to native: `(top, right, bottom, left)` → `(top/s, right/s, bottom/s, left/s)` where `s = detect_width / native_width`.

### Previous story intelligence

- Story 2.1's `recognize()` was designed for tests + future use; `recognize_dual()` is the production path. The two share `Registry` and the same tolerance default.
- Story 2.2's writer means `people.json` is now real and atomic — the worker reading it once at startup is safe; no half-written-file race.
- Story 1.4's `Player.show_greeting(name)` is the queue consumer in Story 2.4 — no changes needed in this story.

### Config keys consumed

| Key | Default | Used for |
|---|---|---|
| `camera_device_index` | `0` | `cv2.VideoCapture` argument |
| `recognition_tolerance` | `0.5` | Match threshold |
| `people_db_path` | `"people.json"` | Registry load |

All already in `config.yaml.example`.

### References

- [`_bmad-output/planning-artifacts/epics.md:365-380`](_bmad-output/planning-artifacts/epics.md) — Story 2.3 BDD.
- [`_bmad-output/planning-artifacts/prd.md:352-355`](_bmad-output/planning-artifacts/prd.md) — Process model + frame strategy (downsample-detect, native-embed, skip-if-behind).
- [`_bmad-output/planning-artifacts/prd.md:497`](_bmad-output/planning-artifacts/prd.md) — NFR1 latency budget the worker must hit.
- [`recognition/recognize.py`](recognition/recognize.py) — single-resolution `recognize()` from Story 2.1 (kept for tests/fixtures).
- [`recognition/registry.py`](recognition/registry.py) — `load_registry()` reused here.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (claude-opus-4-7)

### Debug Log References

- 22:05: Marked 2.3 `in-progress`. Wrote `tests/test_recognition_dual.py` and `tests/test_worker.py` first (TDD).
- 22:10: Added `recognize_dual` to `recognition/recognize.py` and created `recognition/worker.py`. RED → GREEN on first run; 55/55 pass.
- 22:12: Two test classes' empty-registry warnings leak to stderr (`WARNING: registry at does-not-exist.json is empty`) — cosmetic, not a failure. Could be silenced with `mock.patch.object(sys, "stderr", ...)` if it becomes noisy later.

### Completion Notes List

- **Worker is camera-aware but otherwise pure**: no Qt, no Telegram, no greeting overlay coupling. Story 2.4 plugs in the queue without changing the signature.
- **Skip-if-behind is grab-only**: `grab()` is cheap (no decode), `retrieve()` decodes the freshest buffered frame. This matches AR8's "never queue stale frames" rule.
- **`recognize_dual` falls back to single-res `recognize`** when the input is already ≤ `detect_width` — keeps unit tests passing without special-casing tiny frames.
- **Stop semantics**: a `multiprocessing.Event` set externally causes the next loop iteration to return cleanly. Story 3.1's supervisor will use this.
- **Operator manual smoke pending hardware**: cannot exercise the camera path without a real device — `python -m recognition.worker` is ready for that test on Sanja's demo machine.

### File List

- `recognition/worker.py` (new)
- `recognition/recognize.py` (modified — added `recognize_dual`)
- `tests/test_recognition_dual.py` (new)
- `tests/test_worker.py` (new)
- `_bmad-output/implementation-artifacts/2-3-run-recognition-worker-as-separate-process-with-camera-capture.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-15: Story 2.3 implemented. Recognition worker module + dual-resolution recognize, 8 new tests. Ready for camera smoke on the demo machine and Story 2.4 queue plumbing.
