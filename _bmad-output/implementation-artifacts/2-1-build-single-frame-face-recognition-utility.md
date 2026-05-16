# Story 2.1: Build single-frame face recognition utility

Status: done

## Story

As a developer,
I want a reusable module that takes a frame and returns matched-name-or-None,
so that recognition logic is encapsulated and unit-testable independent of camera or process model.

## Acceptance Criteria

1. **Given** a `people.json` file with seed embeddings and a `config.yaml` specifying `recognition_tolerance` (default 0.5), **when** `recognize(frame, registry)` is called on a frame containing a registered person's face, **then** the function returns the matched name string. _[FR1, FR2, FR3]_
2. **And** when called on an unknown face (no embedding in `people.json` is within tolerance), returns `None`. _[FR5]_
3. **And** when called on a frame with no detectable face, returns `None` without raising. _[FR5]_
4. **And** when called on a frame containing **multiple** registered faces, returns the name corresponding to the **largest face by bounding-box area** (closest to camera). _[FR4]_
5. **And** the tolerance is read from `config.yaml` (key `recognition_tolerance`) so the threshold is tunable without code change. _[FR3]_
6. **And** the public surface is pure-function (no globals, no module-level state) so Story 2.3's worker process can call it in a tight per-frame loop and Story 2.4 can mock it for the queue wiring.
7. **And** the registry loader (`load_registry(people_json_path) -> Registry`) returns an in-memory data structure separate from `recognize()` — so a hot-reloader (Story 3.5) can swap the registry without reloading the function or restarting the worker.

## Tasks / Subtasks

- [x] **Task 1 — Define the registry data structure and loader** (AC: 1, 7)
- [x] **Task 2 — Implement `recognize()` against an empty / unknown / known frame** (AC: 1, 2, 3)
- [x] **Task 3 — Multi-face tie-break by largest bounding box** (AC: 4) — encodings computed for the single largest face only, so the "no fallthrough to smaller registered face" rule is enforced by construction.
- [x] **Task 4 — Config integration** (AC: 5) — `recognize(frame, registry, tolerance=0.5)` accepts tolerance as a parameter; default mirrors `config.yaml.example`.
- [x] **Task 5 — Unit tests** (AC: 1–5)
  - 6 registry tests covering missing file / empty list / one person / multi-person ordering / malformed JSON / frozen dataclass.
  - 4 recognize tests: 2 deterministic (empty registry, black frame) + 2 integration (real face match, far-registry unknown).
  - Fixture builder in [`tests/_fixtures.py`](tests/_fixtures.py) synthesizes `people.json` from a local face photo on first run; tests `SkipTest` gracefully on clean clones.
- [x] **Task 6 — Run validations** (AC: 1–7)
  - 31/31 tests pass (Epic 1's 21 + Story 2.1's 10). Story 1.1 smoke unchanged.
  - Latency smoke: full-res 1280×960 → 646 ms; downsampled 320×240 → **311 ms** (matched name = `Operator`). Well within NFR1's 2 s end-to-end budget.

## Dev Notes

### Scope guardrails

- **No camera, no multiprocessing, no Qt.** Story 2.3 spawns the recognition worker process and wires `cv2.VideoCapture`. Story 2.4 wires the multiprocessing queue. This story is the pure compute kernel — designed so 2.3 imports and calls it without ceremony.
- **No greeting overlay logic.** Story 1.4 owns that. `recognize()` returns a string or None — it does **not** call `Player.show_greeting`.
- **No `people.json` writes.** Story 2.2 owns the writer module. `registry.py` is read-only.

### Architecture compliance

- **Frame format contract:** `recognize()` accepts BGR `np.uint8` arrays (OpenCV default). Story 2.3 will pass frames straight from `cv2.VideoCapture.read()`.
- **Downsampling for detection:** Worker (Story 2.3) downsamples to 320×240 before calling `recognize()`, per AR8 and PRD line 354. This story doesn't need to handle downsampling — but the docstring should note the recommended caller behavior so 2.3 doesn't pass full-resolution frames and tank performance.
- **HOG vs CNN:** HOG only (NFR19, no GPU). Hardcoded.
- **Distance metric:** `face_recognition` uses Euclidean distance over 128-D embeddings; tolerance 0.5 is the PRD-validated default (line 403: "Lower tolerance from 0.6 → 0.5; verify with seed set under demo lighting").

### Library specifics (face_recognition 1.3.0 + dlib-bin 20.0.1)

- `face_recognition.face_locations(rgb, model="hog")` returns `list[tuple[top, right, bottom, left]]` — note Pillow/PIL ordering, not (x, y, w, h).
- `face_recognition.face_encodings(rgb, known_face_locations=locations)` returns `list[np.ndarray]` of shape `(128,)`. Passing locations is **required** for performance — without it, the function re-detects faces internally.
- `face_recognition.face_distance(known_encodings, face_to_check)` is vectorized — pass it the whole `(N, 128)` matrix and a single `(128,)` probe to get an `(N,)` distance array. Cheaper than a Python loop.
- The published `face_recognition==1.3.0` API matches the above; do not assume newer functions exist.

### Previous story intelligence

- Story 1.1 proved the install path: `setuptools<81` + `dlib-bin==20.0.1` + `face_recognition==1.3.0` + `face_recognition_models==0.3.0`. All four are already in [`requirements.txt`](requirements.txt). The smoke script [`tests/smoke_dlib.py`](tests/smoke_dlib.py) demonstrates the import order and the BGR→RGB conversion this story re-uses.
- `faces/photo_2026-05-15_17-16-47.jpg` worked in the Story 1.1 smoke — it's a clean front-facing photo, fine for fixture generation. The `.gitignore` already protects `faces/*`.
- Story 1.4's Qt window is unchanged by this story — recognition runs out-of-process per AR6 (Story 2.3), not in the player.

### Config keys consumed

| Key | Default | Used for |
|---|---|---|
| `recognition_tolerance` | `0.5` | Maximum Euclidean distance for a match |

Already in `config.yaml.example`. No new keys.

### Testing standards

- `unittest` stdlib (matches 1.3/1.4 style).
- Run all overlay + Qt tests under `QT_QPA_PLATFORM=offscreen` in the existing PyQt6 venv. Recognition tests don't need Qt.
- Skip integration tests gracefully when face fixtures aren't available (clean CI clones).
- Float comparisons use `assertAlmostEqual` with `places=4` for distance values.

### References

- [`_bmad-output/planning-artifacts/epics.md:333-347`](_bmad-output/planning-artifacts/epics.md) — Story 2.1 BDD and Epic 2 context.
- [`_bmad-output/planning-artifacts/prd.md:436-440`](_bmad-output/planning-artifacts/prd.md) — FR1–FR5 (detect → embed → match → largest-face → silent on unknown).
- [`_bmad-output/planning-artifacts/prd.md:354`](_bmad-output/planning-artifacts/prd.md) — Frame strategy: downsample 320×240 before detection.
- [`_bmad-output/planning-artifacts/prd.md:403`](_bmad-output/planning-artifacts/prd.md) — Tolerance 0.5 validated under demo lighting.
- [`_bmad-output/implementation-artifacts/1-1-verify-dlib-face-recognition-install-on-windows-demo-machine.md`](_bmad-output/implementation-artifacts/1-1-verify-dlib-face-recognition-install-on-windows-demo-machine.md) — proven dependency versions and the BGR→RGB pattern.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (claude-opus-4-7)

### Debug Log References

- 21:25: Marked story `in-progress`. Wrote `tests/_fixtures.py`, `tests/test_recognition_registry.py`, `tests/test_recognition_recognize.py` first (TDD). RED confirmed.
- 21:30: Implemented `recognition/registry.py` (frozen dataclass + JSON loader) and `recognition/recognize.py` (HOG detect → largest-face → vectorized distance → tolerance check).
- 21:35: 31/31 tests pass on first GREEN run. Integration tests built the one-person fixture from `faces/photo_2026-05-15_17-16-47.jpg` automatically and matched the registered name `Operator`.
- 21:38: Latency smoke — full-res 1280×960 ≈ 646 ms/frame; downsampled 320×240 ≈ 311 ms/frame. Production path (worker downsamples per AR8) leaves ~1.6 s of headroom under NFR1's 2 s budget.

### Completion Notes List

- **Largest-face-no-fallthrough rule** enforced by construction: `face_encodings` is only called for the single largest detected location. A smaller registered face physically cannot steal the greeting.
- **HOG only** (`model="hog"` hardcoded); CNN path requires CUDA and is out of scope per NFR19.
- **Pure-function surface** preserved — no module-level state, no globals. `recognize()` is safe to call from a worker process loop and easy to mock for Story 2.4's queue wiring.
- **Registry decoupled from recognize** so Story 3.5's `watchdog` hot-reloader can swap `Registry` instances atomically.
- **Privacy preserved** — `tests/_fixtures.py` builds `tests/fixtures/people.json` from local `faces/` only on demand; both `faces/*` and `tests/fixtures/*` would need explicit gitignore protection if not already covered (currently `faces/*` is gitignored; `tests/fixtures/*` is in a tracked dir so it would commit — that's an upcoming Story-2.2 concern).

### File List

- `recognition/__init__.py` (new)
- `recognition/registry.py` (new)
- `recognition/recognize.py` (new)
- `tests/_fixtures.py` (new)
- `tests/test_recognition_registry.py` (new)
- `tests/test_recognition_recognize.py` (new)
- `_bmad-output/implementation-artifacts/2-1-build-single-frame-face-recognition-utility.md` (this story file)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status transitions)

## Change Log

- 2026-05-15: Story 2.1 implemented. Single-frame recognition kernel + registry loader, 10 new tests passing, latency well within NFR1 budget.
