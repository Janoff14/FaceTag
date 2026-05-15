"""Fade-in / fade-out greeting overlay (Story 1.4).

The overlay is a child widget of the main window — never of QVideoWidget —
so Qt's video pipeline never repaints the overlay region and there's no
chance of stutter in the underlying video stream.

PyQt6 6.11 traps avoided here:
* QGraphicsOpacityEffect and QGraphicsDropShadowEffect can't both attach to
  the same widget (Qt only honors one QGraphicsEffect per widget), so the
  drop-shadow goes on an inner QLabel and the opacity goes on the outer
  container.
* QSequentialAnimationGroup is held as an instance attribute (and parented
  to self) so Python's GC can't kill the animation before it starts.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QPauseAnimation,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

MIN_FONT_PT = 24
DEFAULT_FONT_SIZE_FACTOR = 0.08
DEFAULT_HOLD_MS = 5_000
DEFAULT_FADE_MS = 400


def compute_font_size(display_height_px: int, factor: float) -> int:
    """Return the font point size for the greeting overlay.

    Implements NFR25 (font height >= 8 % of display height) with a sensible
    floor so tiny / offscreen displays still produce a legible widget in
    tests.  The conversion from px to pt is approximate (assumes ~96 DPI):
    1 pt ≈ 1.333 px on a standard Windows display.
    """
    if display_height_px <= 0:
        return MIN_FONT_PT
    pixel_height = display_height_px * factor
    # Convert approximate pixel height to point size (1 pt ≈ 1.333 px at 96 DPI).
    point_size = int(pixel_height / 1.333)
    return max(MIN_FONT_PT, point_size)


class GreetingOverlay(QWidget):
    """Transparent overlay that fades a greeting in and out over the video.

    On Windows, ``QVideoWidget`` uses a native Media Foundation surface that
    composites at the HWND level — so a sibling widget cannot stack on top
    of it. The reliable cross-driver pattern is to make the overlay a
    **top-level frameless translucent window** positioned over the player
    window. The window has `WindowStaysOnTopHint` and is mouse-transparent
    so it never steals focus from the kiosk.
    """

    def __init__(
        self,
        anchor_window: QWidget,
        font_size_factor: float = DEFAULT_FONT_SIZE_FACTOR,
        hold_ms: int = DEFAULT_HOLD_MS,
        fade_ms: int = DEFAULT_FADE_MS,
    ) -> None:
        super().__init__(None)  # top-level window, not parented
        self._anchor = anchor_window
        self.font_size_factor = font_size_factor
        self.hold_ms = hold_ms
        self.fade_ms = fade_ms

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Inner label carries the text + drop shadow.
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: white;")
        self._apply_font()

        shadow = QGraphicsDropShadowEffect(self.label)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 220))
        self.label.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        # Opacity effect on the container — independent of the inner shadow.
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)

        self.animation_group: Optional[QSequentialAnimationGroup] = None
        self.hide()
        self.reposition()

    # ------------------------------------------------------------------ API

    def reposition(self) -> None:
        """Snap the overlay to cover the anchor window."""
        if self._anchor is None:
            return
        # Use the anchor's screen-space geometry so we sit exactly on top
        # regardless of where Windows placed the main window.
        top_left = self._anchor.mapToGlobal(self._anchor.rect().topLeft())
        self.setGeometry(
            top_left.x(),
            top_left.y(),
            self._anchor.width(),
            self._anchor.height(),
        )
        self._apply_font()

    def start_fade(self, text: str) -> None:
        """Trigger a fade-in / hold / fade-out cycle with *text*.

        If a previous animation is running, it is stopped and replaced. The
        opacity effect itself is reused so the GPU pipeline stays warm.
        """
        self.label.setText(text)
        self.raise_()
        self.show()

        if self.animation_group is not None:
            self.animation_group.stop()
            self.animation_group.deleteLater()
            self.animation_group = None

        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(self.fade_ms)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        hold = QPauseAnimation(self.hold_ms)

        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(self.fade_ms)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        group = QSequentialAnimationGroup(self)
        group.addAnimation(fade_in)
        group.addAnimation(hold)
        group.addAnimation(fade_out)
        group.finished.connect(self._on_finished)

        self.animation_group = group
        group.start()

    # --------------------------------------------------------------- helpers

    def _apply_font(self) -> None:
        height = self._anchor.height() if self._anchor is not None else 1080
        font = QFont("Segoe UI")
        font.setBold(True)
        font.setPointSize(compute_font_size(height, self.font_size_factor))
        self.label.setFont(font)

    def _on_finished(self) -> None:
        # Hide after fade-out so we don't sit at opacity 0 absorbing paint events.
        self.hide()
