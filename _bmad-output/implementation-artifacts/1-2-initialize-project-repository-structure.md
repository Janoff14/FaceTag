# Story 1.2: Initialize project repository structure

Status: done

## Story

As the operator,
I want a clean project root with the canonical folder layout, pinned dependencies, and protected secrets,
so that all subsequent code has a known place to live and no sensitive files leak into git.

## Acceptance Criteria

1. Given `git init` is run in the project folder, when project setup completes, then the project has the canonical layout required by Epic 1:
   - `videos/.gitkeep`
   - `tests/assets/seed-promo.mp4`
   - `tests/smoke_dlib.py` from Story 1.1
   - `faces/`
   - `logs/`
   - `run.py`
   - `requirements.txt`
   - `config.yaml.example`
   - `.gitignore`
   - `README.md`
2. `requirements.txt` pins all direct Python dependencies with exact `==` versions.
3. `.gitignore` protects `config.yaml`, `.env`, local virtualenvs, `logs/`, `faces/`, `videos/*`, `videos/.tmp/`, and local tooling/artifact folders while keeping required `.gitkeep` files trackable.
4. `config.yaml.example` is committed as a safe template only. Real Telegram token and admin chat IDs must not be written into tracked files.
5. `README.md` contains skeleton sections: Setup, Architecture, Selection Strategy, Threading Model, Benchmark Results.
6. Setup notes explain that `tests/assets/seed-promo.mp4` should be copied into `videos/` before running the player locally.
7. Running repository status checks shows no Telegram token, `.env`, `config.yaml`, face photos, logs, promo media, or playlist videos pending commit.
8. The local git repository is attached to `https://github.com/Janoff14/FaceTag.git` as `origin`, preserving the remote `main` branch history.

## Tasks / Subtasks

- [x] Initialize/attach repository (AC: 1, 8)
  - [x] Initialize git if missing.
  - [x] Attach `origin` to `https://github.com/Janoff14/FaceTag.git`.
  - [x] Track `main` from `origin/main` without overwriting user assets.
- [x] Create canonical folders and placeholder files (AC: 1, 3)
  - [x] Create `videos/`, `videos/.tmp/`, `faces/`, `logs/`, and `tests/assets/`.
  - [x] Add trackable `.gitkeep` placeholders for folders that should exist in a fresh clone.
  - [x] Preserve Story 1.1 `tests/smoke_dlib.py`.
  - [x] Create empty `run.py`.
  - [x] Create `tests/assets/seed-promo.mp4`.
- [x] Add dependency and config templates (AC: 2, 4)
  - [x] Create `requirements.txt` with exact pinned direct dependencies.
  - [x] Create `config.yaml.example` without real secrets.
- [x] Add ignore rules and README skeleton (AC: 3, 5, 6)
  - [x] Create `.gitignore` covering secrets, runtime data, media, virtualenvs, and local BMad/tooling artifacts.
  - [x] Update `README.md` with required sections and seed-promo copy instruction.
- [x] Verify repository safety and setup artifacts (AC: 1, 2, 3, 6, 7, 8)
  - [x] Verify files/directories exist.
  - [x] Verify requirements use `==` pins.
  - [x] Verify `origin` remote.
  - [x] Verify ignored secrets/media are not pending commit.
  - [x] Verify no real Telegram token appears in tracked project files.

### Review Findings

_2026-05-15 — bmad-code-review (Blind Hunter + Edge Case Hunter + Acceptance Auditor)_

**Decision needed (resolve before commit):**

- [ ] [Review][Decision] **Real Telegram bot token shared in chat** — Operator pasted a live token in this session. Revoke + reissue via `@BotFather` (`/revoke`, then `/token`). Confirm rotation before any commit so the compromised token cannot be tied back to this repo's commit history.
- [ ] [Review][Decision] **`config.yaml.example` placeholder convention** — Value is `"${TELEGRAM_BOT_TOKEN}"` literal. PyYAML does not expand env vars on load. Pick one: (a) keep as plain "fill-me-in" placeholder and update README to say "edit `config.yaml` directly", or (b) commit to env-var expansion at load time and choose a clearer marker (e.g. `"${TELEGRAM_BOT_TOKEN:?set me}"`). Loader code is Story 3.2 — decide convention now so 3.2 has a contract. [`config.yaml.example:4`, `README.md:21`]
- [ ] [Review][Decision] **`_bmad-output/` ignored — story spec & sprint-status cannot be committed** — `.gitignore:30` excludes the directory that contains `1-2-initialize-project-repository-structure.md` and `sprint-status.yaml`, both listed in this story's File List. Either (a) commit BMad artifacts (remove `_bmad-output/` from `.gitignore`, optionally keep `_bmad-output/**/.tmp/` ignored), or (b) accept that planning/implementation docs live local-only and remove them from the File List. [`.gitignore:30`]
- [ ] [Review][Decision] **`_bmad/` runtime config ignored — fresh clone has no BMad** — Same call as above: `_bmad/config.toml`, `_bmad/bmm/`, `_bmad/core/`, `_bmad/scripts/` are runtime config, not user working state. Collaborators who clone won't have BMad available. Decide whether to track. [`.gitignore:29`]

**Patches (unambiguous fixes):**

- [ ] [Review][Patch] **`tests/smoke_dlib.py` defaults to `tests/assets/smoke-face.jpg`, which is not tracked** — Running with no args always fails. Either make the `image` arg required (drop `nargs="?"` and `default=None`), or ship a small tracked test face image. [`tests/smoke_dlib.py:20`]
- [ ] [Review][Patch] **Commit the Story 1.2 scaffold** — Working tree is uncommitted on `main`; AC8 says origin is attached preserving history, so create a commit (e.g. `chore(1.2): scaffold repository structure`) before merging. [working tree]
- [ ] [Review][Patch] **Tighten `_bmad/` and `_bmad-output/` ignore patterns with leading slash** — Without `/`, the patterns match any nested `_bmad/` (e.g. a future vendored dir would be silently ignored). Change to `/_bmad/` and `/_bmad-output/`. Only relevant if the Decision items above resolve as "keep ignored". [`.gitignore:29-30`]
- [ ] [Review][Patch] **Redundant `videos/.tmp/` ignore rule** — `videos/*` on line 19 already covers it. Drop line 21 or keep as a self-documenting comment. [`.gitignore:21`]

**Deferred (real but not blocking 1.2):**

- [x] [Review][Defer] `smoke_dlib.py` says "image file unreadable" when `cv2.imread` returns None on a non-image file — wording is misleading. [`tests/smoke_dlib.py:49`] — deferred, UX nit.
- [x] [Review][Defer] `smoke_dlib.py` silently picks first face on multi-face image — doesn't exercise the "largest face wins" selection strategy promised in README. [`tests/smoke_dlib.py:56-60`] — deferred, selection strategy lives in Epic 2.
- [x] [Review][Defer] No `tests/assets/.gitkeep` — folder relies on the mp4 to exist in git. [`tests/assets/`] — deferred, low risk.
- [x] [Review][Defer] No secondary safety net (pre-commit hook) for accidental face-photo staging if `faces/*` ignore is ever weakened. [`.gitignore:15`] — deferred, defensive layer.
- [x] [Review][Defer] `.venv*/` wildcard could over-match a hypothetical future tracked `.venv-docs/`. [`.gitignore:8`] — deferred, hypothetical.

**Dismissed as false positives:**

- Blind Hunter flagged `requirements.txt` versions as fabricated. Story 1.1 install log (`_bmad-output/implementation-artifacts/1-1-dlib-corrected-install.log`) shows successful installs for every pinned version including `dlib-bin-20.0.1`, `numpy-2.4.4`, `opencv-python-4.13.0.92`, `Pillow-12.2.0`, `setuptools-80.10.2`.
- Edge Case Hunter flagged `numpy 2.4.4` vs installed `2.3.3` mismatch — the active interpreter was a different venv; Story 1.1's proven venv used 2.4.4.
- Edge Case Hunter flagged `setuptools 80.10.2` breaks `face-recognition-models` install via removed `2to3` — Story 1.1 log proves the install succeeds with these exact pins.
- Empty `run.py` flagged as broken — per story scope ("Create empty run.py"), implementation lives in later Epic 1 stories.
- `PyYAML` listed but unused — intentional pre-pin for Story 3.2 loader.
- README "FaceTag" vs project name "facial recognition - uzc" — "FaceTag" is the operator-chosen product/repo name (matches GitHub remote).
- `videos/seed-promo.mp4` copy step UX concerns — `videos/.gitkeep` is tracked, so the folder exists on fresh clone.

## Dev Notes

### Scope

- This story is repository scaffolding only. Do not implement the player, recognition worker, Telegram bot, writer module, or CLI fallbacks.
- Do not write the real Telegram bot token into any tracked file, log, story, or README. Use placeholders or environment variable names only.
- Existing local `faces/` and `promos/` folders may contain private/media assets. Preserve them on disk, but do not make them pending tracked files.

### Required Layout

- Canonical runtime folders: `videos/`, `faces/`, `logs/`.
- Playlist files go under `videos/`, but `videos/*` must be ignored except `videos/.gitkeep`.
- Temporary video writes later use `videos/.tmp/`, which must be ignored.
- Face source photos stay under `faces/` and must be ignored.
- Runtime logs stay under `logs/` and must be ignored.

### Dependency Notes

- Story 1.1 proved the Windows install path requires `dlib-bin` plus `face_recognition --no-deps`, with `setuptools<81` because `face_recognition_models==0.3.0` imports `pkg_resources`.
- `requirements.txt` should keep the proven exact package versions from Story 1.1 and add the direct dependencies needed by later planned stories: PyQt6, watchdog, python-telegram-bot, and PyYAML.

### References

- `_bmad-output/planning-artifacts/epics.md` - Story 1.2 and AR2-AR5, AR10, AR13.
- `_bmad-output/planning-artifacts/prd.md` - NFR16, NFR28, project setup and README expectations.
- `_bmad-output/implementation-artifacts/1-1-verify-dlib-face-recognition-install-on-windows-demo-machine.md` - proven dependency versions and smoke script.
- GitHub remote: `https://github.com/Janoff14/FaceTag.git`

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- 2026-05-15T18:xx: Story 1.1 completed and sprint status showed Story 1.2 as the next backlog story.
- 2026-05-15T18:xx: User provided GitHub remote and a Telegram token. Token treated as sensitive and not written into project files.
- 2026-05-15T18:39: Initialized local git repository, attached `origin`, fetched `origin/main`, and checked out local `main` tracking remote history.
- 2026-05-15T18:39: Created canonical folders and placeholders: `videos/.gitkeep`, `faces/.gitkeep`, `logs/.gitkeep`, `videos/.tmp/`, and `tests/assets/`.
- 2026-05-15T18:39: Generated small tracked sample video `tests/assets/seed-promo.mp4` using OpenCV; verified it opens with 48 frames at 320x180.
- 2026-05-15T18:39: Added `.gitignore`, exact-pinned `requirements.txt`, secret-free `config.yaml.example`, empty `run.py`, and README skeleton with seed-promo copy instruction.
- 2026-05-15T18:39: Verified `git status --short -uall` shows only safe scaffold files pending; private face photos, local promo assets, config secrets, logs, and playlist videos are ignored.
- 2026-05-15T18:39: Secret scan for Telegram-token-shaped values returned no matches in project files.
- 2026-05-15T18:39: Re-ran Story 1.1 smoke script against `faces\photo_2026-05-15_17-16-47.jpg`; output `OK: faces=1 embedding_dim=128`.

### Completion Notes List

- Initialized local repo on `main` tracking `origin/main` at `https://github.com/Janoff14/FaceTag.git`.
- Created the Story 1.2 repository skeleton while preserving local private face photos and promo videos as ignored assets.
- Added pinned dependency file, config template with placeholders only, README skeleton, empty entrypoint, tracked folder placeholders, and a small tracked seed promo.
- Verified no real Telegram token or private media is pending commit. Story 1.2 is ready for review.

### File List

- `_bmad-output/implementation-artifacts/1-2-initialize-project-repository-structure.md`
- `.gitignore`
- `README.md`
- `config.yaml.example`
- `requirements.txt`
- `run.py`
- `videos/.gitkeep`
- `faces/.gitkeep`
- `logs/.gitkeep`
- `tests/assets/seed-promo.mp4`
- `tests/smoke_dlib.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-05-15: Created Story 1.2 and started implementation.
- 2026-05-15: Implemented repository skeleton and moved Story 1.2 to review.
