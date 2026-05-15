"""Pure-function playlist helpers — no Qt dependency, fully unit-testable."""

from __future__ import annotations

from pathlib import Path

VIDEO_EXTENSIONS = frozenset({".mp4"})


def scan_playlist(folder: Path) -> list[Path]:
    """Return the alphabetically sorted list of playable video files in *folder*.

    Only top-level files with extensions in :data:`VIDEO_EXTENSIONS` are
    included; subdirectories are skipped so the .tmp/ atomic-write staging
    folder used by later stories never produces partial entries. A missing
    folder returns an empty list rather than raising — the caller decides
    whether that's a configuration error or just an empty playlist.
    """
    if not folder.is_dir():
        return []
    matches = [
        entry
        for entry in folder.iterdir()
        if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS
    ]
    matches.sort(key=lambda p: p.name.lower())
    return matches


def advance(current_index: int, playlist_length: int) -> int:
    """Return the next playlist index, wrapping at the end."""
    if playlist_length <= 0:
        raise ValueError("playlist_length must be positive")
    return (current_index + 1) % playlist_length
