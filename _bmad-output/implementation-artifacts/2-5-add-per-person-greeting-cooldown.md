# Story 2.5: Add per-person greeting cooldown

Status: done

## Story

As a visitor,
I want to not be greeted again every time I walk past the screen within a short window,
so that the kiosk feels intelligent rather than spammy.

## Acceptance Criteria

1. **Given** the worker has just emitted a greeting event for person X at time T, **when** the same person X is detected again at time T+30 s within the default 60 s cooldown, **then** the worker suppresses the event and no new event is pushed to the queue. _[FR8]_
2. **And** when person X is detected again at time T+90 s, past cooldown, **then** a fresh greeting event is emitted normally. _[FR8]_
3. **And** the cooldown table is an in-memory `dict[name, last_greeted_at]` in the worker, cleared on worker restart. _[PRD Implementation Considerations]_
4. **And** the cooldown duration is configurable via `config.yaml`, defaulting to 60 seconds. _[FR9]_

## Tasks / Subtasks

- [x] **Task 1 - Add cooldown helper tests** - Cover first greeting allowed, same person suppressed inside cooldown, same person allowed after cooldown, different person allowed immediately, and non-positive cooldown disables suppression.
- [x] **Task 2 - Implement worker cooldown helper** - Add an in-memory `dict[str, float]` and helper logic in `recognition.worker`.
- [x] **Task 3 - Wire cooldown into queue emission** - Use `cooldown_seconds` from config, default `60`; suppress queue events inside cooldown without blocking the camera loop.
- [x] **Task 4 - Regression verification** - Run full test suite and confirm no Story 2.1-2.4 regressions.

## Dev Notes

- Cooldown belongs in the worker because it is closest to the recognition event source and survives player restarts only as long as the worker does, matching the PRD.
- `MATCH: <name>` diagnostic output can remain per-recognition; the cooldown only suppresses greeting queue events.
- Story 3.5 hot-reload and Story 3.1 supervisor are still out of scope.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-15: Created story file from `epics.md` because no dedicated 2.5 artifact existed yet.
- 2026-05-15: Added failing cooldown tests, implemented worker-side in-memory cooldown, and verified full regression suite.

### Completion Notes List

- Added `DEFAULT_COOLDOWN_SECONDS = 60.0` and config-driven `cooldown_seconds` parsing in the worker.
- Added `_should_emit_greeting(...)` with per-person `dict[name, last_greeted_at]` state scoped to the worker process lifetime.
- Queue events are suppressed inside cooldown; `MATCH: <name>` diagnostic lines still print per recognition, preserving Story 2.3 behavior.
- Verified `.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`: 63/63 pass.

### File List

- `recognition/worker.py` (modified - per-person greeting cooldown)
- `tests/test_worker.py` (modified - cooldown helper and integration coverage)
- `_bmad-output/implementation-artifacts/2-5-add-per-person-greeting-cooldown.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-15: Story 2.5 created and started.
- 2026-05-15: Story 2.5 implemented and verified; status set to done.
