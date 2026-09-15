"""
Logging setup.

PENTING (Section 21/27 spec): foto wajah / raw image bytes / embedding TIDAK
BOLEH pernah masuk ke log. Modul lain hanya boleh log metadata (employee_code,
similarity score, hash, latency) — tidak pernah log payload gambar.
"""
from __future__ import annotations

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # sudah di-setup, hindari duplicate handler

    root.setLevel(settings.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
