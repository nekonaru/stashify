from stashify import doctor


def test_doctor_all_pass(monkeypatch, capsys):
    monkeypatch.setattr(doctor, "check_python", lambda: ("py", True, "ok"))
    monkeypatch.setattr(doctor, "check_ffmpeg", lambda: ("ffmpeg", True, "ok"))
    monkeypatch.setattr(doctor, "check_ffprobe", lambda: ("ffprobe", True, "ok"))
    monkeypatch.setattr(doctor, "check_download_dir", lambda: ("dir", True, "ok"))
    monkeypatch.setattr(doctor, "check_spotify_embed", lambda: ("embed", True, "ok"))
    monkeypatch.setattr(doctor, "check_youtube", lambda: ("yt", True, "ok"))
    monkeypatch.setattr(doctor, "check_lyrics_api", lambda: ("lyrics", True, "ok"))
    assert doctor.run_doctor() == 0
    out = capsys.readouterr().out
    assert "All 7 checks passed" in out


def test_download_dir_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "stashify.doctor.default_download_dir", lambda: tmp_path / "nope"
    )
    _, ok, detail = doctor.check_download_dir()
    assert ok is False
    assert "does not exist" in detail


def test_lyrics_api_404_is_up(monkeypatch):
    class Resp:
        status_code = 404

    monkeypatch.setattr(doctor.requests, "get", lambda *a, **k: Resp())
    _, ok, detail = doctor.check_lyrics_api()
    assert ok is True
    assert "not found" in detail


def test_doctor_reports_failures(monkeypatch, capsys):
    monkeypatch.setattr(doctor, "check_python", lambda: ("py", True, "ok"))
    monkeypatch.setattr(doctor, "check_ffmpeg", lambda: ("ffmpeg", False, "missing"))
    monkeypatch.setattr(doctor, "check_ffprobe", lambda: ("ffprobe", True, "ok"))
    monkeypatch.setattr(doctor, "check_download_dir", lambda: ("dir", False, "read-only"))
    monkeypatch.setattr(doctor, "check_spotify_embed", lambda: ("embed", True, "ok"))
    monkeypatch.setattr(doctor, "check_youtube", lambda: ("yt", False, "bot check"))
    monkeypatch.setattr(doctor, "check_lyrics_api", lambda: ("lyrics", True, "ok"))
    assert doctor.run_doctor() == 1
    out = capsys.readouterr().out
    assert "3 of 7 checks failed" in out
