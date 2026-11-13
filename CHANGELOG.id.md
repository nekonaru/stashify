# Changelog

Semua perubahan penting di Stashify didokumentasikan di file ini. Formatnya mengikuti [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), dan project ini mengikuti [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
