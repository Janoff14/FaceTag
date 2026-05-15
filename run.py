"""Kiosk entry point.

Currently boots only the fullscreen video player (Story 1.3). The
supervisor that fans out to recognition worker + Telegram bot lands in
Story 3.1; until then ``run.py`` is a thin loader around
:func:`player.main.run_player`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from player.main import run_player

REPO_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = REPO_ROOT / "config.yaml"
EXAMPLE_CONFIG_PATH = REPO_ROOT / "config.yaml.example"


def load_config() -> dict[str, Any]:
    """Load ``config.yaml`` if present, otherwise fall back to the example.

    The example file ships with safe defaults and a placeholder token. The
    fallback is meant for fresh clones that haven't created a real
    ``config.yaml`` yet — log a warning so the operator notices.
    """
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_CONFIG_PATH
    if path is EXAMPLE_CONFIG_PATH:
        print(
            f"WARNING: {CONFIG_PATH.name} not found; using {EXAMPLE_CONFIG_PATH.name} defaults",
            file=sys.stderr,
        )
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    config = load_config()
    return run_player(config)


if __name__ == "__main__":
    raise SystemExit(main())
