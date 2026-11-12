<div align="center">
  <img src="assets/stashify-mark.png" alt="Stashify logo" width="120" />
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
> Stashify reads your Spotify library through the official Spotify Web API, using your own free developer app. It never asks for your Spotify password.

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

**Stashify** is a command line tool that turns a Spotify link into a properly tagged audio file on your machine. It resolves the link against the Spotify Web API, finds the best matching source for each track on YouTube, converts it with FFmpeg and tags it with title, artists, album, track number, release date, ISRC, cover art and lyrics.

> _"Your Spotify library, stashed as real files."_

---

## Features

### Download

| Feature | Description |
|---------|-------------|
| **Track, album, playlist, artist** | Any Spotify link resolves to a full track list and downloads everything in it |
| **Best-match source** | YouTube results are scored on duration and word overlap, the strongest match wins |
| **Audio formats** | MP3, M4A, Opus, FLAC or WAV, converted through FFmpeg |
| **Bitrate control** | Choose the bitrate for lossy formats, default `192k` |
| **Skip existing** | Files that already exist are skipped, `--overwrite` forces a re-download |
| **Dry run** | `--dry-run` prints the matched source per track without downloading anything |

### Metadata

| Feature | Description |
|---------|-------------|
| **Full tagging** | Title, artists, album, album artist, track and disc numbers, release year, ISRC |
| **Cover art** | Original cover is embedded when available |
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
| **Spotify developer app** | n/a | Free, required to read metadata |

> [!TIP]
> You do not need a Spotify Premium account. Any free account can create the developer app used for metadata.

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

### Option A: Install directly with pip (easiest)

1. Make sure Python 3.10 or newer is installed (`python --version` should answer)
2. Make sure FFmpeg is installed (`ffmpeg -version` should answer). If not:
   - Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) or `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (or your distribution's package manager)
3. Install Stashify:

```bash
pip install git+https://github.com/nekonaru/stashify.git
```

4. Verify the install:

```bash
stashify --version
```

### Option B: Build from source (for development / to read or change the code)

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

Stashify reads metadata from the Spotify Web API, which needs a free developer app:

1. Go to the [Spotify developer dashboard](https://developer.spotify.com/dashboard) and create an app (any name works)
2. Copy the app's **Client ID** and **Client Secret**
3. Expose them to your shell (do not paste them into files that get committed):

```bash
# Windows (PowerShell)
$env:SPOTIFY_CLIENT_ID = "your-client-id"
$env:SPOTIFY_CLIENT_SECRET = "your-client-secret"

# macOS and Linux (bash)
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
```

4. Download your first playlist:

```bash
stashify download "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
```

> [!NOTE]
> The credentials stay in your shell environment. Stashify never writes them to disk and never logs them.

### Everyday use

- Download a single track, an album, a playlist or an artist's top tracks by passing their links to `stashify download`
- Pick the audio format with `-f mp3|m4a|opus|flac|wav` (default `mp3`)
- Change the output folder with `-o "D:\Music"` and the naming scheme with `-t "{album}/{track_number} {title}"`
- Skip cover art or lyrics with `--no-cover` / `--no-lyrics`, or re-fetch everything with `--overwrite`
- Preview the match without downloading with `--dry-run`
- Keep a folder in sync with a playlist: `stashify sync "PLAYLIST_URL" -o "D:\Music\MyList"`
- Retag files you already have: `stashify meta file1.mp3 file2.mp3 --url "ALBUM_URL"`
- Export the resolved metadata as JSON: `stashify save "ALBUM_URL" --save-file album.json`
- Print the source URL that would be used per track: `stashify url "PLAYLIST_URL"`

The path template supports `{artist}`, `{artists}`, `{title}`, `{album}`, `{album_artist}`, `{track_number}`, `{disc_number}` and `{release_year}`. Use `/` to create subfolders. Illegal file name characters are removed automatically.

---

## Configuration

Preferences can be stored in a config file; secrets cannot. Credentials are read from the environment or from `--client-id` / `--client-secret` flags only.

Config file locations: `%APPDATA%\stashify\config.json` (Windows), `~/.config/stashify/config.json` (macOS and Linux).

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `output_dir` | string | `.` | Output directory for downloads |
| `audio_format` | string | `mp3` | Default audio format |
| `bitrate` | string | `192k` | Bitrate for lossy formats |
| `template` | string | `{artist} - {title}` | Output path template |
| `market` | string | `US` | Two-letter market code used for Spotify lookups |
| `overwrite` | boolean | `false` | Re-download files that already exist |
| `no_cover` | boolean | `false` | Never embed cover art |
| `no_lyrics` | boolean | `false` | Never embed lyrics |

Command line flags always win over the config file.

---

## Data Sources

Stashify is online only when it resolves metadata, searches for a source or fetches lyrics. Audio is sourced from YouTube.

| Purpose | Source |
|---------|--------|
| Track, album, playlist and artist metadata | Spotify Web API (your own developer app) |
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
│       ├── spotify.py            # Spotify Web API client
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
│       └── release.yml           # draft release from changelog on tags
├── pyproject.toml                # packaging and tool configuration
├── SECURITY.md                   # vulnerability reporting policy
├── LICENSE
├── README.md                     # main documentation (English)
└── README.id.md                  # documentation (Bahasa Indonesia)
```

---

## Development

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
<summary><b>Do I need Spotify Premium or a login?</b></summary>

No. Metadata is read through the official Web API with a free developer app you create yourself. Stashify never sees your password.

</details>

<details>
<summary><b>Is my client secret safe?</b></summary>

Yes. Stashify reads it from the environment or from command line flags, never from files it writes. Do not commit it, do not share it. If it leaks, rotate it in the dashboard.

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

Stashify is an independent open-source project and is not affiliated with or endorsed by Spotify, Google, YouTube or the operators of lyrics.ovh. Downloading music may violate the terms of service of those platforms and may infringe copyright in your jurisdiction. Stashify is provided for personal, lawful use only; you are responsible for how you use it.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
