"""Uji kamus offline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kamus import KamusLokal


def _kamus_mini(tmp_path: Path) -> KamusLokal:
    txt = tmp_path / "kata.txt"
    txt.write_text("abadi\nkucing\nmakan\n", encoding="utf-8")

    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "nama,kelas,submakna,contoh,kata_dasar\n"
        "abadi,n,langgeng; tidak berkesudahan,makna abadi,\n"
        "kucing,,,\"membawa kucing\",\n",
        encoding="utf-8",
    )
    return KamusLokal(txt_path=txt, csv_path=csv_file).muat()


def test_ada_kata(tmp_path):
    kamus = _kamus_mini(tmp_path)
    assert kamus.ada("abadi") is True
    assert kamus.ada("kucing") is True
    assert kamus.ada("tidakada") is False


def test_ada_tanpa_case(tmp_path):
    kamus = _kamus_mini(tmp_path)
    assert kamus.ada("ABADI") is True


def test_cari_definisi(tmp_path):
    kamus = _kamus_mini(tmp_path)
    entri = kamus.cari("abadi")
    assert len(entri) == 1
    assert "langgeng" in entri[0]["submakna"]


def test_render_html(tmp_path):
    kamus = _kamus_mini(tmp_path)
    html = kamus.render_html("abadi")
    assert html is not None
    assert "kelas" in html and "langgeng" in html


def test_render_html_kosong_none(tmp_path):
    kamus = _kamus_mini(tmp_path)
    assert kamus.render_html("tidakada") is None


def test_saran(tmp_path):
    kamus = _kamus_mini(tmp_path)
    hasil = kamus.saran("ma")
    assert "makan" in hasil


def test_tebak_kata_dasar(tmp_path):
    kamus = _kamus_mini(tmp_path)
    # "memakan" -> tebakan dasar "makan" yang ada di kamus
    assert kamus.ada("memakan") is True
