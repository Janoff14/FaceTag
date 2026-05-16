# Story 5.3: Admin web UI — people CRUD

Status: done

## Story

As a judge or onsite operator,
I want a small graphical admin panel on `localhost:8000` for managing registered people,
so that I can demo/operate the kiosk without Telegram and without typing CLI commands.

## Acceptance Criteria

1. **Given** the webapp is running, **when** I visit `http://127.0.0.1:8000/`, **then** I see a list of registered people with their photos and a form to add a new person (name + image upload).
2. **And** submitting the add form invokes `recognition.writer.add_person` (the same code path as the bot — AR9) and on success redirects back to `/` with a success flash message.
3. **And** the no-face / decode-failure / empty-name cases render a clear error message on the page rather than a stack trace.
4. **And** each row has a "Delete" button that posts to `/people/delete` and calls `remove_person`. The page redirects back with a "Removed X" flash.
5. **And** the UI is styled (dark theme, modern type, generous spacing) and works without a network connection — no CDN dependencies.
6. **And** the webapp binds to `127.0.0.1` only — never `0.0.0.0`.

## Tasks / Subtasks

- [ ] **Task 1 — `webapp.py`** at repo root with the Flask app and routes (`/`, `POST /people/add`, `POST /people/delete`).
- [ ] **Task 2 — Templates** under `webapp/templates/`:
  - `base.html` — shared layout (head + nav + flash slot).
  - `index.html` — two-pane layout, people column populated from `Registry`.
- [ ] **Task 3 — Static CSS** at `webapp/static/style.css` — dark navy theme, system font stack, soft shadows, two-column responsive layout. No CDN.
- [ ] **Task 4 — Serve face photos** from `faces/` via a Flask route (`/faces/<safe>.jpg`) — they're outside Flask's default static folder.
- [ ] **Task 5 — Tests** in `tests/test_webapp_people.py`:
  - Index renders with no people.
  - Index renders with one registered person (name + photo URL).
  - POST `/people/add` with a fake image calls `add_person` and redirects.
  - POST `/people/add` with NoFaceInImageError surfaces the error.
  - POST `/people/delete` calls `remove_person` and redirects.

## Dev Notes

### Stack choice

Flask + Jinja2 — single-file app, server-rendered, no JS framework. ~150 lines of CSS for the look-and-feel. Easy to mock in tests via `app.test_client()`.

### Reuse from bot/CLI

`recognition.writer.add_person` / `remove_person` / `load_registry` — same modules. AR9 stays satisfied: bot + CLI + webapp all hit the same code path.

### Flash messages

Flask's `flash()` + `get_flashed_messages()` is built in. Use it for both success and error to keep state out of the route URLs.

### Photo serving

`/faces/<filename>` route reads from the configured `faces_folder` (NOT Flask's default `static/`) and serves via `flask.send_from_directory`. Validates against directory traversal automatically.

### Out of scope here

Videos UI — Story 5.4. Just the people half is plenty for one story.

## Dev Agent Record

### Agent Model Used

_TBD_

### File List

_Expected:_

- `webapp.py` (new)
- `webapp/__init__.py` (new — empty)
- `webapp/templates/base.html` (new)
- `webapp/templates/index.html` (new)
- `webapp/static/style.css` (new)
- `tests/test_webapp_people.py` (new)
- `requirements.txt` (modified — Flask + deps already added)
- `_bmad-output/implementation-artifacts/5-3-admin-web-ui-people.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 5.3 created, status set to ready-for-dev.
