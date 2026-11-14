

from stashify.download import verify_media
from stashify.models import Track


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
        "stashify.download._ffprobe_duration", lambda path: 214.0
    )
    ok, detail = verify_media(target, make_track(213573))
    assert ok is True
    assert "verified" in detail


def test_warning_when_duration_wildly_off(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"some audio")
    monkeypatch.setattr(
        "stashify.download._ffprobe_duration", lambda path: 900.0
    )
    ok, detail = verify_media(target, make_track(213573))
    assert ok is True
    assert "mismatch" in detail


def test_corrupt_ffprobe_failure(monkeypatch, tmp_path):
    target = tmp_path / "track.mp3"
    target.write_bytes(b"definitely not audio")

    def boom(path):
        from stashify.errors import DownloadError

        raise DownloadError("ffprobe could not read")

    monkeypatch.setattr("stashify.download._ffprobe_duration", boom)
    ok, detail = verify_media(target, make_track())
    assert ok is False
    assert "ffprobe" in detail
