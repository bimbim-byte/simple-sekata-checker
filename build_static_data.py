"""Bangun payload data tertanam untuk halaman statis (GitHub Pages).

Menghasilkan file ``static/embedded-data.js`` yang berisi data kata terkompresi
(di-deflate via gzip lalu di-encode base64). Halaman statis memuat file ini untuk
mendapatkan kamus offline penuh tanpa server.

Jalankan:
    python build_static_data.py
"""
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import config

OUTPUT = Path(__file__).resolve().parent / "static" / "embedded-data.js"
MAX_SUBMAKNA = 300
MAX_CONTOH = 150
MAX_KELAS = 40


def bangun_baris() -> list[list[str]]:
    import csv

    if not config.DATA_CSV.exists():
        raise SystemExit(f"File data tidak ditemukan: {config.DATA_CSV}")

    definisi: dict[str, list[str]] = {}
    urutan: list[str] = []

    with open(config.DATA_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            nama = (r.get("nama") or "").strip().lower()
            if not nama:
                continue
            submakna = (r.get("submakna") or "").strip()
            contoh = (r.get("contoh") or "").strip()
            if nama not in definisi:
                definisi[nama] = []
                urutan.append(nama)
            if submakna or contoh:
                definisi[nama] = [
                    (r.get("kelas") or "").strip()[:MAX_KELAS],
                    submakna[:MAX_SUBMAKNA],
                    contoh[:MAX_CONTOH],
                ]

    # Gabungkan kata dari daftar kata lokal (versi KBBI lain) supaya tidak ada
    # kata valid yang hilang meski definisinya tidak tersedia di CSV ini.
    if config.DATA_TXT.exists():
        with open(config.DATA_TXT, encoding="utf-8") as f:
            for baris in f:
                kata = baris.strip().lower()
                if kata and kata not in definisi:
                    definisi[kata] = []
                    urutan.append(kata)

    return [[kata] + definisi[kata] for kata in urutan]


def main() -> None:
    baris = bangun_baris()
    data = json.dumps(baris, ensure_ascii=False, separators=(",", ":"))
    b64 = base64.b64encode(gzip.compress(data.encode("utf-8"), 9)).decode()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("// Dibuat otomatis oleh build_static_data.py - jangan diedit manual.\n")
        f.write(f"// Jumlah entri: {len(baris)}. Ukuran payload: {len(b64) / 1e6:.2f} MB (base64 gzip).\n")
        f.write(f'window.SEKATA_DATA_GZ = "{b64}";\n')

    print(f"Payload tertanam: {len(baris)} entri -> {OUTPUT} ({len(b64) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
