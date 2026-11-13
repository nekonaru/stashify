import argparse
import json
from pathlib import Path

import pytest

from stashify import config
from stashify.cli import _options
from stashify.config import (
    clamp_jobs,
    default_download_dir,
    load_config,
)
from stashify.errors import StashifyError


def test_download_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("STASHIFY_DOWNLOAD_DIR", str(tmp_path))
    assert default_download_dir() == tmp_path


def test_download_dir_windows(monkeypatch):
    monkeypatch.delenv("STASHIFY_DOWNLOAD_DIR", raising=False)
    monkeypatch.delenv("XDG_DOWNLOAD_DIR", raising=False)
    monkeypatch.setattr(config.os, "name", "nt")
    monkeypatch.setenv("USERPROFILE", "C:\\Users\\example")
    assert default_download_dir() == Path("C:\\Users\\example") / "Downloads"


def test_download_dir_xdg_env(monkeypatch):
    monkeypatch.delenv("STASHIFY_DOWNLOAD_DIR", raising=False)
    monkeypatch.setattr(config.os, "name", "posix")
    monkeypatch.setenv("XDG_DOWNLOAD_DIR", "/data/downloads")
    assert default_download_dir() == Path("/data/downloads")


def test_download_dir_user_dirs_file(monkeypatch, tmp_path):
    monkeypatch.delenv("STASHIFY_DOWNLOAD_DIR", raising=False)
    monkeypatch.delenv("XDG_DOWNLOAD_DIR", raising=False)
    monkeypatch.setattr(config.os, "name", "posix")
    fake_home = tmp_path / "home"
    config_dir = fake_home / ".config"
    config_dir.mkdir(parents=True)
    (config_dir / "user-dirs.dirs").write_text(
        'XDG_DOWNLOAD_DIR="$HOME/Data/Downloads"\n', encoding="utf-8"
    )
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    result = default_download_dir()
    assert str(result).replace("\\", "/") == f"{fake_home.as_posix()}/Data/Downloads"


def test_download_dir_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("STASHIFY_DOWNLOAD_DIR", raising=False)
    monkeypatch.delenv("XDG_DOWNLOAD_DIR", raising=False)
    monkeypatch.setattr(config.os, "name", "posix")
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    assert default_download_dir() == fake_home / "Downloads"


def test_clamp_jobs():
    assert clamp_jobs(1) == 1
    assert clamp_jobs(8) == 8
    assert clamp_jobs("4") == 4
    with pytest.raises(StashifyError):
        clamp_jobs(0)
    with pytest.raises(StashifyError):
        clamp_jobs(9)
    with pytest.raises(StashifyError):
        clamp_jobs("many")


def test_load_config_rejects_bad_jobs(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"jobs": "two"}), encoding="utf-8")
    with pytest.raises(StashifyError):
        load_config(path)
    path.write_text(json.dumps({"jobs": 3}), encoding="utf-8")
    assert load_config(path)["jobs"] == 3


def _namespace(**kwargs):
    base = dict(
        output=None,
        template=None,
        audio_format=None,
        bitrate=None,
        overwrite=None,
        dry_run=None,
        no_cover=None,
        no_lyrics=None,
        jobs=None,
    )
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_options_default_downloads(monkeypatch, tmp_path):
    monkeypatch.setenv("STASHIFY_DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("stashify.cli.load_config", lambda *a, **k: {})
    options = _options(_namespace())
    assert options.out_dir == tmp_path
    assert options.jobs == 2


def test_options_jobs_flag_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("STASHIFY_DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("stashify.cli.load_config", lambda *a, **k: {"jobs": 5})
    options = _options(_namespace(jobs=3))
    assert options.jobs == 3
    options = _options(_namespace())
    assert options.jobs == 5
