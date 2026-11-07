"""Helper keamanan: sanitasi input dan pembatas laju sederhana."""
from __future__ import annotations

import re
import time
from collections import deque

from markupsafe import Markup

_ALLOWED_TAGS = {
    "div", "span", "em", "i", "strong", "b", "br", "p", "ul", "ol", "li", "sup", "sub",
}
_TAG_RE = re.compile(r"</?([a-zA-Z0-9]+)(?:\s[^>]*)?>")
_KATA_RE = re.compile(r"^[a-zA-Z][a-zA-Z\-\s']{0,59}$")


def bersihkan_kata(kata: str) -> str:
    """Normalisasi input pengguna: trim, lower, dan validasi bentuk kata."""
    kata = (kata or "").strip().lower()
    if not kata or not _KATA_RE.match(kata):
        return ""
    return " ".join(kata.split())


def sanitasi_html(html_mentah: str) -> Markup:
    """Buang tag di luar daftar putih dari HTML hasil scraping.

    Atribut kelas dipertahankan agar tampilan tetap konsisten, sedangkan atribut
    lain (mis. onclick, style, href) dibuang untuk mencegah XSS.
    """
    if not html_mentah:
        return Markup("")

    def ganti(match: re.Match) -> str:
        tag = match.group(1).lower()
        if tag not in _ALLOWED_TAGS:
            return ""
        penutup = match.group(0).startswith("</")
        if penutup or tag == "br":
            return f"</{tag}>" if penutup and tag != "br" else ("<br>" if tag == "br" else f"</{tag}>")

        kelas = re.search(r"""class\s*=\s*["']([^"']*)["']""", match.group(0))
        if kelas:
            kelas_aman = re.sub(r"[^a-zA-Z0-9\-\s]", "", kelas.group(1))
            return f'<{tag} class="{kelas_aman}">'
        return f"<{tag}>"

    aman = _TAG_RE.sub(ganti, html_mentah)
    # Buang sisa tag yang mungkin lolos (mis. komentar atau tag rusak).
    aman = re.sub(r"<!--.*?-->", "", aman, flags=re.DOTALL)
    return Markup(aman)


class PembatasLaju:
    """Rate limiter in-memory berbasis jendela waktu (per IP)."""

    def __init__(self, maks: int, jendela: int):
        self.maks = maks
        self.jendela = jendela
        self._catatan: dict[str, deque] = {}

    def izinkan(self, kunci: str) -> bool:
        sekarang = time.time()
        catatan = self._catatan.setdefault(kunci, deque())
        while catatan and sekarang - catatan[0] > self.jendela:
            catatan.popleft()
        if len(catatan) >= self.maks:
            return False
        catatan.append(sekarang)
        return True
