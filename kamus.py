"""Kamus offline berbasis data lokal.

Memuat daftar kata dan definisi ringkas dari data_kata sehingga aplikasi tetap
berfungsi tanpa koneksi internet. Pencarian daftar kata memakai ``set`` agar
lookup O(1), dan definisi dipersempit ke kata yang benar-benar ada saja.
"""
from __future__ import annotations

import csv
import html
import re
from functools import lru_cache
from pathlib import Path

import config

_WORD_RE = re.compile(r"^[a-z]+$")
_BASE_WORD_RE = re.compile(r"\s*\(\d+\)\s*$")


class KamusLokal:
    """Kamus offline yang dimuat sekali lalu dipakai berulang kali."""

    def __init__(self, txt_path: Path | None = None, csv_path: Path | None = None):
        self.txt_path = Path(txt_path or config.DATA_TXT)
        self.csv_path = Path(csv_path or config.DATA_CSV)
        self._kata: set[str] = set()
        self._definisi: dict[str, list[dict]] = {}
        self._loaded = False
        self._definisi_loaded = False

    # ------------------------------------------------------------------ muat
    def muat(self) -> "KamusLokal":
        """Muat daftar kata (wajib) dan definisi ringkas (opsional)."""
        self._muat_kata()
        self._muat_definisi()
        return self

    def _muat_kata(self) -> None:
        if self._loaded:
            return
        if self.txt_path.exists():
            with open(self.txt_path, encoding="utf-8") as f:
                self._kata = {baris.strip().lower() for baris in f if baris.strip()}
        self._loaded = True

    def _muat_definisi(self) -> None:
        if self._definisi_loaded:
            return
        if not self.csv_path.exists():
            self._definisi_loaded = True
            return

        with open(self.csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for baris in reader:
                nama = (baris.get("nama") or "").strip()
                if not nama or not _WORD_RE.match(nama.lower()):
                    continue
                kata = nama.lower()
                self._kata.add(kata)
                self._definisi.setdefault(kata, []).append(
                    {
                        "kata_dasar": (baris.get("kata_dasar") or "").strip(),
                        "kelas": (baris.get("kelas") or "").strip(),
                        "submakna": (baris.get("submakna") or "").strip(),
                        "contoh": (baris.get("contoh") or "").strip(),
                    }
                )
        self._definisi_loaded = True

    # ---------------------------------------------------------------- pencarian
    def ada(self, kata: str) -> bool:
        self._muat_kata()
        kata = (kata or "").strip().lower()
        if not kata:
            return False
        if kata in self._kata:
            return True
        # Coba bentuk dasar bila kata berupa turunan sederhana.
        for dasar in self._kata_dasar(kata):
            if dasar in self._kata:
                return True
        return False

    @staticmethod
    def _kata_dasar(kata: str) -> list[str]:
        """Tebakan bentuk dasar dari kata berimbuhan umum."""
        hasil = set()
        for awalan in ("me", "men", "mem", "meng", "ber", "ter", "pe", "per", "di", "ke", "se"):
            if kata.startswith(awalan) and len(kata) > len(awalan) + 2:
                hasil.add(kata[len(awalan):])
        for akhiran in ("kan", "an", "nya", "i"):
            if kata.endswith(akhiran) and len(kata) > len(akhiran) + 2:
                hasil.add(kata[: -len(akhiran)])
        return list(hasil)

    def cari(self, kata: str) -> list[dict]:
        """Kembalikan daftar entri definisi untuk kata (boleh kosong)."""
        self._muat_definisi()
        return self._definisi.get((kata or "").strip().lower(), [])

    def saran(self, awalan: str, batas: int = 10) -> list[str]:
        """Saran kata yang berawalan ``awalan`` (untuk autocomplete)."""
        self._muat_kata()
        awalan = (awalan or "").strip().lower()
        if not awalan:
            return []
        hasil = []
        for kata in self._kata:
            if kata.startswith(awalan):
                hasil.append(kata)
                if len(hasil) >= batas * 10:
                    break
        hasil.sort(key=len)
        return hasil[:batas]

    def render_html(self, kata: str) -> str | None:
        """Bentuk HTML definisi bergaya sama dengan hasil daring."""
        entri_list = self.cari(kata)
        if not entri_list:
            return None

        kata_aman = html.escape(kata)
        bagian = []
        for entri in entri_list[:8]:
            kelas = (
                f"<span class='kelas'>({html.escape(entri['kelas'])})</span> "
                if entri["kelas"]
                else ""
            )
            submakna = (
                f"<span class='submakna'>{html.escape(entri['submakna'])}: </span>"
                if entri["submakna"]
                else ""
            )
            contoh = (
                f"<span class='contoh'>— {html.escape(entri['contoh'])}</span>"
                if entri["contoh"]
                else ""
            )
            if not (kelas or submakna or contoh):
                continue
            bagian.append(f"<div class='makna-item'>{kelas}{submakna}{contoh}</div>")

        if not bagian:
            return None

        dasar = entri_list[0]["kata_dasar"]
        dasar_txt = f"{html.escape(_BASE_WORD_RE.sub('', dasar))} >> " if dasar else ""
        return (
            "<div class='pelafalan-kata-dasar'>"
            f"<div class='kata-dasar'>{dasar_txt}{kata_aman}</div>"
            "</div>"
            f"<div class='makna'>{''.join(bagian)}</div>"
        )


@lru_cache(maxsize=1)
def kamus() -> KamusLokal:
    """Kamus lokal tunggal (singleton) yang sudah dimuat."""
    return KamusLokal().muat()
