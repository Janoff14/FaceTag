# Story 4.3: Implement benchmark.py self-test for accuracy + latency boundary

Status: done

## Story

As Sanji (and the buildathon judges),
I want a one-command script that produces reproducible accuracy and latency numbers,
so that the README's claims can be verified by anyone who runs the project. _[FR33, FR34, FR35, NFR30]_

## Acceptance Criteria

1. **Given** `people.json` contains the seed set (Story 2.6) and a `tests/strangers/` folder contains the stranger control set (AR12), **when** I run `python benchmark.py`, **then** the script measures TPR, FPR, and recognition-pipeline p50/p95 latency. _[FR33, FR34]_
2. **And** the script prints a fixed, machine-readable report ready for README pasting. _[NFR30, AR13]_

   ```
   Recognition pipeline latency p50: 0.82 s, p95: 1.64 s
   True-positive rate: 96% (48/50 attempts)
   False-positive rate: 0.0% (0/50 attempts)
   Tolerance: 0.50
   Seed set: 5 people x 10 attempts; control set: 5 strangers x 10 attempts
   ```

3. **And** if TPR < 95% or FPR > 0% on a clean run, the script flags the violation on stderr (e.g., `WARNING: TPR 92% below NFR10 target of 95%`) and exits 0 regardless. _[NFR10, NFR9]_
4. **And** the benchmark includes a capacity fixture with up to 200 synthesized registered embeddings and confirms latency remains within NFR1 (p50 ≤ 1.0 s, p95 ≤ 2.0 s) at that size. _[NFR20, NFR1]_
5. **And** the script does not require the player, worker, or supervisor to be running — it operates purely on `people.json` plus the seed/control image sets. _[FR33, FR35]_
6. **And** when seed or stranger images are missing (clean clone), the script prints a clear message naming the missing path and exits with a non-zero code, rather than producing meaningless numbers.

## Tasks / Subtasks

- [ ] **Task 1 — `benchmark.py` skeleton** with pure helpers (testable without face_recognition):
  - `percentile(values_s, p) -> float` — wraps `np.percentile`, returns seconds.
  - `format_report(*, p50_s, p95_s, tp, total_pos, fp, total_neg, tolerance, seed_people, attempts_per_person, strangers_count, attempts_per_stranger) -> str` — produces the exact README block.
  - `compute_violations(tp, total_pos, fp, total_neg) -> list[str]` — returns NFR9/NFR10 warning lines (empty when within targets).
  - `gather_probe_images_for(name, faces_folder, seed_folder=None) -> list[Path]` — prefers `seed_folder/<safe>/*.{jpg,png}`, falls back to the canonical `faces_folder/<safe>.jpg`; returns up to 10 paths.
  - `gather_stranger_images(strangers_folder) -> list[Path]` — flat list of `.jpg`/`.png` files.
- [ ] **Task 2 — Probe loop** in `_run_attempts(probe_paths, expected_name, registry, tolerance, recognize_fn, *, attempts) -> (matches, latencies_s)`. The `recognize_fn` parameter is the test seam — tests pass a fake; the real script wires `recognition.recognize.recognize_dual`. If `probe_paths` has < `attempts` images, repeat the available ones round-robin so each person contributes a full 10 attempts.
- [ ] **Task 3 — Capacity check** — pad the registry up to 200 entries with synthetic random `np.float64` embeddings, run the recognize_fn on one representative probe image (the first registered person's first probe), record p50/p95 over a small loop (e.g., 5 calls). Print as a separate report block:

  ```
  Capacity (200 registered): p50 0.91 s, p95 1.34 s
  ```

  Warn on stderr if p50 > 1.0 s or p95 > 2.0 s.
- [ ] **Task 4 — Main flow** — parse config (`recognition_tolerance`, `people_db_path`, `faces_folder`); load registry; check for missing seed/control sets with a clear error; run the probe loop for each registered person and each stranger; aggregate; print the report and any warnings; exit 0 unless a missing-data precondition fails (then exit 2).
- [ ] **Task 5 — Tests** in `tests/test_benchmark.py`:
  - `percentile` returns the right number on a known list.
  - `format_report` produces the exact expected block (literal-string comparison).
  - `compute_violations` flags low TPR and any FP; returns empty list for clean.
  - `_run_attempts` with a fake recognize that returns the expected name 9/10 times yields `(matches=9, latencies len=10)`.
  - `_run_attempts` with too few probe images cycles through them (1 probe + 10 attempts → recognize called 10 times).
  - Integration: monkey-patch `recognize_dual` to a deterministic stub, run `main([])` against a synthesized temp registry + temp seed/strangers tree, assert exit code 0 and report has expected structure.
- [ ] **Task 6 — Regression** — full suite green (was 159/159 after Story 4.2).

## Dev Notes

### Probe-image discovery

A clean clone has none of the demo's seed photos checked in (NFR15 — `faces/` is gitignored). So tests must NOT rely on real photos. They use:

- Synthesized embeddings (random 128-D vectors) for the registry.
- A fake `recognize_fn` injected via the seam, so no actual face detection runs in tests.

Real benchmark runs use `recognition.recognize.recognize_dual` and need real seed + stranger photos on disk. The clean-clone path (AC 6) prints a clear "missing seed/control set" error and exits 2.

### Latency measurement

`time.perf_counter()` before/after each `recognize_fn` call. Seconds, not ms. `format_report` formats to 2 decimals (`0.82 s`).

### Capacity padding

Use `numpy.random.default_rng(seed=0).standard_normal((extra_rows, 128))` to synthesize embeddings deterministically. Pass through `Registry(names=names, encodings=padded)` so the real recognize path sees a 200-row matrix. Random embeddings won't match a real face (huge distances), so the recognize result will still be `None` or the original seed name — what we care about here is wall-clock, not correctness.

### Exit codes

- `0` — ran to completion, report printed (NFR violations flagged on stderr but not fatal).
- `2` — preconditions not met (missing `people.json`, missing seed photos, missing `tests/strangers/`).

### Out of scope

- Multi-machine reproducibility (different CPUs → different latency). The README will quote the demo machine's numbers.
- Receiver-operating-characteristic curves / threshold sweeps — single-tolerance run is enough for the AC.

## Dev Agent Record

### Agent Model Used

_TBD_

### Debug Log References

- 2026-05-16: Story file created after Stories 4.1 + 4.2 shipped (CLI fallbacks). Full suite at 159/159.

### Completion Notes List

_To be filled by dev agent._

### File List

_Expected:_

- `benchmark.py` (new)
- `tests/test_benchmark.py` (new)
- `_bmad-output/implementation-artifacts/4-3-implement-benchmark-py-self-test-for-accuracy-latency-boundary.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 4.3 created from epics.md, status set to ready-for-dev.
