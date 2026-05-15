# Story 1.1: Verify dlib + face_recognition install on Windows demo machine

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a buildathon operator,
I want to verify that dlib and face_recognition install cleanly on the Windows demo machine,
so that the dominant platform risk (AR1) is eliminated within the first 30 minutes.

## Acceptance Criteria

1. Given a clean Python 3.11+ virtualenv on the Windows demo machine, when I run the corrected two-step install sequence, then the face-recognition runtime stack installs without source-compiling `dlib`, invoking CMake, or requiring Visual Studio C++ Build Tools:
   - `python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models`
   - `python -m pip install face_recognition --no-deps`
2. The install log must show `dlib-bin` wheel installation and no source `dlib` build. The elapsed install time and cache state must be recorded; cached repeat install target is less than 60 seconds.
3. `pip check` may report `face-recognition` missing distribution `dlib`; this is an accepted packaging metadata exception only if runtime imports and the 128-dimensional embedding smoke test pass.
4. I can run a smoke-test script that loads a sample image, detects at least one face, and computes a 128-dimensional embedding without error.
5. The smoke-test script is saved as `tests/smoke_dlib.py` for future re-verification on a fresh machine.
6. If no real sample face image exists yet, the smoke test must fail with a clear message telling the operator where to put the image, rather than silently passing or downloading external data.
7. The verification result is captured in the story Dev Agent Record with Python version, pip version, installed package versions, command used, elapsed install time, cache state, `pip check` result, smoke output, and whether source compilation was avoided.

## Tasks / Subtasks

- [x] Confirm local Windows Python environment baseline (AC: 1, 6)
  - [x] Record `python --version` and `python -m pip --version`.
  - [x] Create or identify a clean virtualenv for the verification run.
  - [x] Upgrade pip in that virtualenv before installing packages.
- [x] Document failed original dependency path (AC: 7)
  - [x] Run `python -m pip install dlib-bin face_recognition opencv-python` inside the clean virtualenv.
  - [x] Time the install and record whether it completes in less than 60 seconds.
  - [x] Inspect install output for source-build red flags: `Building wheel for dlib`, CMake errors, compiler errors, or Visual Studio Build Tools prompts.
  - [x] Record installed versions using `python -m pip freeze`.
- [x] Verify corrected dependency installation path (AC: 1, 2, 3, 7)
  - [x] Create or identify a fresh clean virtualenv for the corrected verification run.
  - [x] Run `python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models` inside the clean virtualenv.
  - [x] Run `python -m pip install face_recognition --no-deps` inside the same virtualenv.
  - [x] Time the install and record cache state.
  - [x] Inspect install output for source-build red flags: `Building wheel for dlib`, CMake errors, compiler errors, or Visual Studio Build Tools prompts.
  - [x] Record installed versions using `python -m pip freeze`.
  - [x] Run and record `pip check`; treat only the known missing `dlib` distribution warning as acceptable if runtime smoke passes.
- [x] Create durable smoke-test script (AC: 4, 5, 6)
  - [x] Create `tests/smoke_dlib.py`.
  - [x] The script accepts an optional image path argument and defaults to `tests/assets/smoke-face.jpg`.
  - [x] The script imports `cv2`, `dlib`, `face_recognition`, and `face_recognition_models`.
  - [x] The script loads the image from disk, converts BGR to RGB when using OpenCV, detects faces, computes encodings, asserts the first encoding length is 128, and prints a concise success line.
  - [x] If the image is missing, unreadable, has no faces, or produces no encodings, the script exits non-zero with a clear operator-facing error.
- [x] Run and record smoke verification (AC: 4, 7)
  - [x] Place or reference a local face image for the smoke test.
  - [x] Run `python tests/smoke_dlib.py <path-to-local-face-image>`.
  - [x] Record the output and any remediation needed.
- [x] Update story records only after verification is real (AC: 7)
  - [x] Add the corrected install command, elapsed time, cache state, versions, `pip check` result, and smoke-test result to Dev Agent Record.
  - [x] Add `tests/smoke_dlib.py` to File List.
  - [x] Do not mark this story complete if package installation or smoke-test execution was not actually performed.

### Review Findings

- [x] [Review][Patch] Resolve default smoke image relative to the script path [tests/smoke_dlib.py:20] - fixed by deriving `DEFAULT_IMAGE` from `Path(__file__).resolve().parent`, so the default path is stable even when the script is launched from another working directory.
- [x] [Review][Patch] Remove stale completion and changelog wording from the story record [_bmad-output/implementation-artifacts/1-1-verify-dlib-face-recognition-install-on-windows-demo-machine.md:155] - fixed by replacing outdated blocked/ready-for-dev text with the final reviewed status.

## Dev Notes

### Critical Scope

- This story is a platform-risk spike plus durable smoke test. It does not initialize the full repo layout, create `requirements.txt`, create `.gitignore`, or build the video player. Those belong to Story 1.2 and later.
- The only expected project file addition is `tests/smoke_dlib.py`; a local sample image may be used for verification, but avoid committing biometric/source face images unless a later story explicitly allows it.
- No outbound network behavior belongs in the smoke script. Package installation naturally uses pip; the runtime smoke test must use only a local file.

### Technical Requirements

- Use Python 3.11+ on Windows. Current local machine observation during story creation: `Python 3.13.8`, `pip 25.3`.
- Use `dlib-bin`, not the source `dlib` package, for this first install path. The corrected install path must install runtime dependencies explicitly, then install `face_recognition --no-deps`.
- Pin `setuptools<81` because `face_recognition_models==0.3.0` imports `pkg_resources`, which setuptools removed in v82.
- `pip check` may report that `face-recognition` requires distribution `dlib`; this is acceptable only when `import dlib` resolves to the `dlib-bin` module and the smoke test produces a 128-dimensional embedding.
- Use `face_recognition` as the high-level API for face locations and 128-dimensional encodings. Use OpenCV only for image loading/color conversion in this smoke test.
- Smoke-test behavior should be deterministic and small:
  - Input: path to one local image containing a visible front-facing face.
  - Output success: one line including face count and embedding dimension, for example `OK: faces=1 embedding_dim=128`.
  - Output failure: one clear error to stderr and a non-zero exit code.

### Architecture Compliance

- Project type is a Python 3.11+ Windows desktop application. Later stories add PyQt6 player, multiprocessing recognition worker, Telegram bot, shared writer module, and config. Do not introduce those in Story 1.1.
- MVP privacy rule: camera frames and biometric data stay on-device. For this story, the smoke script must not download images, call cloud APIs, or persist camera frames.
- Later architecture depends on dlib/face_recognition being viable before any UI or supervisor work begins. If this verification fails, stop and document the exact failure; do not continue into Story 1.2 blindly.

### Library / Framework Facts

- PyPI shows `dlib-bin` latest version `20.0.1`, released March 30, 2026, with Windows x86-64 wheels for modern CPython versions including 3.10, 3.11, 3.12, 3.13, and 3.14. Source: https://pypi.org/project/dlib-bin/
- PyPI shows `face-recognition` latest version `1.3.0`, released February 20, 2020. Its history notes dlib minimum requirements and speed improvements from the 5-point face pose estimator. Source: https://pypi.org/project/face-recognition/
- PyPI/OpenCV packaging docs state `opencv-python` provides prebuilt wheels for supported non-EOL Python 3 versions through Python 3.13. Source: https://pypi.org/project/opencv-python/
- Because `face-recognition` is old relative to current Python versions, the developer must trust the actual clean-venv install result over assumptions. Capture the real versions and failure mode if it does not install.
- Technical research concluded the original single install command is invalid for this environment and should be replaced by the two-step `dlib-bin` plus `face_recognition --no-deps` sequence. Source: `_bmad-output/planning-artifacts/research/technical-windows-face-recognition-dependency-strategy-research-2026-05-15T180423+05-00.md`
- Correct Course approved this as a minor direct adjustment. Source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-15-181640.md`

### File Structure Requirements

- Create: `tests/smoke_dlib.py`
- Optional local-only verification asset path: `tests/assets/smoke-face.jpg`
- Do not create final project layout here except parent directories needed for the smoke script.
- Story 1.2 will create the canonical layout: `videos/`, `faces/`, `logs/`, `run.py`, `requirements.txt`, `config.yaml.example`, `.gitignore`, and README skeleton.

### Testing Requirements

- The smoke script itself is the executable verification artifact.
- Run it inside the same virtualenv where the packages were installed.
- It must fail loudly for missing image, unreadable image, no detected faces, and no face encodings.
- A passing smoke run requires at least one 128-dimensional encoding.

### Project Structure Notes

- Current repo state during story creation: no app source files, no git repository, and no existing test tree. Only BMAD planning/config folders are present.
- There is no separate architecture or UX file. Architecture-relevant requirements are embedded in `_bmad-output/planning-artifacts/prd.md` and `_bmad-output/planning-artifacts/epics.md`.

### References

- `_bmad-output/planning-artifacts/epics.md` - Story 1.1, Epic 1 sequencing, AR1.
- `_bmad-output/planning-artifacts/prd.md` - Desktop Application Specific Requirements, Platform Support, Implementation Considerations, Risk Mitigation Strategy.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - sprint order and current story key.
- PyPI `dlib-bin`: https://pypi.org/project/dlib-bin/
- PyPI `face-recognition`: https://pypi.org/project/face-recognition/
- PyPI `opencv-python`: https://pypi.org/project/opencv-python/

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Story creation: loaded BMAD sprint status, epics, PRD, config, template, checklist.
- Story creation: no architecture/UX documents found; no `project-context.md` found; no git repository found.
- Story creation: local shell reported `Python 3.13.8` and `pip 25.3`.
- 2026-05-15T17:56:27+05:00: Story moved to `in-progress` in sprint status.
- 2026-05-15T17:56:xx+05:00: Baseline environment: `Python 3.13.8`; global pip: `pip 25.3`.
- 2026-05-15T17:56:xx+05:00: Created clean verification virtualenv at `.venv-smoke-dlib`.
- 2026-05-15T17:57:xx+05:00: Upgraded virtualenv pip from `25.2` to `26.1.1`.
- 2026-05-15T18:00:38+05:00: Ran install command in clean venv: `python -m pip install dlib-bin face_recognition opencv-python`; elapsed `150.185` seconds; full log saved to `_bmad-output/implementation-artifacts/1-1-dlib-install.log`.
- 2026-05-15T18:00:38+05:00: Install failed. `dlib-bin-20.0.1-cp313-cp313-win_amd64.whl` was downloaded, but `face_recognition` dependency resolution also downloaded source `dlib-20.0.1.tar.gz`, attempted `Building wheel for dlib`, invoked CMake, and failed because Visual Studio C++ Build Tools are not installed.
- 2026-05-15T18:00:38+05:00: `python -m pip freeze` in `.venv-smoke-dlib` returned no installed application packages after the failed install.
- 2026-05-15: Technical research completed and recommended keeping dlib/face_recognition while replacing the install command with explicit dependencies plus `face_recognition --no-deps`.
- 2026-05-15: Correct Course proposal approved and applied as a minor direct adjustment.
- 2026-05-15T18:19:xx+05:00: Created fresh corrected verification virtualenv at `.venv-smoke-dlib-corrected` and upgraded pip to `26.1.1`.
- 2026-05-15T18:20:xx+05:00: Ran corrected install sequence: `python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models` followed by `python -m pip install face_recognition --no-deps`; elapsed `17.847` seconds using cached wheels; full log saved to `_bmad-output/implementation-artifacts/1-1-dlib-corrected-install.log`.
- 2026-05-15T18:20:xx+05:00: Corrected install log shows `dlib_bin-20.0.1-cp313-cp313-win_amd64.whl` and cached wheels for all packages. No `Building wheel for dlib`, CMake, Visual Studio, compiler, or failed-wheel red flags were found.
- 2026-05-15T18:21:xx+05:00: Corrected virtualenv versions: `Python 3.13.8`; `pip 26.1.1`; packages `click==8.3.3`, `colorama==0.4.6`, `dlib-bin==20.0.1`, `face-recognition==1.3.0`, `face_recognition_models==0.3.0`, `numpy==2.4.4`, `opencv-python==4.13.0.92`, `pillow==12.2.0`, `setuptools==80.10.2`.
- 2026-05-15T18:22:xx+05:00: `pip check` returned the expected metadata exception only: `face-recognition 1.3.0 requires dlib, which is not installed.`
- 2026-05-15T18:22:xx+05:00: Runtime import proof passed for `cv2`, `dlib`, `face_recognition`, and `face_recognition_models`; `dlib.__version__` reported `20.0.1`; model path resolved to the installed `dlib_face_recognition_resnet_model_v1.dat`.
- 2026-05-15T18:22:xx+05:00: Created `tests/smoke_dlib.py`. Running without an image exits non-zero with clear message telling the operator to place a clear front-facing image at the script-local `tests\assets\smoke-face.jpg` path or pass a local image path.
- 2026-05-15T18:26:xx+05:00: Ran smoke verification with user-provided local image `faces\photo_2026-05-15_17-16-47.jpg`; output: `OK: faces=1 embedding_dim=128`.
- 2026-05-15T18:26:xx+05:00: All Story 1.1 acceptance criteria satisfied; story moved to `review`.
- 2026-05-15T18:31:xx+05:00: Code review completed. Fixed default smoke image path to resolve relative to `tests/smoke_dlib.py` instead of the caller working directory, cleaned stale story notes, reran smoke success and missing-image checks from both project-root and external working directories, and moved story to `done`.

### Completion Notes List

- Created comprehensive Story 1.1 context for dlib/face_recognition Windows install verification.
- Story was implemented, verified, reviewed, and completed.
- Original install path failed as expected and was documented: it attempted source compilation of `dlib`, invoked CMake, and failed on missing Visual Studio C++ Build Tools.
- Correct Course changed the install strategy to explicit runtime dependencies plus `face_recognition --no-deps`.
- Corrected dependency verification passed in `.venv-smoke-dlib-corrected`: cached install completed in `17.847` seconds, used the `dlib-bin` wheel, avoided source compilation, and runtime imports resolve.
- Smoke-test script was added and its missing-image failure path was verified.
- Smoke verification passed against `faces\photo_2026-05-15_17-16-47.jpg` with output `OK: faces=1 embedding_dim=128`.
- Code review findings were resolved and Story 1.1 is done.

### File List

- `_bmad-output/implementation-artifacts/1-1-verify-dlib-face-recognition-install-on-windows-demo-machine.md`
- `_bmad-output/implementation-artifacts/1-1-dlib-install.log`
- `_bmad-output/implementation-artifacts/1-1-dlib-corrected-install.log`
- `tests/smoke_dlib.py`
- `_bmad-output/planning-artifacts/research/technical-windows-face-recognition-dependency-strategy-research-2026-05-15T180423+05-00.md`
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-15-181640.md`

## Change Log

- 2026-05-15: Created Story 1.1 context file and marked ready-for-dev.
- 2026-05-15: Started Story 1.1 verification and documented failed Windows dependency install gate.
- 2026-05-15: Corrected Story 1.1 install strategy via approved Correct Course proposal.
- 2026-05-15: Verified corrected dependency install path and added durable smoke-test script.
- 2026-05-15: Ran smoke verification with a local face image and moved Story 1.1 to review.
- 2026-05-15: Resolved code-review findings and moved Story 1.1 to done.
