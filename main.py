"""Server Flask untuk pengecekan kata Sekata (KBBI).

Alur: cek kamus lokal lebih dulu (cepat, tanpa internet), lalu fallback ke KBBI
daring bila kata belum ada. Semua respons definisi disanitasi sebelum dikirim.
"""
from __future__ import annotations

import html as html_lib
from functools import lru_cache

from flask import Flask, jsonify, render_template, request

import config
from keamanan import PembatasLaju, bersihkan_kata, sanitasi_html
from kamus import kamus
from kbbi import KBBI, TidakDitemukan

app = Flask(__name__)
pembatas = PembatasLaju(config.RATE_LIMIT_MAX, config.RATE_LIMIT_WINDOW)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/saran")
def saran():
    """Saran kata untuk autocomplete."""
    awalan = bersihkan_kata(request.args.get("q", ""))
    if not awalan:
        return jsonify({"saran": []})
    return jsonify({"saran": kamus().saran(awalan, batas=10)})


@lru_cache(maxsize=config.CACHE_SIZE)
def _cek_daring(kata: str) -> tuple[str, str]:
    """Ambil definisi dari KBBI daring. Kembalikan (status, html_mentah)."""
    try:
        data = KBBI(kata)
    except TidakDitemukan:
        return "tidak_ada", ""
    except Exception as galat:  # noqa: BLE001 - termasuk galat jaringan
        if "ConnectionError" in str(galat.__class__) or "Timeout" in str(galat.__class__):
            return "offline", ""
        return "galat", ""

    try:
        mentah = data.serialisasi()
        entri = mentah["entri"][0]
    except Exception:  # noqa: BLE001 - struktur tak terduga
        return "galat", ""

    pelafalan = entri.get("nama", kata)
    kata_dasar = entri.get("kata_dasar", [])
    kata_dasar_txt = "; ".join(kata_dasar) + " >> " if kata_dasar else ""

    makna_html = ""
    for makna in entri.get("makna", []):
        kelas = " ".join(f"({item['kode']})" for item in makna.get("kelas", []))
        submakna = "; ".join(makna.get("submakna", []))
        contoh = "; ".join(makna.get("contoh", []))

        makna_html += "<div class='makna-item'>"
        if kelas:
            makna_html += f"<span class='kelas'>{kelas}</span> "
        if submakna:
            makna_html += f"<span class='submakna'>{submakna}: </span> "
        if contoh:
            makna_html += f"<span class='contoh'>— {contoh}</span>"
        makna_html += "</div>"

    definisi = (
        "<div class='pelafalan-kata-dasar'>"
        f"<div class='kata-dasar'>{kata_dasar_txt} {pelafalan}</div>"
        "</div>"
        f"<div class='makna'>{makna_html}</div>"
    )
    return "valid", definisi


def _definisi_lokal_html(kata: str) -> str:
    html_def = kamus().render_html(kata)
    if html_def:
        return html_def
    kata_aman = html_lib.escape(kata)
    return (
        "<div class='pelafalan-kata-dasar'>"
        f"<div class='kata-dasar'>{kata_aman}</div>"
        "</div><div class='makna'></div>"
    )


@app.route("/cek_kata", methods=["POST"])
def cek_kata():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "anon").split(",")[0]
    if not pembatas.izinkan(ip):
        return jsonify({"status": "error", "message": "Terlalu banyak permintaan, coba lagi nanti."}), 429

    kata = bersihkan_kata((request.get_json(silent=True) or {}).get("kata", ""))
    if not kata:
        return jsonify({"status": "error", "message": "Kata kosong atau tidak valid"}), 400

    # 1) Kamus lokal lebih dulu bila tersedia definisinya.
    if kamus().cari(kata):
        return jsonify({"status": "valid", "sumber": "lokal", "definisi": _definisi_lokal_html(kata)})

    # 2) Fallback ke KBBI daring.
    status, definisi = _cek_daring(kata)
    if status == "valid":
        return jsonify({"status": "valid", "sumber": "daring", "definisi": str(sanitasi_html(definisi))})

    if status in {"offline", "galat"}:
        if kamus().ada(kata):
            return jsonify({"status": "valid", "sumber": "lokal", "definisi": _definisi_lokal_html(kata)})
        return jsonify({
            "status": "invalid",
            "message": f"Tidak dapat memeriksa '{kata}' daring dan kata tidak ditemukan di data lokal.",
        })

    return jsonify({"status": "invalid", "message": f"Kata '{kata}' tidak ditemukan dalam KBBI."})


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
