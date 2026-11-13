"""Load non-secret user configuration.

Secrets (Spotify client id and secret) are read from the environment or from
command line flags, never from the config file. The config file only holds
preferences such as the output directory and default audio format.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import StashifyError

DEFAULT_TEMPLATE = "{artist} - {title}"
DEFAULT_FORMAT = "mp3"
DEFAULT_BITRATE = "192k"

_KNOWN_KEYS = {
    "output_dir": str,
    "audio_format": str,
    "bitrate": str,
    "template": str,
    "market": str,
    "overwrite": bool,
    "no_cover": bool,
    "no_lyrics": bool,
    "provider": str,
    "detailed": bool,
}


def config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "stashify"
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "stashify"


def default_config_path() -> Path:
    return config_dir() / "config.json"


def load_config(path: Path | None = None) -> dict:
    path = Path(path) if path else default_config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StashifyError(f"Could not read config file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise StashifyError(f"Config file {path} must contain a JSON object.")
    cleaned: dict = {}
    for key, expected in _KNOWN_KEYS.items():
        value = data.get(key)
        if value is None:
            continue
        if expected is bool and not isinstance(value, bool):
            raise StashifyError(f"Config key {key!r} must be a boolean.")
        if expected is str and not isinstance(value, str):
            raise StashifyError(f"Config key {key!r} must be a string.")
        cleaned[key] = value
    return cleaned
