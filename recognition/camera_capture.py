"""Capture a still frame from the local camera for enrollment flows."""

from __future__ import annotations

from pathlib import Path

import cv2


class CameraCaptureError(RuntimeError):
    """Raised when a still image cannot be captured from the camera."""


def capture_frame_to_file(
    camera_index: int,
    output_path: Path,
    *,
    warmup_frames: int = 8,
) -> Path:
    """Capture one frame from ``camera_index`` and write it to ``output_path``."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(int(camera_index))
    try:
        if not capture.isOpened():
            raise CameraCaptureError(f"camera {camera_index} is not available")
        frame = None
        for _ in range(max(1, warmup_frames)):
            ok, frame = capture.read()
            if not ok:
                frame = None
        if frame is None:
            raise CameraCaptureError("camera did not return a frame")
        if not cv2.imwrite(str(output_path), frame):
            raise CameraCaptureError(f"could not write captured frame to {output_path}")
    finally:
        capture.release()
    return output_path
