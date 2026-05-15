"""Fullscreen Qt player — main process of the kiosk.

Story 1.3 scope: scan ``video_folder`` for .mp4 files, play the first one
fullscreen on the primary display, advance on EndOfMedia, loop forever,
exit cleanly on Esc.

Forward-compatibility hooks for later stories:

* :attr:`Player.main_window` and :attr:`Player.video_widget` are exposed so
  Story 1.4 can stack a QLabel overlay above the video widget without
  re-wiring construction.
* :meth:`Player.show_greeting` is a no-op stub. Story 1.4 fills in the fade
  animation; Story 2.4 calls it from a multiprocessing.Queue poller. Do
  NOT add queue polling here.

PyQt6 6.11 gotchas baked into this module:

* QMediaPlaylist was removed in Qt6 — playlist advancement is manual via
  the EndOfMedia mediaStatusChanged signal.
* Qt6 split audio out of QMediaPlayer; QAudioOutput is wired explicitly.
* QApplication, QMainWindow, QMediaPlayer, QVideoWidget, and QAudioOutput
  are all retained as Player attributes so Qt6's silent GC of media
  objects can't kill playback.
* setSource takes a QUrl, not a string — QUrl.fromLocalFile is used so
  Windows drive-letter colons aren't reinterpreted as URI schemes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QKeyEvent, QResizeEvent
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QApplication, QMainWindow

from player.overlay import GreetingOverlay
from player.playlist import advance, scan_playlist

OVERLAY_AUTO_TRIGGER_MS = 10_000


class _PlayerWindow(QMainWindow):
    """QMainWindow subclass that exits cleanly on Esc and forwards G keypress."""

    def __init__(self, on_close, on_greeting_trigger) -> None:
        super().__init__()
        self._on_close = on_close
        self._on_greeting_trigger = on_greeting_trigger
        self._overlay: GreetingOverlay | None = None

    def attach_overlay(self, overlay: GreetingOverlay) -> None:
        self._overlay = overlay

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        if event.key() == Qt.Key.Key_G:
            self._on_greeting_trigger()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self._overlay is not None:
            self._overlay.reposition()
        super().resizeEvent(event)

    def closeEvent(self, event) -> None:
        self._on_close()
        super().closeEvent(event)


class Player:
    """Controller that owns the Qt window, media pipeline, and playlist state."""

    def __init__(
        self,
        playlist: list[Path],
        font_size_factor: float = 0.08,
        display_duration_seconds: int = 5,
    ) -> None:
        if not playlist:
            raise ValueError("playlist must contain at least one video")
        self._playlist = playlist
        self._index = 0

        self.main_window = _PlayerWindow(
            on_close=self._shutdown,
            on_greeting_trigger=lambda: self.show_greeting("TEST GREETING"),
        )
        self.video_widget = QVideoWidget(self.main_window)
        self.main_window.setCentralWidget(self.video_widget)

        # Overlay is a top-level translucent window above the main window —
        # the only reliable way to composite over QVideoWidget's native
        # Media Foundation surface on Windows.
        self.overlay = GreetingOverlay(
            self.main_window,
            font_size_factor=font_size_factor,
            hold_ms=display_duration_seconds * 1000,
        )
        self.main_window.attach_overlay(self.overlay)

        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)

        self._shutdown_done = False
        self._auto_trigger_timer: QTimer | None = None

    def start(self) -> None:
        self.main_window.showFullScreen()
        # Snap overlay to the main window now that it has a real geometry.
        self.overlay.reposition()
        self._load_and_play(self._index)
        # One-shot trigger 10s after startup so the overlay can be validated
        # without a recognition worker. Story 2.4 will replace this with the
        # multiprocessing queue poller.
        self._auto_trigger_timer = QTimer(self.main_window)
        self._auto_trigger_timer.setSingleShot(True)
        self._auto_trigger_timer.timeout.connect(lambda: self.show_greeting("TEST GREETING"))
        self._auto_trigger_timer.start(OVERLAY_AUTO_TRIGGER_MS)

    def show_greeting(self, name: str) -> None:
        """Fade a greeting overlay over the video.

        Story 2.4 wires this from a multiprocessing.Queue poller — the
        signature must stay ``(name: str) -> None``.
        """
        display_text = f"Welcome, {name}!" if name and name != "TEST GREETING" else "TEST GREETING"
        self.overlay.reposition()
        self.overlay.start_fade(display_text)

    def _load_and_play(self, index: int) -> None:
        path = self._playlist[index]
        self.media_player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.media_player.play()

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._index = advance(self._index, len(self._playlist))
            self._load_and_play(self._index)

    def _shutdown(self) -> None:
        if self._shutdown_done:
            return
        self._shutdown_done = True
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        if self.overlay is not None:
            self.overlay.close()  # close the top-level overlay window too
        app = QApplication.instance()
        if app is not None:
            app.quit()


def run_player(config: dict[str, Any]) -> int:
    """Boot the Qt application and play the kiosk loop.

    Returns the Qt exit code so ``run.py`` can pass it to ``sys.exit``.
    """
    video_folder = Path(config.get("video_folder", "videos")).resolve()
    playlist = scan_playlist(video_folder)
    if not playlist:
        print(
            f"ERROR: no .mp4 files found in {video_folder}",
            file=sys.stderr,
        )
        return 1

    app = QApplication.instance() or QApplication(sys.argv)
    player = Player(
        playlist,
        font_size_factor=float(config.get("font_size_factor", 0.08)),
        display_duration_seconds=int(config.get("display_duration_seconds", 5)),
    )
    player.start()
    # Keep a reference attached to the app so GC can't kill the pipeline.
    app._kiosk_player = player  # type: ignore[attr-defined]
    return app.exec()
