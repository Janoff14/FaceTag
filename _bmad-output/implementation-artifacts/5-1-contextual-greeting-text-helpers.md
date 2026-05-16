# Story 5.1: Contextual greeting text helpers

Status: done

## Story

As Dilnoza (and demo judges),
I want the kiosk to greet people with a phrase that fits the time of day, holiday, and possibly a per-person flavor,
so that the greeting feels alive and personal instead of `Welcome, Alice!` 100 times in a row.

## Acceptance Criteria

1. **Given** a registered person's name and the current local time, **when** the worker emits a greeting event, **then** the overlay shows a phrase that varies by time-of-day band: morning, afternoon, evening, and late-night.
2. **And** when a holiday or weekend matches the current date in `config.yaml`, the overlay swaps in a holiday line ahead of the time-of-day default.
3. **And** when a person has a `flavor` array in `people.json` (e.g., `["nice scarf today", "favorite Uzbek?"]`), one entry is appended at random; missing/empty falls back silently to the bare greeting.
4. **And** the helper is a pure function — given the same inputs (`name`, `now`, `flavors`, `holidays`), output is deterministic when the random seed is provided (for tests).
5. **And** the legacy single-name fall-through (`Welcome, <name>!`) still works when no contextual data is present; nothing in the existing tests should break.

## Tasks / Subtasks

- [ ] **Task 1 — New module `player/greeting_text.py`** with:
  - `band_for_hour(hour: int) -> str` → `"morning" | "afternoon" | "evening" | "late"`.
  - `holiday_for_date(date_iso: str, holidays: dict[str, str]) -> str | None`. `holidays` maps `"MM-DD"` → headline (e.g., `"03-21": "Navruz mubarak"`). Returns the headline or `None`.
  - `build_greeting(name, *, now, holidays=None, flavors=None, rng=None) -> str` — composes the line. Picks holiday → time-band template → applies name → optionally appends flavor.
  - Templates are simple constants at module top; easy to hand-edit. Use Uzbek-friendly defaults (English chosen for the buildathon audience).
- [ ] **Task 2 — Extend `Registry`/`people.json` schema (additive)**:
  - `recognition.registry.load_registry` already returns `(names, encodings)`. Add a parallel optional `flavors: list[list[str]]` so the worker has the per-person data available.
  - `recognition.writer.add_person` accepts an optional `flavor` argument (defaults to empty list) so the bot/CLI can be extended later without schema break.
  - Existing entries without a `flavor` key keep working (default to `[]`).
- [ ] **Task 3 — Wire into the player** `show_greeting`:
  - Read `holidays` from config at boot (default `{}`).
  - Read the matched person's `flavors` from the registry — but the player doesn't have direct registry access. Two options:
    - (a) Have the worker include `flavors` in the greeting event (`{name, timestamp, flavors}`). **Pick (a)** — keeps the player stateless about people data.
  - On greeting, call `build_greeting(name, now=datetime.now(), holidays=config_holidays, flavors=event_flavors)`.
- [ ] **Task 4 — Update the worker** to read flavors from the registry and put them on the queue alongside name+timestamp.
- [ ] **Task 5 — Config additions**:
  - `holidays:` (dict of `MM-DD` → headline) — optional, default empty in `config.yaml.example`.
- [ ] **Task 6 — Tests** in `tests/test_greeting_text.py`:
  - `band_for_hour` returns correct band for boundary hours (0, 11, 12, 17, 22, 23).
  - `holiday_for_date` matches; non-match returns None.
  - `build_greeting` with a fixed `rng` deterministically picks a flavor.
  - `build_greeting` with no holiday, no flavor → falls back to time-band template.
  - Backward compatibility — `build_greeting("Alice", now=...)` works with all defaults.

## Dev Notes

### Templates — first pass

```python
TIME_BAND_TEMPLATES = {
    "morning":   "Good morning, {name}!",
    "afternoon": "Good afternoon, {name}!",
    "evening":   "Good evening, {name}!",
    "late":      "Still here, {name}?",
}
```

Keep it light. The flavor field is where personality lives; the time band is a non-monotonic but neutral default.

### Bands

- morning: hour < 12
- afternoon: 12 ≤ hour < 17
- evening: 17 ≤ hour < 22
- late: hour ≥ 22 OR hour < 5

(That last "OR" is the wrap-around for very early morning hours feeling like night.)

### Flavor format

`flavors` is `list[str]`. `build_greeting` chooses one uniformly. If a flavor contains the substring `{name}`, format it; otherwise it's appended as ` — <flavor>`.

### Why pure

Lets us unit-test exhaustively with a deterministic RNG and frozen `now` without Qt or face_recognition.

## Dev Agent Record

### Agent Model Used

_TBD_

### Debug Log References

- 2026-05-16: Story file created at the start of Epic 5 (post-MVP polish) after 179/179 tests green from Epic 4 work.

### Completion Notes List

_To be filled by dev agent._

### File List

_Expected:_

- `player/greeting_text.py` (new)
- `player/main.py` (modified — `show_greeting` uses the builder; reads `holidays` from config)
- `recognition/registry.py` (modified — load `flavors` per person)
- `recognition/writer.py` (modified — optional `flavor` param on `add_person`)
- `recognition/worker.py` (modified — include `flavors` in queue events)
- `config.yaml.example` (modified — `holidays:` placeholder)
- `tests/test_greeting_text.py` (new)
- `_bmad-output/implementation-artifacts/5-1-contextual-greeting-text-helpers.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 5.1 created, status set to ready-for-dev.
