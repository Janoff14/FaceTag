---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief.md
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 0
classification:
  projectType: desktop_app
  secondaryTypes:
    - cli_tool
    - bot
  domain: general
  complexity: low
  technicalComplexity: medium
  projectContext: greenfield
---

# Product Requirements Document - facial recognition - uzc

**Author:** Sanja
**Date:** 2026-05-15

## Executive Summary

A camera-and-monitor unit at an office entrance that loops promotional video by default, and acknowledges registered people by name with a fade-in greeting overlay — without ever pausing the video. The camera runs invisibly in the background; only the greeting is ever rendered. Recognition runs entirely on-device via Python + dlib + `face_recognition`, with a Telegram bot serving as the admin interface (no web panel). Built as a 24-hour solo buildathon entry, but the design intent extends beyond the contest: the same architecture should drop into any office that already has a kiosk display.

**Problem:** Office entrance monitors today are mute wallpaper. The camera and display are already there; the personalization layer isn't. Adding a person to existing systems means SSH or a clunky web admin — friction that kills adoption.

**Users:**
- **The visitor / employee** walking up to the door — wants a half-second of recognition, doesn't interact.
- **The office manager / receptionist** — adds people via Telegram in <30s, never opens a terminal.
- **Buildathon judges** — need to see the demo flow run cleanly under stage conditions.

### What Makes This Special

Two deliberate bets, each defensible independently:

1. **The screen never pauses for the greeting, and the camera never appears on screen.** The looping video keeps playing; a transparent text overlay fades the greeting in and out. Recognition happens entirely off-screen — the magic is that the visitor sees nothing but their own name appear over the promo. This is the highest-visibility scoring vector on stage, and the architectural restraint (overlay isolated from the video pipeline) is what protects "zero stutter."
2. **Telegram bot as the kiosk's remote controller, not a web panel — as a product opinion, not a hackathon shortcut.** The bot doesn't only manage people; it manages the **promo video playlist** too. An admin can add or remove videos from their phone, in chat, alongside adding faces. This makes the kiosk a single chat-managed surface — exactly what the people who run office displays would want over an SSH-and-web-admin workflow. The bot ships with CLI fallbacks (`add_person.py`, `add_video.py`) so the demo never depends on venue Wi-Fi.

**Core insight:** On-device facial recognition is now a `pip install`, not a cloud API. That collapses the whole "who runs the recognition service / where do embeddings live / what about privacy" stack down to "a folder on the laptop." Combined with chat-bot administration, this is the smallest viable kiosk-personalization product.

## Project Classification

| Field | Value |
|---|---|
| **Project Type** | Desktop application (Python, single-machine, fullscreen). Secondary surfaces: Telegram bot (admin) and CLI script (fallback admin). |
| **Domain** | General — no regulated-industry constraints. All data stays on-device; no cloud, no PII export, no compliance burden meaningful enough to shape the PRD. |
| **Domain complexity** | Low. |
| **Technical complexity** | Medium. Real risks live in parallel-process coordination, frame-rate-sensitive overlay timing, dlib install on Windows, IPC + DB hot-reload. |
| **Project Context** | Greenfield — no prior code, schemas, or production system to integrate with. |
| **Build constraints** | Solo developer, 24-hour fixed budget, single demo machine. |

## Success Criteria

### User Success

**The visitor / employee at the door**
- Recognition fires within **2 seconds** of the visitor's face entering frame at normal walking speed (≈1 m from camera).
- The greeting shows their **correct name**, in the right language (English for MVP).
- The video **does not stutter, pause, or skip** when the greeting fades in or out — the visitor's experience is "the screen just said hi to me; nothing else changed."
- An **unregistered visitor sees nothing happen.** No false greeting, no flash, no acknowledgement.

**The office manager / receptionist (admin)**
- Adds a new person to the database in **under 30 seconds**, on a phone, without reading instructions.
- The new person is recognized on the **next time they walk past the camera** — no app restart, no waiting on a daily reload, no manual re-embedding.

### Business Success

This is a buildathon. Business success = scoring well on the published rubric. Specific targets:

| Outcome | Target |
|---|---|
| Buildathon placement | **Top 3** (primary); **win** (stretch) |
| Personal pass/fail bar | All four runtime components (player, recognition worker, Telegram bot, hot-reload watcher) **boot cleanly from a cold start on the demo machine** and a registered face triggers a greeting within 2 seconds on the **first** attempt. |
| Demo deliverable | 1–3 min demo video recorded by **hour 22** of the build budget, regardless of remaining bugs. |
| Submission deliverable | README + architecture diagram + selection-strategy note in the repo at submission time. |

### Technical Success

| Metric | Target | Rubric vector |
|---|---|---|
| Recognition latency (face entering frame → overlay visible) | **p95 ≤ 2.0 s, p50 ≤ 1.0 s** | Speed (15%) |
| True-positive rate on registered faces under demo lighting | **≥ 95%** measured on a **5-person seed set** with 10 walk-past attempts each | Recognition accuracy (20%) |
| False-positive rate on unregistered faces | **< 2%** at tolerance ~0.5 (down from default 0.6) | Recognition accuracy (20%) |
| Overlay smoothness | 300–500 ms ease-in / ease-out, **no measurable dropped frames** in the underlying video during fade | Player + overlay quality (20%) |
| Continuous-run stability | **≥ 60 minutes** uninterrupted with no crash, video lag, or memory growth >100 MB | Parallel stream stability (10%) |
| Cold-start time | Full system ready (player up, worker pulling frames, bot connected) in **< 30 s** from `python run.py` | Personal pass/fail bar |
| DB hot-reload latency | New face from Telegram → recognized in ≤ **5 s** | DB + video UX (15%) |
| Telegram `/add_person` end-to-end | < **30 s** for a non-technical user from sending photo to receiving confirmation | DB + video UX (15%) |
| Code quality artifacts in repo at submission | README + ASCII architecture diagram + selection-strategy paragraph + threading-model paragraph + pinned `requirements.txt` + named `.gitignore` for `config.yaml`/`.env` — all present and accurate | Code quality (10%) |
| Creativity / "headline extra" | (a) Telegram bot manages **both** people and promo videos (uncommon at hackathons); (b) CLI fallback shipped as MVP, not contingency — demo survives Wi-Fi failure on stage | Creativity (10%) |

### Measurable Outcomes

Three outcomes that, taken together, mean the project shipped successfully:

1. **A clean 60-minute run video** captured before the demo, showing player + bot + worker running concurrently with at least 5 successful recognitions and 0 crashes.
2. **A scripted 60-second demo** that walks through: known person greeted → unknown person ignored → admin adds a new person via Telegram → that person walks up and is greeted → admin pushes a new promo video via Telegram and it appears in the loop. Recorded artifact exists in the repo.
3. **Cold-boot reproducibility**: a fresh checkout + `pip install -r requirements.txt` + `python run.py` brings the full system up on the demo machine in under 5 minutes of human time.

## Product Scope

### MVP — Minimum Viable Product

- Fullscreen looping video playlist from a local `videos/` folder
- On-device face detection + 128-dim embedding + match against local DB
- Greeting overlay: fade-in/out, 4–6 s on screen, 60 s per-person cooldown
- "Largest face wins" selection strategy when multiple known faces are in frame
- Telegram bot commands (people): `/add_person`, `/list_people`, `/delete_person`
- Telegram bot commands (videos): `/add_video`, `/list_videos`, `/delete_video` — bot accepts uploaded video files (≤20 MB Telegram bot-API limit), saves into `videos/` folder, replies with playlist confirmation
- DB hot-reload (worker re-reads `people.json` when bot or CLI writes to it)
- Player rescans `videos/` folder at the end of each video, so newly added/removed videos are picked up within one playlist iteration
- **CLI fallbacks**: `add_person.py <name> <image>` and `add_video.py <path>` scripts (offline-capable; `add_video.py` is also the path for videos >20 MB that can't pass through the Telegram bot)
- README with setup steps + architecture diagram (ASCII OK) + selection-strategy explanation
- 1–3 minute submitted demo video
- **Latency + recognition self-test script** (`benchmark.py`) that runs the 5-person × 10-attempt protocol and prints the p95/p50 + accuracy numbers

### Growth Features (Post-MVP)

- Time-of-day greeting variants (morning / afternoon / evening)
- `/register` self-registration with admin approval — strategically valuable bonus; demonstrates the "chat-bot admin > web admin" thesis
- Per-person language preference (UZ / EN / RU)
- Visitor event log (`events.log` with timestamp + name)
- Per-person personalized message / birthday field

### Vision (Future)

- **Drop-in deployment to existing office kiosks** — single installable that runs on any laptop with a USB camera and HDMI out
- Multi-camera + multi-display support (one bot, many entrances)
- Recognition-triggered *content* (e.g., switch to a department-specific promo when a known visitor walks in)
- Optional encrypted cloud sync for multi-site organizations
- Self-registration as the primary admin flow (admin approval becoming the exception)

### Out of Scope (Deliberately Excluded)

The following are intentionally *not* in MVP, Growth, or Vision — they were considered and rejected as poor fits for the product or the buildathon scope:

- **Web admin panel.** Replaced by the Telegram bot as a deliberate product opinion (see Executive Summary). Not a fallback, not a "nice-to-have for later" — actively rejected.
- **Authentication beyond the Telegram chat-ID allowlist.** No usernames, passwords, OAuth, or RBAC. The chat-ID allowlist (FR26, NFR16) is sufficient for the kiosk-admin threat model and avoids inventing an identity system.
- **Slack notifications.** Out of scope — the product communicates with admins via Telegram, period. No multi-channel notification system.
- **Scheduled playlists by time of day.** Different from the time-of-day greeting variants (which is a Growth feature). Scheduled playlist management (e.g., "play these videos 9–12, those 12–18") is rejected as scope creep — the playlist is a flat folder, not a calendar.
- **Cloud-managed face DB.** Recognition data lives on the demo machine, full stop. The Vision tier mentions *optional* cloud sync for multi-site orgs as a future possibility, but cloud as the *primary* data path is excluded.
- **User-facing analytics or dashboards.** No "today the system greeted N people" UI. The visitor event log (Growth Tier) is a flat append-only log file for ad-hoc inspection, not a dashboard.

## User Journeys

### Journey 1 — Aziza, the registered employee returning from lunch (happy path)

**Persona.** Aziza, 27, marketing coordinator. Walks past the entrance display ten times a day. Was added to the system on her first day by the office manager.

**Opening scene.** It's 14:17. Aziza walks into the lobby holding a coffee, looking at her phone. The entrance monitor is playing the usual promo loop — a 30-second video about the company.

**Rising action.** She doesn't look at the monitor. She doesn't need to. She's heading to the elevator. The camera, mounted just above the screen, sees her face from about 1.5 m away.

**Climax.** As she crosses the 1 m threshold, the words **"Welcome back, Aziza!"** fade in over the still-playing video. She catches it out of the corner of her eye. The video underneath hasn't paused; the brand sting hasn't skipped. Just text, 4 seconds, then it fades back out and the monitor is just a promo again.

**Resolution.** Aziza smiles slightly. She keeps walking. She doesn't tell anyone, but later that week she mentions to a colleague that "the screen knows me now." That's the win.

**Capabilities revealed:** real-time face detection from camera feed; embedding match against local DB; cooldown-managed greeting overlay; non-blocking video playback.

### Journey 2 — Marco, the unregistered visitor (silent-ignore path)

**Persona.** Marco, a vendor visiting the office for the first time. Nobody has ever seen his face before; he's not in the database.

**Opening scene.** Marco arrives at reception with a meeting scheduled at 11:00. He walks in, glances around, sees the promo monitor.

**Rising action.** The camera detects his face. The recognition worker computes an embedding. It compares against every entry in `people.json`. Closest match scores 0.62 — above the tolerance threshold of 0.5. No match.

**Climax.** **Nothing happens.** The video continues. No flicker, no "Unknown person detected" message, no acknowledgement. The system has, correctly, decided that Marco is not someone it knows, and so it has nothing to say.

**Resolution.** Marco approaches the receptionist, signs in normally. The system has held its tongue — which is the entire reason it can be trusted to greet Aziza correctly. (False positives would destroy the magic; *both* journeys are part of the product.)

**Capabilities revealed:** tolerance-tuned matching (0.5 threshold); explicit no-op on unknown faces; no false-positive UI states.

### Journey 3 — Aziza walks past a second time within a minute (cooldown / anti-spam path)

**Opening scene.** Twenty seconds after Journey 1, Aziza realizes she left her badge on her desk. She turns around and walks back past the entrance.

**Rising action.** Camera sees her again. Recognition worker matches her embedding again. The greeting queue is about to fire — but the per-person cooldown table says "Aziza was greeted 0:00:24 ago. Suppress."

**Climax.** **Nothing happens** — for a *different* reason than Marco's. The system knows her, but is exercising restraint. The screen just keeps playing the promo.

**Resolution.** Aziza retrieves her badge, walks out again at minute 1:35 — past the 60-second cooldown — and the greeting fires once more. Restraint, then warmth. Both are intentional.

**Capabilities revealed:** per-person greeting cooldown (60 s default, configurable); state retention across recognition events; demonstrably "this isn't a goldfish."

### Journey 4 — Dilnoza, office manager, adding a new hire via Telegram

**Persona.** Dilnoza, 35, runs the front office. She is fluent in WhatsApp and Telegram. She has never opened a terminal in her life and never will. The previous kiosk system required her to email IT a photo and wait two days; she stopped doing it after the third hire.

**Opening scene.** Tuesday morning, 09:12. A new developer named Bekzod has just been onboarded. Dilnoza takes a clean front-facing photo of him on her phone.

**Rising action.** She opens Telegram, finds the office's "Welcome Bot" chat, and types `/add_person`. The bot replies: *"Send me a name, then a photo."* She types `Bekzod Yusupov`. Then she sends the photo. Total elapsed time from opening Telegram: 22 seconds.

**Climax.** The bot replies: *"✅ Bekzod Yusupov added. He'll be greeted starting now."* Behind the scenes, the bot has computed his face embedding, written it to `people.json`, and the recognition worker (watching the file) has reloaded the DB within 5 seconds.

**Resolution.** Bekzod walks past the entrance display 40 minutes later for his first coffee run. **"Welcome, Bekzod!"** fades in. He immediately Slacks Dilnoza: *"How did the screen know me??"* That moment — the new hire being recognized on day one without IT involvement — is the office-manager win.

**Capabilities revealed:** Telegram bot command parsing; image upload + embedding extraction; safe write to local DB; file-watcher hot reload in worker; admin-allowlist on Telegram chat IDs.

### Journey 4b — Dilnoza pushes a new promo video from her phone (admin remote-control path)

**Opening scene.** Friday afternoon, 16:40. Marketing has finished a new 25-second product clip and dropped it in the office Slack. Dilnoza wants it live on the lobby display before the weekend.

**Rising action.** She doesn't email IT. She doesn't open a laptop. She opens the same Telegram bot she uses for adding people, and types `/add_video`. The bot replies: *"Send me the video file."* She forwards the clip from Slack. The bot acknowledges receipt, downloads the file (under 20 MB, well within Telegram's bot-API limit), saves it into the `videos/` folder, and replies: *"✅ Added marketing-q2.mp4. Playlist now has 4 videos."*

**Climax.** The video player, halfway through its current loop iteration, finishes the current promo, rescans the `videos/` folder, picks up the new file, and includes it in the next loop. Within one playlist iteration (typically 30–60 s), the new clip appears on the lobby monitor. **No restart, no maintenance window, no IT ticket.**

**Resolution.** Dilnoza walks past the lobby on her way out at 17:05, sees the new clip playing, takes a photo of it for the marketing team, and goes home. The kiosk has become a single chat-managed surface — the strategic Telegram-bot-as-admin thesis from the Executive Summary, demonstrated end-to-end.

**Capabilities revealed:** Telegram bot file-upload handling; bot-side file-size check + helpful error message for >20 MB uploads; atomic write into `videos/` folder (write to `videos/.tmp/`, then `os.replace()` to final path); player rescan of `videos/` at end-of-video; `/list_videos` and `/delete_video` for full playlist control; CLI fallback `add_video.py` for files exceeding the 20 MB bot-API limit.

### Journey 5 — Sanji (developer/operator), recovering when the Wi-Fi dies at the venue (operational path)

**Opening scene.** Buildathon morning, 9:50. Demo at 10:00. Sanji is on stage doing pre-flight checks. He needs to add one more demo person — a judge who'll volunteer to be recognized live. He opens Telegram on his phone. The connection bar is gray.

**Rising action.** Venue Wi-Fi is down. The Telegram bot can't reach Telegram's servers. The judge is walking up. Five minutes to demo.

**Climax.** Sanji opens a terminal on the demo laptop and runs `python add_person.py "Judge Karimov" judge.jpg`. The script computes the embedding, writes it to `people.json`, and the file-watcher in the recognition worker picks it up within seconds. **No restart. No Telegram.**

**Resolution.** Demo starts on time. Sanji's volunteer is recognized successfully on the first walk-past. Wi-Fi being down — which would have killed the demo for any team that depended on it — is a sentence in the architecture talk afterward, not a disaster.

**Capabilities revealed:** CLI fallback (`add_person.py`) with identical write semantics to the bot; DB hot-reload triggered by *any* writer, not just the bot; system that survives partial-network conditions.

### Journey Requirements Summary

| Capability area | Required by journeys | Surface |
|---|---|---|
| Live face detection from USB camera at ≤320×240 downsampled | 1, 2, 3 | Recognition worker |
| 128-dim embedding extraction + tolerance-thresholded match (~0.5) | 1, 2, 3, 4 | Recognition worker |
| Per-person cooldown table (default 60 s, in-memory) | 1, 3 | Recognition worker → greeting queue |
| Greeting overlay: fade-in/out, 4–6 s, never blocks video | 1, 3, 4 | Player |
| "Largest face wins" selection when multiple known faces present | 1 (extension), 3 (corner case) | Recognition worker |
| Telegram bot people commands: `/add_person`, `/list_people`, `/delete_person` with admin allowlist | 4 | Bot process |
| Telegram bot video commands: `/add_video`, `/list_videos`, `/delete_video` with file-size check | 4b | Bot process |
| CLI fallback `add_person.py` with same write contract as bot | 5 | Standalone script |
| CLI fallback `add_video.py` for >20 MB files and offline ops | 4b, 5 | Standalone script |
| `people.json` write atomicity (no half-written file) | 4, 5 | Bot + CLI shared writer |
| Atomic video file placement into `videos/` (write to `.tmp/`, then `os.replace()`) | 4b | Bot + CLI shared writer |
| File-watcher hot reload in worker, ≤5 s propagation | 4, 5 | Recognition worker |
| Player rescan of `videos/` at end of each video | 4b | Player |
| Cold-boot supervisor (`run.py`) that spawns + monitors all 3 processes | 5 (and every demo) | Supervisor |
| Pre-flight check / self-test (`benchmark.py`) | 5 | Standalone script |

## Domain-Specific Requirements

### Privacy & Data Handling

Although the buildathon scope doesn't trigger formal regulatory compliance (no production deployment, no multi-tenant data, no cross-border transfer), the system processes facial biometric data, which warrants a defensible posture even in a demo:

- **All data stays on the demo machine.** No cloud APIs, no telemetry, no remote sync. Recognition runs locally via dlib; the only network egress is the Telegram bot calling Telegram's API.
- **Embeddings, not raw images, are the canonical store.** `people.json` holds 128-dimension vectors keyed by name; source photos in `faces/` are kept only for re-embedding if the model changes, and can be deleted without losing recognition capability.
- **Enrolment is opt-in and admin-mediated.** A face only enters the database when an admin (Telegram allowlist) actively runs `/add_person` or the CLI fallback. There is no passive enrolment from camera footage.
- **Deletion is one command.** `/delete_person <name>` (or removing the line from `people.json`) drops the person's embedding and all greeting-cooldown state. No soft-delete, no archive.
- **No retention of camera frames.** The recognition worker reads frames into memory, processes them, and discards them. No frame is ever written to disk during normal operation.

For a productionisation path beyond the buildathon, the natural additions would be: explicit consent capture at enrolment time, encryption-at-rest for `people.json`, an audit log of admin actions, and per-person right-to-be-forgotten verification. These are noted here for completeness; none are in MVP scope.

## Desktop Application — Specific Requirements

### Project-Type Overview

A Python 3.11+ desktop application running fullscreen on a single Windows laptop. Three coordinated processes — video player, recognition worker, Telegram bot — supervised by a top-level `run.py` that spawns and restarts children. Hardware footprint: laptop + USB webcam + monitor (HDMI or built-in display). No installer, no auto-update, no system service. The whole system is "git checkout, install, run."

### Platform Support

| Aspect | Decision |
|---|---|
| **Target OS** | Windows 10 / 11 only. Demo machine is Windows; no cross-platform build burden in scope. |
| **Python version** | 3.11+. Required for current `face_recognition`, `python-telegram-bot` v21+, and reliable `multiprocessing` semantics. |
| **CPU target** | Single demo laptop, no GPU dependency. Recognition pipeline downsamples to 320×240 to stay CPU-fine on a typical laptop. |
| **Display** | One fullscreen monitor. Resolution detected at runtime; overlay text scales to display height (e.g., font size = 8% of display height). |
| **dlib install path** | **Resolved within the first 30 minutes of the build budget.** Use prebuilt wheel (`pip install dlib-bin` or `cmake-built dlib` from a known-good wheel) rather than source compilation. This is the dominant platform risk; named explicitly so it's not deferred. |
| **Fallback dev OS** | None. All work happens on Windows. |

### System Integration

| Surface | Integration |
|---|---|
| **USB camera** | `cv2.VideoCapture(<device_index>)`. Default `0`; configurable via `config.yaml` because device indices shift on Windows when peripherals are plugged/unplugged. Bring own camera to the venue; verify on demo machine 15 min before going on stage. |
| **Display** | PyQt6 `QMainWindow` in `showFullScreen()` mode. `QMediaPlayer` + `QVideoWidget` for video; `QLabel` with `QGraphicsOpacityEffect` (animated via `QPropertyAnimation`) for the greeting overlay. Overlay sits in a stacked layout above the video widget — never modifies the video frame. |
| **Filesystem** | Single project root. `videos/` for promo loop, `faces/` for source photos, `people.json` for embeddings, `events.log` (bonus tier) for greeting history. All paths relative to repo root. |
| **Network** | Outbound HTTPS to Telegram's API only. Inbound: none. No ports opened. |
| **System services / startup** | None. Operator launches `python run.py` manually. No Windows service registration, no startup-folder shortcut, no background auto-launch. |
| **Logging** | Per-process stdout/stderr captured to `logs/<process>.log` by the supervisor, with a rolling tail printed to console. Useful both for buildathon judging ("is the system actually working?") and for venue-debug. |

### Update Strategy

| Aspect | Decision |
|---|---|
| **Update mechanism** | None. Manual `git pull && pip install -r requirements.txt` on the demo machine. |
| **Versioning** | Pin all dependencies in `requirements.txt` with exact versions (`==`). Hackathon code; reproducibility > flexibility. |
| **Database migration** | `people.json` schema is intentionally flat and forward-compatible. New optional fields (e.g., `lang_pref`, `birthday`) added in growth-tier features must default to `None` so existing records keep working without migration. |
| **Rollback** | `git checkout <last-good-sha>`. No state migration story needed at this scope. |

### Offline Capabilities

| Component | Offline behaviour |
|---|---|
| **Video player** | 100% offline. Plays from local `videos/` folder. |
| **Recognition worker** | 100% offline. dlib models bundled at install time; no network calls during inference. |
| **Telegram bot** | **Requires internet.** Fails gracefully — bot process exits with a logged error if it can't reach Telegram; supervisor logs and continues running player + worker. |
| **CLI fallback** | 100% offline. `add_person.py <name> <image>` does the same write to `people.json` as the bot would. This is the **explicit offline path** for venue-Wi-Fi-failure scenarios (see Journey 5). |
| **Hot-reload** | 100% offline. `watchdog` on `people.json`; no network involved. |

### Secondary Surfaces

#### CLI tool — `add_person.py`

- Single-purpose: `python add_person.py <name> <path/to/image.jpg>`
- Computes embedding, atomically writes to `people.json`, exits.
- Identical write semantics to the bot (same shared writer module). No drift between code paths.
- No flags beyond `--help`; no interactive prompts; no config required.

#### Telegram bot

- Built on `python-telegram-bot` v21+, runs as its own OS process.
- People commands: `/add_person` (name → photo two-step prompt), `/list_people`, `/delete_person`.
- Video commands: `/add_video` (prompt → video file upload), `/list_videos`, `/delete_video`. On `/add_video`, the bot checks file size against the **20 MB Telegram bot-API download limit** and replies with a clear "use the CLI fallback" message if the file exceeds it.
- **Admin allowlist** by Telegram chat ID, hardcoded in `config.yaml`. Non-allowlisted chat IDs receive "Unauthorized" reply and the event is logged. The same allowlist gates *all* commands (people and video).
- Bot crash is non-fatal: supervisor restarts it; player + worker keep running.
- Bot token stored in `config.yaml` (gitignored) or `.env` — never committed.

#### CLI tool — `add_video.py`

- Single-purpose: `python add_video.py <path/to/video.mp4>`
- Atomically copies the file into `videos/` (write to `videos/.tmp/<file>`, then `os.replace()` to final path), exits.
- Identical write semantics to the bot's video handler (same shared writer module).
- The mandatory path for videos exceeding the 20 MB Telegram bot-API limit. Also the offline path when venue Wi-Fi is unavailable.

### Implementation Considerations

- **Process model:** `multiprocessing.Process` for the recognition worker; subprocess for the bot; main process is the player. `multiprocessing.Queue` for greeting events (worker → player). `watchdog.Observer` in the worker watches `people.json` for changes.
- **GIL avoidance:** Recognition runs in its own process, not a thread, so dlib's CPU work doesn't compete with Qt's event loop for the GIL. This is the architectural reason the player stays smooth.
- **Frame strategy:** Worker pulls frames from camera at native rate, downsamples to 320×240 for detection, embeds at native crop. **Skip frames if behind — never queue them.** Old frames are useless.
- **Greeting cooldown:** In-memory `dict[name, last_greeted_at]` in the worker. Cleared on worker restart (acceptable; cooldown is a UX nicety, not a correctness requirement).
- **Atomic file writes:** `people.json` writes go to `people.json.tmp` then `os.replace()` — never partial writes that could be observed mid-update by the watcher.
- **Config:** Single `config.yaml` with telegram token, admin chat IDs, camera device index, recognition tolerance, cooldown seconds, video folder, font size factor. Loaded once at startup; no hot-reload of config in MVP scope.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** *Demo-grade reliability MVP* — neither the canonical "problem-solving MVP" nor "experience MVP." The product solves a problem that already has many crude solutions; the goal of the MVP is not to validate market fit but to **demonstrate, on stage, that an architectural opinion holds together under live conditions.** Specifically: that a parallel-process Python system can deliver invisible-recognition + visible-greeting on a single Windows laptop, with **chat-bot remote-control administration** (people *and* content), in a way that survives 60+ minutes of unattended runtime.

**Doctrinal consequence:** every hour saved in scope is reinvested in **stability, latency, and polish** — never in new features. If MVP block 3 (integration) finishes early, hour 13 is spent shaving 200 ms off greeting latency, not adding `/register`. This rule is what protects the personal pass/fail bar from feature-creep death spirals.

**MVP test** — four questions, all of which must answer "yes" before submission:
1. Does a registered face produce a correct greeting within 2 seconds, on the first try, after a cold boot?
2. Does the system run for 60 unattended minutes without crashing, leaking, or stuttering?
3. Can a non-technical person add a new face via Telegram in under 30 seconds?
4. Can a non-technical person push a new promo video via Telegram and see it appear in the loop within one playlist iteration?

If any answer is "no" at hour 20, the cutoff rules apply (see below).

**Resource Requirements:**
- **Team size:** 1 (solo).
- **Time budget:** 24 hours, fixed.
- **Skill profile required:** Python (intermediate), PyQt or equivalent (basic), `multiprocessing` familiarity (basic), Telegram Bot API including file-upload handling (basic). No ML expertise required.

### Phased Scope (Cross-Reference)

The MVP, Growth, and Vision feature lists live in the **Product Scope** section above and are not duplicated here. This section adds the *strategy* and *risks* around those tiers, not the tier contents.

**Core User Journeys Supported by MVP:** Journeys 1, 2, 3, 4, 4b, and 5 are all in MVP scope.

**Realistic post-MVP yield:** with video management consuming ~1.5–3 h of the original 2–3 h bonus budget, expect to ship **0–1 of the bonus items** rather than 2–3. The bonus tier is a priority-ranked list of options, not commitments. Priority order: (1) `/register` self-registration with admin approval — strategically the highest-value bonus because it directly demonstrates the chat-bot-as-admin thesis; (2) time-of-day greeting variants; (3) visitor event log; (4) per-person language preference; (5) per-person personalized message field.

### Forward-Compatibility Constraints

The MVP architecture must not foreclose Phase 3. Two architectural commitments enforce this:

- **Resource-management pattern is uniform.** The bot already manages two resource types (people + videos) via a shared admin allowlist + atomic-write pattern. Adding a third (per-person greeting messages, per-time-of-day playlists) is incremental, not a rewrite.
- **Player rescan-on-loop-end is the seed pattern for recognition-driven content.** The rescan can later become "rescan according to *who is currently in front of the camera*" without changing the player's core architecture.

### Risk Mitigation Strategy

**Technical Risks**

| Risk | Phase | Mitigation | Trigger if mitigation fails |
|---|---|---|---|
| dlib install pain on Windows | Pre-build (hour 0–0.5) | Use prebuilt wheel (`dlib-bin`) verified to install cleanly before any other coding starts | Drop dlib for `mediapipe` face detection — slower to embed, but installs cleanly |
| Video stutter when overlay fades | Mid-build (block 1–3) | Overlay is isolated Qt widget on top of `QVideoWidget`; never touches video pipeline. Test on real video at hour 4 | Replace fade animation with hard cut (still acceptable, less polish) |
| Recognition false positives | Mid-build (block 2) | Lower tolerance from 0.6 → 0.5; verify with seed set under demo lighting | Lower further to 0.45 |
| Greeting latency >2s | Mid-build (block 3) | Downsample frames to 320×240 for detection; skip frames if behind | Display latency in benchmark output and own it in the README |
| Video file write race (player tries to read mid-upload) | Mid-build (block 4) | Bot writes to `videos/.tmp/<file>` then `os.replace()` to final path — player only ever sees finished files | Player's rescan ignores `.tmp/` directory entirely as a defensive backstop |
| Telegram >20 MB upload rejected by user | Pre-demo | Bot replies with explicit "use `add_video.py` for files > 20 MB" message; documented in README | Demo videos sized <20 MB at recording time; this is a real constraint, not a workaround |
| Camera device-index surprise on demo machine | Demo-day (T-15 min) | Bring own camera; `config.yaml` makes index swap a one-line change | Manual verification step in pre-flight checklist |

**Operational / Demo Risks**

| Risk | Phase | Mitigation | Trigger if mitigation fails |
|---|---|---|---|
| Venue Wi-Fi down → Telegram bot dead | Demo-day | CLI fallbacks (`add_person.py`, `add_video.py`) are **MVP, not bonus**. Demo flow can be done end-to-end without Telegram | Operator pre-loads all demo people + videos via CLI before going on stage; bot becomes optional flair |
| Laptop reboots during prep | Demo-day | Manual `python run.py` is fast (<30 s cold start) | Operator stays at laptop until demo starts |
| Demo machine performance worse than dev | Mid-build (block 5) | Stability shakedown block runs on the **actual demo machine**, not dev hardware | Drop video resolution; reduce overlay font size if needed |

**Resource Risks (Time)**

- **Hour 14 cutoff:** if integration (block 3) isn't done → drop the Telegram bot entirely from MVP, ship CLI-only admin (both `add_person.py` and `add_video.py` still ship), document the choice in README.
- **Hour 17 cutoff:** if video-management bot commands aren't working → drop them from MVP, keep CLI fallback only, update demo script to demo file-system-add of a video instead of bot-add. The four-question MVP test downgrades to three.
- **Hour 20 cutoff:** if no clean 30+-min run achieved → freeze all features, debug-only mode until demo recording.
- **Hour 22 cutoff:** demo video gets recorded *no later than this point*, even with known minor bugs.

**Market / Acceptance Risks** (hackathon-equivalent)

| Risk | Mitigation |
|---|---|
| Judges miss the architectural cleverness (parallel processes, chat-bot-as-admin) | README + 3-minute architecture walkthrough cover both explicitly. Selection-strategy and threading-model paragraphs are non-optional in the README. |
| Judges don't perceive the polish (overlay restraint, "screen never pauses") | Demo script intentionally pauses on the moment the greeting fades over the still-playing video — the visual proof of the bet. |
| Judges expect a flashier UI than the deliberately restrained one | Frame the restraint as the choice in the demo opening line: "*The screen never stops the video. Watch.*" Make the restraint visible. |

## Functional Requirements

### Recognition

- **FR1**: System can detect human faces appearing in the camera's field of view in real time.
- **FR2**: System can compute a stable mathematical representation (embedding) of each detected face.
- **FR3**: System can compare a detected face's representation against the stored set of registered people and decide whether it matches a registered person, within a configurable similarity threshold.
- **FR4**: When two or more registered people are visible simultaneously, system can select the one closest to the camera as the greeting target.
- **FR5**: System takes no visible action when a detected face does not match any registered person — no greeting, no acknowledgement, no UI flash.

### Greeting Display

- **FR6**: System can display a personalized text greeting addressed to a recognized person, overlaid on the currently playing promo video.
- **FR7**: System can render the greeting with a fade-in/out animation for a configurable display duration of 3–10 seconds (default 5 s), without pausing or interrupting the underlying video.
- **FR8**: System can suppress repeat greetings for the same person within a configurable cooldown window.
- **FR9**: Operator can configure the greeting display duration and cooldown window via configuration.

### Promo Video Playback

- **FR10**: System can play promo videos from a designated local folder in fullscreen, looping continuously while the application is running.
- **FR11**: System can detect newly added or removed promo videos at the end of each video iteration and adjust the playlist accordingly, without restart.
- **FR12**: System can continue uninterrupted playback while administrative actions (face DB updates, playlist updates) occur in the background.

### People Management

- **FR13**: Admin can add a new registered person by providing a name and a face photo via the Telegram bot.
- **FR14**: Admin can add a new registered person via a command-line script (`add_person.py`), providing the same name + photo input as the bot.
- **FR15**: Admin can list all currently registered people via the Telegram bot.
- **FR16**: Admin can remove a registered person by name via the Telegram bot.
- **FR17**: System can persist registered people's data (name + face representation) to local storage, surviving restarts.
- **FR18**: System can begin recognizing a newly added person within 5 seconds of their addition, without requiring a restart.
- **FR19**: System can stop recognizing (and immediately stop greeting) a removed person within 5 seconds of their removal.

### Video Management

- **FR20**: Admin can upload a new promo video via the Telegram bot, subject to the bot platform's file-size limit.
- **FR21**: Admin can add a new promo video of any size via a command-line script (`add_video.py`).
- **FR22**: Admin can list all current promo videos in the playlist via the Telegram bot.
- **FR23**: Admin can remove a promo video from the playlist by name via the Telegram bot.
- **FR24**: System guarantees that a video file added through any path (bot or CLI) is fully written before the player makes it available for playback.
- **FR25**: System communicates file-size constraints clearly to admins when an upload is rejected, including the alternative path (CLI) for files that exceed the bot limit.

### Admin Access Control

- **FR26**: System restricts administrative actions (people management and video management) to a defined allowlist of Telegram chat IDs.
- **FR27**: System rejects and logs unauthorized administrative requests, and replies to the requester with a clear "unauthorized" message.

### System Operations

- **FR28**: Operator can start the entire system with a single command.
- **FR29**: System runs its three coordinated components (player, recognition, admin bot) concurrently from a single entry point.
- **FR30**: System detects when the recognition worker, the Telegram bot, or the supervisor itself has crashed, and restarts the failed component within 5 seconds, without disrupting components that remain running.
- **FR31**: System fails gracefully when an external dependency (e.g., Telegram connectivity) is unavailable — the player and recognition continue to function; only the affected component is degraded.
- **FR32**: System captures per-component logs to local files for post-hoc inspection.

### Self-Test & Verification

- **FR33**: Operator can run a self-test that measures recognition accuracy (true-positive and false-positive rates) against a defined seed set of registered people.
- **FR34**: Operator can run a self-test that measures end-to-end latency from face detection to greeting display, reporting both p50 and p95.
- **FR35**: Self-test results are printed in a form suitable for inclusion in project documentation (README).

## Non-Functional Requirements

### Performance

- **NFR1**: End-to-end recognition latency (face entering camera frame → greeting overlay visible on screen) shall be **p50 ≤ 1.0 s and p95 ≤ 2.0 s** under demo conditions, measured by `benchmark.py` against the 5-person seed set with 10 walk-past attempts each.
- **NFR2**: Greeting overlay fade-in/out animation shall complete within **300–500 ms** at each end, with no measurable dropped frames in the underlying video during the fade.
- **NFR3**: Cold-boot time from `python run.py` to "all three components ready (player rendering, recognition pulling frames, bot connected to Telegram)" shall be **< 30 s** on the demo machine.
- **NFR4**: DB hot-reload propagation time, from a write to `people.json` to the recognition worker using the new data, shall be **≤ 5 s**.
- **NFR5**: Newly added videos shall be picked up by the player within **one playlist iteration** (≤ 60 s for typical promo lengths) without restart.
- **NFR6**: End-to-end Telegram `/add_person` round-trip — from a non-technical user starting the command to receiving the bot's confirmation — shall be **< 30 s**.

### Reliability

- **NFR7**: System shall run **≥ 60 minutes** of continuous unattended operation with zero crashes, zero unrecoverable error states, and no video-playback degradation.
- **NFR8**: System shall maintain memory footprint growth **≤ 100 MB** over a 60-minute run.
- **NFR9**: System shall exhibit **zero recognition false positives** against a baseline 5-stranger seed set during a 60-minute run, at the configured similarity tolerance.
- **NFR10**: System shall maintain **≥ 95% recognition true-positive rate** for the registered 5-person seed set under demo lighting conditions.
- **NFR11**: Component crash recovery shall be **automatic and transparent to the visitor** — no on-screen artifact, no greeting interruption, no video stutter when a non-player component restarts.
- **NFR12**: System shall continue full visitor-facing operation (player + recognition + greeting) when network connectivity is unavailable. Only administrative bot operations are degraded under network loss.

### Security & Privacy

- **NFR13**: All facial biometric data (embeddings) shall remain on the demo machine. The system shall make **no outbound network calls** other than to Telegram's API on behalf of the admin bot.
- **NFR14**: Camera frames shall **not be persisted** to disk during normal operation. Frames are processed in memory and discarded.
- **NFR15**: Source face photos uploaded via the bot or CLI shall be stored locally in `faces/` solely to enable re-embedding; deletion of a person via `/delete_person` shall remove both their embedding and any associated source photo.
- **NFR16**: The Telegram bot token and admin chat-ID allowlist shall not be committed to version control. The repository's `.gitignore` shall enforce this for `config.yaml` and `.env`.
- **NFR17**: All write operations to `people.json` shall be **atomic** (write-to-tmp + `os.replace()`), preventing any reader from observing a partially written file.
- **NFR18**: All write operations adding video files to `videos/` shall be **atomic** (write to `videos/.tmp/` + `os.replace()` to final path), preventing the player from picking up a partially written video.

### Resource & Capacity

- **NFR19**: System shall operate on a single Windows 10/11 laptop with **no GPU dependency** — recognition must run on CPU at the latency targets above.
- **NFR20**: System shall support a registered-people set of **up to 200 entries** without recognition latency exceeding NFR1 targets.
- **NFR21**: System shall support a video playlist of **up to 50 entries** without playback issues.
- **NFR22**: Telegram bot uploads of video files shall enforce the **20 MB Telegram bot-API limit** and reject larger files with a clear message pointing to the CLI fallback.

### Usability

- **NFR23**: A non-technical admin (no terminal, no documentation in hand) shall be able to add a new person via Telegram in **< 30 seconds** — measured from opening the bot chat to receiving the confirmation reply.
- **NFR24**: A non-technical admin shall be able to add a new promo video via Telegram in **< 60 seconds** — measured from opening the bot chat to seeing the playlist confirmation reply.
- **NFR25**: Greeting text shall be rendered at a font size **≥ 8% of display height**, sufficient to be readable from the typical office-entrance viewing distance (2–3 m).
- **NFR26**: All bot replies (success, failure, unauthorized) shall be **single-message, plain-language** — no command-syntax dumps, no markdown chrome that confuses non-technical users.
- **NFR27**: Bot file-size rejection (NFR22) shall include the alternative path in plain language: e.g., *"This video is over 20 MB. Please upload it via the `add_video.py` script on the laptop."*

### Observability & Diagnosability

- **NFR28**: Each runtime component (player, recognition worker, Telegram bot, supervisor) shall write its stdout/stderr to a per-component log file under `logs/<component>.log`, retained for the duration of the run.
- **NFR29**: The supervisor shall print a rolling tail of all component logs to the console on demand, sufficient to identify which component crashed or degraded during a demo.
- **NFR30**: The `benchmark.py` self-test shall produce machine-readable output (latency p50/p95, accuracy true-positive/false-positive rates) suitable for direct inclusion in the README.
- **NFR31**: Unauthorized bot access attempts (FR27) shall be logged with **timestamp + chat ID + attempted command**, retained in `logs/bot.log`.
