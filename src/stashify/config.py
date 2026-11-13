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
DEFAULT_JOBS = 2

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
    "jobs": int,
}


def config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "stashify"
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "stashify"


def _is_windows() -> bool:
    return os.name == "nt"


def default_download_dir() -> Path:
    """The user's downloads folder, resolved the same way other apps do it."""
    override = os.environ.get("STASHIFY_DOWNLOAD_DIR")
    if override:
        return Path(override).expanduser()
    if _is_windows():
        profile = os.environ.get("USERPROFILE") or str(Path.home())
        return Path(profile) / "Downloads"
    xdg = os.environ.get("XDG_DOWNLOAD_DIR")
    if xdg:
        return Path(xdg).expanduser()
    user_dirs = Path.home() / ".config" / "user-dirs.dirs"
    try:
        for line in user_dirs.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("XDG_DOWNLOAD_DIR="):
                raw = line.split("=", 1)[1].strip().strip('"')
                raw = raw.replace("$HOME", str(Path.home()))
                return Path(raw)
    except OSError:
        pass
    return Path.home() / "Downloads"


def clamp_jobs(value) -> int:
    try:
        jobs = int(value)
    except (TypeError, ValueError):
        raise StashifyError(f"jobs must be a number between 1 and 8, got {value!r}.") from None
    if not 1 <= jobs <= 8:
        raise StashifyError(f"jobs must be between 1 and 8, got {jobs}.")
    return jobs


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
        if expected is int and not isinstance(value, int):
            raise StashifyError(f"Config key {key!r} must be an integer.")
        cleaned[key] = value
    return cleaned
