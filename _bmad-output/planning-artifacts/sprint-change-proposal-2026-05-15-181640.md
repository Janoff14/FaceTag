# Sprint Change Proposal: Story 1.1 Windows Dependency Install Correction

**Date:** 2026-05-15  
**Project:** facial recognition - uzc  
**Scope:** Minor direct adjustment  
**Status:** Approved by user request

## 1. Issue Summary

Story 1.1 revealed that the planned Windows install command:

```powershell
python -m pip install dlib-bin face_recognition opencv-python
```

does not satisfy the project goal of a clean wheel-only dlib install. On Python 3.13, `dlib-bin` downloads successfully, but `face_recognition==1.3.0` declares a dependency on the distribution package `dlib>=19.7`. Because `dlib-bin` is a separate distribution package, pip still downloads source `dlib`, attempts `Building wheel for dlib`, invokes CMake, and fails without Visual Studio C++ Build Tools.

Evidence:

- Failed install log: `_bmad-output/implementation-artifacts/1-1-dlib-install.log`
- Technical research report: `_bmad-output/planning-artifacts/research/technical-windows-face-recognition-dependency-strategy-research-2026-05-15T180423+05-00.md`
- Local proof showed runtime imports work on Python 3.13 with explicit dependencies, `setuptools<81`, `dlib-bin`, and `face_recognition --no-deps`.

## 2. Impact Analysis

### Epic Impact

Epic 1 remains valid. Story 1.1 still eliminates the Windows dlib platform risk before UI/player work begins. No epic needs to be added, removed, renumbered, or resequenced.

### Story Impact

Story 1.1 requires direct correction:

- Replace the single install command with a two-step explicit install sequence.
- Add `setuptools<81` because `face_recognition_models==0.3.0` imports `pkg_resources`, removed from setuptools v82.
- Document that `pip check` may report a metadata exception because `dlib-bin` does not satisfy the `dlib` distribution requirement, even though runtime `import dlib` succeeds.
- Keep the smoke-test requirement: local image -> face detection -> 128-dimensional encoding.

Story 1.2 should later preserve this dependency choreography in setup documentation and pinned dependency artifacts.

### Artifact Conflicts

PRD and epics do not require strategic changes. They already say the dlib install path must be resolved early and source compilation should be avoided. The conflict is in Story 1.1's concrete install command, not in the product direction.

No UX artifacts are affected.

## 3. Recommended Approach

Recommended path: **Direct Adjustment**.

Rationale:

- Keeps the existing dlib/face_recognition identity-embedding architecture.
- Avoids Visual Studio C++ Build Tools and source compilation.
- Avoids a premature MediaPipe pivot; MediaPipe provides face detection/landmarking, not a direct replacement for identity embeddings.
- Minimizes timeline impact and lets `bmad-dev-story` resume immediately after the story edit.

Effort: Low  
Risk: Low to Medium, limited to dependency installation and smoke verification.

## 4. Detailed Change Proposals

### Story 1.1 Acceptance Criteria

OLD:

```markdown
1. Given a clean Python 3.11+ virtualenv on the Windows demo machine, when I run `python -m pip install dlib-bin face_recognition opencv-python`, then all three packages install in less than 60 seconds without source compilation.
2. The install log must show wheel installation for dlib via `dlib-bin`; it must not build `dlib` from source, invoke CMake, or require Visual Studio Build Tools.
```

NEW:

```markdown
1. Given a clean Python 3.11+ virtualenv on the Windows demo machine, when I run the corrected two-step install sequence, then the face-recognition runtime stack installs without source-compiling `dlib`, invoking CMake, or requiring Visual Studio C++ Build Tools:
   - `python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models`
   - `python -m pip install face_recognition --no-deps`
2. The install log must show `dlib-bin` wheel installation and no source `dlib` build. The elapsed install time and cache state must be recorded; cached repeat install target is less than 60 seconds.
3. `pip check` may report `face-recognition` missing distribution `dlib`; this is an accepted packaging metadata exception only if runtime imports and the 128-dimensional embedding smoke test pass.
```

Rationale: Package metadata requires a controlled `--no-deps` install while preserving runtime behavior.

### Story 1.1 Tasks

OLD task:

```markdown
- [ ] Verify dependency installation path (AC: 1, 2, 6)
  - [x] Run `python -m pip install dlib-bin face_recognition opencv-python` inside the clean virtualenv.
```

NEW task:

```markdown
- [ ] Verify corrected dependency installation path (AC: 1, 2, 3, 7)
  - [ ] Run `python -m pip install "setuptools<81" dlib-bin opencv-python numpy Pillow Click face-recognition-models` inside a clean virtualenv.
  - [ ] Run `python -m pip install face_recognition --no-deps` inside the same virtualenv.
  - [ ] Time the install and record cache state.
  - [ ] Inspect install output for source-build red flags: `Building wheel for dlib`, CMake errors, compiler errors, or Visual Studio Build Tools prompts.
  - [ ] Record installed versions using `python -m pip freeze`.
  - [ ] Run and record `pip check`; treat only the known missing `dlib` distribution warning as acceptable if runtime smoke passes.
```

## 5. Implementation Handoff

Scope classification: **Minor**.

Handoff:

- Developer agent updates Story 1.1 with the corrected ACs/tasks and notes.
- Developer agent resumes Story 1.1 implementation using the corrected install path.
- Developer agent creates `tests/smoke_dlib.py`, runs the smoke verification, and moves Story 1.1 to review only if runtime verification passes.

Success criteria:

- Corrected install avoids source dlib and CMake.
- Runtime imports pass: `cv2`, `dlib`, `face_recognition`, `face_recognition_models`.
- Local image smoke test produces at least one 128-dimensional encoding.
- Story file and sprint status reflect the real verification state.

## 6. Checklist Summary

- [x] Trigger identified: Story 1.1 dependency install failed.
- [x] Core problem defined: package metadata mismatch causes source dlib build.
- [x] Evidence captured: failed log, research report, local workaround proof.
- [x] Epic impact assessed: Epic 1 remains valid.
- [x] PRD impact assessed: no MVP replan required.
- [x] Recommended path selected: Direct Adjustment.
- [x] User approval obtained by explicit request to update Story 1.1 and resume dev-story.
- [x] Sprint status changes: no epic/story additions/removals needed.
