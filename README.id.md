<div align="center">
  <img src="assets/stashify-mark.png" alt="Stashify logo" width="120" />
  <h1>Stashify: Spotify Music Downloader</h1>
  <p><b>Temukan track, album, atau playlist apa pun dari Spotify di YouTube dan simpan secara lokal<br/>
  dengan cover art, lirik dan metadata lengkap.</b></p>

  <a href="https://github.com/nekonaru/stashify/releases"><img src="https://img.shields.io/github/v/release/nekonaru/stashify?style=flat-square&color=blue" alt="Release" /></a>
  <a href="https://github.com/nekonaru/stashify/actions/workflows/ci.yml"><img src="https://github.com/nekonaru/stashify/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-555555?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square" alt="Status" />
</div>

<br />

[English](README.md) | **Bahasa Indonesia**

> [!NOTE]
> Stashify membaca library Spotify kamu lewat Spotify Web API resmi, memakai developer app milikmu yang gratis. Stashify tidak pernah meminta password Spotify.

---

## Table of Contents

- [Tentang](#tentang)
- [Fitur](#fitur)
- [Kebutuhan](#kebutuhan)
- [Instalasi](#instalasi)
- [Penggunaan](#penggunaan)
- [Konfigurasi](#konfigurasi)
- [Sumber Data](#sumber-data)
- [Struktur Proyek](#struktur-proyek)
- [Pengembangan](#pengembangan)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [FAQ](#faq)
- [Author](#author)
- [Disclaimer](#disclaimer)
- [Lisensi](#lisensi)

---

## Tentang

**Stashify** adalah command line tool yang mengubah link Spotify menjadi audio file dengan tag metadata lengkap di mesin kamu. Stashify me-resolve link lewat Spotify Web API, menemukan source yang paling cocok untuk tiap track di YouTube, mengonversi dengan FFmpeg, lalu menulis tag: title, artists, album, nomor track, tanggal rilis, ISRC, cover art dan lirik.

> _"Library Spotify-mu, tersimpan rapi sebagai file asli."_

---

## Fitur

### Unduhan

| Fitur | Deskripsi |
|---------|-------------|
| **Track, album, playlist, artist** | Link Spotify apa pun di-resolve menjadi daftar track lengkap dan langsung diunduh semua |
| **Source terbaik** | Hasil pencarian YouTube dinilai dari kecocokan durasi dan kata, skor tertinggi yang dipilih |
| **Format audio** | MP3, M4A, Opus, FLAC atau WAV, dikonversi lewat FFmpeg |
| **Bitrate control** | Bitrate bisa dipilih untuk format lossy, default `192k` |
| **Skip existing** | File yang sudah ada dilewati, `--overwrite` memaksa unduh ulang |
| **Dry run** | `--dry-run` mencetak source yang dipilih per track tanpa mengunduh apa pun |

### Metadata

| Fitur | Deskripsi |
|---------|-------------|
| **Full tagging** | Title, artists, album, album artist, nomor track dan disc, tahun rilis, ISRC |
| **Cover art** | Cover asli disematkan saat tersedia |
| **Lirik** | Lirik plain-text dari community lyrics API dan disematkan saat ditemukan |
| **Retag existing files** | `stashify meta` menulis metadata yang sama ke file yang sudah kamu punya |
| **Path templates** | Template gaya `{artist} - {title}`, termasuk subfolder, aman untuk semua OS |
| **Save as JSON** | `stashify save` dump metadata tanpa mengunduh audio |

### Sync

| Fitur | Deskripsi |
|---------|-------------|
| **Playlist sync** | `stashify sync` menjaga folder tetap sinkron dengan playlist: lagu baru diunduh, lagu yang hilang dihapus |
| **Self-contained state** | State file `stashify.sync.json` melacak file mana yang diunduh Stashify; file yang bukan buatan Stashify tidak pernah disentuh |

---

## Kebutuhan

| Dependency | Versi Minimum | Catatan |
|------------|-----------------|-------|
| **Python** | 3.10 | Wajib |
| **FFmpeg** | 6 | Wajib untuk konversi audio |
| **Spotify developer app** | n/a | Gratis, wajib untuk membaca metadata |

> [!TIP]
> Kamu tidak butuh akun Spotify Premium. Akun gratis apa pun bisa membuat developer app yang dipakai untuk metadata.

### Belum pernah pakai terminal? Mulai dari sini

<details>
<summary><b>Cara membuka terminal di OS kamu</b></summary>

**Windows**

1. Tekan tombol **Windows**, ketik `PowerShell`, lalu tekan **Enter**
2. Jendela biru terbuka. Di situlah kamu mengetik perintah

**macOS**

1. Tekan **Command** + **Space**, ketik `Terminal`, lalu tekan **Enter**
2. Jendela dengan prompt terbuka

**Linux**

1. Buka app launcher, ketik `terminal`, lalu tekan **Enter**
2. Jendela dengan prompt terbuka

Setiap perintah `stashify ...` di panduan ini diketik di jendela tersebut, diikuti **Enter**.

</details>

---

## Instalasi

### Opsi A: Install langsung dengan pip (paling mudah)

1. Pastikan Python 3.10 atau lebih baru terpasang (`python --version` harus menjawab)
2. Pastikan FFmpeg terpasang (`ffmpeg -version` harus menjawab). Jika belum:
   - Windows: unduh dari [ffmpeg.org](https://ffmpeg.org/download.html) atau `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (atau package manager distribusi kamu)
3. Install Stashify:

```bash
pip install git+https://github.com/nekonaru/stashify.git
```

4. Verifikasi instalasi:

```bash
stashify --version
```

### Opsi B: Build dari source (untuk development / untuk membaca atau mengubah kode)

#### 1. Ambil kode proyek

<details>
<summary><b>Saya punya Git</b></summary>

```bash
git clone https://github.com/nekonaru/stashify.git
cd stashify
```

</details>

<details>
<summary><b>Saya tidak punya Git</b></summary>

1. Buka halaman repository di GitHub
2. Klik tombol hijau **`Code`**, pilih **`Download ZIP`**
3. Ekstrak ZIP ke folder pilihan kamu
4. Di terminal, masuk ke folder hasil ekstraksi, misalnya:

```bash
cd Downloads/stashify-main
```

</details>

#### 2. Install dependency dan verifikasi

```bash
python -m pip install -e .[dev]
python -m pytest -q
```

> [!IMPORTANT]
> Test suite harus lolos sebelum kamu build atau publish apa pun.

#### 3. Build dan cek

```bash
python -m ruff check src tests
```

Stashify adalah pure Python package. Tidak ada binary yang dikompilasi; instalasi adalah langkah packaging-nya.

---

## Penggunaan

### Pertama kali

Stashify membaca metadata dari Spotify Web API, yang membutuhkan developer app gratis:

1. Buka [Spotify developer dashboard](https://developer.spotify.com/dashboard) dan buat app (nama bebas)
2. Salin **Client ID** dan **Client Secret** app tersebut
3. Ekspose ke shell kamu (jangan tempel ke file yang dikomit):

```bash
# Windows (PowerShell)
$env:SPOTIFY_CLIENT_ID = "your-client-id"
$env:SPOTIFY_CLIENT_SECRET = "your-client-secret"

# macOS dan Linux (bash)
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
```

4. Unduh playlist pertamamu:

```bash
stashify download "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
```

> [!NOTE]
> Credential tersimpan di shell environment kamu. Stashify tidak pernah menulis credential ke disk dan tidak pernah memasukkannya ke log.

### Pemakaian sehari-hari

- Unduh satu track, album, playlist, atau top tracks seorang artist dengan memberikan linknya ke `stashify download`
- Pilih format audio dengan `-f mp3|m4a|opus|flac|wav` (default `mp3`)
- Ubah folder output dengan `-o "D:\Music"` dan pola penamaan dengan `-t "{album}/{track_number} {title}"`
- Abaikan cover art atau lirik dengan `--no-cover` / `--no-lyrics`, atau ulangi semua dengan `--overwrite`
- Preview hasil match tanpa mengunduh dengan `--dry-run`
- Sinkronkan folder dengan playlist: `stashify sync "PLAYLIST_URL" -o "D:\Music\MyList"`
- Retag file yang sudah kamu punya: `stashify meta file1.mp3 file2.mp3 --url "ALBUM_URL"`
- Ekspor metadata ke JSON: `stashify save "ALBUM_URL" --save-file album.json`
- Cetak source URL yang akan dipakai per track: `stashify url "PLAYLIST_URL"`

Path template mendukung `{artist}`, `{artists}`, `{title}`, `{album}`, `{album_artist}`, `{track_number}`, `{disc_number}` dan `{release_year}`. Gunakan `/` untuk membuat subfolder. Karakter ilegal untuk nama file dihapus otomatis.

---

## Konfigurasi

Preferensi bisa disimpan di config file; secret tidak bisa. Credential hanya dibaca dari environment atau dari flag `--client-id` / `--client-secret`.

Lokasi config file: `%APPDATA%\stashify\config.json` (Windows), `~/.config/stashify/config.json` (macOS dan Linux).

| Key | Tipe | Default | Efek |
|-----|------|---------|--------|
| `output_dir` | string | `.` | Folder output untuk unduhan |
| `audio_format` | string | `mp3` | Format audio default |
| `bitrate` | string | `192k` | Bitrate untuk format lossy |
| `template` | string | `{artist} - {title}` | Template path output |
| `market` | string | `US` | Kode market dua huruf untuk lookup Spotify |
| `overwrite` | boolean | `false` | Unduh ulang file yang sudah ada |
| `no_cover` | boolean | `false` | Jangan pernah menyematkan cover art |
| `no_lyrics` | boolean | `false` | Jangan pernah menyematkan lirik |

Flag command line selalu lebih diutamakan daripada config file.

---

## Sumber Data

Stashify hanya online saat me-resolve metadata, mencari source, atau mengambil lirik. Audio diambil dari YouTube.

| Tujuan | Sumber |
|---------|--------|
| Metadata track, album, playlist dan artist | Spotify Web API (developer app milikmu) |
| Cover art | Spotify image CDN (disematkan ke file) |
| Audio source | YouTube, lewat yt-dlp |
| Lirik | lyrics.ovh (tanpa key) |

> [!NOTE]
> Beberapa track tidak punya match yang layak di YouTube. Stashify melaporkan kandidat terbaik yang ditemukan dan melewati track dengan skor terlalu rendah daripada mengunduh lagu yang salah.

---

## Struktur Proyek

```
stashify/
├── src/
│   └── stashify/
│       ├── __init__.py           # versi package
│       ├── __main__.py           # entry point python -m stashify
│       ├── cli.py                # argument parsing dan command
│       ├── pipeline.py           # shared download pipeline
│       ├── spotify.py            # Spotify Web API client
│       ├── models.py             # data model Track
│       ├── sources.py            # pencarian dan scoring YouTube
│       ├── download.py           # download yt-dlp dan konversi FFmpeg
│       ├── tagger.py             # tagging MP3, M4A, FLAC, Opus dan WAV
│       ├── lyrics.py             # client lyrics.ovh
│       ├── output.py             # path template dan file naming
│       ├── sync.py               # state handling playlist sync
│       ├── config.py             # config file loading
│       └── errors.py             # error types
├── tests/                        # pytest suite (offline, network di-mock)
├── assets/                       # logo dan icons
├── .github/
│   └── workflows/
│       ├── ci.yml                # lint dan tests di setiap push
│       └── release.yml           # draft release dari changelog di tag
├── pyproject.toml                # packaging dan konfigurasi tool
├── SECURITY.md                   # kebijakan pelaporan kerentanan
├── LICENSE
├── README.md                     # dokumentasi utama (English)
└── README.id.md                  # dokumentasi (Bahasa Indonesia)
```

---

## Pengembangan

### Bekerja pada kode

1. Install package dalam mode editable dengan dev extras: `python -m pip install -e .[dev]`
2. Buat perubahanmu
3. Jalankan checks: `python -m ruff check src tests` dan `python -m pytest -q`

### Menambahkan format audio yang didukung

1. Tambahkan format ke `AUDIO_FORMATS` di `src/stashify/download.py` dan ke `_CODEC_MAP`
2. Tambahkan tagging path di `src/stashify/tagger.py` (lihat `_tag_flac` sebagai contoh)
3. Tambahkan test yang merender dan retag file pendek dengan FFmpeg, lihat `tests/test_tagger.py`

> [!WARNING]
> `assets/` dikomit. Jangan commit audio hasil unduhan, cover art rilis asli, atau config file kamu. File apa pun yang mirip media pribadi tidak boleh masuk repository.

---

## Testing

Verifikasi sebelum setiap push, keduanya harus bersih:

```bash
python -m ruff check src tests
python -m pytest -q
```

| Check | Requirement |
|-------|-------------|
| `python -m ruff check src tests` | Harus melaporkan **All checks passed** (nol error, nol warning) |
| `python -m pytest -q` | Harus lolos seluruh suite |

Lint rule ditegakkan lewat section `[tool.ruff]` di `pyproject.toml`.

---

## Continuous Integration

| Workflow | Tujuan |
|----------|---------|
| `ci.yml` | Ruff dan test suite di Python 3.10 dan 3.12, di setiap push dan pull request |
| `release.yml` | Test suite plus draft GitHub release yang dibangun dari changelog, di tag `v*` |

---

## FAQ

<details>
<summary><b>Apakah saya butuh Spotify Premium atau login?</b></summary>

Tidak. Metadata dibaca lewat Web API resmi dengan developer app gratis yang kamu buat sendiri. Stashify tidak pernah melihat password kamu.

</details>

<details>
<summary><b>Apakah client secret saya aman?</b></summary>

Ya. Stashify membacanya dari environment atau dari command line flag, tidak pernah dari file yang ditulisnya. Jangan commit, jangan bagikan. Jika bocor, rotate di dashboard.

</details>

<details>
<summary><b>Beberapa lagu dilewati atau gagal diunduh. Kenapa?</b></summary>

Kemungkinan tidak ada match yang layak di YouTube (track unreleased, remix yang sangat tidak jelas, upload private), atau yt-dlp butuh update karena YouTube sering berubah. Jalankan `pip install --upgrade yt-dlp` lalu coba lagi.

</details>

<details>
<summary><b>Versi lagu yang salah terunduh. Apa yang bisa saya lakukan?</b></summary>

Scorer sangat mengutamakan audio dengan durasi cocok dan kata "official" di judul, dan menolak karaoke, cover dan live version kecuali kamu memintanya. Gunakan `--dry-run` terlebih dahulu; jika match terus salah, buka issue dengan link Spotify-nya.

</details>

<details>
<summary><b>Ada file yang sudah ada. Apakah akan ditimpa?</b></summary>

Tidak. File yang ada dilewati. Berikan `--overwrite` untuk mengunduh ulang.

</details>

<details>
<summary><b>Bisakah folder library saya sinkron dengan playlist Spotify?</b></summary>

Bisa. `stashify sync "PLAYLIST_URL" -o "D:\Music\MyList"` mengunduh track baru dan menghapus hanya file yang diunduh Stashify yang sudah hilang dari playlist. Semua file lain di folder tidak tersentuh.

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

Stashify adalah project open-source independen dan tidak berafiliasi atau diendorse oleh Spotify, Google, YouTube, maupun operator lyrics.ovh. Mengunduh musik bisa melanggar terms of service platform tersebut dan bisa melanggar copyright di yurisdiksi kamu. Stashify disediakan hanya untuk pemakaian pribadi yang sah; kamu bertanggung jawab atas cara kamu menggunakannya.

---

## Lisensi

Didistribusikan di bawah **MIT License**. Lihat [`LICENSE`](LICENSE) untuk informasi lebih lanjut.
