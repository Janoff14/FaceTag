"""Temporary camera/debug overlay for local recognition tuning."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

DEBUG_OVERLAY_WIDTH = 360
DEBUG_OVERLAY_HEIGHT = 330
DEBUG_IMAGE_WIDTH = 320
DEBUG_IMAGE_HEIGHT = 240
DEBUG_MARGIN = 24


class DebugCameraOverlay(QWidget):
    """Small top-right overlay showing the worker camera feed and status."""

    def __init__(self, anchor_window: QWidget) -> None:
        super().__init__(None)
        self._anchor = anchor_window

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(DEBUG_IMAGE_WIDTH, DEBUG_IMAGE_HEIGHT)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("background: #111; color: white;")

        self.log_label = QLabel("camera debug: waiting for frames", self)
        self.log_label.setWordWrap(True)
        self.log_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        font = QFont("Consolas")
        font.setPointSize(9)
        self.log_label.setFont(font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.log_label)

        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(0, 0, 0, 185);
                border: 1px solid rgba(255, 255, 255, 170);
                color: white;
            }
            QLabel {
                border: 0;
            }
            """
        )
        self.reposition()

    def reposition(self) -> None:
        if self._anchor is None:
            return
        top_right = self._anchor.mapToGlobal(self._anchor.rect().topRight())
        self.setGeometry(
            top_right.x() - DEBUG_OVERLAY_WIDTH - DEBUG_MARGIN,
            top_right.y() + DEBUG_MARGIN,
            DEBUG_OVERLAY_WIDTH,
            DEBUG_OVERLAY_HEIGHT,
        )

    def update_event(self, event: dict) -> None:
        jpeg = event.get("jpeg")
        if isinstance(jpeg, bytes):
            pixmap = QPixmap()
            if pixmap.loadFromData(jpeg, "JPG"):
                self.image_label.setPixmap(pixmap)

        lines = event.get("lines")
        if isinstance(lines, list):
            self.log_label.setText("\n".join(str(line) for line in lines[-5:]))

        self.reposition()
        self.raise_()
        self.show()
