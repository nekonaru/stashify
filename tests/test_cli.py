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


def test_url_output_order_preserved(monkeypatch, capsys):
    from stashify.models import Track
    from stashify.sources import Source

    tracks = [Track(title=f"Song {i}", artists=["Artist"]) for i in range(6)]
    monkeypatch.setattr("stashify.cli._fetch", lambda args, urls: tracks)
    monkeypatch.setattr(
        "stashify.cli.find_source",
        lambda track: Source(url=f"https://youtu.be/id{track.title[-1]}", title=track.title),
    )
    code = main(["url", "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"])
    captured = capsys.readouterr().out
    lines = captured.strip().splitlines()
    assert [line.rsplit("id", 1)[-1] for line in lines] == ["0", "1", "2", "3", "4", "5"]
    assert code == 0


def test_url_failure_exit_code(monkeypatch, capsys):
    from stashify.errors import StashifyError
    from stashify.models import Track

    tracks = [Track(title="Song", artists=["Artist"])]
    monkeypatch.setattr("stashify.cli._fetch", lambda args, urls: tracks)

    def boom(track):
        raise StashifyError("no results")

    monkeypatch.setattr("stashify.cli.find_source", boom)
    code = main(["url", "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"])
    assert code == 1
    assert "no results" in capsys.readouterr().out
