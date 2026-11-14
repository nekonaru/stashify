

import pytest

from stashify.download import validate_bitrate, verify_media
from stashify.errors import DownloadError
from stashify.models import Track


@pytest.mark.parametrize(
    "bitrate",
    ["128k", "192k", "320k", "192", "128K", " 96k "],
)
def test_validate_bitrate_accepts(bitrate):
    assert validate_bitrate(bitrate) in {"128k", "192k", "320k", "192", "96k"}


@pytest.mark.parametrize(
    "bitrate",
    ["", "banana", "k", "1k9", "128kk", "--audio-bitrate", "0x20"],
)
def test_validate_bitrate_rejects(bitrate):
    with pytest.raises(DownloadError):
        validate_bitrate(bitrate)


def make_track(duration_ms=213573):
    return Track(
        title="Song",
        artists=["Artist"],
        duration_ms=duration_ms,
    )


def test_missing_file_fails(tmp_path):
    ok, detail = verify_media(tmp_path / "missing.mp3", make_track())
    assert ok is False
    assert "missing" in detail


def test_empty_file_fails(tmp_path):
    target = tmp_path / "empty.mp3"
    target.write_bytes(b"")
    ok, detail = verify_media(target, make_track())
    assert ok is False
    assert "empty" in detail


def test_verified_when_duration_close(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"not really audio")
    monkeypatch.setattr(
        "stashify.download._ffprobe_duration", lambda path, ffprobe=None: 214.0
    )
    ok, detail = verify_media(target, make_track(213573))
    assert ok is True
    assert "verified" in detail


def test_warning_when_duration_wildly_off(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"some audio")
    monkeypatch.setattr(
        "stashify.download._ffprobe_duration", lambda path, ffprobe=None: 900.0
    )
    ok, detail = verify_media(target, make_track(213573))
    assert ok is True
    assert "mismatch" in detail


def test_corrupt_ffprobe_failure(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"definitely not audio")

    def boom(path, ffprobe=None):
        from stashify.errors import DownloadError

        raise DownloadError("ffprobe could not read")

    monkeypatch.setattr("stashify.download._ffprobe_duration", boom)
    ok, detail = verify_media(target, make_track())
    assert ok is False
    assert "ffprobe" in detail


def test_missing_ffprobe_keeps_file(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"these are the bytes that matter")
    monkeypatch.setattr("stashify.download.shutil.which", lambda name: None)
    ok, detail = verify_media(target, make_track())
    assert ok is True
    assert "could not verify" in detail
    assert target.exists()


def test_ffprobe_timeout_keeps_file(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"slow disk, big file")

    def boom(path, ffprobe=None):
        from stashify.errors import DownloadError

        raise DownloadError(f"ffprobe timed out on {path}.")

    monkeypatch.setattr("stashify.download._ffprobe_duration", boom)
    ok, detail = verify_media(target, make_track())
    assert ok is True
    assert "could not verify" in detail
