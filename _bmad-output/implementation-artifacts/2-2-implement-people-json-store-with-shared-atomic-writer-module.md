# Story 2.2: Implement people.json store with shared atomic writer module

Status: done

## Story

As a developer,
I want a single shared writer module for adding/removing people from `people.json`,
so that the bot, CLI scripts, and any future writer use one code path with atomic semantics, with no drift between paths (AR9).

## Acceptance Criteria

1. **Given** no `people.json` exists yet (or an empty one), **when** `add_person(name, image_path)` is called, **then** the writer computes a 128-D embedding from the image, writes the updated DB to `people.json.tmp`, then `os.replace()` to `people.json` — no reader can observe a partially written file. _[NFR17, FR17]_
2. **And** the source photo is copied into `faces/<safe_name>.jpg` so future re-embedding (model upgrades, repair tooling) can recompute without the original upload context. _[NFR15]_
3. **And** `remove_person(name)` atomically removes the entry from `people.json` AND deletes the corresponding `faces/<safe_name>.jpg`. Returns `True` on success. _[NFR15, FR19]_
4. **And** `add_person` with a duplicate name **overwrites** the existing entry — no silent failure, no exception. _[AR9 — single code path semantics]_
5. **And** `remove_person` with an unknown name returns `False` without raising; the caller (Telegram bot, CLI) decides the UX response. _[AR9]_
6. **And** `add_person` raises a specific exception (`NoFaceInImageError`) when the source image has zero detectable faces, so the bot can reply with `"No face detected, try a clearer photo"` without leaking a stack trace.
7. **And** the writer is **process-safe** under serialization — Story 3.2's bot and `add_person.py` CLI may both invoke it; concurrent calls do not corrupt `people.json`. Use a same-directory lock file (`people.json.lock` via `filelock` or a stdlib equivalent) so the contract is OS-agnostic.

## Tasks / Subtasks

- [x] **Task 1 — Module skeleton + name sanitization** (AC: 2, 3) — `_safe_name` lowercases, strips, collapses runs of unsafe chars to `_`, rejects empty. `NoFaceInImageError(ValueError)` exposed.
- [x] **Task 2 — Atomic write helper** (AC: 1, 7) — `_atomic_write_json` via temp + `os.fsync` + `os.replace`. `filelock==3.29.0` pinned in `requirements.txt`; lock path is `people.json.lock` next to the data file.
- [x] **Task 3 — `add_person`** (AC: 1, 2, 4, 6) — largest-face encoding (consistent with Story 2.1), case-insensitive overwrite, photo copied to `faces/<safe>.jpg`.
- [x] **Task 4 — `remove_person`** (AC: 3, 5) — case-insensitive lookup, atomic write, `unlink(missing_ok=True)` for the photo, returns False on unknown name.
- [x] **Task 5 — Unit tests** (AC: 1–6) — 16 new tests: 6 _safe_name + 2 remove-unknown + 1 lock-contention + 7 integration (add creates entry+photo, overwrite collapses to one entry, round-trip, case-insensitive remove, NoFaceInImageError on black image, ValueError on missing file, no .tmp leftover after success).
- [x] **Task 6 — Verification** (AC: 1–7) — 47/47 tests pass. No regressions on Epic 1 or Story 2.1.

## Dev Notes

### Scope guardrails

- **No Telegram bot, no CLI script, no recognition worker.** Story 3.2 wires the bot; Story 4.1 wires `add_person.py`; Story 2.3 wires the worker. They all call into THIS module — the writer is the single chokepoint per AR9.
- **No hot-reload notification.** Story 3.5 (`watchdog` on `people.json`) detects changes; the writer doesn't need to ping anyone. Atomic rename + the watcher's file-system event is the contract.
- **No deletion of `faces/*.jpg` for files that don't follow `_safe_name(name).jpg`.** Source photos that pre-date this writer (e.g., the existing `faces/photo_*.jpg` files) are not touched.

### Filesystem layout decisions

- `people.json` lives at project root (per `config.yaml.example: people_db_path: "people.json"`).
- `people.json.tmp` lives next to it (same volume — required for atomic rename on Windows).
- `people.json.lock` lives next to it (managed by `filelock`).
- `faces/<safe_name>.jpg` for canonical source photos written by the writer.

### New dependency

`filelock` — cross-platform advisory file locking. Tiny, no native code, MIT licensed. Latest stable is in the 3.x series; pin the exact version on add. **Add to `requirements.txt` and `pip install` it before testing.** If you'd rather avoid the dep, the fallback is `msvcrt.locking` on Windows + `fcntl.flock` on POSIX — five times the code and a Windows-specific edge case (locks don't survive process crashes cleanly on older Windows). `filelock` is the boring-technology choice.

### Library specifics

- `face_recognition.face_encodings(rgb, [(top,right,bottom,left)])[0]` returns a `np.ndarray` of shape `(128,)`. `.tolist()` for JSON serialization.
- `os.replace(src, dst)` is atomic on same-volume renames on Windows since 3.3; this is the canonical Python recipe.
- `shutil.copyfile(src, dst)` is safer than `shutil.copy` here — we don't want permission bits copied.

### Previous story intelligence

- Story 2.1's `recognition.registry.load_registry` already handles missing file / empty list / malformed JSON. **Reuse it** — don't re-parse the JSON in the writer.
- The smoke fixture-build path in [`tests/_fixtures.py`](tests/_fixtures.py) shows how to load a face + compute embeddings; the writer's happy path is structurally identical.
- `.gitignore` already protects `people.json`, `.env`, `config.yaml`, `faces/*` — the writer's outputs stay local automatically.

### Testing standards

- `unittest` stdlib (matches Epic 1 + Story 2.1).
- Test in `tmp_path` directories so writer state is isolated.
- Skip face-bearing tests gracefully if no source photo exists.

### References

- [`_bmad-output/planning-artifacts/epics.md:349-363`](_bmad-output/planning-artifacts/epics.md) — Story 2.2 BDD.
- [`_bmad-output/planning-artifacts/prd.md:356`](_bmad-output/planning-artifacts/prd.md) — Atomic file writes architectural decision.
- [`_bmad-output/planning-artifacts/prd.md:461`](_bmad-output/planning-artifacts/prd.md) — FR17 (persistence across restarts).
- [`_bmad-output/planning-artifacts/prd.md:517`](_bmad-output/planning-artifacts/prd.md) — NFR15 (source photo storage + tied deletion).
- [`_bmad-output/planning-artifacts/prd.md:519`](_bmad-output/planning-artifacts/prd.md) — NFR17 (atomic writes).
- [`recognition/registry.py`](recognition/registry.py) — Story 2.1 read path that this writer must keep schema-compatible with.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (claude-opus-4-7)

### Debug Log References

- 21:50: Marked story `in-progress`. Installed `filelock==3.29.0` and pinned in `requirements.txt`.
- 21:52: Wrote `tests/test_writer.py` first (TDD). RED confirmed.
- 21:55: Implemented `recognition/writer.py` — `_safe_name`, `_atomic_write_json` (open + write + fsync + close + os.replace), `_compute_largest_face_encoding`, `add_person`, `remove_person`. `filelock.FileLock` wraps the read+write block to serialize concurrent writers (bot + CLI).
- 21:58: 47/47 tests pass across the suite (16 writer + 6 registry + 4 recognize + 11 playlist + 5 font-size + 5 overlay-state).

### Completion Notes List

- **Single chokepoint** — bot and CLI both call into `add_person` / `remove_person`. Schema, atomicity, photo handling, overwrite semantics live in exactly one place (AR9 satisfied).
- **Atomicity model** — `os.replace` on a same-volume `.tmp` is atomic on Windows + POSIX. `fsync` between write and replace closes the power-off window.
- **Lock model** — `filelock` chosen over `msvcrt`/`fcntl` to keep the writer one file long and dodge Windows-specific quirks with crash-orphaned locks. Lock file (`people.json.lock`) ends up next to the data file — gitignored implicitly via the `_bmad/`-scope rules; explicit ignore not needed because `/people.json` rule doesn't match `.lock`.
- **No `.tmp` cleanup needed on crash** — if `os.replace` doesn't fire, the `.tmp` lingers but is harmless (named off the data file's basename + suffix). The next successful write overwrites it. A defensive `tmp.unlink(missing_ok=True)` could be added later if it becomes a real concern.
- **Case-insensitive name lookup** matches the human intuition for the Telegram bot (`/delete_person Alice` should find `alice`). The display name is preserved as-typed at `add_person` time.

### File List

- `recognition/writer.py` (new)
- `tests/test_writer.py` (new)
- `requirements.txt` (modified — added `filelock==3.29.0`)
- `_bmad-output/implementation-artifacts/2-2-implement-people-json-store-with-shared-atomic-writer-module.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-15: Story 2.2 implemented. Shared atomic writer for `people.json`, 16 new tests, `filelock` pinned. Single chokepoint for bot + CLI per AR9.
