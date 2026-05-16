# Story 5.5: Telegram inline keyboard menus

Status: done

## Story

As Dilnoza,
I want to tap buttons in Telegram instead of typing commands,
so that I can manage the kiosk from my phone without remembering syntax.

## Acceptance Criteria

1. `/start` (admin only) replies with a "Main menu" message and an inline keyboard with three buttons: **People**, **Videos**, **Status**.
2. **People** opens a sub-menu with: Add person, List people, Delete person, Back.
3. **Videos** opens a sub-menu with: Add video, List videos, Delete video, Back.
4. **Status** replies in-place with a single-message summary: bot uptime, total greetings emitted since boot (best-effort, in-memory).
5. Tapping **Add person** or **Add video** continues to use the existing pending-state flow (prompt → text → photo/video).
6. Tapping **Delete person** lists the registered names as a row of buttons; tapping a name removes that person.
7. Tapping **Delete video** lists filenames as buttons; tapping one removes that video.
8. Existing typed commands (`/add_person`, `/list_people`, etc.) keep working — buttons are additive.
9. All callbacks are admin-only — non-allowlisted chats get `Unauthorized`.

## Tasks / Subtasks

- [ ] **Task 1** — Add inline keyboard builders in `bot.py`:
  - `_main_menu_markup()`, `_people_menu_markup()`, `_videos_menu_markup()`.
  - `_delete_people_markup(names)`, `_delete_videos_markup(filenames)` — dynamic per-row buttons.
- [ ] **Task 2** — Replace `start_command` with a version that sends the main menu inline keyboard.
- [ ] **Task 3** — `CallbackQueryHandler` for top-level + sub-menu navigation. Callback data uses a small prefixed protocol: `menu:main`, `menu:people`, `menu:videos`, `menu:status`, `action:add_person`, `action:list_people`, `action:add_video`, `action:list_videos`, `action:delete_person_pick`, `action:delete_video_pick`, `delete_person:<name>`, `delete_video:<filename>`.
- [ ] **Task 4** — Track a process-local `started_at` and `greetings_emitted` counter (will be incremented by Story 5.6 when notifications fire). For now, `greetings_emitted` is set on a bot-side `bot_data["greetings_count"]`.
- [ ] **Task 5** — Make the callback handler admin-only via the existing `admin_only` decorator pattern (adapted for `CallbackQuery`).
- [ ] **Task 6** — Tests in `tests/test_bot_menus.py`:
  - `/start` builds a 3-button main-menu markup with the expected callback data values.
  - Main-menu "People" callback edits the message to show the people sub-menu.
  - "Add person" callback sets pending state + replies prompt.
  - Delete pick callback for an existing name calls `remove_person` and confirms.
  - Unauthorized callback (non-admin chat) doesn't mutate state.
- [ ] **Task 7** — Regression — full suite green (was 212/212 after Story 5.4).

## Dev Notes

### python-telegram-bot 22.x API

`InlineKeyboardMarkup` + `InlineKeyboardButton` from `telegram`. Callback handler imported from `telegram.ext.CallbackQueryHandler`. The `Application` already exists in `build_application` — just add the handler.

Callback data has a 64-byte limit. Filenames could exceed that for unusual cases — for video delete pick, truncate the displayed text to fit the button but pass an index instead of the full filename if needed. For now, pass the filename directly; if it's >64 bytes, fall back to typed `/delete_video`.

### Status counter

Process-local — survives only until bot restart. That's fine; this is informational not audit. Keep it as `application.bot_data["greetings_count"] = 0` and increment when Story 5.6 sends a notification.

### Test seam

`bot._build_main_menu()` and friends should return `InlineKeyboardMarkup` instances; tests inspect `.inline_keyboard` (list-of-lists of buttons) for callback data. Use `_FakeUpdate` patterns from existing tests.

### Out of scope

Recognition notification push — Story 5.6.

## Dev Agent Record

### Agent Model Used

_TBD_

### File List

_Expected:_

- `bot.py` (modified — menu builders, callback handler, registration)
- `tests/test_bot_menus.py` (new)
- `_bmad-output/implementation-artifacts/5-5-telegram-inline-keyboard-menus.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 5.5 created, status set to ready-for-dev.
