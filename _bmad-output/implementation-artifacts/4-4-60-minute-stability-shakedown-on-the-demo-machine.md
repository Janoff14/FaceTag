# Story 4.4: 60-minute stability shakedown on the demo machine

Status: ready-for-dev

## Story

As Sanji,
I want to run the entire system uninterrupted for ≥ 60 minutes on the actual demo machine and verify zero crashes / no memory leak / no playback degradation,
so that I can trust the system on stage. _[NFR7, NFR8, NFR11, AR17]_

## Acceptance Criteria

1. **Given** the full system (Epics 1–3 complete) running on the demo machine (not the dev machine), **when** I leave it running for 60 minutes with intermittent walk-pasts (≥ 5) and ≥ 2 admin actions (one `/add_person`, one `/add_video`), **then** the supervisor reports zero unrecoverable crashes — Story 3.1 component restarts within contract are acceptable and counted.
2. **And** memory growth is ≤ 100 MB measured at start vs end across player + worker + bot combined. _[NFR8]_
3. **And** ≥ 5 successful greetings logged and zero false-positive greetings. _[NFR9]_
4. **And** camera frames are not persisted to disk during normal operation. _[NFR14]_
5. **And** the video continues to play smoothly throughout — operator inspects 3 random 30-second windows, no stutter / skip / freeze.
6. **And** the run is documented in `tests/shakedown.md` with start time, end time, walk-past count, greeting count, memory before/after, and any anomalies.
7. **And** hard gate per AR17: if this story does not pass by hour 20 of the build budget, freeze all feature work and operate in debug-only mode until the demo recording.

## Tasks / Subtasks

This is an **operator-driven** story. There is no code to write; the deliverable is a completed `tests/shakedown.md` log.

- [x] **Task 1 — Create `tests/shakedown.md` template** with the structure the operator fills in during the run.
- [ ] **Task 2 — Run the shakedown** — operator action on the demo machine.
- [ ] **Task 3 — Fill in the log** — paste timestamps, memory readings, walk-past / greeting counts, and any anomalies observed.

## Dev Notes

### Measuring memory

On Windows:

```powershell
Get-Process python | Select-Object Id, ProcessName, @{Name="WS_MB";Expression={[math]::Round($_.WorkingSet64 / 1MB, 1)}}
```

Capture this before launching `run.py` (baseline → near zero) and again at the end. The three relevant processes are the supervisor's player (main), recognition worker (`multiprocessing.Process`), and bot subprocess.

### What counts as a "crash"

- An unrecoverable exit of the supervisor itself, OR
- A component restart > 5 s after exit (violates FR30), OR
- A player freeze that requires Ctrl+C to recover.

A clean restart inside FR30's contract (worker or bot exits non-zero, supervisor restarts within 5 s) is NOT a failure — but log it in the anomalies section.

### Frame persistence check

Camera frames are decoded in memory only — Story 2.3 never writes them to disk. The check here is a spot-audit: during the run, look at `logs/` and `videos/` and confirm no `.jpg` or `.png` files appeared.

### Out of scope

- Stress tests beyond the AC (multi-camera, 200-person walk-pasts, etc.).
- Automated alerting — this is a human-observed run.

## Dev Agent Record

### Agent Model Used

N/A (operator-driven)

### Debug Log References

- 2026-05-16: Story file + shakedown template created. Real run pending operator action on the demo machine.

### Completion Notes List

_To be filled after the shakedown run._

### File List

- `tests/shakedown.md` (new — template; populated by operator)
- `_bmad-output/implementation-artifacts/4-4-60-minute-stability-shakedown-on-the-demo-machine.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 4.4 created from epics.md, status set to ready-for-dev. Shakedown template added at `tests/shakedown.md`.
