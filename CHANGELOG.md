# Changelog

All notable changes to Stashify are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.3.0

Stashify now ships as a properly packaged PyPI distribution, ready to publish with a trusted publisher.

### New features

- **PyPI packaging.** Stashify is distributed on PyPI as `stashify-cli` (the name `stashify` already belongs to someone else). The `stashify` command and import name are unchanged; `pip install stashify-cli` is the new recommended install.

### Improvements

- **Trusted publishing.** A manual publish workflow builds the wheel and sdist, checks them with `twine check`, smoke tests the wheel and publishes over OIDC without any stored API token.
- **Complete metadata.** Project URLs, SPDX license expression, license file and classifiers set; PyPI now renders the full README.
- **Pre-commit hook.** Optional `.pre-commit-config.yaml` runs ruff and gitleaks before each commit.

### Usage

Until the first PyPI publish (one-time maintainer setup, then run **Publish** from the Actions tab on the tag):

```bash
pip install git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

After the package is live on PyPI:

```bash
pip install stashify-cli
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.2.1

Internal audit: every entry point re-checked, real end-to-end downloads verified, security pass re-run.

### Bug fixes

- **Sync state portability.** `stashify.sync.json` stores forward slashes, and older files with OS backslashes are read correctly, so deletes never silently fail after a folder is moved between OSes.
- **Bitrate validation.** `--bitrate` now rejects malformed values up front instead of feeding them to the converter.
- **Clear error for unwritable output.** Writing `--save-file` to an unwritable path now reports a clear error instead of a raw OS traceback.

### Improvements

- **Parallel and ordered URL lookup.** `stashify url` resolves tracks in parallel and keeps the input order.
- **Deeper JSON hardening.** RecursionError from deeply nested embed pages produces a clear error, and WAV tagging is covered by a round trip test.

### Usage

```bash
pip install --upgrade git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.2.0

Downloads now land in the operating system's Downloads folder, and large playlists download in parallel.

### New features

- **Parallel downloads.** `--jobs N` downloads up to 8 tracks at once, default 2, results are written in input order and duplicate target names never clobber each other.
- **Fallback search.** If YouTube returns nothing for `artist - title`, Stashify retries without the dash and with `audio` appended before giving up.

### Improvements

- **Downloads folder default.** Output defaults to the OS downloads folder (`%USERPROFILE%\Downloads` on Windows, `~/Downloads` or `XDG_DOWNLOAD_DIR` on macOS and Linux), override with `-o`, `output_dir` or `STASHIFY_DOWNLOAD_DIR`.
- **Output location printed.** Every run prints `Saving to:` so the destination is always visible.
- **Parallel metadata.** Per-track detail lookups and metadata enrichment run four at a time.

### Usage

```bash
pip install --upgrade git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.1.0

Stashify works out of the box with any Spotify account: metadata now comes from Spotify's public pages, no developer app or Premium needed.

### New features

- **Embed provider.** Metadata is read from Spotify's public embed pages, so tracks, albums, artist top tracks and public playlists resolve without an account, login or API key.
- **Per-track enrichment.** Artists, release year and cover art are resolved per track for playlists, disable with `--no-details`.

### Improvements

- **Public-page diagnostics.** Private or removed links now produce a clear message instead of a silent failure.
- **Official API updated.** February 2026 Web API changes are applied: playlists and artist top tracks are rejected with guidance on `--provider api` (tracks and albums still work there), and 403 responses now include the server's message.

### Usage

```bash
pip install --upgrade git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

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
- **CI.** Ruff and the test suite run on Python 3.10 and 3.12 on every push and pull request.

### Usage

```bash
pip install git+https://github.com/nekonaru/stashify.git
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```
