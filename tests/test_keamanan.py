"""Uji keamanan: sanitasi input dan pembatas laju."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from keamanan import PembatasLaju, bersihkan_kata, sanitasi_html


def test_bersihkan_kata_valid():
    assert bersihkan_kata("  Abadi  ") == "abadi"
    assert bersihkan_kata("kekal  abadi") == "kekal abadi"


def test_bersihkan_kata_menolak_tag_dan_angka():
    assert bersihkan_kata("<script>alert(1)</script>") == ""
    assert bersihkan_kata("kata123") == ""
    assert bersihkan_kata("") == ""
    assert bersihkan_kata("   ") == ""


def test_sanitasi_html_mempertahankan_tag_diizinkan():
    hasil = str(sanitasi_html("<div class='makna-item'><span class='kelas'>(n)</span></div>"))
    assert "<div class=\"makna-item\">" in hasil
    assert "<span class=\"kelas\">" in hasil


def test_sanitasi_html_membuang_tag_berbahaya():
    hasil = str(sanitasi_html("<script>alert(1)</script><div>aman</div>"))
    assert "<script>" not in hasil
    assert "alert(1)" in hasil or "aman" in hasil
    assert "<div>aman</div>" in hasil


def test_sanitasi_html_membuang_atribut_event():
    hasil = str(sanitasi_html("<div onclick='jahat()' class='makna'>isi</div>"))
    assert "onclick" not in hasil
    assert 'class="makna"' in hasil


def test_pembatas_laju():
    batas = PembatasLaju(maks=2, jendela=60)
    assert batas.izinkan("ip1") is True
    assert batas.izinkan("ip1") is True
    assert batas.izinkan("ip1") is False
    assert batas.izinkan("ip2") is True
