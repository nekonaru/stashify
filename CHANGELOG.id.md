# Changelog

Semua perubahan penting di Stashify didokumentasikan di file ini. Formatnya mengikuti [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), dan project ini mengikuti [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.4.0

Stashify sekarang punya health check bawaan, dry run lebih cepat, dan lirik yang lebih andal.

### Fitur baru

- **`stashify doctor`.** Memeriksa Python, FFmpeg, folder Downloads, embed pages Spotify, pencarian YouTube dan lyrics API, lalu mencetak laporan pass/fail. Gunakan saat unduhan gagal dan kamu ingin tahu bagian stack mana yang rusak.

### Peningkatan

- **Lirik dari lrclib.net.** Matching lebih akurat dengan artist, title, album dan durasi, dengan lyrics.ovh sebagai fallback. Track instrumental tidak diberi lirik nyasar.
- **Lewati detail lookup saat tidak dibutuhkan.** `--dry-run` dan `url` tidak lagi mengambil detail per track, menghemat jaringan untuk playlist besar.
- **Flag cover dan lirik simetris.** `--cover`, `--no-cover`, `--lyrics` dan `--no-lyrics` bekerja sebagai pasangan, sehingga CLI bisa menimpa config di kedua arah.

### Perbaikan bug

- **`meta --no-cover` / `--no-lyrics` dihormati.** Sebelumnya command membaca config file dan mengabaikan flag, sekarang flag yang menang.
- **`url` mendapat `--provider`.** Sebelumnya flag ini tidak ada di command `url`, sekarang semua command metadata menerimanya.
- **Flag bersama yang konsisten.** `--provider` dan `--no-details` pindah ke satu parser bersama sehingga semua command metadata menawarkannya.

### Penggunaan

```bash
pip install --upgrade stashify-cli
stashify doctor
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.3.0

Stashify sekarang dikemas sebagai distribusi PyPI yang rapi, siap diterbitkan dengan trusted publisher.

### Fitur baru

- **PyPI packaging.** Stashify didistribusikan di PyPI sebagai `stashify-cli` (nama `stashify` milik orang lain). Command dan nama import `stashify` tidak berubah; `pip install stashify-cli` adalah cara install yang direkomendasikan.

### Peningkatan

- **Trusted publishing.** Workflow publish manual membangun wheel dan sdist, memeriksanya dengan `twine check`, smoke test wheel, dan menerbitkan lewat OIDC tanpa token API yang tersimpan.
- **Metadata lengkap.** Project URLs, ekspresi lisensi SPDX, license file dan classifiers diatur; PyPI sekarang merender README sepenuhnya.
- **Pre-commit hook.** `.pre-commit-config.yaml` opsional menjalankan ruff dan gitleaks sebelum setiap commit.

### Penggunaan

Sampai publish PyPI pertama (setup maintainer satu kali, lalu jalankan **Publish** dari tab Actions pada tag):

```bash
pip install git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

Setelah paket masuk ke PyPI:

```bash
pip install stashify-cli
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.2.1

Audit internal: setiap entry point diperiksa ulang, unduhan end-to-end nyata diverifikasi, security pass dijalankan lagi.

### Perbaikan bug

- **Portabilitas sync state.** `stashify.sync.json` menyimpan forward slash, dan file lama dengan backslash OS dibaca dengan benar, sehingga delete tidak pernah gagal diam-diam saat folder dipindah antar OS.
- **Validasi bitrate.** `--bitrate` sekarang menolak nilai yang salah sejak awal, bukan memberikannya ke converter.
- **Error jelas untuk output yang tidak bisa ditulis.** Menulis `--save-file` ke path yang tidak bisa ditulis sekarang melaporkan error yang jelas, bukan traceback OS mentah.

### Peningkatan

- **URL lookup paralel dan berurutan.** `stashify url` me-resolve track secara paralel dan menjaga urutan input.
- **Penguatan JSON lebih dalam.** RecursionError dari halaman embed yang sangat dalam menghasilkan error yang jelas, dan tagging WAV dibuktikan dengan round trip test.

### Penggunaan

```bash
pip install --upgrade git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.2.0

Unduhan sekarang mendarat di folder Downloads milik OS, dan playlist besar diunduh secara paralel.

### Fitur baru

- **Download paralel.** `--jobs N` mengunduh hingga 8 track sekaligus, default 2, hasil ditulis mengikuti urutan input dan nama target yang sama tidak pernah menimpa satu sama lain.
- **Fallback search.** Jika YouTube tidak mengembalikan apa pun untuk `artist - title`, Stashify mencoba lagi tanpa strip dan dengan `audio` di belakang sebelum menyerah.

### Peningkatan

- **Default folder Downloads.** Output default ke folder Downloads OS (`%USERPROFILE%\Downloads` di Windows, `~/Downloads` atau `XDG_DOWNLOAD_DIR` di macOS dan Linux), ubah dengan `-o`, `output_dir` atau `STASHIFY_DOWNLOAD_DIR`.
- **Lokasi output dicetak.** Setiap run mencetak `Saving to:` agar tujuan selalu terlihat.
- **Metadata paralel.** Lookup detail per track dan enrichment metadata berjalan empat sekaligus.

### Penggunaan

```bash
pip install --upgrade git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.1.0

Stashify langsung berfungsi dengan akun Spotify apa pun: metadata sekarang diambil dari halaman publik Spotify, tanpa developer app atau Premium.

### Fitur baru

- **Embed provider.** Metadata dibaca dari public embed pages Spotify, sehingga track, album, artist top tracks dan playlist publik di-resolve tanpa akun, login atau API key.
- **Per-track enrichment.** Artists, tahun rilis dan cover art di-resolve per track untuk playlist, nonaktifkan dengan `--no-details`.

### Peningkatan

- **Public-page diagnostics.** Link privat atau yang dihapus sekarang menghasilkan pesan yang jelas, bukan kegagalan diam.
- **Official API updated.** Perubahan Web API Februari 2026 diterapkan: playlist dan artist top tracks ditolak dengan panduan di `--provider api` (tracks dan album tetap berfungsi di sana), dan respons 403 sekarang menyertakan pesan dari server.

### Penggunaan

```bash
pip install --upgrade git+https://github.com/nekonaru/stashify.git
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```

## v1.0.0

Stashify me-resolve link Spotify apa pun menjadi audio file dengan tag metadata lengkap di mesin kamu, diambil dari YouTube.

### Fitur baru

- **Download command.** Link track, album, playlist dan artist diunduh ke file lokal sebagai MP3, M4A, Opus, FLAC atau WAV, dengan cover art, lirik, album, nomor track, tahun rilis dan ISRC tertulis di tag.
- **Best-match source.** Kandidat YouTube dinilai dari kecocokan durasi dan kata, match dengan skor rendah ditolak, bukan diunduh.
- **Save command.** Dump metadata hasil resolve dari sebuah link sebagai JSON tanpa mengunduh audio.
- **URL command.** Cetak source URL yang dipilih per track untuk inspeksi.
- **Meta command.** Retag file audio yang sudah ada dengan metadata dari link Spotify, sesuai urutan file.
- **Sync command.** Jaga folder tetap sinkron dengan playlist lewat state file `stashify.sync.json`, track baru diunduh dan track yang hilang dihapus, sisanya tidak disentuh.
- **Path templates.** Nama output diambil dari template dengan `{artist}`, `{title}` dan kawan-kawan, termasuk subfolder, karakter ilegal dihapus otomatis.
- **Dry run.** `--dry-run` mencetak source yang dipilih per track tanpa mengunduh apa pun.
- **Config file.** Preferensi non-secret disimpan di `config.json` per user, flag command line selalu lebih diutamakan.

### Peningkatan

- **Safe file naming.** Segment template disanitasi untuk semua OS dan collision ditangani secara prediktif.
- **Security policy.** `SECURITY.md` dipublikasikan, dengan credential hanya dibaca dari environment.
- **CI.** Ruff dan pytest suite berjalan di Python 3.10 dan 3.12 di setiap push dan pull request.

### Penggunaan

```bash
pip install git+https://github.com/nekonaru/stashify.git
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
stashify download "https://open.spotify.com/playlist/PLAYLIST_ID"
```
