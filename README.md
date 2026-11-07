# Simple Sekata Game Checker (Mini KBBI)

Alat untuk memvalidasi kata bahasa Indonesia terhadap KBBI — berguna untuk game
"Sekata". Tersedia dalam **dua mode**:

| Mode | Cara pakai | Internet | Definisi |
|------|-----------|----------|----------|
| **Statis (GitHub Pages)** | buka [static/index.html](static/index.html) | tidak perlu | dari kamus offline tertanam |
| **Server (Flask)** | `python main.py` | untuk definisi daring | lokal + fallback KBBI daring |

## Versi statis untuk GitHub Pages (gratis)

Halaman statis mandiri tanpa server — cocok di-host gratis di GitHub Pages.

**Coba langsung:** <https://bimbim-byte.github.io/simple-sekata-checker/>

Fitur:
- Pencarian ketik **atau** **input suara** (klik tombol 🎤 lalu ucapkan satu kata).
- Hanya **satu kata** yang diproses: dari ucapan berulang/frasa, kata pertama diambil
  dan pengulangan kata yang sama dalam 2 detik diabaikan.
- Switch **mode terang/gelap** dan tampilan responsif untuk ponsel.

Menjalankan lokal:

```bash
python build_static_data.py   # bangun static/embedded-data.js dari data_kata/
```

Lalu buka `static/index.html` di browser.

**Deploy otomatis:** workflow [.github/workflows/pages.yml](.github/workflows/pages.yml)
membangun payload dan menerbitkannya ke GitHub Pages setiap kali push ke `main`.
Aktifkan lebih dulu di **Settings → Pages → Source: GitHub Actions**.

> Catatan: file `static/embedded-data.js` (~4,8 MB) di-*generate*, jadi tidak
> ikut di-commit (lihat [.gitignore](.gitignore)). Workflow yang membuatnya.

## Versi server (Flask)

```bash
pip install -r requirements.txt
python main.py
```

Buka `http://127.0.0.1:5000` (atau `localhost:5000`). Tekan `Ctrl+C` untuk berhenti.

Versi server juga mendukung **input suara** (klik 🎤), dengan aturan yang sama:
hanya satu kata yang diproses dan pengulangan dalam 2 detik diabaikan.

Alur pengecekan: **kamus lokal lebih dulu** (cepat, tanpa internet), lalu fallback
ke KBBI daring bila definisi belum tersedia. Endpoint:

- `GET /` — antarmuka web
- `POST /cek_kata` — `{"kata": "abadi"}` → `{status, sumber, definisi}`
- `GET /saran?q=aba` — saran kata (autocomplete)

## Konfigurasi

Semua pengaturan terpusat di [config.py](config.py) dan dapat di-override lewat
variabel lingkungan:

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `SEKATA_HOST` | `127.0.0.1` | host server |
| `SEKATA_PORT` | `5000` | port server |
| `SEKATA_DEBUG` | `false` | mode debug Flask |
| `SEKATA_KBBI_TIMEOUT` | `6` | timeout permintaan daring (detik) |
| `SEKATA_CACHE_SIZE` | `2048` | ukuran cache hasil daring |
| `SEKATA_RATE_LIMIT_MAX` | `60` | maksimal permintaan per jendela per IP |
| `SEKATA_RATE_LIMIT_WINDOW` | `60` | panjang jendela rate limit (detik) |
| `SEKATA_DATA_DIR` | `data_kata` | lokasi berkas data |

## Pengujian

```bash
python -m pytest -q
```

## Catatan input suara

Input suara memakai **Web Speech API** (didukung Chrome, Edge, dan Safari terbaru;
belum di Firefox). Membutuhkan koneksi internet saat pengenalan suara karena
browser mengirim audio ke layanan pengenalan miliknya, walau kamusnya sendiri
berjalan offline.

## Struktur proyek

```
config.py               Konfigurasi terpusat
kamus.py                Kamus offline (set + definisi CSV)
keamanan.py             Sanitasi HTML & rate limiter
main.py                 Server Flask
kbbi.py                 Klien scraping KBBI daring
build_static_data.py    Membuat payload statis (static/embedded-data.js)
cleaning_kata.py        Pra-pemrosesan daftar kata dari CSV
static/index.html       Aplikasi web statis (GitHub Pages)
templates/index.html    Antarmuka web versi server
data_kata/              Dataset KBBI
tests/                  Pengujian pytest
```

## Lisensi

Lihat [LICENSE](LICENSE).
