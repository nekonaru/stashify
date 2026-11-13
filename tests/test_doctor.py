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
