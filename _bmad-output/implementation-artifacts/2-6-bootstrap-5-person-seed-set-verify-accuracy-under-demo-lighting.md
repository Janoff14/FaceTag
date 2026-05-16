# Story 2.6: Bootstrap 5-person seed set + verify accuracy under demo lighting

Status: review

## Story

As the operator,
I want a known set of 5 registered demo faces installed and verified to recognize correctly under the actual demo lighting,
so that the recognition pipeline's accuracy claims are proven before the bot is built.

## Acceptance Criteria

1. **Given** 5 source photos exist, one per demo person, and Story 2.2's writer module is functional, **when** I add each of the 5 demo people via the writer module, **then** `people.json` contains 5 valid entries with 128-dimensional embeddings. _[AR11, FR3]_
2. **And** when each person performs 10 walk-past attempts under demo lighting conditions, the system achieves >= 95% true-positive rate across 50 attempts. _[NFR10]_
3. **And** when 5 strangers perform 10 walk-past attempts each, the system produces 0 false-positive greetings at the configured tolerance. _[NFR9]_
4. **And** if accuracy targets are not met, the operator lowers the tolerance from the default `0.5` and re-tests, documenting the chosen value in `config.yaml`.

## Tasks / Subtasks

- [x] **Task 1 - Add repeatable seed bootstrap tool** - Use the shared writer module to add exactly 5 seed people from local photos.
- [x] **Task 2 - Add seed bootstrap tests** - Cover manifest parsing, folder discovery, count validation, and writer invocation without requiring real face embeddings.
- [x] **Task 3 - Bootstrap current local seed set** - Run the tool against the 5 photos currently present in `faces/` and verify `people.json` has 5 valid 128-dim rows.
- [x] **Task 4 - Record demo-lighting verification status** - Document that live 10-attempt person/stranger verification requires the actual camera and walk-past session.
- [x] **Task 5 - Regression verification** - Run full test suite.

## Dev Notes

- Use `recognition.writer.add_person`; do not duplicate embedding or write logic.
- `faces/` and `people.json` are intentionally gitignored because they contain local biometric/runtime data.
- If real display names are available, prefer a CSV manifest with `name,image_path`; otherwise the speed path can register sorted photos as `Demo Person 1` through `Demo Person 5`.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-15: Created story file from `epics.md`; found 5 local source photos in `faces/`.
- 2026-05-15: Added seed bootstrap module, CLI, and tests; seeded the current 5-photo set into local `people.json`.
- 2026-05-15: Recorded live walk-past verification template because NFR9/NFR10 require the actual demo camera and participants.

### Completion Notes List

- Added `recognition.seed` helpers for manifest loading, source-folder discovery, exact-count validation, writer invocation, and final registry shape validation.
- Added `seed_people.py` CLI. It supports a real-name CSV manifest (`name,image_path`) or a fast source-folder path that registers sorted photos as `Demo Person 1..5`.
- Ran `seed_people.py --source-dir faces --expected-count 5`; local `people.json` now contains five people with a `(5, 128)` embedding matrix.
- Added `tests/seed-verification.md` as the operator log for the required 50 registered and 50 stranger live attempts.
- Live demo-lighting accuracy is not yet proven in this environment; story is ready for operator review/walk-past verification, not claimed as physically validated.
- Verified `.\.venv-smoke-dlib-corrected\Scripts\python.exe -m unittest discover -s tests`: 70/70 pass.

### File List

- `recognition/seed.py` (new - seed bootstrap helpers)
- `seed_people.py` (new - 5-person seed CLI)
- `tests/test_seed.py` (new - seed helper tests)
- `tests/seed-verification.md` (new - live accuracy verification log)
- `people.json` (local gitignored runtime data - seeded 5 people)
- `faces/demo_person_1.jpg` through `faces/demo_person_5.jpg` (local gitignored canonical photo copies)
- `_bmad-output/implementation-artifacts/2-6-bootstrap-5-person-seed-set-verify-accuracy-under-demo-lighting.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-15: Story 2.6 created and started.
- 2026-05-15: Seed tooling implemented, local 5-person registry bootstrapped, verification log added, status set to review pending live walk-past validation.
