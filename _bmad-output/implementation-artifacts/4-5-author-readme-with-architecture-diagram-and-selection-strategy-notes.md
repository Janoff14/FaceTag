# Story 4.5: Author README with architecture diagram and selection-strategy notes

Status: review

## Story

As the buildathon judges (and any future operator),
I want a clear README explaining setup, architecture, threading model, selection strategy, and the latest accuracy/latency numbers,
so that the project is comprehensible and reproducible from a fresh checkout. _[AR13, FR35]_

## Acceptance Criteria

1. **Given** the project is feature-complete (Stories 4.1–4.4 done) and `benchmark.py` has produced fresh output, **when** I write `README.md`, **then** it contains these sections in order: Setup, Architecture, Selection strategy, Threading model, Benchmark results, CLI fallback.
2. Setup covers Python 3.11+, `pip install dlib-bin face_recognition opencv-python`, `pip install -r requirements.txt`, `Copy-Item config.yaml.example config.yaml`, filling `telegram_token` + `admin_chat_ids`, and `python run.py`.
3. Architecture includes an ASCII diagram showing the 3 processes (player / worker / bot), IPC queue (worker → player), file-watcher on `people.json` (worker), shared atomic writer module (bot + CLI), and playlist rescan at end-of-video (player).
4. Selection strategy explains "largest face wins" (FR4) and why this heuristic was chosen.
5. Threading model explains why recognition runs in its own OS process (GIL avoidance for dlib CPU, isolation from Qt event loop).
6. Benchmark results include verbatim `benchmark.py` output with a timestamp.
7. CLI fallback section has brief usage for `add_person.py` and `add_video.py`, plus the explicit note that they exist for both > 20 MB videos and offline operation.
8. README is written for a non-technical-but-curious reader (judge with engineering background, no project familiarity).
9. All paths and commands shown work on a fresh clone.

## Tasks / Subtasks

- [ ] **Task 1 — Rewrite `README.md`** with all sections per AC.
- [ ] **Task 2 — Verify commands work on a fresh checkout context** — read through each step mentally; spot-check any path that's changed during Epic 2/3/4.
- [ ] **Task 3 — Leave a TODO marker for benchmark verbatim output** so the operator can paste the actual numbers post-shakedown (Story 4.4) without re-editing the rest of the README.

## Dev Notes

The README is the judge's first impression. Optimize for "I can follow this without asking a question." Brevity beats completeness — link to story files for the deep dive.

The Setup section assumes the smoke venv approach used during the build:
- `.\.venv-smoke-dlib-corrected\Scripts\python.exe` is the local dev venv name, but the README should use the canonical pattern (a venv called `.venv` is what a fresh clone gets).

Out of scope: tutorial-style screenshots; this is a buildathon submission, not a product page.

## Dev Agent Record

### Agent Model Used

_TBD_

### Debug Log References

- 2026-05-16: Story file created after Stories 4.1–4.3 shipped (CLI fallbacks + benchmark). Story 4.4 (shakedown) template ready but not yet run.

### Completion Notes List

_To be filled by dev agent._

### File List

_Expected:_

- `README.md` (rewritten)
- `_bmad-output/implementation-artifacts/4-5-author-readme-with-architecture-diagram-and-selection-strategy-notes.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 4.5 created from epics.md, status set to ready-for-dev.
