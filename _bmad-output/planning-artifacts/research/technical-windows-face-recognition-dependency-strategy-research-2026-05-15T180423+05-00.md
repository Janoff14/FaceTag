---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Windows face-recognition dependency strategy after face_recognition pulls source dlib on Python 3.13'
research_goals: 'Find the fastest reliable Windows install path for the project after Story 1.1 failed: decide whether to keep dlib/face_recognition with adjusted install constraints, pin Python, use dlib-bin differently, install C++ build tools, or switch to a fallback stack such as MediaPipe.'
user_name: 'Sanja'
date: '2026-05-15T18:04:23+05:00'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-15T18:04:23+05:00
**Author:** Sanja
**Research Type:** technical

---

## Research Overview

This research investigates the Windows dependency failure discovered during Story 1.1: `pip install dlib-bin face_recognition opencv-python` downloaded `dlib-bin`, but `face_recognition` still pulled source `dlib`, invoked CMake, and failed without Visual Studio C++ Build Tools. The goal was to determine whether the project should correct its dlib/face_recognition install path, pin Python, install build tools, or switch to a fallback such as MediaPipe.

The evidence supports a narrow course correction: keep the current dlib/face_recognition architecture, but replace the single install command with an explicit wheel-first sequence using `setuptools<81`, `dlib-bin`, explicit runtime dependencies, and `face_recognition --no-deps`. Local proof on Python 3.13 validated runtime imports after this correction. See the Research Synthesis section for the final recommendation and Correct Course handoff.

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technical Research Scope Confirmation

**Research Topic:** Windows face-recognition dependency strategy after `face_recognition` pulls source `dlib` on Python 3.13

**Research Goals:** Find the fastest reliable Windows install path for the project after Story 1.1 failed: decide whether to keep dlib/face_recognition with adjusted install constraints, pin Python, use dlib-bin differently, install C++ build tools, or switch to a fallback stack such as MediaPipe.

**Technical Research Scope:**

- Architecture Analysis - impact on the recognition worker and future benchmark requirements
- Implementation Approaches - install strategy, smoke-test strategy, and dependency pinning
- Technology Stack - Python, dlib-bin, face_recognition, OpenCV, MediaPipe fallback
- Integration Patterns - local image/frame input, embeddings, future worker process compatibility
- Performance Considerations - CPU-only Windows demo machine, no GPU requirement, install-time risk

**Research Methodology:**

- Current web data with source verification from PyPI and official vendor docs
- Local proof run in a clean Python 3.13 venv to validate the likely workaround
- Confidence levels stated where package metadata and runtime behavior differ

**Scope Confirmed:** 2026-05-15T18:04:23+05:00

## Technology Stack Analysis

### Programming Languages

Python remains the right language for this project because every current project artifact assumes a Python desktop app on a single Windows laptop. The failed install happened on `Python 3.13.8`; current package metadata shows this version is not inherently the blocker for `dlib-bin` or `opencv-python`.

Key finding: Python 3.13 can import the dlib/face_recognition runtime when dependencies are installed manually, but the default `pip install dlib-bin face_recognition opencv-python` command fails because `face_recognition` asks pip for the `dlib` distribution name, not `dlib-bin`.

_Popular Languages:_ Python is still the practical choice for this buildathon scope; switching language would invalidate most planning artifacts.

_Language Evolution:_ Python 3.13 venvs may not include old compatibility modules that legacy packages expect. In local testing, `face_recognition_models` needed `pkg_resources`, requiring `setuptools<81`.

_Performance Characteristics:_ Python is acceptable because the PRD already isolates CPU-heavy recognition in a separate worker process. No language change is recommended.

_Sources:_ PyPI `face-recognition` metadata and docs show Python support claims plus Windows caveat and `dlib` dependency: https://pypi.org/pypi/face_recognition/1.3.0/json and https://pypi.org/project/face-recognition/. Local proof log: `_bmad-output/planning-artifacts/research/dlib-nodeps-install-proof.log`.

### Development Frameworks and Libraries

**Recommended primary stack:** keep `dlib-bin` + `face_recognition`, but correct the install path:

```powershell
python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models
python -m pip install face_recognition --no-deps
```

Local proof on Python 3.13 completed the package install in `14.885s` from cache, then imported `cv2`, `dlib`, `face_recognition`, and `face_recognition_models` successfully after pinning `setuptools<81`. `dlib.__version__` reported `20.0.1`; `face_recognition.__version__` reported `1.2.3` even though package metadata reports `face-recognition==1.3.0`, so use `pip show`/`pip freeze` for package evidence.

**Why the original stack failed:** `face_recognition==1.3.0` declares `Requires-Dist: dlib (>=19.7)`. `dlib-bin==20.0.1` installs an importable `dlib` module but is a separate distribution, so pip still downloads source `dlib` to satisfy `face_recognition`. That triggers CMake and Visual Studio C++ Build Tools on Windows.

**Alternative stack:** MediaPipe is a strong face-detection fallback but not a drop-in identity-recognition replacement. Official MediaPipe Face Detector docs cover face locations/keypoints in images/video/live streams, not 128-dimensional person identity embeddings. Switching to MediaPipe alone would require a new identity embedding strategy and would change Epic 2/4 acceptance criteria.

_Major Frameworks:_ `face_recognition` provides the simplest identity-embedding API; MediaPipe provides modern prebuilt face detection/landmark tasks.

_Ecosystem Maturity:_ `face_recognition` is old: PyPI package `1.3.0` was uploaded February 20, 2020 and its docs state Windows is not officially supported. `dlib-bin` is current enough for Python 3.13 wheels. `opencv-python 4.13.0.92` has Windows x86-64 wheels tagged CPython 3.7+.

_Source:_ `face_recognition` requires `dlib>=19.7`: https://pypi.org/pypi/face_recognition/1.3.0/json. `dlib-bin` Windows cp313 wheel exists on PyPI: https://pypi.org/project/dlib-bin/. `opencv-python` Windows cp37-abi3 wheel metadata: https://pypi.org/project/opencv-python/4.13.0.92/. MediaPipe Face Detector docs: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/python.

### Database and Storage Technologies

No database technology change is implicated by this dependency issue. The planned `people.json` flat file remains appropriate for the MVP because Story 1.1 only proves package install and smoke embedding generation. Later stories still own atomic writes, hot reload, and deletion semantics.

_Relational Databases:_ Not recommended for this correction.

_NoSQL / File Storage:_ Keep `people.json` as planned.

_In-Memory Storage:_ Later worker process can keep embeddings in memory exactly as planned.

_Source:_ Existing PRD/epics define `people.json`; no web source changes this.

### Development Tools and Platforms

The cleanest developer-platform correction is to avoid compiling `dlib` on Windows. Installing Visual Studio C++ Build Tools would make source compilation possible, but it directly conflicts with Story 1.1 and AR1 intent: prove a prebuilt wheel path quickly.

Important tool finding: `pip check` may report `face-recognition` missing `dlib` when using the `dlib-bin` + `--no-deps` workaround, because runtime import succeeds but package metadata dependency resolution remains unsatisfied. This should be documented as an accepted packaging exception if this path is adopted.

_IDE and Editors:_ No impact.

_Version Control:_ No impact; repo initialization is still Story 1.2.

_Build Systems:_ Avoid source build tools for dlib in MVP. Use pip with explicit install steps and package pins.

_Testing Frameworks:_ Story 1.1 smoke test should verify imports and 128-dimensional embedding generation from a local image. Add one extra import check for `face_recognition_models` and document the `setuptools<81` pin.

_Sources:_ Local failed install log: `_bmad-output/implementation-artifacts/1-1-dlib-install.log`; local workaround proof log: `_bmad-output/planning-artifacts/research/dlib-nodeps-install-proof.log`.

### Cloud Infrastructure and Deployment

No cloud infrastructure is needed or recommended. The PRD privacy posture remains correct: all recognition data stays on-device, with outbound network only for Telegram in later stories.

_Major Cloud Providers:_ Not applicable.

_Container Technologies:_ Not needed for the buildathon Windows laptop target.

_Serverless Platforms:_ Not applicable.

_CDN and Edge Computing:_ Not applicable.

_Source:_ `face_recognition` docs mention Docker as a deployment workaround for cloud, but this project targets a local Windows laptop, so Docker adds risk rather than reducing it: https://pypi.org/project/face-recognition/.

### Technology Adoption Trends

The stack choice is between a mature but stale identity-recognition wrapper (`face_recognition`) and a modern, well-packaged face-detection toolkit (MediaPipe). For this project, the deciding constraint is identity recognition, not detection. MediaPipe can help detect/crop faces, but it does not replace dlib's 128-dimensional identity encodings without adding another embedding model.

_Migration Pattern:_ Keep dlib/face_recognition for MVP if the corrected install path is accepted. Revisit MediaPipe only if identity accuracy or install reproducibility remains unacceptable.

_Emerging Technologies:_ MediaPipe Tasks are current and prebuilt, with official Python docs and Windows wheels. They are attractive for face detection/landmarking but create scope expansion for identity embeddings.

_Legacy Technology:_ `face_recognition` is legacy but exactly matches the current PRD's embedding/tolerance model. Its install metadata is the weak point.

_Community / Package Trend:_ Current PyPI package facts favor explicit pinning and smoke tests over trusting transitive dependency resolution.

_Source:_ MediaPipe Face Detector docs state it detects faces and keypoints in image/video/live stream, with `python -m pip install mediapipe`: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/python. MediaPipe PyPI `0.10.35` has Windows x86-64 wheel uploaded April 27, 2026: https://pypi.org/project/mediapipe/.

### Technology Stack Recommendation

**Recommendation:** Correct Story 1.1 to use the explicit wheel-only dlib path:

1. Pin `setuptools<81`.
2. Install `dlib-bin`, `face-recognition-models`, `opencv-python`, `numpy`, `Pillow`, and `Click`.
3. Install `face_recognition --no-deps`.
4. Run a smoke script that imports `cv2`, `dlib`, `face_recognition`, and `face_recognition_models`, then computes a 128-dimensional encoding from a local image.
5. Document that `pip check` may not be clean because `dlib-bin` does not satisfy the `dlib` distribution metadata dependency, even though runtime import works.

**Do not recommend** Visual Studio Build Tools for MVP unless the project explicitly abandons the “no source compilation” constraint.

**Do not recommend** MediaPipe as a direct replacement yet. It is a fallback requiring a broader architecture/story change because it solves face detection, not person identity recognition.

## Integration Patterns Analysis

### API Design Patterns

The application-facing API can remain `face_recognition` because the corrected installation path does not change runtime calls. The library exposes the exact primitives the PRD and Epic 2 assume:

- `face_locations(img, model='hog')` returns face boxes and defaults to CPU-friendly HOG detection.
- `face_encodings(image, known_face_locations=None, model='small')` returns 128-dimensional encodings.
- `compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6)` and `face_distance(...)` support tolerance-based matching.

For Story 1.1, the smoke-test API should use `face_recognition.face_locations(rgb_image)` and `face_recognition.face_encodings(rgb_image, face_locations)` after OpenCV BGR-to-RGB conversion. For later stories, this keeps the PRD's configurable tolerance model intact.

_RESTful APIs:_ Not applicable; this is an on-device library integration.

_GraphQL APIs:_ Not applicable.

_RPC and gRPC:_ Not applicable.

_Webhook Patterns:_ Not applicable.

_Source:_ Face Recognition API docs: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations

### Communication Protocols

There is no network protocol change for the recognition stack. The integration pattern is local in-process imports inside the smoke script and later inside the recognition worker process. The corrected install flow must be treated as packaging choreography, not a runtime communication protocol.

Important runtime implication: `dlib-bin` installs an importable `dlib` module, but pip metadata does not identify it as the `dlib` distribution required by `face_recognition`. Therefore:

- Use `face_recognition --no-deps` only after installing all runtime dependencies explicitly.
- Validate runtime with imports and a real encoding smoke test, not only `pip check`.
- Document that `pip check` may report `face-recognition` missing `dlib` even when `import dlib` succeeds.

_HTTP/HTTPS Protocols:_ Used only by pip during installation; not used by the smoke test or recognition runtime.

_WebSocket Protocols:_ Not applicable.

_Message Queue Protocols:_ Later worker-to-player queue remains unaffected.

_gRPC and Protocol Buffers:_ Not applicable.

_Source:_ pip docs define `--no-deps` as not installing package dependencies: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-deps. Local proof: `_bmad-output/planning-artifacts/research/dlib-nodeps-install-proof.log`.

### Data Formats and Standards

The key data integration contract remains a NumPy image array and a 128-dimensional embedding vector. This matches both the current PRD and `face_recognition` API docs. The corrected installation path does not require changing `people.json`; later stories can still persist names plus embeddings as planned.

For Story 1.1 smoke testing:

- Input file: local `.jpg`/`.png` image path.
- OpenCV read format: BGR NumPy array.
- Conversion: BGR -> RGB before calling `face_recognition`.
- Face location format: CSS order tuple `(top, right, bottom, left)`.
- Embedding format: one 128-dimensional vector per detected face.
- Success output: concise plain text such as `OK: faces=1 embedding_dim=128`.

_JSON and XML:_ JSON remains planned for `people.json`, but Story 1.1 should not create or mutate it.

_Protobuf and MessagePack:_ Not applicable.

_CSV and Flat Files:_ The smoke script is a local-file integration.

_Custom Data Formats:_ The dlib `.dat` model files are provided by `face_recognition_models`; they require resource lookup that currently depends on `pkg_resources`.

_Source:_ Face Recognition docs specify 128-dimensional encodings and face location tuple format: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations.

### System Interoperability Approaches

The main interoperability risk is between Python packaging metadata and runtime import behavior:

- `face-recognition==1.3.0` requires the distribution `dlib>=19.7`.
- `dlib-bin==20.0.1` provides an importable `dlib` module, but it is not the `dlib` distribution.
- `face_recognition_models==0.3.0` imports `pkg_resources`; `setuptools 82.0.1` docs state `pkg_resources` is removed in v82.0.0.

The practical integration pattern is an explicit compatibility layer in install instructions:

```powershell
python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models
python -m pip install face_recognition --no-deps
```

This avoids source compilation while preserving the runtime API that future stories expect.

_Point-to-Point Integration:_ Smoke script -> local image -> OpenCV -> face_recognition/dlib -> local stdout.

_API Gateway Patterns:_ Not applicable.

_Service Mesh:_ Not applicable.

_Enterprise Service Bus:_ Not applicable.

_Source:_ PyPI `face-recognition` JSON requires `dlib>=19.7`: https://pypi.org/pypi/face_recognition/1.3.0/json. Setuptools docs state `pkg_resources` is not included as of v82.0.0: https://setuptools.pypa.io/en/stable/deprecated/pkg_resources.html.

### Microservices Integration Patterns

Microservices are not relevant for this project. The future architecture uses local OS processes, not services: player, recognition worker, and Telegram bot under one supervisor. This research does not change that.

The corrected dependency stack must be installed in the same virtualenv used by all local processes. Do not install `dlib-bin` globally and assume child processes can import it.

_API Gateway Pattern:_ Not applicable.

_Service Discovery:_ Not applicable.

_Circuit Breaker Pattern:_ Later supervisor restart logic remains unaffected.

_Saga Pattern:_ Not applicable.

_Source:_ Existing PRD process model in `_bmad-output/planning-artifacts/prd.md`; no external source needed.

### Event-Driven Integration

No event-driven architecture change is needed. Later stories still use `multiprocessing.Queue` for worker-to-player greeting events and a file watcher for `people.json`. The only impact is that the recognition worker should include startup self-checks/import errors in logs so a packaging regression is obvious.

_Publish-Subscribe Patterns:_ Not applicable for Story 1.1.

_Event Sourcing:_ Not applicable.

_Message Broker Patterns:_ Not applicable.

_CQRS Patterns:_ Not applicable.

_Source:_ Existing PRD implementation considerations in `_bmad-output/planning-artifacts/prd.md`.

### Integration Security Patterns

The corrected install path does not introduce new runtime security exposure. It does introduce a supply-chain clarity requirement: because `face_recognition --no-deps` bypasses dependency resolution, Story 1.1 and Story 1.2 should explicitly list and pin every dependency later in `requirements.txt`.

Recommended guardrails:

- Use PyPI packages only; do not rely on random third-party wheel files.
- Avoid Visual Studio/CMake source compilation for MVP unless explicitly approved.
- Do not download image assets in the smoke script.
- Do not persist face images in Story 1.1.
- Capture package versions with `pip freeze` and import proof output.

_OAuth 2.0 and JWT:_ Not applicable.

_API Key Management:_ Not applicable until Telegram bot stories.

_Mutual TLS:_ Not applicable.

_Data Encryption:_ Not impacted by this dependency correction.

_Source:_ PyPI package pages for `dlib-bin`, `face-recognition`, `opencv-python`, and pip `--no-deps` documentation cited above.

### Integration Recommendation

For the upcoming Correct Course proposal, classify this as a **minor-to-moderate story correction**, not a full architecture pivot:

1. Replace Story 1.1 AC install command with the explicit two-step install sequence.
2. Add `setuptools<81` as a required compatibility pin because `face_recognition_models` still imports `pkg_resources`.
3. Keep the smoke-test API based on `face_recognition`; include import checks for `face_recognition_models`.
4. Add a documented packaging exception: `pip check` is allowed to report missing `dlib` only if runtime import and embedding smoke test pass.
5. Do not switch to MediaPipe unless the corrected dlib-bin path fails on the actual demo machine.

## Architectural Patterns and Design

### System Architecture Patterns

The current architecture remains valid if the corrected dlib-bin install path is adopted. This is a dependency/packaging correction, not a system architecture pivot.

Current planned pattern:

- Main process: fullscreen player.
- Worker process: camera capture plus face detection/embedding.
- Bot subprocess: admin surface in later stories.
- IPC: `multiprocessing.Queue` for greeting events.
- Storage: local `people.json` for embeddings.

Keeping `face_recognition` preserves the identity-recognition API and future story contracts. The worker can still call `face_locations`, `face_encodings`, `face_distance`, and `compare_faces` without changing the PRD's 128-dimensional embedding model.

MediaPipe would be a different architecture pattern: face detection/landmarking plus a separate identity embedding model. Official docs confirm MediaPipe Face Detector outputs bounding boxes and keypoints for still images, video frames, and live streams, not person identity embeddings. That would affect Epic 2, benchmark design, data schema, and acceptance thresholds.

_Source:_ Face Recognition API docs for embeddings and comparisons: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations. MediaPipe Face Detector overview: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector.

### Design Principles and Best Practices

The correct design response is to isolate dependency quirks at the install/verification boundary, not leak them into feature architecture.

Recommended design principles:

- Keep runtime code normal: `import dlib`, `import face_recognition`.
- Put packaging exceptions in setup docs / Story 1.1 / future `requirements.txt` notes.
- Require a smoke test that proves real runtime behavior rather than relying on package metadata alone.
- Avoid installing system build tools unless the project intentionally changes AR1.

The package metadata mismatch is an example of “distribution package vs import package.” Python packaging docs distinguish distribution metadata from importable packages; this explains why `dlib-bin` can provide `import dlib` while not satisfying the `dlib` distribution dependency declared by `face_recognition`.

_Source:_ Python Packaging User Guide includes “Distribution package vs. import package” under package metadata topics: https://packaging.python.org/en/latest/specifications/section-distribution-metadata/. Python `importlib.metadata` docs describe distribution metadata and mapping import names to distribution packages: https://docs.python.org/3.15/library/importlib.metadata.html.

### Scalability and Performance Patterns

For the MVP, the performance-critical architecture remains CPU-only dlib HOG detection plus embedding in a separate worker process. The `face_recognition` docs state `face_locations(..., model='hog')` is less accurate but faster on CPUs, while `cnn` is more accurate and GPU/CUDA-oriented. That aligns with the PRD's no-GPU Windows laptop constraint.

Architecture implication:

- Story 1.1 should use a single local image smoke test.
- Later worker stories should default to HOG on CPU and reserve CNN for explicit GPU-capable environments.
- Keep frame skipping/downsampling strategy from the PRD; the dependency correction does not change it.

MediaPipe has an attractive live-stream pattern: official docs say live stream mode returns immediately and ignores new frames if the task is busy. This matches the PRD's “skip frames if behind” philosophy, but again it does not solve identity embeddings by itself.

_Source:_ Face Recognition API docs for `model='hog'` and CNN/GPU note: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations. MediaPipe Python Face Detector docs for live stream behavior: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/python.

### Integration and Communication Patterns

The architecture should treat package verification as a startup/preflight concern:

- Story 1.1: prove imports and 128-dimensional encoding.
- Story 1.2: pin dependencies and document the install exception.
- Story 2.1: wrap recognition calls in a small utility, so later fallback experimentation can happen behind one local module if needed.
- Story 3.1: worker process logs import/startup failures clearly.

No inter-process communication changes are required. The worker process boundary remains the correct place to isolate dlib CPU work from the Qt event loop.

_Source:_ Existing PRD process model in `_bmad-output/planning-artifacts/prd.md`; Face Recognition and MediaPipe docs cited above.

### Security Architecture Patterns

The corrected dlib-bin path is safer for this buildathon than installing arbitrary third-party binary wheels or compiling from source under time pressure. Recommended supply-chain posture:

- Prefer PyPI-hosted wheels only.
- Avoid random wheel downloads from forums or personal sites.
- Record exact package versions and logs.
- Do not download smoke-test face images in code.
- Do not persist camera frames or biometric data in Story 1.1.

The `--no-deps` step is safe only if the dependency list is explicit and verified. This must be documented because it bypasses pip's normal dependency resolver for `face_recognition`.

_Source:_ pip `--no-deps` option documentation: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-deps. PyPI package pages cited in prior sections.

### Data Architecture Patterns

No data architecture change is required if the dlib-bin workaround is adopted. The planned data model remains:

- `people.json` stores names plus 128-dimensional embeddings.
- Source face photos later live under `faces/` for re-embedding.
- Story 1.1 creates no database and stores no biometric data.

If the project switches to MediaPipe, data architecture would need rework because landmarks/bounding boxes are not equivalent to face identity embeddings. A separate embedding model would define vector dimensions, thresholds, and benchmark expectations.

_Source:_ dlib docs state `compute_face_descriptor` converts a face into a 128D descriptor: https://dlib.net/python/index.html?highlight=dlib+frontal+face+detector. Face Recognition docs also state `face_encodings` returns 128-dimensional face encodings: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations.

### Deployment and Operations Architecture

The deployment architecture should use a two-tier validation:

1. Install validation: wheel-only install path, elapsed time, no CMake/source-build indicators.
2. Runtime validation: imports plus local face image -> detected face -> 128-dimensional encoding.

For Story 1.1, the acceptance criteria should be corrected from “single pip command installs everything” to “explicit wheel-only install sequence completes quickly and avoids source `dlib`.” This keeps the operational goal intact: eliminate Windows install risk early.

The old command should remain documented as the failed path, not retried as-is. It is expected to pull source `dlib` on Python 3.13 because `face_recognition` declares `dlib>=19.7`.

_Source:_ Local failed log `_bmad-output/implementation-artifacts/1-1-dlib-install.log`; local proof log `_bmad-output/planning-artifacts/research/dlib-nodeps-install-proof.log`; PyPI `dlib` page shows source distribution for `dlib 20.0.1`: https://pypi.org/project/dlib/.

### Architecture Decision

**Decision:** Keep the current dlib/face_recognition architecture and correct Story 1.1's installation strategy.

**Rationale:**

- The runtime API and data model match existing PRD/epics.
- Local proof shows the corrected stack imports successfully on Python 3.13.
- Switching to MediaPipe would require an additional identity embedding model and broader story changes.
- Installing Visual Studio Build Tools undermines AR1's wheel-first risk reduction and may cost more time than the workaround.

**Change Scope:** Minor-to-moderate. Update Story 1.1 and later Story 1.2 dependency pinning; no need to rewrite Epic 2 unless the corrected path fails on the actual demo machine.

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategies

Adopt the corrected dlib-bin path incrementally:

1. Correct Story 1.1 only.
2. Re-run the install proof in a fresh venv, preferably with pip cache cleared or timings noted as cached/uncached.
3. Create `tests/smoke_dlib.py` only after install/import succeeds.
4. If smoke embedding succeeds, update Story 1.2 so dependency pinning and setup docs preserve the explicit two-step install.
5. Keep MediaPipe as a documented fallback trigger, not an immediate rewrite.

This avoids a big-bang architecture change and keeps the current PRD intact. It also keeps the fallback decision objective: switch only if the corrected stack fails on the actual demo machine.

_Source:_ pip `--no-deps` docs: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-deps. Python Packaging guide recommends virtual environments for isolated installs: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/.

### Development Workflows and Tooling

Use explicit commands rather than trying to hide `--no-deps` inside `requirements.txt`. `pip install --no-deps face_recognition` is a command-level behavior, and the safest BMAD handoff is to make Story 1.1 say exactly what to run.

Recommended development workflow:

```powershell
python -m venv .venv-smoke-dlib
.\.venv-smoke-dlib\Scripts\python.exe -m pip install --upgrade pip
.\.venv-smoke-dlib\Scripts\python.exe -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models
.\.venv-smoke-dlib\Scripts\python.exe -m pip install face_recognition --no-deps
.\.venv-smoke-dlib\Scripts\python.exe -m pip freeze
```

For Story 1.2, use either a small setup script or README setup sequence. A plain `requirements.txt` may pin packages, but the `face_recognition --no-deps` step must remain explicit unless the team chooses a custom wheel/metadata patch, which is unnecessary for this buildathon.

_Source:_ pip docs define `--no-deps`; pip caching docs explain why cached wheels speed later installs and why timing should note cache state: https://pip.pypa.io/en/stable/topics/caching.html.

### Testing and Quality Assurance

Story 1.1 should use two verification layers:

**Install verification**

- Log command output.
- Record elapsed time.
- Search log for source-build red flags:
  - `Building wheel for dlib`
  - `CMake`
  - `Visual Studio`
  - `Failed building wheel`
- Record `pip freeze`.
- Record that `pip check` may show the metadata exception; do not use it as the sole pass/fail gate.

**Runtime smoke verification**

`tests/smoke_dlib.py` should:

- Import `cv2`, `dlib`, `face_recognition`, and `face_recognition_models`.
- Accept optional image path; default `tests/assets/smoke-face.jpg`.
- Fail non-zero with a clear message if image is missing/unreadable/no face/no encoding.
- Convert OpenCV BGR to RGB before calling `face_recognition`.
- Call `face_locations` and `face_encodings`.
- Assert first encoding length is 128.
- Print `OK: faces=N embedding_dim=128`.

This runtime smoke test is stronger than package metadata because it proves the exact API needed by later stories.

_Source:_ Face Recognition API docs for `face_locations`, `face_encodings`, and image loading: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations. Setuptools docs for `pkg_resources` removal: https://setuptools.pypa.io/en/stable/deprecated/pkg_resources.html.

### Deployment and Operations Practices

For the demo machine, install validation should be part of pre-flight:

- Run the corrected install in a clean venv.
- Run smoke test with a local face image.
- Keep logs under `_bmad-output/implementation-artifacts/` while BMAD stories are active.
- Later, after Story 1.2 initializes repo structure, move durable setup instructions into README/setup docs.

If internet speed makes the first install exceed 60 seconds due to model downloads, distinguish package-resolution success from wall-clock network cost. The original AC says less than 60 seconds; after research, a more reliable AC is “wheel-only install with no source compilation, with elapsed time recorded; cached repeat install target under 60 seconds.” This avoids judging network throughput as platform feasibility.

_Source:_ pip cache docs on wheel/cache behavior: https://pip.pypa.io/en/stable/topics/caching.html.

### Team Organization and Skills

This remains a solo developer task. Required skills:

- Basic Python venv and pip usage.
- Ability to inspect pip logs.
- Ability to distinguish distribution metadata from importable modules.
- Ability to write a small smoke script with clear failure modes.

No ML model training skill is required if the dlib/face_recognition path works.

_Source:_ Project PRD skill profile in `_bmad-output/planning-artifacts/prd.md`; Python packaging and Face Recognition docs cited above.

### Cost Optimization and Resource Management

Avoiding Visual Studio Build Tools saves setup time and avoids a heavy system dependency on the demo machine. Keeping dlib-bin avoids introducing a new embedding model. MediaPipe remains cost-effective only if the dlib path fails, because otherwise it creates new design and benchmark work.

Resource considerations:

- `face_recognition_models` is large; first install can be network-bound.
- pip cache materially affects repeat install timing.
- The project should avoid committing face image assets in Story 1.1.
- Keep venv directories out of future git tracking once Story 1.2 creates `.gitignore`.

_Source:_ pip cache docs: https://pip.pypa.io/en/stable/topics/caching.html.

### Risk Assessment and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| `face_recognition` pulls source `dlib` | Blocks Windows install | Install dependencies manually, then `face_recognition --no-deps` |
| `face_recognition_models` cannot import `pkg_resources` | Runtime import fails | Pin `setuptools<81` |
| `pip check` reports missing `dlib` | False negative for metadata | Treat as documented exception only if runtime smoke passes |
| First install exceeds 60 seconds due to downloads | AC ambiguity | Record cached/uncached timing and update AC to focus on wheel-only/no-source-build |
| MediaPipe switch considered too early | Scope expansion | Keep as fallback only after corrected dlib path fails |
| Random third-party dlib wheels | Supply-chain risk | Use PyPI-hosted `dlib-bin` only |

_Source:_ Local failure/proof logs plus PyPI, pip, setuptools, and Face Recognition docs cited above.

## Technical Research Recommendations

### Implementation Roadmap

1. Run Correct Course for a narrow Story 1.1 correction.
2. Update Story 1.1 ACs/tasks:
   - Replace original single install command.
   - Add `setuptools<81`.
   - Add `face_recognition --no-deps`.
   - Add documented `pip check` exception.
   - Keep smoke-test requirements.
3. Resume Dev Story `DS` for Story 1.1.
4. Recreate the clean venv and run corrected install.
5. Create and run `tests/smoke_dlib.py`.
6. If pass: move Story 1.1 to review.
7. In Story 1.2: encode the dependency strategy into setup docs and pinned dependency artifacts.

### Technology Stack Recommendations

Primary:

- Python 3.13 remains acceptable based on local proof.
- `dlib-bin==20.0.1`
- `face-recognition==1.3.0`, installed with `--no-deps`
- `face_recognition_models==0.3.0`
- `setuptools<81`
- `opencv-python==4.13.0.92`
- `numpy`, `Pillow`, `Click` pinned from the successful environment when Story 1.2 creates `requirements.txt`.

Fallback:

- MediaPipe only if corrected dlib-bin runtime smoke fails on the actual demo machine.
- If MediaPipe is used, plan an additional identity embedding decision; do not treat MediaPipe Face Detector as identity recognition.

### Skill Development Requirements

- Python packaging basics: venv, pip, wheels, `--no-deps`, `pip freeze`.
- Reading pip logs for source-build indicators.
- OpenCV image read and BGR-to-RGB conversion.
- Basic `face_recognition` API usage.

### Success Metrics and KPIs

For corrected Story 1.1:

- Clean venv created.
- Corrected install avoids source `dlib`; no CMake/Visual Studio Build Tools in log.
- Runtime imports pass: `cv2`, `dlib`, `face_recognition`, `face_recognition_models`.
- Smoke image produces at least one 128-dimensional encoding.
- Failure modes are clear and non-zero.
- Dev Agent Record captures command, elapsed time, versions, log path, cache state, and smoke output.

### Final Recommendation

Proceed to `bmad-correct-course` with a narrow proposal: **Correct Story 1.1 dependency strategy; do not replan the product.**

# Windows Face Recognition Dependency Strategy: Comprehensive Technical Research

## Executive Summary

Story 1.1 found a real platform risk: on Windows/Python 3.13, the planned command `pip install dlib-bin face_recognition opencv-python` does not guarantee a wheel-only dlib path. `dlib-bin` downloads successfully, but `face_recognition==1.3.0` declares a dependency on the distribution package `dlib>=19.7`; because `dlib-bin` is a separate distribution, pip still downloads source `dlib`, attempts to build it with CMake, and fails without Visual Studio C++ Build Tools.

The project does not need a full architecture pivot. The current PRD depends on 128-dimensional identity embeddings and tolerance-based matching; `face_recognition` provides those directly, while MediaPipe Face Detector provides face boxes/keypoints, not identity embeddings. The fastest reliable path is to correct Story 1.1 and later Story 1.2 dependency instructions, not rewrite Epic 2.

**Key Technical Findings:**

- `face_recognition` declares `dlib>=19.7`, so normal dependency resolution pulls source `dlib` even when `dlib-bin` is installed.
- `dlib-bin==20.0.1` provides an importable `dlib` module and has Windows/Python 3.13 wheels.
- `face_recognition_models==0.3.0` still imports `pkg_resources`; setuptools v82 removed `pkg_resources`, so `setuptools<81` is required for this stack.
- Local proof on Python 3.13 validated the corrected runtime imports after installing `setuptools<81`.
- MediaPipe is a viable detection fallback, but not a drop-in identity-recognition replacement.

**Technical Recommendations:**

- Correct Story 1.1 to use an explicit two-step install:

```powershell
python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models
python -m pip install face_recognition --no-deps
```

- Add a documented packaging exception: `pip check` may report `face-recognition` missing `dlib`; runtime import and 128-dimensional embedding smoke test are the pass/fail gate.
- Keep MediaPipe as fallback only if the corrected dlib-bin path fails on the actual demo machine.
- Update Story 1.2 later so setup docs and pinned dependencies preserve this install choreography.

## Table of Contents

1. Technical Research Introduction and Methodology
2. Technical Landscape and Architecture Analysis
3. Implementation Approaches and Best Practices
4. Technology Stack Evolution and Current Trends
5. Integration and Interoperability Patterns
6. Performance and Scalability Analysis
7. Security and Compliance Considerations
8. Strategic Technical Recommendations
9. Implementation Roadmap and Risk Assessment
10. Future Technical Outlook and Innovation Opportunities
11. Technical Research Methodology and Source Verification
12. Technical Appendices and Reference Materials

## 1. Technical Research Introduction and Methodology

### Technical Research Significance

The Story 1.1 failure is strategically important because it happened at the project’s first intended platform gate. The PRD explicitly treats Windows dlib installation as the dominant risk and requires that risk to be resolved before UI, worker, or bot development. The failure did not invalidate the product concept; it exposed an incorrect packaging assumption.

_Technical Importance:_ The project depends on local face embeddings, not just face detection. A wrong dependency decision would cascade into Epic 2 recognition, Epic 4 benchmarking, and README claims.

_Business Impact:_ Correcting the install path preserves the 24-hour buildathon plan. Switching stacks prematurely would consume time in new embedding research and acceptance-criteria rewrites.

_Source:_ Story failure log `_bmad-output/implementation-artifacts/1-1-dlib-install.log`; Story 1.1 and PRD in `_bmad-output/planning-artifacts/`.

### Technical Research Methodology

- **Technical Scope:** Windows/Python packaging, dlib-bin, face_recognition, OpenCV, MediaPipe fallback, runtime smoke testing.
- **Data Sources:** PyPI package metadata, official Face Recognition docs, dlib docs, MediaPipe docs, pip docs, setuptools docs, local proof logs.
- **Analysis Framework:** Compare package metadata, runtime import behavior, project architecture fit, and story impact.
- **Time Period:** Current package state as of May 15, 2026.
- **Technical Depth:** Focused enough to feed `bmad-correct-course` and unblock Story 1.1.

## 2. Technical Landscape and Architecture Analysis

### Current Technical Architecture Patterns

The current architecture remains correct: a Python desktop app with recognition in a separate worker process, using face embeddings persisted to local storage. `face_recognition` maps cleanly to this architecture because it provides 128-dimensional encodings and tolerance-based comparison.

MediaPipe should not replace this stack unless the corrected dlib-bin path fails. Official MediaPipe Face Detector docs describe boxes/keypoints in images/video/live streams, not person identity embeddings.

_Source:_ Face Recognition API docs: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations. MediaPipe Face Detector docs: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector.

### System Design Principles and Best Practices

The design response should isolate packaging quirks in setup instructions and smoke tests. Runtime code should remain simple: `import dlib`, `import face_recognition`, call the normal API.

_Source:_ Python packaging docs distinguish distribution metadata from importable packages: https://packaging.python.org/en/latest/specifications/section-distribution-metadata/.

## 3. Implementation Approaches and Best Practices

### Current Implementation Methodologies

Use a clean virtualenv and explicit install commands. Do not hide `face_recognition --no-deps` inside an ordinary requirements line. The command sequence itself is part of the implementation contract.

### Implementation Framework and Tooling

Recommended proof workflow:

```powershell
python -m venv .venv-smoke-dlib
.\.venv-smoke-dlib\Scripts\python.exe -m pip install --upgrade pip
.\.venv-smoke-dlib\Scripts\python.exe -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models
.\.venv-smoke-dlib\Scripts\python.exe -m pip install face_recognition --no-deps
.\.venv-smoke-dlib\Scripts\python.exe -m pip freeze
```

_Source:_ pip `--no-deps` docs: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-deps.

## 4. Technology Stack Evolution and Current Trends

### Current Technology Stack Landscape

Primary stack:

- Python 3.13 acceptable based on local proof.
- `dlib-bin==20.0.1`
- `face-recognition==1.3.0`, installed with `--no-deps`
- `face_recognition_models==0.3.0`
- `setuptools<81`
- `opencv-python==4.13.0.92`

MediaPipe is current and well-packaged but shifts the problem from “install dlib” to “choose and validate an identity embedding model.”

_Source:_ PyPI `face-recognition`: https://pypi.org/pypi/face_recognition/1.3.0/json. PyPI `opencv-python`: https://pypi.org/project/opencv-python/4.13.0.92/. PyPI `mediapipe`: https://pypi.org/project/mediapipe/.

### Technology Adoption Patterns

Adopt the corrected dlib path incrementally. Keep the fallback documented but inactive.

## 5. Integration and Interoperability Patterns

### Current Integration Approaches

The integration issue is metadata-level. `dlib-bin` provides the import package `dlib`, but `face_recognition` depends on the distribution package `dlib`. The corrected install bypasses that dependency resolution after manually installing all runtime pieces.

_Source:_ PyPI `face-recognition` metadata requires `dlib>=19.7`: https://pypi.org/pypi/face_recognition/1.3.0/json.

### Interoperability Standards and Protocols

The smoke test should prove interoperability by importing `cv2`, `dlib`, `face_recognition`, and `face_recognition_models`, then producing a 128-dimensional encoding from a local image.

## 6. Performance and Scalability Analysis

### Performance Characteristics and Optimization

The PRD’s CPU-only plan remains aligned with `face_recognition` defaults. The API docs state HOG is the CPU-friendly detector, while CNN is GPU/CUDA-oriented.

_Source:_ Face Recognition API docs: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations.

### Scalability Patterns and Approaches

No scalability change is needed now. Later benchmark work should validate up to 200 registered people as already planned.

## 7. Security and Compliance Considerations

### Security Best Practices and Frameworks

Use PyPI-hosted packages only. Avoid random wheel downloads from forums. Do not download face images in the smoke script. Do not persist biometric data in Story 1.1.

### Compliance and Regulatory Considerations

No new compliance requirement is introduced. The PRD’s on-device privacy posture remains intact.

## 8. Strategic Technical Recommendations

### Technical Strategy and Decision Framework

Recommended strategy: **direct adjustment**. Correct Story 1.1 and keep the current architecture.

Technology selection:

- Keep `face_recognition` for identity embeddings.
- Use `dlib-bin` to avoid source compilation.
- Pin `setuptools<81` for `pkg_resources` compatibility.
- Use MediaPipe only as fallback if the corrected path fails.

### Competitive Technical Advantage

The advantage is speed: this correction preserves the planned demo path and avoids a broader recognition redesign.

## 9. Implementation Roadmap and Risk Assessment

### Technical Implementation Framework

1. Run `bmad-correct-course`.
2. Update Story 1.1 ACs/tasks to the explicit install sequence.
3. Resume `bmad-dev-story`.
4. Recreate clean venv and run corrected install.
5. Create `tests/smoke_dlib.py`.
6. Run smoke with a local face image.
7. If pass, move Story 1.1 to review.
8. Update Story 1.2 setup docs/pins later.

### Technical Risk Management

| Risk | Mitigation |
|---|---|
| `face_recognition` pulls source `dlib` | Use explicit dependencies and `face_recognition --no-deps` |
| `pkg_resources` missing | Pin `setuptools<81` |
| `pip check` false negative | Use runtime smoke test as pass/fail gate |
| First install exceeds 60s due to network | Record cached/uncached timing and focus AC on wheel-only/no source build |
| MediaPipe considered too early | Keep it as fallback only |

## 10. Future Technical Outlook and Innovation Opportunities

### Emerging Technology Trends

MediaPipe remains valuable if the team later wants face tracking, landmarks, or liveness-style features. It should be reconsidered post-MVP or if dlib proves unusable on the demo machine.

### Innovation and Research Opportunities

If MediaPipe fallback is triggered, research a separate embedding model before changing stories. Detection alone is not recognition.

## 11. Technical Research Methodology and Source Verification

### Comprehensive Technical Source Documentation

Primary sources:

- Face Recognition PyPI metadata: https://pypi.org/pypi/face_recognition/1.3.0/json
- Face Recognition API docs: https://face-recognition.readthedocs.io/en/latest/face_recognition.html?highlight=face_locations
- dlib Python docs: https://dlib.net/python/index.html?highlight=dlib+frontal+face+detector
- dlib PyPI source package page: https://pypi.org/project/dlib/
- dlib-bin PyPI page: https://pypi.org/project/dlib-bin/
- OpenCV Python PyPI page: https://pypi.org/project/opencv-python/4.13.0.92/
- MediaPipe Face Detector docs: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/python
- pip install docs: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-deps
- pip cache docs: https://pip.pypa.io/en/stable/topics/caching.html
- setuptools `pkg_resources` docs: https://setuptools.pypa.io/en/stable/deprecated/pkg_resources.html

Local evidence:

- Failed install log: `_bmad-output/implementation-artifacts/1-1-dlib-install.log`
- Workaround proof log: `_bmad-output/planning-artifacts/research/dlib-nodeps-install-proof.log`

### Technical Research Quality Assurance

Confidence level: **High** for the narrow recommendation. It is supported by package metadata, official docs, and local Python 3.13 proof.

Limitation: The workaround proof used cached packages for timing. Corrected Story 1.1 should record cache state and rerun on the actual demo machine.

## 12. Technical Appendices and Reference Materials

### Corrected Install Sequence

```powershell
python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models
python -m pip install face_recognition --no-deps
```

### Corrected Smoke Test Contract

- Import: `cv2`, `dlib`, `face_recognition`, `face_recognition_models`
- Input: local face image path, default `tests/assets/smoke-face.jpg`
- Processing: OpenCV load, BGR -> RGB, `face_locations`, `face_encodings`
- Pass: at least one encoding, first encoding length `128`
- Fail: missing image, unreadable image, no face, no encoding

---

## Technical Research Conclusion

### Summary of Key Technical Findings

The original Story 1.1 install command is wrong for the current Windows/Python 3.13 environment because pip resolves `face_recognition`’s `dlib` dependency to source `dlib`. The corrected dlib-bin path works at runtime when dependencies are explicit and `face_recognition` is installed with `--no-deps`.

### Strategic Technical Impact Assessment

This is not an architecture failure. It is a packaging correction that should be handled through Correct Course and then resumed in Dev Story.

### Next Steps Technical Recommendations

1. Run `bmad-correct-course`.
2. Apply a narrow Story 1.1 correction.
3. Resume `bmad-dev-story`.
4. Keep MediaPipe in reserve only if the corrected dlib path fails.

---

**Technical Research Completion Date:** 2026-05-15T18:04:23+05:00  
**Research Period:** Current comprehensive technical analysis  
**Source Verification:** All technical facts cited with current sources  
**Technical Confidence Level:** High for corrected dlib-bin path; medium for install timing until uncached demo-machine rerun
