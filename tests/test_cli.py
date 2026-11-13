import pytest

from stashify.cli import main


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "download" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "stashify" in capsys.readouterr().out


def test_missing_command():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_save_api_without_credentials(monkeypatch, capsys):
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    code = main([
        "save",
        "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "--provider", "api",
    ])
    assert code == 1
    captured = capsys.readouterr()
    assert "credentials" in (captured.err + captured.out).lower()


def test_meta_api_without_credentials(monkeypatch, capsys):
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    code = main([
        "meta",
        "song.mp3",
        "--url",
        "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "--provider", "api",
    ])
    assert code == 1
