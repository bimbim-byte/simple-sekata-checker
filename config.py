"""Konfigurasi terpusat untuk aplikasi sekata checker.

Nilai dapat di-override lewat variabel lingkungan (opsional via file .env).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _env(name, default):
    return os.environ.get(name, default)


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# Lokasi data
DATA_DIR = Path(_env("SEKATA_DATA_DIR", BASE_DIR / "data_kata"))
DATA_CSV = DATA_DIR / "kbbi_v.csv"
DATA_TXT = DATA_DIR / "kbbi_edited.txt"

# Server
HOST = _env("SEKATA_HOST", "127.0.0.1")
PORT = _env_int("SEKATA_PORT", 5000)
DEBUG = _env_bool("SEKATA_DEBUG", False)

# Pencarian daring
KBBI_TIMEOUT = _env_int("SEKATA_KBBI_TIMEOUT", 6)
CACHE_SIZE = _env_int("SEKATA_CACHE_SIZE", 2048)

# Batas sederhana untuk mencegah penyalahgunaan endpoint
RATE_LIMIT_MAX = _env_int("SEKATA_RATE_LIMIT_MAX", 60)
RATE_LIMIT_WINDOW = _env_int("SEKATA_RATE_LIMIT_WINDOW", 60)
