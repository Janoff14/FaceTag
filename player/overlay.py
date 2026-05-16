"""Greeting overlay shown above the fullscreen video player.

The overlay is a top-level translucent window positioned over the player.
That is the reliable Windows/Qt pattern for drawing above QVideoWidget's
native Media Foundation surface without interfering with playback.
"""

from __future__ import annotations

import string
from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPauseAnimation,
    QPropertyAnimation,
    QRect,
    QSequentialAnimationGroup,
    Qt,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

MIN_FONT_PT = 24
DEFAULT_FONT_SIZE_FACTOR = 0.08
DEFAULT_HOLD_MS = 5_000
DEFAULT_FADE_MS = 400
MIN_HOLD_MS = 4_000
MAX_HOLD_MS = 6_000

CARD_QSS = """
QFrame#greetingCard {
    border-radius: 28px;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(10, 16, 28, 232),
        stop: 0.52 rgba(27, 43, 64, 222),
        stop: 1 rgba(10, 16, 28, 232)
    );
    border: 1px solid rgba(255, 255, 255, 54);
}
QLabel#greetingBadge {
    color: #10202c;
    border-radius: 28px;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 245),
        stop: 1 rgba(145, 230, 210, 235)
    );
}
QLabel#greetingEyebrow {
    color: rgba(221, 250, 242, 210);
    font-weight: 700;
    letter-spacing: 0px;
}
QLabel#greetingTitle {
    color: #ffffff;
    font-weight: 800;
    letter-spacing: 0px;
}
QLabel#greetingDetail {
    color: rgba(255, 255, 255, 218);
    font-weight: 500;
    letter-spacing: 0px;
}
"""


def compute_font_size(display_height_px: int, factor: float) -> int:
    """Return the font point size for the greeting overlay."""
    if display_height_px <= 0:
        return MIN_FONT_PT
    pixel_height = display_height_px * factor
    point_size = int(pixel_height / 1.333)
    return max(MIN_FONT_PT, point_size)


def clamp_hold_ms(hold_ms: int) -> int:
    """Constrain the visible hold duration to the requested 4-6 seconds."""
    return max(MIN_HOLD_MS, min(MAX_HOLD_MS, int(hold_ms)))


def split_greeting_text(text: str) -> tuple[str, str]:
    """Split a greeting into title and optional detail text."""
    normalized = " ".join(str(text).strip().split())
    for separator in (" - ", " \u2014 ", " \u00e2\u20ac\u201d "):
        if separator in normalized:
            title, detail = normalized.split(separator, 1)
            return title.strip(), detail.strip()
    return normalized, ""


class GreetingOverlay(QWidget):
    """Animated welcome card that fades over the video."""

    def __init__(
        self,
        anchor_window: QWidget,
        font_size_factor: float = DEFAULT_FONT_SIZE_FACTOR,
        hold_ms: int = DEFAULT_HOLD_MS,
        fade_ms: int = DEFAULT_FADE_MS,
    ) -> None:
        super().__init__(None)
        self._anchor = anchor_window
        self.font_size_factor = font_size_factor
        self.hold_ms = clamp_hold_ms(hold_ms)
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

        self.card = QFrame(self)
        self.card.setObjectName("greetingCard")
        self.card.setStyleSheet(CARD_QSS)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(52)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 185))
        self.card.setGraphicsEffect(shadow)

        self.badge = QLabel("Hi", self.card)
        self.badge.setObjectName("greetingBadge")
        self.badge.setFixedSize(56, 56)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.eyebrow = QLabel("Welcome back", self.card)
        self.eyebrow.setObjectName("greetingEyebrow")

        self.label = QLabel("", self.card)
        self.label.setObjectName("greetingTitle")
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.label.setWordWrap(False)

        self.detail_label = QLabel("", self.card)
        self.detail_label.setObjectName("greetingDetail")
        self.detail_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.detail_label.setWordWrap(False)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        text_layout.addWidget(self.eyebrow)
        text_layout.addWidget(self.label)
        text_layout.addWidget(self.detail_label)

        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(28, 22, 32, 22)
        card_layout.setSpacing(20)
        card_layout.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        card_layout.addLayout(text_layout)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setWindowOpacity(0.0)

        self.animation_group: Optional[QSequentialAnimationGroup] = None
        self._apply_font()
        self.hide()
        self.reposition()

    def reposition(self) -> None:
        """Snap the overlay window to the anchor window."""
        if self._anchor is None:
            return
        top_left = self._anchor.mapToGlobal(self._anchor.rect().topLeft())
        self.setGeometry(
            top_left.x(),
            top_left.y(),
            self._anchor.width(),
            self._anchor.height(),
        )
        self._apply_font()
        self._layout_card()

    def start_fade(self, text: str) -> None:
        """Trigger a fade-in, hold, fade-out cycle with the greeting text."""
        title, detail = split_greeting_text(text)
        self.label.setText(title)
        self.detail_label.setText(detail)
        self.detail_label.setVisible(bool(detail))
        self.badge.setText(self._badge_text(title))
        self._layout_card()
        self.setWindowOpacity(0.0)
        self.opacity_effect.setOpacity(0.0)
        self.raise_()
        self.show()

        if self.animation_group is not None:
            self.animation_group.stop()
            self.animation_group.deleteLater()
            self.animation_group = None

        target = self.card.geometry()
        start_w = int(target.width() * 0.94)
        start_h = int(target.height() * 0.94)
        start_x = target.x() + (target.width() - start_w) // 2
        start_y = target.y() + 20
        start_rect = QRect(start_x, start_y, start_w, start_h)

        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(self.fade_ms)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        settle_in = QPropertyAnimation(self.card, b"geometry")
        settle_in.setDuration(self.fade_ms)
        settle_in.setStartValue(start_rect)
        settle_in.setEndValue(target)
        settle_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        enter = QParallelAnimationGroup(self)
        enter.addAnimation(fade_in)
        enter.addAnimation(settle_in)

        hold = QPauseAnimation(self.hold_ms)

        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(self.fade_ms)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        group = QSequentialAnimationGroup(self)
        group.addAnimation(enter)
        group.addAnimation(hold)
        group.addAnimation(fade_out)
        group.finished.connect(self._on_finished)

        self.animation_group = group
        group.start()

    def _apply_font(self) -> None:
        height = self._anchor.height() if self._anchor is not None else 1080
        title_size = min(52, compute_font_size(height, self.font_size_factor))

        title_font = QFont("Segoe UI")
        title_font.setBold(True)
        title_font.setPointSize(title_size)
        self.label.setFont(title_font)

        detail_font = QFont("Segoe UI")
        detail_font.setPointSize(max(16, int(title_size * 0.36)))
        detail_font.setWeight(QFont.Weight.Medium)
        self.detail_label.setFont(detail_font)

        eyebrow_font = QFont("Segoe UI")
        eyebrow_font.setPointSize(max(11, int(title_size * 0.24)))
        eyebrow_font.setBold(True)
        self.eyebrow.setFont(eyebrow_font)

        badge_font = QFont("Segoe UI")
        badge_font.setPointSize(max(16, int(title_size * 0.32)))
        badge_font.setBold(True)
        self.badge.setFont(badge_font)

    def _layout_card(self) -> None:
        """Place the card in the lower third with responsive width."""
        max_width = max(460, int(self.width() * 0.88))
        text_width = max(300, max_width - 136)
        self.eyebrow.setMaximumWidth(text_width)
        self.label.setMaximumWidth(text_width)
        self.detail_label.setMaximumWidth(text_width)

        self.card.adjustSize()
        width = min(max_width, max(420, self.card.sizeHint().width()))
        height = max(104, self.card.sizeHint().height())
        x = max(24, (self.width() - width) // 2)
        y = max(24, int(self.height() * 0.66) - height // 2)
        if y + height > self.height() - 48:
            y = max(24, self.height() - height - 48)
        self.card.setGeometry(x, y, width, height)

    def _badge_text(self, title: str) -> str:
        punctuation = string.punctuation + "!?.,"
        for token in reversed(title.split()):
            cleaned = token.strip(punctuation)
            if cleaned and cleaned[0].isalpha():
                return cleaned[0].upper()
        return "Hi"

    def _on_finished(self) -> None:
        self.opacity_effect.setOpacity(0.0)
        self.setWindowOpacity(0.0)
        self.hide()
