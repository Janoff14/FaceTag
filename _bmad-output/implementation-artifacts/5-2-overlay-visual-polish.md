# Story 5.2: Overlay visual polish

Status: done

## Story

As a demo judge,
I want the greeting overlay to look modern and intentional rather than a stock white label,
so that the kiosk reads as a real product instead of a hack.

## Acceptance Criteria

1. The greeting text sits inside a rounded "pill" backdrop with a soft gradient fill and a thin highlight border, instead of plain text on the video.
2. The pill auto-sizes to its content; it does not stretch to the full screen width.
3. A short scale-in animation accompanies the fade-in (~400 ms, OutBack easing, 92% → 100% of natural size). Fade-out remains as before.
4. The pill remains centered relative to the player window across resize events.
5. All 197 existing tests still pass — no behavior tests touched.

## Tasks / Subtasks

- [x] **Task 1** — Add `PILL_QSS` stylesheet constant in `player/overlay.py`: rounded corners, qlineargradient fill at ~85% opacity, 1 px highlight border.
- [x] **Task 2** — Switch the label to an `objectName="greetingPill"` and apply the stylesheet. Call `label.adjustSize()` after each `setText` so the pill hugs the text.
- [x] **Task 3** — Replace the `QSequentialAnimationGroup` enter step with a `QParallelAnimationGroup` (fade-in + geometry-based scale-in via `OutBack` easing).
- [x] **Task 4** — Increase drop shadow radius and offset for the new pill scale.

## Dev Notes

The pill backdrop is rendered through Qt Style Sheets (QSS), not custom painting — keeps the change confined to a single string constant and avoids overriding `paintEvent`. QSS supports `qlineargradient` for backgrounds and `border-radius` for rounded corners, which is all we need.

The scale-in uses `geometry` animation on the inner label widget, not a transform — Qt animations on QGraphicsTransform require a graphics-view, which we don't use. Geometry animation works for a fixed-position element and stays inside a single repaint region.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### Completion Notes List

- Pill QSS uses semitransparent navy gradient stops (`rgba(20,24,38,215)` → `rgba(36,44,68,200)` → mirror) for a glassy look that reads over any video color palette.
- Drop shadow bumped from blur 20 / offset 2 to blur 40 / offset 6 to compensate for the larger pill size.
- `QParallelAnimationGroup` runs the fade and scale concurrently inside the sequential group's first step, so the existing hold + fade-out timing is unchanged.
- 197/197 tests pass.

### File List

- `player/overlay.py` (modified)
- `_bmad-output/implementation-artifacts/5-2-overlay-visual-polish.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 5.2 implemented and shipped. 197/197 tests pass.
