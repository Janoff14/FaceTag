# Story 3.3: Implement /add_person via Telegram bot

Status: done

## Story

As Dilnoza,
I want to add a new registered person from my phone by sending name + photo to the bot,
so that I never have to email IT or open a terminal.

## Acceptance Criteria

1. **Given** I am an allowlisted admin, **when** I send `/add_person`, **then** the bot replies `Send me a name, then a photo`. _[NFR26]_
2. **And** when I reply with a name, the bot stores it as pending state for my chat.
3. **And** when I subsequently send a photo, the bot downloads it, invokes the shared writer module from Story 2.2, and replies `<name> added`. _[AR9, NFR17]_
4. **And** if I send a photo with no detectable face, the bot replies `No face detected in that photo. Please try a clearer front-facing photo.` and clears my pending state.
5. **And** the flow remains allowlisted; unauthorized users receive `Unauthorized` before any add-person behavior leaks.

## Tasks / Subtasks

- [x] **Task 1 - Add bot conversation tests** - Cover `/add_person`, name capture, photo success, no-face failure, and unauthorized gating.
- [x] **Task 2 - Implement pending add-person state** - Store per-chat pending names in `context.bot_data`.
- [x] **Task 3 - Implement photo download/write flow** - Download Telegram photo to a temp file, call `recognition.writer.add_person`, reply success or no-face message, and clear state.
- [x] **Task 4 - Register Telegram handlers** - Wire command, text, and photo handlers in the application.
- [x] **Task 5 - Regression verification** - Run full test suite.

## Dev Notes

- Use `recognition.writer.add_person`; do not duplicate face embedding or atomic-write code.
- Use `people_db_path` and `faces_folder` from config.
- Story 3.4 will add list/delete commands; avoid adding those here.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-16: Created story file from `epics.md` after Story 3.2 bot allowlist was working live.
- 2026-05-16: Added failing offline add-person conversation tests, then implemented pending state and photo handling.

### Completion Notes List

- Added `/add_person` command guarded by the existing admin allowlist.
- Added per-chat pending state in `context.bot_data["pending_add_person"]`.
- Text replies during the pending flow store the person name and prompt for a photo.
- Photo replies download the largest Telegram photo variant to a temporary file, call shared `recognition.writer.add_person`, and reply `<name> added`.
- `NoFaceInImageError` replies `No face detected in that photo. Please try a clearer front-facing photo.` and clears pending state.
- Verified `.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`: 88/88 pass.
- Tightened live testing feedback after first manual attempt: bot now logs `ADD_PERSON_*` progress lines, replies `Photo received. Processing...` before embedding, re-prompts if text is sent while waiting for a photo, and catches decode/generic writer failures with visible replies instead of going quiet.
- Verified tightened flow with `.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`: 90/90 pass.

### File List

- `bot.py` (modified - `/add_person` conversation flow)
- `tests/test_bot.py` (modified - add-person flow tests)
- `_bmad-output/implementation-artifacts/3-3-implement-add-person-via-telegram-bot.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 3.3 created and started.
- 2026-05-16: Story 3.3 implemented and verified; status set to done.
