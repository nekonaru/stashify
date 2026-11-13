<div align="center">
  <img src="https://raw.githubusercontent.com/nekonaru/stashify/main/assets/stashify-mark.png" alt="Stashify logo" width="120" />
  <h1>Stashify: Spotify Music Downloader</h1>
  <p><b>Find any track, album or playlist from Spotify on YouTube and save it locally<br/>
  with cover art, lyrics and full metadata.</b></p>

  <a href="https://github.com/nekonaru/stashify/releases"><img src="https://img.shields.io/github/v/release/nekonaru/stashify?style=flat-square&color=blue" alt="Release" /></a>
  <a href="https://github.com/nekonaru/stashify/actions/workflows/ci.yml"><img src="https://github.com/nekonaru/stashify/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-555555?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square" alt="Status" />
</div>

<br />

**English** | [Bahasa Indonesia](README.id.md)

> [!NOTE]
> Stashify reads public Spotify pages, no account or login required. It can only see what is public: tracks, albums, artists and public playlists.

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Data Sources](#data-sources)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [FAQ](#faq)
- [Author](#author)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## About

**Stashify** is a command line tool that turns a Spotify link into a properly tagged audio file on your machine. It resolves the link against Spotify's public pages, finds the best matching source for each track on YouTube, converts it with FFmpeg and tags it with title, artists, album, track number, release year, cover art and lyrics.

> _"Your Spotify library, stashed as real files."_

---

## Features

### Download

| Feature | Description |
|---------|-------------|
| **Track, album, playlist, artist** | Public Spotify links resolve to a track list and every track downloads (artist links fetch the artist's top 10 tracks, public playlists show up to 50 tracks) |
| **No account needed** | Metadata comes from Spotify's public embed pages, nothing to create or configure |
| **Best-match source** | YouTube results are scored on duration and word overlap, the strongest match wins |
| **Audio formats** | MP3, M4A, Opus, FLAC or WAV, converted through FFmpeg |
| **Bitrate control** | Choose the bitrate for lossy formats, default `192k` |
| **Skip existing** | Files that already exist are skipped, `--overwrite` forces a re-download |
| **Parallel downloads** | N tracks at a time with `--jobs` (default 2, max 8), faster on large playlists |
| **Dry run** | `--dry-run` prints the matched source per track without downloading anything |

### Metadata

| Feature | Description |
|---------|-------------|
| **Full tagging** | Title, artists, album (when known), album artist (when known), track number (albums), disc numbers, release year, cover art |
| **Cover art** | Original cover embedded, per track for playlists and artists, album cover for albums |
| **Lyrics** | Plain-text lyrics fetched from a community lyrics API and embedded when found |
| **Retag existing files** | `stashify meta` writes the same metadata into files you already have |
| **Path templates** | `{artist} - {title}` style templates, subfolders included, safe for any OS |
| **Save as JSON** | `stashify save` dumps the resolved metadata without downloading audio |

### Sync

| Feature | Description |
|---------|-------------|
| **Playlist sync** | `stashify sync` keeps a folder in sync with a playlist: new songs are downloaded, removed songs are deleted |
| **Self-contained state** | A small `stashify.sync.json` state file tracks which files Stashify downloaded, it never touches files it did not create |

---

## Requirements

| Dependency | Minimum Version | Notes |
|------------|-----------------|-------|
| **Python** | 3.10 | Required |
| **FFmpeg** | 6 | Required for audio conversion |

> [!TIP]
> No Spotify account is required. Only public content (tracks, albums, artists and public playlists) can be resolved; private playlists are not reachable without an official API entitlement.

### Never used a terminal? Start here

<details>
<summary><b>How to open a terminal on your OS</b></summary>

**Windows**

1. Press the **Windows** key, type `PowerShell`, then press **Enter**
2. A blue window opens. That is where you type commands

**macOS**

1. Press **Command** + **Space**, type `Terminal`, then press **Enter**
2. A window with a prompt opens

**Linux**

1. Open your app launcher and type `terminal`, then press **Enter**
2. A window with a prompt opens

Every `stashify ...` command in this guide is typed in that window, followed by **Enter**.

</details>

---

## Installation

### Option A: Install from PyPI (easiest)

1. Make sure Python 3.10 or newer is installed (`python --version` should answer)
2. Make sure FFmpeg is installed (`ffmpeg -version` should answer). If not:
   - Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) or `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (or your distribution's package manager)
3. Install Stashify from PyPI:

```bash
pip install stashify-cli
```

4. Verify the install:

```bash
stashify --version
```

> [!NOTE]
> The PyPI package is `stashify-cli`; the command it installs is `stashify`. If pip cannot find the package on PyPI yet, use Option B.

### Option B: Install directly from GitHub

```bash
pip install git+https://github.com/nekonaru/stashify.git
stashify --version
```

Needs Python 3.10+ and FFmpeg, same as above.

### Option C: Build from source (for development / to read or change the code)

#### 1. Get the project code

<details>
<summary><b>I have Git installed</b></summary>

```bash
git clone https://github.com/nekonaru/stashify.git
cd stashify
```

</details>

<details>
<summary><b>I don't have Git</b></summary>

1. Open the repository page on GitHub
2. Click the green **`Code`** button, choose **`Download ZIP`**
3. Extract the ZIP to a folder of your choice
4. In the terminal, go into the extracted folder, for example:

```bash
cd Downloads/stashify-main
```

</details>

#### 2. Install the dependencies and verify

```bash
python -m pip install -e .[dev]
python -m pytest -q
```

> [!IMPORTANT]
> The test suite must pass before you build or publish anything.

#### 3. Build and check

```bash
python -m ruff check src tests
```

Stashify is a pure Python package. There is no binary to compile; installation is the packaging step.

---

## Usage

### First launch

Stashify needs no account, no login and no API keys. Install it, then download:

1. Find any Spotify link for a track, album, playlist or artist (public content only)
2. Run:

```bash
stashify download "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
```

> [!NOTE]
> The download works for public content only. Private playlists are not reachable: Spotify requires an official API entitlement for that, which Development Mode apps no longer get.

### Everyday use

- Download a single track, an album, a playlist or an artist's top tracks by passing their links to `stashify download`; files land in your Downloads folder by default
- Pick the audio format with `-f mp3|m4a|opus|flac|wav` (default `mp3`)
- Change the output folder with `-o "D:\Music"` and the naming scheme with `-t "{album}/{track_number} {title}"`
- Download up to 8 tracks at once with `--jobs 4` (default 2)
- Skip cover art or lyrics with `--no-cover` / `--no-lyrics`, or re-fetch everything with `--overwrite`
- Preview the match without downloading with `--dry-run`
- Keep a folder in sync with a playlist: `stashify sync "PLAYLIST_URL" -o "D:\Music\MyList"`
- Retag files you already have: `stashify meta file1.mp3 file2.mp3 --url "ALBUM_URL"`
- Export the resolved metadata as JSON: `stashify save "ALBUM_URL" --save-file album.json`
- Print the source URL that would be used per track: `stashify url "PLAYLIST_URL"`

The path template supports `{artist}`, `{artists}`, `{title}`, `{album}`, `{album_artist}`, `{track_number}`, `{disc_number}` and `{release_year}`. Use `/` to create subfolders. Illegal file name characters are removed automatically.

---

## Configuration

Preferences can be stored in a config file; secrets cannot. The default provider needs none.

Config file locations: `%APPDATA%\stashify\config.json` (Windows), `~/.config/stashify/config.json` (macOS and Linux).

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `output_dir` | string | your Downloads folder | Output directory for downloads (Windows: `%USERPROFILE%\Downloads`, macOS and Linux: `~/Downloads` or `XDG_DOWNLOAD_DIR`) |
| `jobs` | integer | `2` | Parallel downloads, between 1 and 8 |
| `audio_format` | string | `mp3` | Default audio format |
| `bitrate` | string | `192k` | Bitrate for lossy formats |
| `template` | string | `{artist} - {title}` | Output path template |
| `market` | string | `US` | Two-letter market code (only used with `--provider api`) |
| `provider` | string | `embed` | `embed` (default, no account) or `api` (official Web API, needs a Premium-entitled developer app) |
| `detailed` | boolean | `true` | Fetch per-track details (artists, cover, release year) for playlists |
| `overwrite` | boolean | `false` | Re-download files that already exist |
| `no_cover` | boolean | `false` | Never embed cover art |
| `no_lyrics` | boolean | `false` | Never embed lyrics |

Command line flags always win over the config file. The default output directory is your Downloads folder; set the `STASHIFY_DOWNLOAD_DIR` environment variable, the `-o` flag or the `output_dir` key to change it.

Use `--provider api` with `--client-id` and `--client-secret` (or `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` environment variables) if you have an official Web API entitlement; it adds ISRC and album metadata for tracks and albums.

---

## Data Sources

Stashify is online only when it resolves metadata, searches for a source or fetches lyrics. Audio is sourced from YouTube.

| Purpose | Source |
|---------|--------|
| Track, album, playlist and artist metadata | Spotify's public embed pages (default) or the Spotify Web API (`--provider api`) |
| Cover art | Spotify image CDN (embedded into files) |
| Audio source | YouTube, through yt-dlp |
| Lyrics | lyrics.ovh (no key required) |

> [!NOTE]
> Some tracks have no usable match on YouTube. Stashify reports the best candidate it found and skips tracks whose score is too low instead of downloading the wrong song.

---

## Project Structure

```
stashify/
├── src/
│   └── stashify/
│       ├── __init__.py           # package version
│       ├── __main__.py           # python -m stashify entry point
│       ├── cli.py                # argument parsing and commands
│       ├── pipeline.py           # shared download pipeline
│       ├── spotify.py            # Spotify Web API client (optional, --provider api)
│       ├── embed.py              # public embed page resolver (default provider)
│       ├── models.py             # Track data model
│       ├── sources.py            # YouTube search and scoring
│       ├── download.py           # yt-dlp download and FFmpeg conversion
│       ├── tagger.py             # MP3, M4A, FLAC, Opus and WAV tagging
│       ├── lyrics.py             # lyrics.ovh client
│       ├── output.py             # path templates and file naming
│       ├── sync.py               # playlist sync state handling
│       ├── config.py             # config file loading
│       └── errors.py             # error types
├── tests/                        # pytest suite (offline, network mocked)
├── assets/                       # logo and icons
├── .github/
│   └── workflows/
│       ├── ci.yml                # lint and tests on every push
│       ├── publish.yml           # publish to PyPI on demand (OIDC)
│       └── release.yml           # draft release from changelog on tags
├── pyproject.toml                # packaging and tool configuration
├── SECURITY.md                   # vulnerability reporting policy
├── LICENSE
├── README.md                     # main documentation (English)
└── README.id.md                  # documentation (Bahasa Indonesia)
```

---

## Development

### Publishing to PyPI

One-time setup, done by the maintainer on PyPI:

1. Open [pypi.org](https://pypi.org), sign in, go to **Account → Publishing**
2. Add a pending publisher with these exact values:
   - Project name: `stashify-cli`
   - Owner: `nekonaru`
   - Repository: `stashify`
   - Workflow name: `publish.yml`
   - Environment name: leave empty
3. Push a release tag, then run **Publish** from the Actions tab on the tag you want to release

The workflow builds the wheel and sdist, checks them with `twine check`, smoke tests the wheel and publishes via OIDC. No API token is stored anywhere.

> [!WARNING]
> Stashify is distributed on PyPI as `stashify-cli` because the name `stashify` already belongs to someone else. Do not try to claim it.

### Working on the code

1. Install the package in editable mode with the dev extras: `python -m pip install -e .[dev]`
2. Make your change
3. Run the checks: `python -m ruff check src tests` and `python -m pytest -q`

### Adding a new supported audio format

1. Add the format to `AUDIO_FORMATS` in `src/stashify/download.py` and to `_CODEC_MAP`
2. Add a tagging path in `src/stashify/tagger.py` (see `_tag_flac` for an example)
3. Add a test that renders and retags a short file with FFmpeg, see `tests/test_tagger.py`

> [!WARNING]
> `assets/` is committed. Do not commit downloaded audio, cover art from real releases, or your config file. Anything that looks like personal media stays out of the repository.

---

## Testing

Verification before every push, both must be clean:

```bash
python -m ruff check src tests
python -m pytest -q
```

| Check | Requirement |
|-------|-------------|
| `python -m ruff check src tests` | Must report **All checks passed** (zero errors, zero warnings) |
| `python -m pytest -q` | Must pass the full suite |

Lint rules are enforced through the `[tool.ruff]` section in `pyproject.toml`.

---

## Continuous Integration

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Ruff and the test suite on Python 3.10 and 3.12, on every push and pull request |
| `release.yml` | Test suite plus a draft GitHub release built from the changelogs, on tags `v*` |

---

## FAQ

<details>
<summary><b>Do I need a Spotify account, login or developer app?</b></summary>

No. The default provider reads Spotify's public pages, exactly what a browser sees without logging in. Nothing to create, nothing to log into, nothing to leak.

</details>

<details>
<summary><b>Why does my private playlist fail?</b></summary>

Public pages only exist for public content. If the playlist is private, the embed page shows a not-found page and Stashify reports it. Making the playlist public fixes it. Alternatively, official API access to your own playlists requires a Premium-entitled developer app, then `stashify ... --provider api` with your own credentials.

</details>

<details>
<summary><b>Why is some metadata missing (ISRC, album name)?</b></summary>

Public pages do not carry every field. Stashify tags what is available: title, artists, duration, release year, cover art, album name and track numbers for albums. ISRC is only available through the official Web API.

</details>

<details>
<summary><b>Some songs are skipped or fail to download. Why?</b></summary>

Either there is no usable match on YouTube (unreleased tracks, very obscure remixes, private uploads) or yt-dlp needs an update, because YouTube changes frequently. Run `pip install --upgrade yt-dlp` and try again.

</details>

<details>
<summary><b>The wrong version of a song gets downloaded. What can I do?</b></summary>

The scorer strongly prefers duration-matched audio with "official" in the title and rejects karaoke, covers and live versions unless you ask for them. Use `--dry-run` first; if the match keeps coming out wrong, open an issue with the Spotify link.

</details>

<details>
<summary><b>A file already exists. Will it be overwritten?</b></summary>

No. Existing files are skipped. Pass `--overwrite` to re-download them.

</details>

<details>
<summary><b>Can I keep my library folder in sync with a Spotify playlist?</b></summary>

Yes. `stashify sync "PLAYLIST_URL" -o "D:\Music\MyList"` downloads new tracks and deletes only the files that Stashify downloaded and that have since disappeared from the playlist. Everything else in the folder is untouched.

</details>

---

## Author

<div align="center">

| [![Nicolas Dwi Dharma](https://github.com/nekonaru.png?size=100)](https://github.com/nekonaru) |
|:---:|
| **Nicolas Dwi Dharma** |
| [github.com/nekonaru](https://github.com/nekonaru) |

</div>

---

## Disclaimer

Stashify is an independent open-source project and is not affiliated with or endorsed by Spotify, Google, YouTube or the operators of lyrics.ovh. The default provider parses Spotify's public embed pages; this is not a documented API and can change or break at any time. Downloading music may violate the terms of service of those platforms and may infringe copyright in your jurisdiction. Stashify is provided for personal, lawful use only; you are responsible for how you use it.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
