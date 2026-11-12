# Changelog

All notable changes to Stashify are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0

Stashify resolves any Spotify link to a properly tagged audio file on your machine, sourced from YouTube.

### New features

- **Download command.** Track, album, playlist and artist links download to local files as MP3, M4A, Opus, FLAC or WAV, with cover art, lyrics, album, track number, release year and ISRC written into the tags.
- **Best-match source.** YouTube candidates are scored on duration and word overlap, low-scoring matches are rejected instead of downloaded.
- **Save command.** Dump the resolved metadata for a link as JSON without downloading audio.
- **URL command.** Print the matched source URL per track for inspection.
- **Meta command.** Retag existing audio files with the metadata from a Spotify link, in file order.
- **Sync command.** Keep a folder in sync with a playlist through a `stashify.sync.json` state file, new tracks are downloaded and removed tracks are deleted, everything else is untouched.
- **Path templates.** Output names come from a template with `{artist}`, `{title}` and friends, subfolders included, illegal characters removed automatically.
- **Dry run.** `--dry-run` prints the matched source per track without downloading anything.
- **Config file.** Non-secret preferences live in a per-user `config.json`, command line flags always win.

### Improvements

- **Safe file naming.** Template segments are sanitized for every supported OS and collisions are handled predictably.
- **Security policy.** `SECURITY.md` published, with credentials read from the environment only.
- **CI.** Ruff and the pytest suite run on Python 3.10 and 3.12 on every push and pull request.
