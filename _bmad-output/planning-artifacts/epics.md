---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
---

# facial recognition - uzc — Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for **facial recognition - uzc** (Office Face-Greeting Display), decomposing the requirements from the PRD into implementable stories sized for the 24-hour solo buildathon budget.

**No separate Architecture document exists** — architecturally relevant content (process model, IPC pattern, atomic-write contract, hot-reload mechanism, supervisor pattern, platform specifics) lives inside the PRD's *Desktop Application — Specific Requirements*, *Implementation Considerations*, and *Risk Mitigation Strategy* sections, and is extracted into "Additional Requirements" below where it affects story sequencing.

**No separate UX Design document exists** — UX-equivalent content (greeting layout, font ratio, fade timing, bot reply microcopy) lives inside the PRD's NFRs and *Greeting Display* / *Telegram bot* sections, and is treated as part of the regular FR/NFR set rather than a separate UX-DR section.

## Requirements Inventory

### Functional Requirements

#### Recognition

- **FR1**: System can detect human faces appearing in the camera's field of view in real time.
- **FR2**: System can compute a stable mathematical representation (embedding) of each detected face.
- **FR3**: System can compare a detected face's representation against the stored set of registered people and decide whether it matches a registered person, within a configurable similarity threshold.
- **FR4**: When two or more registered people are visible simultaneously, system can select the one closest to the camera as the greeting target.
- **FR5**: System takes no visible action when a detected face does not match any registered person — no greeting, no acknowledgement, no UI flash.

#### Greeting Display

- **FR6**: System can display a personalized text greeting addressed to a recognized person, overlaid on the currently playing promo video.
- **FR7**: System can render the greeting with a fade-in/out animation for a configurable display duration of 3–10 seconds (default 5 s), without pausing or interrupting the underlying video.
- **FR8**: System can suppress repeat greetings for the same person within a configurable cooldown window.
- **FR9**: Operator can configure the greeting display duration and cooldown window via configuration.

#### Promo Video Playback

- **FR10**: System can play promo videos from a designated local folder in fullscreen, looping continuously while the application is running.
- **FR11**: System can detect newly added or removed promo videos at the end of each video iteration and adjust the playlist accordingly, without restart.
- **FR12**: System can continue uninterrupted playback while administrative actions (face DB updates, playlist updates) occur in the background.

#### People Management

- **FR13**: Admin can add a new registered person by providing a name and a face photo via the Telegram bot.
- **FR14**: Admin can add a new registered person via a command-line script (`add_person.py`), providing the same name + photo input as the bot.
- **FR15**: Admin can list all currently registered people via the Telegram bot.
- **FR16**: Admin can remove a registered person by name via the Telegram bot.
- **FR17**: System can persist registered people's data (name + face representation) to local storage, surviving restarts.
- **FR18**: System can begin recognizing a newly added person within 5 seconds of their addition, without requiring a restart.
- **FR19**: System can stop recognizing (and immediately stop greeting) a removed person within 5 seconds of their removal.

#### Video Management

- **FR20**: Admin can upload a new promo video via the Telegram bot, subject to the bot platform's file-size limit.
- **FR21**: Admin can add a new promo video of any size via a command-line script (`add_video.py`).
- **FR22**: Admin can list all current promo videos in the playlist via the Telegram bot.
- **FR23**: Admin can remove a promo video from the playlist by name via the Telegram bot.
- **FR24**: System guarantees that a video file added through any path (bot or CLI) is fully written before the player makes it available for playback.
- **FR25**: System communicates file-size constraints clearly to admins when an upload is rejected, including the alternative path (CLI) for files that exceed the bot limit.

#### Admin Access Control

- **FR26**: System restricts administrative actions (people management and video management) to a defined allowlist of Telegram chat IDs.
- **FR27**: System rejects and logs unauthorized administrative requests, and replies to the requester with a clear "unauthorized" message.

#### System Operations

- **FR28**: Operator can start the entire system with a single command.
- **FR29**: System runs its three coordinated components (player, recognition, admin bot) concurrently from a single entry point.
- **FR30**: System detects when the recognition worker, the Telegram bot, or the supervisor itself has crashed, and restarts the failed component within 5 seconds, without disrupting components that remain running.
- **FR31**: System fails gracefully when an external dependency (e.g., Telegram connectivity) is unavailable — the player and recognition continue to function; only the affected component is degraded.
- **FR32**: System captures per-component logs to local files for post-hoc inspection.

#### Self-Test & Verification

- **FR33**: Operator can run a self-test that measures recognition accuracy (true-positive and false-positive rates) against a defined seed set of registered people.
- **FR34**: Operator can run a self-test that measures end-to-end latency from face detection to greeting display, reporting both p50 and p95.
- **FR35**: Self-test results are printed in a form suitable for inclusion in project documentation (README).

### NonFunctional Requirements

#### Performance

- **NFR1**: End-to-end recognition latency p50 ≤ 1.0 s, p95 ≤ 2.0 s, measured by `benchmark.py` against the 5-person × 10-attempt seed set.
- **NFR2**: Greeting overlay fade-in/out 300–500 ms each end, no measurable dropped frames in underlying video during fade.
- **NFR3**: Cold-boot time < 30 s on the demo machine.
- **NFR4**: DB hot-reload propagation ≤ 5 s.
- **NFR5**: New videos picked up within one playlist iteration (≤ 60 s) without restart.
- **NFR6**: Telegram `/add_person` round-trip < 30 s end-to-end.

#### Reliability

- **NFR7**: System runs ≥ 60 minutes continuous unattended operation with zero crashes, zero unrecoverable error states, no playback degradation.
- **NFR8**: Memory footprint growth ≤ 100 MB over a 60-minute run.
- **NFR9**: Zero recognition false positives against baseline 5-stranger seed set during a 60-minute run, at configured tolerance.
- **NFR10**: ≥ 95% recognition true-positive rate on registered 5-person seed set under demo lighting.
- **NFR11**: Component crash recovery is automatic and transparent to the visitor — no on-screen artifact, no greeting interruption, no video stutter when a non-player component restarts.
- **NFR12**: System continues full visitor-facing operation when network is down; only admin bot operations are degraded.

#### Security & Privacy

- **NFR13**: All facial biometric data remains on the demo machine. No outbound network calls except Telegram API on behalf of the admin bot.
- **NFR14**: Camera frames are not persisted to disk during normal operation.
- **NFR15**: Source face photos in `faces/` are kept for re-embedding only; deletion of a person removes both the embedding and any associated source photo.
- **NFR16**: Telegram bot token and admin chat-ID allowlist are not committed to version control. `.gitignore` enforces this for `config.yaml` and `.env`.
- **NFR17**: All `people.json` writes are atomic (write-to-tmp + `os.replace()`).
- **NFR18**: All video file additions to `videos/` are atomic (write to `videos/.tmp/` + `os.replace()`).

#### Resource & Capacity

- **NFR19**: Operates on a single Windows 10/11 laptop, no GPU dependency.
- **NFR20**: Supports up to 200 registered people without exceeding NFR1 latency targets.
- **NFR21**: Supports up to 50 videos in playlist without playback issues.
- **NFR22**: Bot enforces 20 MB Telegram bot-API file-size limit and rejects larger files with the CLI fallback message.

#### Usability

- **NFR23**: Non-technical admin can add a new person via Telegram in < 30 s without instructions.
- **NFR24**: Non-technical admin can add a new promo video via Telegram in < 60 s without instructions.
- **NFR25**: Greeting text font size ≥ 8% of display height for readability at 2–3 m.
- **NFR26**: All bot replies are single-message, plain-language — no command-syntax dumps, no markdown chrome.
- **NFR27**: File-size rejection includes the alternative CLI path in plain language.

#### Observability & Diagnosability

- **NFR28**: Each runtime component writes stdout/stderr to `logs/<component>.log`, retained for the duration of the run.
- **NFR29**: Supervisor prints rolling-tail of all component logs to console on demand.
- **NFR30**: `benchmark.py` produces machine-readable output (p50/p95 latency + accuracy %) suitable for direct README inclusion.
- **NFR31**: Unauthorized bot access attempts logged with timestamp + chat ID + attempted command in `logs/bot.log`.

### Additional Requirements

These derive from the PRD's *Desktop Application — Specific Requirements*, *Implementation Considerations*, *Privacy & Data Handling*, and *Risk Mitigation Strategy* sections — they affect epic sequencing, project setup, or are operational/build constraints not captured as runtime FR/NFR.

#### Project Setup & Build Constraints

- **AR1 (Pre-build, hour 0–0.5)**: dlib install path on Windows must be resolved before any other coding starts. Use prebuilt wheel (`dlib-bin` or equivalent known-good wheel) — not source compilation. **This is the dominant platform risk and must be the first thing in the build.**
- **AR2**: No starter template — the project starts from `git init` with a clean Python 3.11+ virtualenv. There is no scaffolded codebase to extend.
- **AR3**: All Python dependencies pinned to exact versions (`==`) in `requirements.txt`.
- **AR4**: `.gitignore` includes `config.yaml`, `.env`, `logs/`, `faces/`, `videos/`, and `videos/.tmp/`.
- **AR5**: Single project root. Folder layout: `videos/` (promo loop), `faces/` (source photos for re-embedding), `logs/` (per-component log files), `people.json` (embeddings DB at root), `config.yaml` (gitignored, runtime config), `requirements.txt`, `run.py` (supervisor entry point), individual module files.

#### Process Architecture (binds Epic 4 — System Operations)

- **AR6**: Three-process model with a top-level supervisor: (a) main process = video player, (b) `multiprocessing.Process` = recognition worker, (c) subprocess = Telegram bot. The recognition worker MUST be its own process (not a thread) to avoid GIL contention with Qt's event loop.
- **AR7**: IPC: `multiprocessing.Queue` for greeting events (worker → player). `watchdog.Observer` in worker watches `people.json`. Player rescans `videos/` folder at end-of-video.
- **AR8**: Frame strategy: worker pulls frames at native camera rate, downsamples to 320×240 for detection, embeds at native crop. **Skip frames if behind — never queue them.**
- **AR9**: Atomic write contract: a single shared writer module is used by both the bot and CLI scripts for `people.json` and `videos/` writes — no drift between code paths.

#### Configuration

- **AR10**: Single `config.yaml` (gitignored) with: telegram token, admin chat IDs allowlist, camera device index, recognition tolerance (default 0.5), cooldown seconds (default 60), display duration (default 5 s), video folder path, font-size factor (default 0.08), log directory.

#### Test Data

- **AR11**: A defined **5-person seed set** of registered demo faces (with 10 walk-past attempts each) is used by `benchmark.py` for accuracy + latency measurement (NFR1, NFR10).
- **AR12**: A defined **5-stranger seed set** is used by `benchmark.py` for false-positive rate measurement (NFR9).

#### Submission Deliverables (deliverables, not runtime capabilities)

- **AR13**: `README.md` covering: setup steps (Python version, `dlib-bin` install, requirements install, config file template, run command), ASCII architecture diagram, selection-strategy paragraph (largest-face-wins), threading/process-model paragraph, latency + accuracy numbers from `benchmark.py`.
- **AR14**: 1–3 minute demo video, recorded by hour 22 of the build budget, walking through the 5 demo scenes (known greeted → unknown ignored → admin adds person via bot → that person greeted → admin pushes new video via bot → video appears in loop).

#### Hard Cutoff Rules (from PRD Risk Mitigation — operational doctrine for sequencing)

- **AR15 (hour 14)**: If integration (Epic 4) isn't done → drop the Telegram bot from MVP, ship CLI-only admin (`add_person.py` + `add_video.py` still ship), document the choice in README.
- **AR16 (hour 17)**: If video-management bot commands aren't working → drop them from MVP, keep CLI fallback only, update demo script.
- **AR17 (hour 20)**: If no clean 30+ min run achieved → freeze all features, debug-only mode until demo recording.
- **AR18 (hour 22)**: Demo video gets recorded no later than this point, even with known minor bugs.

### UX Design Requirements

**N/A** — No separate UX Design document exists. UX-equivalent constraints (font ratio, fade timing, overlay layout, bot reply tone, file-size error messaging) are captured in NFRs (NFR2, NFR25, NFR26, NFR27) and the Greeting Display / Telegram bot subsections of the PRD's *Desktop Application — Specific Requirements*. Stories will reference those NFRs directly rather than translate to UX-DRs.

### FR Coverage Map

| FR | Epic(s) | Notes |
|---|---|---|
| FR1, FR2, FR3, FR4, FR5 | E2 | Recognition pipeline |
| FR6, FR7, FR8, FR9 | E2 | Greeting display + cooldown |
| FR10 | E1 | Promo loop |
| FR11 | E3 | Player playlist rescan (needed for video commands) |
| FR12 | E1 → E2 | Uninterrupted playback (introduced E1, proven during admin actions in E2) |
| FR13, FR15, FR16 | E3 | Bot people commands |
| FR14 | E4 | CLI `add_person.py` fallback |
| FR17 | E2 | `people.json` persistence |
| FR18, FR19 | E3 | Hot-reload (DB write → recognition picks up / drops) |
| FR20, FR22, FR23, FR24, FR25 | E3 | Bot video commands |
| FR21 | E4 | CLI `add_video.py` fallback |
| FR26, FR27 | E3 | Admin allowlist + unauthorized handling |
| FR28 | E1 → E3 | Single-command launch (player-only in E1, full system via supervisor in E3) |
| FR29 | E1 → E2 → E3 | Concurrent components (incremental: player, +worker, +bot) |
| FR30 | E3 | Component crash detection + restart |
| FR31 | E3 → E4 | Graceful network degradation (bot side in E3, CLI fallback verified in E4) |
| FR32 | E3 → E4 | Per-component logs (logging starts E3, full per-component verified E4) |
| FR33, FR34, FR35 | E4 | `benchmark.py` self-test |

**All 35 FRs covered. No orphans.**

## Epic List

### Epic 1: Project Foundation & Demo-Ready Promo Loop

**Goal:** Operator launches a single command on the Windows demo machine and the entrance monitor immediately shows a fullscreen looping promo video. The kiosk *exists* — recognition not yet present, but the hardware-software bridge is real and demoable. This is the fall-back demo if everything else collapses.

**Maps to Brief Blocks 0 + 1** (≈ 3.5 hours of build budget).

**FRs covered:** FR10, FR12 (introduced), FR28 (player-only), FR29 (player-only)
**NFRs proven:** NFR3, NFR19, NFR25
**ARs covered:** AR1 (dlib install verified FIRST), AR2, AR3, AR4, AR5, AR10

### Epic 2: Visitor Recognition & Personalized Greeting

**Goal:** A registered visitor walks up to the kiosk and sees "Welcome, [Name]!" fade in over the still-playing promo video. An unregistered visitor sees nothing. The cooldown prevents repeat greetings within 60 seconds. **Journeys 1, 2, and 3 work end-to-end — the actual MVP win.** If the project ships only Epic 1 + Epic 2, the core product is real (just no remote admin).

**Maps to Brief Blocks 2 + 3** (≈ 5.5 hours of build budget).

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR12 (proven), FR17, FR29 (player + worker)
**NFRs proven:** NFR1, NFR2, NFR9, NFR10, NFR11 (worker-side partial), NFR15
**ARs covered:** AR6, AR7, AR8, AR9 (atomic writer module — first use), AR11

### Epic 3: Telegram Remote Control (People + Videos)

**Goal:** The office manager (Dilnoza) can add or remove registered people **and** add or remove promo videos from her phone via Telegram. New entries take effect within 5 seconds without restart. **Journeys 4 and 4b work end-to-end.** The "kiosk as chat-managed surface" thesis becomes demonstrable.

**Maps to Brief Block 4** (≈ 3 hours of build budget).
**Hour 14 cutoff (AR15)** hits at start of this epic — if Epic 2 isn't done by hour 14, this epic gets cut to CLI-only.
**Hour 17 cutoff (AR16)** halves this epic — if video-management bot commands aren't working, drop them and ship people-commands only.

**FRs covered:** FR11, FR13, FR15, FR16, FR18, FR19, FR20, FR22, FR23, FR24, FR25, FR26, FR27, FR29 (full system), FR30, FR31 (Telegram-down case), FR32 (logging starts)
**NFRs proven:** NFR4, NFR5, NFR6, NFR12, NFR16, NFR17, NFR18, NFR22, NFR23, NFR24, NFR26, NFR27, NFR29, NFR31
**ARs covered:** AR9 (writer reused by bot), AR15, AR16

### Epic 4: Offline Resilience, Self-Test & Submission

**Goal:** Operator (Sanji) has CLI fallbacks for both face and video addition that work without internet — Wi-Fi failure at the venue is no longer fatal (Journey 5 works). Operator also has a `benchmark.py` self-test that produces reproducible accuracy and latency numbers for the README and judging. README + ASCII architecture diagram + 1–3 minute demo video exist in the repo at submission time.

**Maps to Brief Blocks 5 + 6 + 7** (≈ 4.5 hours of build budget).
**Hour 20 cutoff (AR17)** gates the stability story — if no clean 30+ min run achieved, freeze features.
**Hour 22 cutoff (AR18)** is the hard stop for demo recording.

**FRs covered:** FR14, FR21, FR31 (full coverage), FR32 (full coverage), FR33, FR34, FR35
**NFRs proven:** NFR7, NFR8, NFR11 (full crash-recovery), NFR13, NFR14, NFR28, NFR30
**ARs covered:** AR12, AR13, AR14, AR17, AR18

### Epic Dependencies

- **Epic 1:** Standalone, fully self-contained.
- **Epic 2:** Depends on Epic 1 (needs the player to overlay onto). After Epic 2: visitor experience complete.
- **Epic 3:** Depends on Epic 1 + Epic 2 (needs player + worker for hot-reload to be observable; reuses Epic 2's writer pattern). After Epic 3: full admin flow works.
- **Epic 4:** Depends on Epic 1 + Epic 2 + Epic 3 (CLI fallbacks share the writer module; benchmark uses recognition pipeline; submission docs need all prior to exist). After Epic 4: PRD's MVP test (4 questions) all answer "yes."

No circular dependencies. Each epic delivers an outcome a real person experiences.

## Epic 1: Project Foundation & Demo-Ready Promo Loop - Stories

**Goal recap:** Operator launches `python run.py` and the entrance monitor immediately shows a fullscreen looping promo video. The kiosk exists. Brief blocks 0 + 1, approximately 3.5 h budget.

**FRs covered:** FR10, FR12 (intro), FR28 (player-only), FR29 (player-only)
**ARs covered:** AR1 (dlib install first), AR2, AR3, AR4, AR5, AR10

### Story 1.1: Verify dlib + face_recognition install on Windows demo machine

As a buildathon operator,
I want to verify that dlib and face_recognition install cleanly on the Windows demo machine,
So that the dominant platform risk (AR1) is eliminated within the first 30 minutes.

**Acceptance Criteria:**

**Given** a clean Python 3.11+ virtualenv on the Windows demo machine
**When** I run `pip install dlib-bin face_recognition opencv-python`
**Then** all three packages install in < 60 s without source compilation
**And** I can run a smoke-test script that loads a sample image, detects a face, and computes a 128-dim embedding without error
**And** the smoke-test script is saved as `tests/smoke_dlib.py` (or captured as a setup artifact if the repo has not been initialized yet) for future re-verification on a fresh machine

### Story 1.2: Initialize project repository structure

As the operator,
I want a clean project root with the canonical folder layout, pinned dependencies, and protected secrets,
So that all subsequent code has a known place to live and no sensitive files leak into git.

**Acceptance Criteria:**

**Given** `git init` is run in an empty folder
**When** project setup completes
**Then** the repo contains: `videos/.gitkeep` (playlist folder present, video files ignored), `tests/assets/seed-promo.mp4` (small tracked sample video for local setup), `tests/smoke_dlib.py` from Story 1.1, `faces/`, `logs/`, an empty `run.py`, `requirements.txt` with all dependencies pinned to exact versions (`==`), `config.yaml.example` committed as template, `.gitignore` covering `config.yaml`, `.env`, `logs/`, `faces/`, `videos/*` with an exception for `videos/.gitkeep`, and `videos/.tmp/`, and a `README.md` skeleton with section headers (Setup / Architecture / Selection Strategy / Threading Model / Benchmark Results)
**And** the setup notes explain that `tests/assets/seed-promo.mp4` should be copied into `videos/` before running the player locally
**And** running `git status` shows zero secrets pending commit

### Story 1.3: Render fullscreen looping promo video player

As a visitor (any human walking past the entrance monitor),
I want to see promo videos playing fullscreen on the entrance monitor,
So that the kiosk delivers the office's branded message even before recognition is built.

**Acceptance Criteria:**

**Given** at least one `.mp4` file exists in `videos/` and `python run.py` is invoked
**When** the player initializes
**Then** a Qt window opens in fullscreen mode on the primary display, plays the first video to completion, and automatically advances to the next file (or loops back to the first if only one)
**And** the playlist continues looping indefinitely until the application is exited
**And** pressing Esc cleanly exits the application without leaving zombie processes
**And** the player runs on Windows 10 / 11 with no GPU dependency (NFR19)

### Story 1.4: Validate fade-in/out greeting overlay over promo video

As a developer,
I want the player to display a fade-in/out text overlay over the video on a manual trigger,
So that I can validate the no-stutter overlay architecture (NFR2, NFR11) before integrating with recognition in Epic 2.

**Acceptance Criteria:**

**Given** the player from Story 1.3 is running fullscreen
**When** I trigger the overlay (via a 10-second timer or keyboard shortcut)
**Then** a "TEST GREETING" text overlay fades in over 300-500 ms, holds for 5 s, and fades out over 300-500 ms
**And** the underlying video does not pause, skip, or visually stutter during the fade animation
**And** the overlay font size is >= 8% of display height (NFR25), centered horizontally
**And** the overlay is rendered as a separate Qt widget composited above the video widget (the video frame is never modified)

**Epic 1 Summary:** 4 stories covering the foundation, visible promo loop, and overlay test. FR10 is covered by Story 1.3; FR12 by Stories 1.3 and 1.4; FR28 by Story 1.3; FR29 by Story 1.3 as the player-only process at this stage. AR1 is covered by Story 1.1; AR2-AR5 by Story 1.2; AR10 partially by `config.yaml.example` in Story 1.2. Dependency order: 1.1 -> 1.2 -> 1.3 -> 1.4.

## Epic 2: Visitor Recognition & Personalized Greeting - Stories

**Goal recap:** A registered visitor walks up and sees "Welcome, [Name]!" fade in over the still-playing promo video. Unknown visitor sees nothing. Cooldown prevents repeats. Journeys 1, 2, and 3 work end-to-end. Brief blocks 2 + 3, approximately 5.5 h budget.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR12 (proven), FR17, FR29 (player + worker)
**ARs covered:** AR6, AR7, AR8, AR9, AR11

### Story 2.1: Build single-frame face recognition utility

As a developer,
I want a reusable module that takes a frame and returns matched-name-or-None,
So that recognition logic is encapsulated and unit-testable independent of camera or process model.

**Acceptance Criteria:**

**Given** a `people.json` file containing seed embeddings and a `config.yaml` specifying recognition tolerance (default 0.5)
**When** I call `recognize(frame_array)` on an image containing a registered person's face
**Then** the function returns the matched name string
**And** when called on an unknown face, returns `None`
**And** when called on a frame with no detectable face, returns `None`
**And** when called on a frame with multiple registered faces, returns the name corresponding to the largest face area (FR4)
**And** the function uses tolerance from `config.yaml` so threshold is configurable without code change (FR3)

### Story 2.2: Implement people.json store with shared atomic writer module

As a developer,
I want a single shared writer module for adding/removing people from `people.json`,
So that the bot, CLI scripts, and any future writer use one code path with atomic semantics, with no drift between paths (AR9).

**Acceptance Criteria:**

**Given** an empty `people.json` (or no file yet)
**When** I call `add_person(name, image_path)` from the writer module
**Then** the writer computes a 128-dim embedding from the image, writes the updated DB to `people.json.tmp`, then `os.replace()` to `people.json` atomically (NFR17)
**And** the source photo is copied into `faces/<name>.jpg` for re-embedding purposes (NFR15)
**And** when I call `remove_person(name)`, the entry is removed atomically and the corresponding `faces/<name>.jpg` is deleted (NFR15)
**And** `add_person` with a duplicate name overwrites the existing entry (no silent failure)
**And** `remove_person` with an unknown name returns `False` without raising (caller handles UX response)

### Story 2.3: Run recognition worker as separate process with camera capture

As the operator,
I want recognition to run in its own OS process pulling frames from the USB camera,
So that the player's Qt event loop is never blocked by dlib's CPU work (AR6 - GIL avoidance).

**Acceptance Criteria:**

**Given** `config.yaml` specifies a camera device index and `people.json` has at least one registered person
**When** the worker is spawned via `multiprocessing.Process`
**Then** it opens `cv2.VideoCapture(<index>)` and pulls frames at native rate
**And** downsamples each frame to 320x240 for face detection (AR8), embeds at native crop
**And** skips frames if it falls behind, never queues stale frames (AR8)
**And** prints `MATCH: <name>` to stdout every time the matcher returns a name (no greeting yet - that is Story 2.4)
**And** prints nothing for unknown faces or empty frames (FR5)
**And** if camera index is invalid, the worker exits with a clear error and exit code 1

### Story 2.4: Wire greeting queue between worker and player

As a visitor,
I want my name to appear on the screen when the camera sees me,
So that the kiosk acknowledges me personally (Journey 1 happy path).

**Acceptance Criteria:**

**Given** the worker (Story 2.3) and the player (Story 1.3 + 1.4 overlay) are both running, and `people.json` contains my registered face
**When** I walk into the camera frame at approximately 1 m distance
**Then** the worker pushes a `{name, timestamp}` event to a `multiprocessing.Queue` (AR7)
**And** the player polls the queue from its event loop and triggers the overlay with text `Welcome, <name>!`
**And** the greeting becomes visible on screen within 2 seconds of my face entering frame (NFR1, p95 <= 2.0 s)
**And** the underlying promo video does not pause, skip, or stutter during the fade (NFR2)
**And** an unregistered visitor walking past produces no event and no UI change (FR5, Journey 2)

### Story 2.5: Add per-person greeting cooldown

As a visitor (Aziza in Journey 3),
I want to not be greeted again every time I walk past the screen within a short window,
So that the kiosk feels intelligent rather than spammy.

**Acceptance Criteria:**

**Given** the worker has just emitted a greeting event for person X at time T
**When** the same person X is detected again at time T+30 s (within the default 60 s cooldown)
**Then** the worker suppresses the event and no new event is pushed to the queue (FR8)
**And** when person X is detected again at time T+90 s (past cooldown)
**Then** a fresh greeting event is emitted normally
**And** the cooldown table is an in-memory `dict[name, last_greeted_at]` in the worker, cleared on worker restart (acceptable per PRD Implementation Considerations)
**And** the cooldown duration is configurable via `config.yaml` (FR9, default 60 s)

### Story 2.6: Bootstrap 5-person seed set + verify accuracy under demo lighting

As the operator,
I want a known set of 5 registered demo faces installed and verified to recognize correctly under the actual demo lighting,
So that the recognition pipeline's accuracy claims (NFR9, NFR10) are proven before the bot is built (AR11).

**Acceptance Criteria:**

**Given** 5 source photos exist (one per demo person), and Story 2.2's writer module is functional
**When** I add each of the 5 demo people via the writer module
**Then** `people.json` contains 5 valid entries with 128-dim embeddings
**And** when each person performs 10 walk-past attempts under demo lighting conditions, the system achieves >= 95% true-positive rate across the 50 attempts (NFR10)
**And** when 5 strangers (control set) perform 10 walk-past attempts each, the system produces 0 false-positive greetings (NFR9) at the configured tolerance
**And** if accuracy targets are not met, the operator lowers the tolerance from default (0.5) and re-tests, documenting the chosen value in `config.yaml`

**Epic 2 Summary:** 6 stories covering the recognition pipeline and the visitor experience. FR1-FR2 are covered by Story 2.3; FR3 by Stories 2.1 and 2.6; FR4 by Story 2.1; FR5 by Stories 2.3 and 2.4; FR6-FR7 by Story 2.4; FR8-FR9 by Story 2.5; FR12 by Stories 2.4 and 2.5; FR17 by Story 2.2; FR29 by Stories 2.3 and 2.4. Dependency order: 2.1 -> 2.2 -> 2.3 -> 2.4 -> 2.5 -> 2.6.

## Epic 3: Telegram Remote Control (People + Videos) - Stories

**Goal recap:** Dilnoza adds/removes people and adds/removes promo videos from her phone via Telegram. New entries take effect within 5 seconds without restart. Journeys 4 and 4b work end-to-end. Brief block 4, approximately 3 h budget.

**FRs covered:** FR11, FR13, FR15, FR16, FR18, FR19, FR20, FR22, FR23, FR24, FR25, FR26, FR27, FR29 (full system), FR30, FR31 (Telegram-down case), FR32 (logging starts)
**ARs covered:** AR9, AR15, AR16

### Story 3.1: Wire supervisor for component lifecycle (start, log, restart)

As the operator,
I want a single `python run.py` to spawn the player, recognition worker, and a temporary bot-process stub, capture their logs, and restart supervised background components,
So that the lifecycle contract is proven before the real Telegram bot is added (FR28, FR29 full, FR30, FR32).

**Acceptance Criteria:**

**Given** `run.py` exists at the project root
**When** I invoke `python run.py`
**Then** the supervisor spawns the player (in main process), the recognition worker (`multiprocessing.Process`), and a minimal `bot.py` stub subprocess that starts, writes `BOT_STUB_READY`, and stays alive until shutdown
**And** all three supervised components are ready (player rendering, worker pulling frames, bot stub running) within < 30 s cold-boot (NFR3)
**And** each component's stdout/stderr is captured to `logs/<component>.log`: `logs/player.log`, `logs/worker.log`, `logs/bot.log`, and `logs/supervisor.log` (NFR28, FR32)
**And** if the bot stub or worker process exits non-zero, the supervisor detects within 5 s and restarts that component without killing the player or the other component (FR30, NFR11)
**And** the supervisor can print a rolling tail of all component logs to the console on demand, sufficient to identify which component crashed or degraded during a demo (NFR29)
**And** pressing Ctrl+C on the supervisor cleanly shuts down all three components (no zombies, no orphan processes)

### Story 3.2: Bootstrap Telegram bot with admin allowlist

As the operator,
I want the bot stub from Story 3.1 replaced by a real Telegram bot process that only responds to allowlisted chat IDs,
So that no random user can manipulate the kiosk (FR26, FR27, NFR16, NFR31).

**Acceptance Criteria:**

**Given** `config.yaml` contains `telegram_token: <token>` and `admin_chat_ids: [N1, N2, ...]` (config file is gitignored per Story 1.2)
**When** the supervisor starts the bot subprocess
**Then** the real Telegram bot replaces the Story 3.1 stub, connects to Telegram, and writes a ready log line without exposing the token
**And** when the bot receives `/start` from an allowlisted chat ID, it replies `Welcome admin` (single-message, plain language per NFR26)
**And** when `/start` (or any command) is received from a non-allowlisted chat ID, the bot replies `Unauthorized` and writes a log entry to `logs/bot.log` containing `[<timestamp>] UNAUTHORIZED chat_id=<id> command=<cmd>` (FR27, NFR31)
**And** the allowlist check runs in middleware before any command handler; no command leaks behavior to non-allowlisted users
**And** the `telegram_token` value is never written to any log file
**And** if Telegram is unreachable on bot startup, the supervisor logs the error to `logs/supervisor.log` and the bot subprocess exits or retries according to supervisor policy; player and worker continue running normally (FR31, NFR12)

### Story 3.3: Implement /add_person via Telegram bot

As Dilnoza (admin in Journey 4),
I want to add a new registered person from my phone by sending name + photo to the bot,
So that I never have to email IT or open a terminal.

**Acceptance Criteria:**

**Given** I am an allowlisted admin
**When** I send `/add_person`
**Then** the bot replies `Send me a name, then a photo` (NFR26)
**And** when I reply with a name (text), the bot stores it as pending state for my chat
**And** when I subsequently send a photo (<= 20 MB per Telegram bot-API limit, NFR22), the bot downloads it, invokes the shared writer module from Story 2.2 (no duplicate write logic - AR9), and replies `<name> added`
**And** the total round-trip from `/add_person` to confirmation is < 30 s for a non-technical user (NFR6, NFR23)
**And** if I send a photo with no detectable face, the bot replies `No face detected in that photo. Please try a clearer front-facing photo.` and clears my pending state
**And** the new entry in `people.json` is written atomically (NFR17 - guaranteed by reusing Story 2.2's writer)

### Story 3.4: Implement /list_people and /delete_person

As Dilnoza,
I want to see who is currently registered and remove people who no longer work here,
So that I can manage the DB without learning anything new.

**Acceptance Criteria:**

**Given** I am an allowlisted admin
**When** I send `/list_people`
**Then** the bot replies with a single message containing newline-separated names of all registered people (FR15, NFR26)
**And** when `people.json` is empty, the bot replies `No people registered yet. Use /add_person to add someone.`
**And** when I send `/delete_person <name>`, the writer module (Story 2.2) removes the entry and deletes `faces/<name>.jpg` (NFR15), and the bot replies `<name> removed`
**And** when I send `/delete_person` for a name that does not exist, the bot replies `Person not found. Use /list_people to see who is registered.`
**And** name matching is case-sensitive and exact (no fuzzy matching to avoid surprise deletions)

### Story 3.5: Add file-watcher hot-reload to recognition worker

As Dilnoza,
I want a person I just added to be recognized the next time they walk past the camera,
So that my admin actions take effect immediately without restarting the system (Journey 4 climax).

**Acceptance Criteria:**

**Given** the recognition worker (Story 2.3) is running
**When** `people.json` is modified by any writer (bot from Story 3.3, CLI from Epic 4, or manual edit)
**Then** the worker's `watchdog.Observer` detects the change and reloads its in-memory embedding set within 5 seconds (FR18, NFR4)
**And** the next camera frame containing the newly-added person triggers a greeting (FR18 demonstrated end-to-end)
**And** when a person is removed, the worker drops them from its in-memory set within 5 seconds; they stop being greeted on the next walk-past (FR19)
**And** the worker handles partial-write states gracefully because Story 2.2's atomic writer (`os.replace()`) guarantees no half-written files, so the watcher only observes valid `people.json` states
**And** a malformed `people.json` (for example, manual hand-edit error) is logged to `logs/worker.log` and the previous valid embedding set is retained (no crash)

### Story 3.6: Implement /add_video via Telegram with size check

As Dilnoza (Journey 4b),
I want to push a new promo video from my phone by sending the file to the bot,
So that the office display can update content without me touching the laptop.

**Acceptance Criteria:**

**Given** I am an allowlisted admin
**When** I send `/add_video`
**Then** the bot replies `Send me the video file` (NFR26)
**And** when I send a video file <= 20 MB (Telegram bot-API limit, NFR22)
**Then** the bot downloads the file, atomically copies it into `videos/<filename>` (writes to `videos/.tmp/<filename>`, then `os.replace()` to final path - NFR18, AR9), and replies `<filename> added. Playlist now has N videos` (FR20)
**And** when I send a video file > 20 MB
**Then** the bot replies `This video is over 20 MB. Please upload it via add_video.py on the laptop.` (FR25, NFR22, NFR27)
**And** the round-trip for a sub-20 MB video from `/add_video` to confirmation is < 60 s (NFR24)
**And** if the file is not a video format the player supports, the bot replies `That file format is not supported. Please use .mp4, .mov, or .webm.` and the file is not written to `videos/`

### Story 3.7: Implement /list_videos, /delete_video, and player playlist rescan

As Dilnoza,
I want to see and remove videos from the playlist, and see new videos appear in the loop without restart,
So that video management is as fluid as people management.

**Acceptance Criteria:**

**Given** at least one video exists in `videos/`
**When** I send `/list_videos`
**Then** the bot replies with a single message containing newline-separated filenames (FR22, NFR26)
**And** when I send `/delete_video <filename>`, the file is removed from `videos/`, the bot replies `<filename> removed. Playlist now has N videos` (FR23)
**And** when I send `/delete_video <unknown>`, the bot replies `Video not found. Use /list_videos to see what is in the playlist.`
**And** the player rescans the `videos/` folder at the end of each video iteration, ignoring the `videos/.tmp/` directory entirely as a defensive backstop (FR11)
**And** when a new video is added (via Story 3.6), it appears in the next playlist iteration, within <= 60 s for typical promo length (NFR5)
**And** when a currently-playing video is deleted, playback continues to its end without error and the file is excluded from the next iteration
**And** the playlist supports up to 50 video files without playback issues during rescan or iteration (NFR21)

**Epic 3 Summary:** 7 stories covering supervisor, bot, people commands, hot-reload, and video commands. Dependency order: 3.1 -> 3.2 -> 3.3 -> 3.4 -> 3.5 -> 3.6 -> 3.7. Stories 3.6 and 3.7 are the AR16 hour-17 drop target and can be cut without breaking Stories 3.1-3.5.

## Epic 4: Offline Resilience, Self-Test & Submission - Stories

**Goal recap:** CLI fallbacks for Wi-Fi failure; reproducible accuracy/latency benchmark for the README; 60-min stability shakedown on the actual demo machine; submission deliverables exist in the repo. Brief blocks 5 + 6 + 7, approximately 4.5 h budget.

**FRs covered:** FR14, FR21, FR31 (full coverage), FR32 (full coverage), FR33, FR34, FR35
**ARs covered:** AR12, AR13, AR14, AR17, AR18

### Story 4.1: Build add_person.py CLI fallback

As Sanji (operator at the venue, with no Wi-Fi),
I want a CLI script that adds a registered person without requiring Telegram or any network connection,
So that I can prep demo people on stage even when venue Wi-Fi is down (Journey 5).

**Acceptance Criteria:**

**Given** the shared writer module from Story 2.2 exists and the worker (Story 2.3) is running with hot-reload (Story 3.5)
**When** I run `python add_person.py "Judge Karimov" path/to/photo.jpg`
**Then** the script invokes the same writer module that the bot uses (no duplicate logic, AR9), prints `Added: Judge Karimov`, and exits 0
**And** the worker's hot-reload picks up the change within 5 s (proves FR18 via CLI path)
**And** when run with missing args, the script prints a usage message (`Usage: python add_person.py "<name>" <image_path>`) and exits non-zero
**And** when the image path does not exist, prints `Error: image file not found: <path>` and exits non-zero
**And** when the image contains no detectable face, prints `Error: no face detected in <path>` and exits non-zero
**And** the script works completely offline with no network calls of any kind (FR14, FR31, NFR13)

### Story 4.2: Build add_video.py CLI fallback

As Sanji,
I want a CLI script that adds a video to the playlist without going through Telegram and without any file-size limit,
So that I can ship large promo videos (>20 MB) and operate offline (Journey 5).

**Acceptance Criteria:**

**Given** the shared atomic-video-writer pattern from Story 3.6 exists and the player (Story 1.3) rescans `videos/` at end-of-iteration (Story 3.7)
**When** I run `python add_video.py path/to/promo.mp4`
**Then** the script atomically copies the file to `videos/<filename>` (writes to `videos/.tmp/`, then `os.replace()` - NFR18), prints `Added: <filename>. Playlist now has N videos.`, and exits 0
**And** the player picks up the new video at end of current playback iteration, within <= 60 s for typical promo length (FR21, NFR5)
**And** files of any size are accepted (no 20 MB limit - the explicit reason for the CLI alternative, NFR22)
**And** when the file path does not exist, prints `Error: video file not found: <path>` and exits non-zero
**And** when the file is not a recognised video extension (`.mp4` / `.mov` / `.webm`), prints `Error: unsupported video format: <ext>. Use .mp4, .mov, or .webm.` and exits non-zero
**And** the script works completely offline with no network calls (FR21, FR31, NFR13)

### Story 4.3: Implement benchmark.py self-test for accuracy + latency boundary

As Sanji (and the buildathon judges),
I want a one-command script that produces reproducible accuracy and latency numbers,
So that the README's claims can be verified by anyone who runs the project (FR33, FR34, FR35, NFR30).

**Acceptance Criteria:**

**Given** `people.json` contains the 5-person seed set (from Story 2.6) and a `tests/strangers/` folder contains the 5-stranger control set (per AR12)
**When** I run `python benchmark.py`
**Then** the script: (a) for each of the 5 registered people, runs 10 walk-past simulations (using their reference photo or a held-out photo set) and computes the true-positive rate (TPR); (b) for each of the 5 strangers, runs 10 attempts and computes the false-positive rate (FPR); (c) measures recognition-pipeline latency from `recognize()` input to greeting-event emission for each successful match and reports p50 + p95 (FR34)
**And** the script clearly labels this latency as `Recognition pipeline latency`; full camera-to-overlay-visible latency is validated by Story 2.4 and demonstrated in Story 4.6
**And** the script prints results in a fixed, machine-readable format ready for direct README pasting (NFR30, AR13):

```text
Recognition pipeline latency p50: 0.82 s, p95: 1.64 s
True-positive rate: 96% (48/50 attempts)
False-positive rate: 0.0% (0/50 attempts)
Tolerance: 0.50
Seed set: 5 people x 10 attempts; control set: 5 strangers x 10 attempts
```

**And** if TPR < 95% or FPR > 0% on a clean run, the script flags the violation in stderr with the specific failure (for example, `WARNING: TPR 92% below NFR10 target of 95%`) and exits 0 either way
**And** the benchmark includes a capacity fixture with up to 200 registered embeddings and confirms recognition latency remains within NFR1 targets at that size (NFR20)
**And** the script does not require the player or supervisor to be running; it operates purely on `people.json` plus the seed/control image sets (FR33, FR35)

### Story 4.4: 60-minute stability shakedown on the demo machine

As Sanji,
I want to run the entire system uninterrupted for >= 60 minutes on the actual demo machine and verify zero crashes / no memory leak / no playback degradation,
So that I can trust the system on stage (NFR7, NFR8, NFR11, AR17).

**Acceptance Criteria:**

**Given** the full system (Epics 1-3 complete) is running on the demo machine (not the dev machine)
**When** I leave the system running for 60 minutes with intermittent walk-pasts (at least 5) and at least 2 admin actions (one `/add_person`, one `/add_video`)
**Then** the supervisor reports zero unrecoverable crashes (component restarts within Story 3.1's contract are acceptable and counted)
**And** memory growth is <= 100 MB measured at start vs end across the player + worker + bot processes combined (NFR8)
**And** at least 5 successful greetings are logged (proving recognition stayed functional) and zero false-positive greetings occurred (NFR9)
**And** camera frames are processed in memory only and are not persisted to disk during normal operation (NFR14)
**And** the video continues to play smoothly throughout; operator visually inspects 3 random 30-second windows during the run, no stutter / skip / freeze
**And** the run is documented in `tests/shakedown.md` with start time, end time, walk-past count, greeting count, memory before/after, and any anomalies
**And** hard gate per AR17: if this story does not pass by hour 20 of the build budget, all feature work freezes and remaining time is debug-only until the demo recording (Story 4.6)

### Story 4.5: Author README with architecture diagram and selection-strategy notes

As the buildathon judges (and any future operator),
I want a clear README explaining setup, architecture, threading model, selection strategy, and the latest accuracy/latency numbers,
So that the project is comprehensible and reproducible from a fresh checkout (AR13, FR35).

**Acceptance Criteria:**

**Given** the project is feature-complete (Stories 4.1-4.4 done) and `benchmark.py` has produced fresh output
**When** I write `README.md`
**Then** it contains all of the following sections, in order:
Setup, Architecture, Selection strategy, Threading model, Benchmark results, and CLI fallback
**And** Setup covers Python 3.11+, `pip install dlib-bin face_recognition opencv-python`, `pip install -r requirements.txt`, copying `config.yaml.example` to `config.yaml`, filling `telegram_token` + `admin_chat_ids`, and `python run.py`
**And** Architecture includes an ASCII diagram showing the 3 processes (player / worker / bot), IPC queue (worker -> player), file-watcher on `people.json` (worker), shared atomic writer module (bot + CLI), and playlist rescan at end-of-video (player)
**And** Selection strategy explains "largest face wins" when multiple registered people are visible (FR4) and why this heuristic was chosen
**And** Threading model explains why the recognition worker runs in its own OS process (`multiprocessing.Process`, not a thread): GIL avoidance for dlib's CPU work, isolation from Qt's event loop, and the architectural reason for no video stutter
**And** Benchmark results include verbatim output from the latest `benchmark.py` run, including timestamp
**And** CLI fallback includes brief usage examples for `add_person.py` and `add_video.py`, plus the explicit note that they exist for both >20 MB videos and offline operation
**And** the README is written assuming a non-technical-but-curious reader (a judge with engineering background but no familiarity with this project)
**And** all paths and commands shown have been verified to actually work on a fresh clone

### Story 4.6: Record 1-3 minute demo video covering all 5 demo scenes

As the buildathon judges (and as protection against live-demo failure),
I want a recorded video showing all 5 demo scenes in sequence,
So that the project's value is visible even if the live demo on stage fails for any reason (AR14, AR18).

**Acceptance Criteria:**

**Given** the system is running cleanly on the demo machine (Story 4.4 has passed)
**When** I record the demo video
**Then** the video shows the following in this order:
Cold boot; registered visitor greeted; unregistered visitor ignored; bot adds person; bot adds video
**And** Cold boot shows terminal running `python run.py`, with the screen alive with promo loop within 30 s (proves NFR3, FR28)
**And** Registered visitor greeted shows a registered demo person walking up, greeting `Welcome, [Name]!` fading in over the still-playing promo and fading out after 5 s, with no video stutter (proves Journey 1, FR1-FR8, NFR1, NFR2)
**And** Unregistered visitor ignored shows an unknown person walking up, nothing happening, and video continuing (proves Journey 2, FR5)
**And** Bot adds person shows admin opening Telegram, sending `/add_person`, name, and photo to the bot; bot replies confirmation; the new person walks up and is greeted (proves Journey 4, FR13, FR18, NFR23)
**And** Bot adds video shows admin sending `/add_video` plus video file via Telegram; bot replies confirmation; the new video appears in the next playlist iteration (proves Journey 4b, FR20, FR11, NFR24)
**And** total video length is 1-3 minutes (<= 180 s)
**And** the recording is saved to the repo at `demo/buildathon-demo.mp4` (gitignored from `videos/` to keep playlist clean)
**And** hard cutoff per AR18: the video must be recorded by hour 22 of the build budget, even if there are known minor bugs at that point

**Epic 4 Summary:** 6 stories covering CLI fallbacks, benchmark, stability gate, README, and demo video. Dependency order: 4.1 -> 4.2 -> 4.3 -> 4.4 -> 4.5 -> 4.6.

## Final Story Inventory

| Epic | Story Count | Hours (brief budget) | Cumulative Stories |
|---|---:|---:|---:|
| 1 - Foundation + Promo Loop | 4 | 3.5 | 4 |
| 2 - Recognition + Greeting | 6 | 5.5 | 10 |
| 3 - Telegram Remote Control | 7 | 3.0 | 17 |
| 4 - Resilience + Submission | 6 | 4.5 | 23 |
| **Total** | **23** | **16.5 named build hours + 7.5 h buffer/sleep** | **23** |

Coverage verification: All 35 FRs map to at least one story. All 31 NFRs are proven by at least one story's acceptance criteria. All 18 ARs are addressed by stories or by hard-cutoff gates baked into stories. No orphan requirements.
