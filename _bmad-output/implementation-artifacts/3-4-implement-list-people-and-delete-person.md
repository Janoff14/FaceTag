# Story 3.4: Implement /list_people and /delete_person

Status: done

## Story

As Dilnoza,
I want to see who is currently registered and remove people who no longer work here,
so that I can manage the face DB from Telegram without learning anything new.

## Acceptance Criteria

1. **Given** I am an allowlisted admin, **when** I send `/list_people`, **then** the bot replies with a single message containing newline-separated names of all registered people. _[FR15, NFR26]_
2. **And** when `people.json` is empty (no registered people), the bot replies `No people registered yet. Use /add_person to add someone.`
3. **And** when I send `/delete_person <name>`, the shared writer module from Story 2.2 (`recognition.writer.remove_person`) removes the entry from `people.json` and deletes `faces/<safe>.jpg`, and the bot replies `<name> removed`. _[FR16, NFR15, NFR17, AR9]_
4. **And** when I send `/delete_person` with no argument, the bot replies `Usage: /delete_person <name>` and makes no changes.
5. **And** when I send `/delete_person <unknown>` for a name that is not in `people.json`, the bot replies `Person not found. Use /list_people to see who is registered.` and makes no changes.
6. **And** name matching is case-sensitive and exact — no fuzzy matching, so a typo cannot silently delete the wrong person.
7. **And** both commands are admin-only — non-allowlisted users receive `Unauthorized` (FR27) before any list or delete behavior runs, and the unauthorized attempt is logged per Story 3.2's pattern.

## Tasks / Subtasks

- [x] **Task 1 — Add failing tests for `/list_people`** in `tests/test_bot.py` (`ListPeopleFlowTests`, 3 tests).
- [x] **Task 2 — Add failing tests for `/delete_person`** in `tests/test_bot.py` (`DeletePersonFlowTests`, 6 tests including case-sensitivity guard).
- [x] **Task 3 — Implement `list_people_command`** in `bot.py` using `recognition.registry.load_registry`.
- [x] **Task 4 — Implement `delete_person_command`** in `bot.py` with case-sensitive pre-check (writer's internal compare is case-insensitive; the bot enforces the user-visible exact-match contract before calling `remove_person`).
- [x] **Task 5 — Register handlers in `build_application`** between `/add_person` and the photo handler, before the catch-all `unknown_command`.
- [x] **Task 6 — Regression** — full suite passes: 99/99 (`.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`).

## Dev Notes

### Architecture compliance

- **AR9 — single writer code path:** `/delete_person` MUST call `recognition.writer.remove_person`. Do not re-implement JSON load → filter → atomic write inside `bot.py`. Story 2.2 already gives atomic semantics (`os.replace`) plus the `faces/<safe>.jpg` cleanup (NFR15). The writer also strips entries via case-insensitive name comparison internally; this story keeps the *user-visible* contract case-sensitive by checking the registry first OR by relying on `remove_person`'s return value (it returns `False` if nothing was removed). The simpler path is to call `remove_person` and branch on its return — no pre-check, no race.
- **NFR26 — single-message, plain-language replies:** No markdown, no code fences, no command-syntax dumps. One `reply_text` per command outcome.
- **NFR31 — unauthorized access logged:** Already handled by `admin_only` + `unauthorized_response` from Story 3.2; do not duplicate.

### Reuse from previous stories

- `bot.admin_only` decorator (Story 3.2) — wrap both new handlers.
- `bot.log_bot_event` — use for `LIST_PEOPLE` and `DELETE_PERSON_*` log lines, mirroring the `ADD_PERSON_*` shape from Story 3.3.
- `bot._chat_id`, `bot._message`, `bot._command` helpers — already exist; reuse rather than re-deriving.
- `recognition.registry.load_registry` — reads `people.json` via the canonical schema; returns an empty `Registry` for missing/empty files, which is exactly what we want for the empty-list reply.
- `recognition.writer.remove_person(name, people_json_path, faces_dir) -> bool` — already does atomic write + photo cleanup. Returns `False` when the name is not present.

### Name parsing for `/delete_person`

`python-telegram-bot` exposes the parsed args on `context.args`, but the existing handlers in this repo do not rely on that (they read `update.effective_message.text` directly to stay easy to unit-test). Stay consistent:

```python
text = (getattr(message, "text", "") or "").strip()
parts = text.split(maxsplit=1)
name = parts[1].strip() if len(parts) > 1 else ""
```

This preserves multi-word names (`/delete_person Judge Karimov` → `Judge Karimov`) and trims trailing whitespace without doing anything fancier than `add_person_command` already does.

### Order of registration in `build_application`

```
CommandHandler("start", ...)
CommandHandler("add_person", ...)
CommandHandler("list_people", ...)   # new
CommandHandler("delete_person", ...) # new
MessageHandler(PHOTO, ...)
MessageHandler(TEXT & ~COMMAND, ...)
MessageHandler(COMMAND, unknown_command)
```

The catch-all `unknown_command` must remain last so it only fires for commands we have not registered.

### Out of scope for this story

- Hot-reload on the worker side (`watchdog.Observer` reacting to `people.json` changes) — that is Story 3.5. `/delete_person` must still write atomically here; Story 3.5 will close the loop so the worker stops greeting the removed person within 5 s (FR19, NFR4).
- Video commands — Stories 3.6 and 3.7.

### Test fixtures

`tests/_fixtures.py` exists from Stories 2.x — reuse `make_people_json(...)` if it is there. Otherwise, write `people.json` directly with `json.dumps({"people": [{"name": "Alice", "encoding": [0.0]*128}, ...]})` inside a `tempfile.TemporaryDirectory()`. The bot tests in `test_bot.py` already use the `tempfile` pattern (see `AddPersonFlowTests.test_photo_reply_downloads_and_calls_shared_writer`); mirror it.

For `/delete_person`, prefer monkey-patching `bot.remove_person` (after importing it at module scope in `bot.py`, same way `add_person` is imported today) so tests do not need real embeddings on disk. The `test_no_face_reply_clears_pending_state` test in Story 3.3 is the model — patch the symbol on `bot`, not the writer module, so the call is observable.

### Previous-story intelligence (from Story 3.3)

- Reply `Photo received. Processing...` was added after the first live test because silence felt broken to the operator. Apply the same instinct here: every command outcome gets a reply, including the failure cases (usage, not-found, unauthorized). No silent no-ops.
- Log lines use the prefix `<COMMAND>_<STATE>` (e.g., `ADD_PERSON_START`, `ADD_PERSON_NO_FACE`). Match this convention: `LIST_PEOPLE`, `DELETE_PERSON_START`, `DELETE_PERSON_REMOVED`, `DELETE_PERSON_NOT_FOUND`.
- Tests assert against `update.effective_message.replies` as an ordered list, so write replies in the order they happen. There is no second "processing" reply needed for list/delete — both are fast synchronous operations against `people.json`.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### Debug Log References

- 2026-05-16: Story file created from `epics.md` Story 3.4 after Story 3.3 (`/add_person`) shipped and verified live.
- 2026-05-16: Implemented `/list_people` + `/delete_person`. Noted that `recognition.writer.remove_person` compares names case-insensitively (designed for add-side dedup); to honor AC 6 ("case-sensitive and exact, no fuzzy matching") the bot pre-checks `registry.names` for exact membership before calling the writer, so `/delete_person alice` against a registered `Alice` returns the not-found reply without mutating state.

### Completion Notes List

- Imported `remove_person` and `load_registry` at module scope in `bot.py` so tests can monkey-patch `bot.remove_person`.
- `list_people_command` returns `"\n".join(registry.names)` (insertion order preserved by `load_registry`); empty registry → `"No people registered yet. Use /add_person to add someone."`.
- `delete_person_command` parses `text.split(maxsplit=1)[1]` to preserve multi-word names (e.g., `/delete_person Judge Karimov`). Missing arg → `Usage: /delete_person <name>` and no writer call.
- Case-sensitive pre-check via `load_registry`: `name not in registry.names` → reply `Person not found. Use /list_people to see who is registered.` and exit before invoking `remove_person`. Defensive post-call branch retained for the (unlikely) race where the file changes between load and remove.
- Log events follow Story 3.3 convention: `LIST_PEOPLE chat_id=… count=…`, `DELETE_PERSON_START|REMOVED|NOT_FOUND|USAGE`.
- Both handlers wrapped with `admin_only`; unauthorized chats get `Unauthorized` before any registry read or writer call.
- Handlers registered before the catch-all `MessageHandler(filters.COMMAND, unknown_command)` so routing is correct.
- Test suite: 99/99 pass (was 90 in Story 3.3; 9 new tests across `ListPeopleFlowTests` and `DeletePersonFlowTests`).

### File List

- `bot.py` (modified — `list_people_command`, `delete_person_command`, handler registration, `load_registry` + `remove_person` imports)
- `tests/test_bot.py` (modified — added `json` import, `_write_people_json` helper, `ListPeopleFlowTests`, `DeletePersonFlowTests`)
- `_bmad-output/implementation-artifacts/3-4-implement-list-people-and-delete-person.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 3.4 created from epics.md, status set to ready-for-dev.
- 2026-05-16: Implemented `/list_people` + `/delete_person`; 99/99 tests pass; status set to review pending live Telegram verification.
