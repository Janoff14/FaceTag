# Story 4.1: Build add_person.py CLI fallback

Status: done

## Story

As Sanji (operator at the venue, with no Wi-Fi),
I want a CLI script that adds a registered person without requiring Telegram or any network connection,
so that I can prep demo people on stage even when venue Wi-Fi is down (Journey 5).

## Acceptance Criteria

1. **Given** the shared writer module from Story 2.2 exists and the worker (Story 2.3) is running with hot-reload (Story 3.5), **when** I run `python add_person.py "Judge Karimov" path/to/photo.jpg`, **then** the script invokes the same writer module the bot uses (no duplicate logic, AR9), prints `Added: Judge Karimov`, and exits 0. _[FR14, AR9]_
2. **And** the worker's hot-reload picks up the change within 5 s (already proven by Story 3.5; CLI path inherits this for free because the writer's `os.replace` is what triggers `PeopleRegistryReloader`). _[FR18 via CLI]_
3. **And** when run with missing args, the script prints `Usage: python add_person.py "<name>" <image_path>` and exits non-zero.
4. **And** when the image path does not exist, prints `Error: image file not found: <path>` and exits non-zero.
5. **And** when the image contains no detectable face, prints `Error: no face detected in <path>` and exits non-zero.
6. **And** the script works completely offline with no network calls of any kind. _[FR14, FR31, NFR13]_
7. **And** the script reads `people_db_path` and `faces_folder` from `config.yaml` (falling back to `config.yaml.example` defaults if no local config is present), matching the bot's resolution pattern.

## Tasks / Subtasks

- [ ] **Task 1 — Create `add_person.py`** at repo root with the CLI surface described above. Reuse `bot.load_config` to resolve `people_db_path` / `faces_folder` so the CLI and bot read the same config keys.
- [ ] **Task 2 — Map writer exceptions to exit codes**:
  - `NoFaceInImageError` → "no face detected" message, exit 2.
  - `FileNotFoundError` / missing-image path → "image file not found" message, exit 2.
  - `ValueError` (decode failure, empty-after-sanitize name) → print the exception message verbatim, exit 2.
  - Missing args → usage message, exit 1.
  - Success → `Added: <name>`, exit 0.
- [ ] **Task 3 — Tests** in `tests/test_add_person_cli.py`:
  - Happy path: monkey-patch `add_person` to a no-op, assert `sys.exit(0)` and stdout has `Added: <name>`.
  - Missing args: empty argv → usage line on stderr, exit code 1.
  - Image not found: real missing path → "image file not found" on stderr, exit code 2.
  - `NoFaceInImageError` from writer → "no face detected" on stderr, exit code 2.
  - Unexpected error from writer → message on stderr, exit code 2.
- [ ] **Task 4 — Regression** — full suite green (was 148/148 at end of Story 3.7).

## Dev Notes

### Wire to the shared writer

The bot already imports `add_person` from `recognition.writer`. The CLI does the same — one call site, AR9 satisfied. The CLI is a 30-line file: parse argv, resolve config, call `add_person`, translate exceptions to messages + exit codes.

### Config resolution

`bot.load_config` is the canonical reader (reads `config.yaml` or falls back to `config.yaml.example`). Importing `bot` from a CLI is a little ugly but avoids drift; alternatively, hoist `load_config` into a tiny shared `config.py` later if Story 4.2's CLI duplicates this. For now, `from bot import load_config` is fine.

### Exit code conventions

- `0` — success.
- `1` — usage error (caller's fault: missing args).
- `2` — operational error (image missing, no face, decode failure, writer error).

This mirrors common Unix CLI patterns and makes it easy to grep logs.

### Out of scope

- Bulk-add (multiple people in one invocation) — not needed for Journey 5.
- Interactive prompts — script must remain non-interactive for headless use.

## Dev Agent Record

### Agent Model Used

_TBD_

### Debug Log References

- 2026-05-16: Story file created from `epics.md` Story 4.1 after Epic 3 closed with 148/148 tests passing.

### Completion Notes List

_To be filled by dev agent._

### File List

_Expected:_

- `add_person.py` (new)
- `tests/test_add_person_cli.py` (new)
- `_bmad-output/implementation-artifacts/4-1-build-add-person-py-cli-fallback.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 4.1 created from epics.md, status set to ready-for-dev.
