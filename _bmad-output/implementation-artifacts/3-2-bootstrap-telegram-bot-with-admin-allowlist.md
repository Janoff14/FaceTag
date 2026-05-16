# Story 3.2: Bootstrap Telegram bot with admin allowlist

Status: done

## Story

As the operator,
I want the bot stub from Story 3.1 replaced by a real Telegram bot process that only responds to allowlisted chat IDs,
so that no random user can manipulate the kiosk.

## Acceptance Criteria

1. **Given** `config.yaml` contains `telegram_token: <token>` and `admin_chat_ids: [N1, N2, ...]`, **when** the supervisor starts the bot subprocess, **then** the real Telegram bot replaces the stub, connects to Telegram, and writes a ready log line without exposing the token. _[FR26, NFR16]_
2. **And** when the bot receives `/start` from an allowlisted chat ID, it replies `Welcome admin`. _[NFR26]_
3. **And** when `/start` or any command is received from a non-allowlisted chat ID, the bot replies `Unauthorized` and writes `[<timestamp>] UNAUTHORIZED chat_id=<id> command=<cmd>` to `logs/bot.log`. _[FR27, NFR31]_
4. **And** the allowlist check runs before command handlers, so no command leaks behavior to non-allowlisted users.
5. **And** the `telegram_token` value is never written to any log file.
6. **And** if Telegram is unreachable on bot startup, the supervisor logs the error to `logs/supervisor.log` and the bot subprocess exits or restarts according to supervisor policy; player and worker continue running normally. _[FR31, NFR12]_

## Tasks / Subtasks

- [x] **Task 1 - Add bot allowlist tests** - Cover admin `/start`, unauthorized `/start`, unauthorized unknown command, and token redaction.
- [x] **Task 2 - Replace bot stub** - Implement a real `python-telegram-bot` app with admin allowlist and safe startup logging.
- [x] **Task 3 - Update supervisor launch naming/tests** - Start the real bot process and keep restart/shutdown/log capture behavior intact.
- [x] **Task 4 - Regression verification** - Run full test suite.
- [x] **Task 5 - Connection smoke** - Use logs to confirm the bot process starts without leaking the token.

## Dev Notes

- Do not print `telegram_token` or include raw tracebacks that might contain request URLs.
- Story 3.3 adds `/add_person`; this story only implements `/start`, unauthorized handling, and command gating.
- `config.yaml` is gitignored and must remain local.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-16: Created story file from `epics.md` after user created local `config.yaml` and pasted Telegram settings.
- 2026-05-16: Added offline bot tests for allowlist behavior and token redaction.
- 2026-05-16: Installed `python-telegram-bot==22.7` into the active smoke venv because it was pinned in `requirements.txt` but not installed locally.
- 2026-05-16: Bot process smoke reached `BOT_READY`; token leak check returned false. Local `admin_chat_ids` is still empty, so all live commands are currently unauthorized until the operator adds a chat ID.

### Completion Notes List

- Replaced the Story 3.1 bot stub with a real `python-telegram-bot` application.
- Added `/start` for allowlisted admins, replying exactly `Welcome admin`.
- Added allowlist gating before command behavior; unauthorized `/start` or any other command replies `Unauthorized` and logs chat ID + command.
- Added safe startup error handling and `sanitize_secret(...)` so token-bearing messages are redacted before logging.
- Allowed an empty `admin_chat_ids` list to start safely with all commands unauthorized; this lets the operator send `/start` once and recover their chat ID from `logs/bot.log`.
- Renamed supervisor bot helpers to `start_bot_process` / `stop_bot_process` and kept restart/shutdown behavior covered by tests.
- Verified bot startup against local `config.yaml`: `BOT_READY`, `token_leaked=False`.
- Verified `.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`: 82/82 pass.

### File List

- `bot.py` (modified - real Telegram bot + allowlist)
- `supervisor.py` (modified - real bot process naming)
- `tests/test_bot.py` (new - allowlist/token-redaction tests)
- `tests/test_supervisor.py` (modified - real bot process lifecycle tests)
- `_bmad-output/implementation-artifacts/3-2-bootstrap-telegram-bot-with-admin-allowlist.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 3.2 created and started.
- 2026-05-16: Story 3.2 implemented and verified; status set to done.
