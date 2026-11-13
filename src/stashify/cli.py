"""Stashify command line interface."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import __version__
from .config import (
    DEFAULT_BITRATE,
    DEFAULT_FORMAT,
    DEFAULT_JOBS,
    DEFAULT_TEMPLATE,
    clamp_jobs,
    default_download_dir,
    load_config,
)
from .download import AUDIO_FORMATS
from .embed import EmbedResolver
from .errors import StashifyError
from .lyrics import fetch_lyrics
from .models import Track
from .pipeline import TrackOptions, process_tracks, summarize
from .sources import find_source
from .spotify import SpotifyClient, client_credentials_from_env
from .sync import load_state, plan_sync, remove_entries, save_state, state_entry
from .tagger import fetch_cover, tag_file

LOG = logging.getLogger("stashify")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stashify",
        description="Find music from your Spotify library on YouTube and save it locally.",
    )
    parser.add_argument("--version", action="version", version=f"stashify {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug output")

    credentials = argparse.ArgumentParser(add_help=False)
    credentials.add_argument(
        "--client-id", default=None,
        help="Spotify app client id (env: SPOTIFY_CLIENT_ID)",
    )
    credentials.add_argument(
        "--client-secret", default=None,
        help="Spotify app client secret (env: SPOTIFY_CLIENT_SECRET)",
    )
    credentials.add_argument(
        "--market", default=None,
        help="two-letter market code (default: US)",
    )

    output = argparse.ArgumentParser(add_help=False)
    output.add_argument(
        "-o", "--output", default=None,
        help="output directory (default: Downloads folder)"
    )
    output.add_argument(
        "-t", "--template", default=None,
        help=f"path template (default: {DEFAULT_TEMPLATE!r})",
    )
    output.add_argument(
        "-f", "--format", dest="audio_format", choices=sorted(AUDIO_FORMATS),
        default=None, help=f"audio format (default: {DEFAULT_FORMAT})",
    )
    output.add_argument(
        "--bitrate", default=None,
        help=f"bitrate for lossy formats (default: {DEFAULT_BITRATE})",
    )
    output.add_argument(
        "--overwrite", action="store_true", default=None,
        help="re-download files that already exist",
    )
    output.add_argument(
        "--no-cover", action="store_true", default=None,
        help="do not embed cover art",
    )
    output.add_argument(
        "--no-lyrics", action="store_true", default=None,
        help="do not embed lyrics",
    )
    output.add_argument(
        "--dry-run", action="store_true", default=None,
        help="print matches without downloading",
    )
    output.add_argument(
        "--provider", choices=["embed", "api"], default=None,
        help="metadata provider (default: embed, no account needed)",
    )
    output.add_argument(
        "--no-details", action="store_true", default=None,
        help="skip per-track detail lookup (faster, fewer cover art files)",
    )
    output.add_argument(
        "--jobs", type=int, default=None, metavar="N",
        help=f"download up to N tracks in parallel (default: {DEFAULT_JOBS}, max 8)",
    )

    sub = parser.add_subparsers(dest="command", metavar="command", required=True)

    p_download = sub.add_parser(
        "download", parents=[credentials, output],
        help="download tracks, albums or playlists",
    )
    p_download.add_argument(
        "urls", nargs="+", help="Spotify track, album, playlist or artist links"
    )

    p_save = sub.add_parser(
        "save", parents=[credentials, output],
        help="save track metadata as JSON without downloading",
    )
    p_save.add_argument("urls", nargs="+", help="Spotify links")
    p_save.add_argument(
        "--save-file", default=None,
        help="where to write the JSON (default: stdout)",
    )

    p_url = sub.add_parser(
        "url", parents=[credentials],
        help="print the matched YouTube source URL per track",
    )
    p_url.add_argument("urls", nargs="+", help="Spotify links")

    p_meta = sub.add_parser(
        "meta", parents=[credentials, output],
        help="write metadata into existing audio files",
    )
    p_meta.add_argument("files", nargs="+", help="audio files, in track order")
    p_meta.add_argument(
        "--url", required=True, help="Spotify link whose tracks are applied"
    )

    p_sync = sub.add_parser(
        "sync", parents=[credentials, output],
        help="sync a directory with a playlist",
    )
    p_sync.add_argument("url", help="playlist, album or artist link")
    p_sync.add_argument(
        "--state", default=None,
        help="state file (default: <output>/stashify.sync.json)",
    )

    return parser


def _client(args: argparse.Namespace) -> SpotifyClient:
    config = load_config()
    market = args.market or config.get("market") or "US"
    client_id_flag = getattr(args, "client_id", None)
    client_secret_flag = getattr(args, "client_secret", None)
    if client_id_flag or client_secret_flag:
        if not client_id_flag or not client_secret_flag:
            raise StashifyError(
                "Pass both --client-id and --client-secret, "
                "or neither to read them from the environment."
            )
        client_id, client_secret = client_id_flag, client_secret_flag
    else:
        client_id, client_secret = client_credentials_from_env()
    return SpotifyClient(client_id=client_id, client_secret=client_secret, market=market)


def _resolver(args: argparse.Namespace):
    config = load_config()
    provider = getattr(args, "provider", None) or config.get("provider", "embed")
    if provider == "embed":
        no_details = bool(getattr(args, "no_details", False))
        detailed = False if no_details else bool(config.get("detailed", True))
        return EmbedResolver(detailed=detailed)
    if provider == "api":
        return _client(args)
    raise StashifyError(f"Unknown provider {provider!r}. Choose from: embed, api.")


def _options(args: argparse.Namespace) -> TrackOptions:
    config = load_config()

    def pick(cli, key, default):
        if cli is not None:
            return cli
        return config.get(key, default)

    no_cover = pick(getattr(args, "no_cover", None), "no_cover", False)
    no_lyrics = pick(getattr(args, "no_lyrics", None), "no_lyrics", False)
    return TrackOptions(
        out_dir=Path(
            pick(getattr(args, "output", None), "output_dir", str(default_download_dir()))
        ),
        template=pick(getattr(args, "template", None), "template", DEFAULT_TEMPLATE),
        audio_format=pick(getattr(args, "audio_format", None), "audio_format", DEFAULT_FORMAT),
        bitrate=pick(getattr(args, "bitrate", None), "bitrate", DEFAULT_BITRATE),
        overwrite=bool(pick(getattr(args, "overwrite", None), "overwrite", False)),
        dry_run=bool(pick(getattr(args, "dry_run", None), "dry_run", False)),
        embed_cover=not no_cover,
        embed_lyrics=not no_lyrics,
        jobs=clamp_jobs(pick(getattr(args, "jobs", None), "jobs", DEFAULT_JOBS)),
    )


def _fetch(args: argparse.Namespace, urls: list[str]) -> list[Track]:
    resolver = _resolver(args)
    tracks: list[Track] = []
    for url in urls:
        tracks.extend(resolver.fetch_tracks(url))
    return tracks


def _cmd_download(args: argparse.Namespace) -> int:
    tracks = _fetch(args, args.urls)
    if not tracks:
        print("No tracks found for the given links.")
        return 1
    options = _options(args)
    print(f"Saving to: {options.out_dir}")
    results = process_tracks(tracks, options)
    counts = summarize(results)
    print(
        f"Done: {counts['downloaded']} downloaded, {counts['skipped']} skipped, "
        f"{counts['failed']} failed."
    )
    return 1 if counts["failed"] else 0


def _cmd_save(args: argparse.Namespace) -> int:
    tracks = _fetch(args, args.urls)
    payload = json.dumps([t.to_dict() for t in tracks], indent=2, ensure_ascii=False)
    if args.save_file:
        save_path = Path(args.save_file)
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(payload + "\n", encoding="utf-8")
        except OSError as exc:
            raise StashifyError(f"Could not write {save_path}: {exc}") from exc
        print(f"Saved {len(tracks)} track(s) to {args.save_file}")
    else:
        print(payload)
    return 0


def _cmd_url(args: argparse.Namespace) -> int:
    tracks = _fetch(args, args.urls)

    def work(index: int, track: Track) -> tuple[int, str, bool]:
        try:
            source = find_source(track)
        except StashifyError as exc:
            return index, f"{track.display()} - not found: {exc}", False
        return index, f"{track.display()} - {source.url}", True

    total = len(tracks)
    rows: list[tuple[str, bool] | None] = [None] * total
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index, line, ok in pool.map(work, range(total), tracks):
            rows[index] = (line, ok)
    failures = 0
    for row in rows:
        assert row is not None
        line, ok = row
        print(line)
        if not ok:
            failures += 1
    return 1 if failures else 0


def _cmd_meta(args: argparse.Namespace) -> int:
    config = load_config()
    tracks = _fetch(args, [args.url])
    files = [Path(f) for f in args.files]
    missing = [f for f in files if not f.is_file()]
    if missing:
        for f in missing:
            print(f"File not found: {f}")
        return 1
    limit = min(len(files), len(tracks))
    if len(files) != len(tracks):
        print(
            f"Warning: {len(files)} file(s) given but {len(tracks)} track(s) "
            f"found; tagging the first {limit}."
        )
    failures = 0
    for path, track in zip(files, tracks, strict=False):
        try:
            cover = fetch_cover(track) if not config.get("no_cover") else None
            lyrics = fetch_lyrics(track) if not config.get("no_lyrics") else None
            tag_file(path, track, cover, lyrics)
            print(f"Tagged {path} -> {track.display()}")
        except Exception as exc:
            failures += 1
            print(f"Could not tag {path}: {exc}")
    return 1 if failures else 0


def _cmd_sync(args: argparse.Namespace) -> int:
    options = _options(args)
    out_dir = options.out_dir
    state_path = Path(args.state) if args.state else out_dir / "stashify.sync.json"
    tracks = _fetch(args, [args.url])
    state = load_state(state_path)
    state["url"] = args.url
    missing, removed = plan_sync(state, tracks)
    print(f"Syncing: {out_dir}")

    deleted = remove_entries(removed, out_dir)
    for path in deleted:
        print(f"Removed (no longer in playlist): {path}")

    if missing:
        results = process_tracks(missing, options)
        for result in results:
            if result.status == "downloaded" and result.path:
                key = state_entry(result.track, result.path, out_dir)["key"]
                state["entries"] = [
                    e for e in state["entries"] if e.get("key") != key
                ]
                state["entries"].append(
                    state_entry(result.track, result.path, out_dir)
                )
    else:
        print("Directory is already in sync.")

    removed_keys = {e.get("key") for e in removed}
    state["entries"] = [e for e in state["entries"] if e.get("key") not in removed_keys]
    save_state(state_path, state)

    counts_failed = 0
    if missing:
        counts_failed = sum(1 for r in results if r.status == "failed")
    print(
        f"Sync complete: {len(missing)} to download, {len(removed)} removed, "
        f"{len(tracks)} track(s) now in the playlist."
    )
    return 1 if counts_failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    handlers = {
        "download": _cmd_download,
        "save": _cmd_save,
        "url": _cmd_url,
        "meta": _cmd_meta,
        "sync": _cmd_sync,
    }
    handler = handlers[args.command]
    try:
        return handler(args)
    except StashifyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # Never leak a traceback unless asked for one.
        if args.verbose:
            raise
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
