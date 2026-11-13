# Changelog

Semua perubahan penting di Stashify didokumentasikan di file ini. Formatnya mengikuti [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), dan project ini mengikuti [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
