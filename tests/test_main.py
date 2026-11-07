"""Uji endpoint Flask tanpa akses jaringan."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main
from kamus import KamusLokal
from kbbi import TidakDitemukan


@pytest.fixture
def klien(tmp_path, monkeypatch):
    """Klien uji dengan kamus mini dan fungsi daring yang dipalsukan."""
    txt = tmp_path / "kata.txt"
    txt.write_text("abadi\nkucing\n", encoding="utf-8")
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "nama,kelas,submakna,contoh,kata_dasar\n"
        "kucing,n,hewan berkaki empat,,\n",
        encoding="utf-8",
    )
    kamus_mini = KamusLokal(txt_path=txt, csv_path=csv_file).muat()
    monkeypatch.setattr(main, "kamus", lambda: kamus_mini)
    main._cek_daring.cache_clear()
    return main.app.test_client()


def test_index(klien):
    assert klien.get("/").status_code == 200


def test_kata_lokal_dengan_definisi(klien):
    r = klien.post("/cek_kata", json={"kata": "kucing"})
    data = r.get_json()
    assert data["status"] == "valid"
    assert data["sumber"] == "lokal"
    assert "hewan berkaki empat" in data["definisi"]


def test_kata_lokal_tanpa_definisi_daring_valid(klien, monkeypatch):
    monkeypatch.setattr(main, "_cek_daring", lambda kata: ("valid", "<div>daring</div>"))
    r = klien.post("/cek_kata", json={"kata": "abadi"})
    data = r.get_json()
    assert data["status"] == "valid"
    assert data["sumber"] == "daring"


def test_kata_offline_fallback_lokal(klien, monkeypatch):
    monkeypatch.setattr(main, "_cek_daring", lambda kata: ("offline", ""))
    r = klien.post("/cek_kata", json={"kata": "abadi"})
    assert r.get_json()["status"] == "valid"


def test_kata_offline_tidak_ada(klien, monkeypatch):
    monkeypatch.setattr(main, "_cek_daring", lambda kata: ("offline", ""))
    r = klien.post("/cek_kata", json={"kata": "tidakada"})
    data = r.get_json()
    assert data["status"] == "invalid"


def test_kata_tidak_ditemukan_daring(klien, monkeypatch):
    monkeypatch.setattr(main, "_cek_daring", lambda kata: ("tidak_ada", ""))
    r = klien.post("/cek_kata", json={"kata": "halusinasi"})
    assert r.get_json()["status"] == "invalid"


def test_input_kosong(klien):
    r = klien.post("/cek_kata", json={"kata": ""})
    assert r.status_code == 400
    assert r.get_json()["status"] == "error"


def test_input_xss_ditolak(klien):
    r = klien.post("/cek_kata", json={"kata": "<script>alert(1)</script>"})
    assert r.status_code == 400


def test_saran_endpoint(klien):
    r = klien.get("/saran?q=kuc")
    assert "kucing" in r.get_json()["saran"]


def test_rate_limit(klien, monkeypatch):
    monkeypatch.setattr(main, "_cek_daring", lambda kata: ("tidak_ada", ""))
    main.pembatas.maks = 2
    main.pembatas._catatan.clear()
    assert klien.post("/cek_kata", json={"kata": "aaa"}).status_code == 200
    assert klien.post("/cek_kata", json={"kata": "bbb"}).status_code == 200
    assert klien.post("/cek_kata", json={"kata": "ccc"}).status_code == 429
