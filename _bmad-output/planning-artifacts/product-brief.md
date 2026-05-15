# Product Brief: Office Face-Greeting Display

**Author:** Sanji
**Audience:** Self (scope-lock + build plan for a 24-hour solo buildathon)
**Date:** 2026-05-15
**Build budget:** 24 hours, solo

---

## Executive Summary

A camera-and-monitor unit mounted at an office entrance. By default the screen loops promotional/brand videos in fullscreen. When the camera sees someone whose face is registered in a local database, a clean "Welcome, [Name]!" overlay fades in over the video for ~5 seconds and fades out — the video never pauses. Unknown faces are ignored.

The build is a solo hackathon project judged on recognition accuracy, overlay polish, response speed, and admin UX. To win the admin-UX category cheaply, the system replaces the conventional web admin panel with a **Telegram bot** as the management interface — admins (and optionally users themselves) add faces by sending a name + photo to the bot, which extracts the embedding and writes it to the local DB. This is faster to build than a web UI and demos better.

The core technical bet: two parallel processes — a video player and a face-recognition worker — sharing a small embedding database and a thread-safe "greeting queue" that the player polls. Built in Python with OpenCV + `face_recognition` for the recognition path and PyQt (or Pygame) for the player + overlay.

## The Problem

Office entrance monitors today do exactly one thing: loop promo videos. The screen sees every person who walks in but acknowledges no one. The hardware (camera + display + GPU) is already there; the personalization layer isn't. Hackathon judges want to see that gap closed with something that actually runs reliably for hours on a normal laptop, not a contrived demo.

Concrete pains being addressed:

- **For office staff:** No quick way to make the entrance feel personal to visitors or teammates without manually rotating content.
- **For visitors / employees:** No moment of recognition on arrival — the screen is impersonal wallpaper.
- **For whoever maintains it:** Adding a new person to such a system normally means SSH, file copies, or a clunky web admin — friction that kills adoption.

## The Solution

A single-machine app with three loosely-coupled parts running in parallel:

1. **Video player + overlay (main UI process):** Fullscreen, looping playlist from a local `videos/` folder. Greeting text rendered as a transparent overlay layer with CSS-style fade-in / fade-out animation. The player never blocks on the recognition pipeline.
2. **Recognition worker (separate process or thread):** Pulls frames from the USB camera, detects faces, computes embeddings, matches against the local DB, and pushes "greet name X" events to a shared queue. Per-person 60s cooldown to avoid spamming the same greeting.
3. **Telegram bot (separate process):** Database management interface. Admin uses `/add_person`, `/list_people`, `/delete_person`. Stretch: `/register` for self-registration with admin approval. The bot writes to the same local embedding store the recognition worker reads from; the worker hot-reloads when the file changes.

Storage is a flat `people.json` (or SQLite, but JSON is fine and trivially diffable) with precomputed embeddings, plus a `faces/` folder of source images for re-embedding if needed. Greeting log appended to a small `events.log`. Everything stays on the box — no cloud calls.

## Technical Approach

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Best face-recognition library ecosystem, fastest to ship in 24h |
| Face detection + embeddings | `face_recognition` (dlib) | Simpler API than DeepFace, single-vector embeddings, CPU-fine for one camera |
| Camera capture | OpenCV `VideoCapture` | Standard, works with any USB cam |
| Video player + overlay | **PyQt6** (QMediaPlayer + QLabel overlay with QGraphicsOpacityEffect for fade) | Hardware video decode, clean transparent overlays, animatable in pure Qt |
| Concurrency model | `multiprocessing` for recognition worker, `QThread` for the player's frame consumer | Player must not share GIL with the recognition loop — that's the whole point |
| IPC | `multiprocessing.Queue` for greeting events + `watchdog` on the DB file for hot reload | Simple, no broker, robust enough for a single machine |
| DB | `people.json` with `{name, embedding[128], image_path, language?, lang_pref?}` records | Diff-friendly, sufficient for tens-hundreds of people |
| Telegram bot | `python-telegram-bot` v21+, run as its own process | Independent lifecycle from the UI; bot can crash without taking down the display |
| Process supervision | `supervisor.py` or a top-level `run.py` that spawns + restarts children | Demo needs to "just keep running" |

**Selection strategy when multiple known faces appear:** **largest face in frame** (closest to camera) → documented in README, simple to defend in judging.

**Recognition pipeline tuning targets:** detect at 320×240 downsampled, embed at native crop, target ≤2s latency from face entering frame to overlay appearing. Skip frames if needed — don't queue them.

## Who This Serves

- **Primary user — the visitor/employee walking up to the door.** Wants a half-second of recognition. Doesn't interact, just sees their name.
- **Primary admin — office manager / receptionist.** Adds people through Telegram in <30 seconds without learning anything new. Doesn't open a terminal.
- **Secondary — judges.** Need to see the demo flow work cleanly: video plays, person walks up, name appears, fades out, video keeps going. Unknown person walks up, nothing happens.

## Success Criteria

Mapped to the buildathon's weighted judging criteria so scope choices follow the points:

| Criterion | Weight | What I need to nail |
|---|---:|---|
| Recognition accuracy | 20% | Tune `face_recognition` tolerance (default 0.6 → consider 0.5). Test under office lighting before demo. |
| Player + overlay quality | 20% | Smooth fade (300–500ms ease), large readable font, no video stutter when overlay shows. |
| Speed / response time | 15% | <2s from face → overlay. Measured and shown in demo. |
| DB + video UX | 15% | Telegram bot works end-to-end. `/add_person` takes <30s for a non-technical user. Videos = drop into `videos/`. |
| Parallel stream stability | 10% | Runs ≥30 min in demo prep without a crash or video lag. |
| Code quality + docs | 10% | Clean README with setup, architecture diagram (even ASCII), explanation of selection strategy + threading model. |
| Creativity / extras | 10% | Telegram bot as admin UI is the headline extra. Add time-of-day greeting if time permits. |

**Personal success bar:** all four MVP modules running on stage from a clean cold start, with a recognized face triggering a greeting in under 2 seconds on first try.

## Scope

### In scope (MVP — must ship)

- Fullscreen looping video playlist from a local folder
- Face detection + embedding match against local DB
- Greeting overlay with fade-in/out, 4–6s duration, 60s per-person cooldown
- "Largest face wins" selection when multiple known faces present
- Telegram bot commands: `/add_person`, `/list_people`, `/delete_person`
- DB hot-reload when bot writes a new face
- README with setup steps + architecture notes
- 1–3 minute demo video

### Bonus (only if MVP is rock-solid with ≥3h left)

- Time-of-day greeting variants (morning / afternoon / evening)
- `/register` self-registration with admin approval
- Per-person language preference (UZ / EN / RU)
- Visitor log (`events.log` with timestamp + name)
- Birthday / personalized message field per person

### Explicitly out

- Web admin panel (replaced by Telegram bot — document this as a deliberate choice)
- Auth on admin panel (Telegram chat ID allow-list is sufficient)
- Slack notifications
- Scheduled playlists by time of day
- Cloud sync or remote DB
- Multi-camera support

## Build Plan (24-hour time budget)

Rough ordering — adjust on the fly, but protect the integration block.

| Block | Hours | Output |
|---|---:|---|
| 0. Repo scaffold + venv + dependencies pinned | 0.5 | `git init`, `requirements.txt`, folder layout |
| 1. Video player + overlay (standalone) | 3 | PyQt window, playlist loop, fade-in/out test overlay |
| 2. Recognition worker (standalone, CLI prints matches) | 3 | Camera feed → detection → match against a seed `people.json` |
| 3. **Integration: queue + cooldown + greeting trigger** | 2.5 | Worker pushes events → player shows overlay |
| 4. Telegram bot: `/add_person`, `/list_people`, `/delete_person` | 3 | Bot writes to DB; worker hot-reloads |
| 5. End-to-end run + stability shakedown | 2 | 30+ min uninterrupted run; fix what breaks |
| 6. README + architecture doc + selection-strategy note | 1.5 | Submission-ready docs |
| 7. Demo recording (1–3 min) | 1 | Captures all four required demo scenes |
| 8. Bonus features (only if buffer remains) | 2–3 | Time-of-day greeting + visitor log are the cheapest wins |
| **Slack / debug buffer** | 1.5 | Everything always takes longer |

**Hard cutoff rules:**
- If hour 14 hits and integration (block 3) isn't done → drop the Telegram bot, ship CLI-based DB management, write README accordingly.
- If hour 20 hits without a clean 30-min run → freeze features, only debug.
- Demo video gets recorded **no later than hour 22**, even if minor bugs remain.

## Risks

- **Video stutter when overlay appears.** Mitigation: overlay is a separate Qt widget, never touches the video pipeline. Test early.
- **Recognition false positives at default tolerance.** Mitigation: lower threshold to ~0.5 and confirm with 2–3 test faces under demo lighting.
- **Telegram bot connectivity at venue.** Mitigation: have a fallback CLI script (`add_person.py <name> <image>`) so demo doesn't depend on Wi-Fi.
- **dlib install pain on Windows.** Mitigation: install + verify environment **in the first 30 minutes**, not at hour 6.
- **Camera permission / device-index surprises on the demo machine.** Mitigation: bring own camera, test on demo machine 15 min before going up.
