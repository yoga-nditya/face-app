"""
Konfigurasi Gunicorn untuk menjalankan FastAPI app tanpa Docker, dengan
worker process model ala production (multi-process, tidak pakai --reload).

Usage:
    gunicorn -c gunicorn_conf.py app.main:app
"""
from __future__ import annotations

import multiprocessing
import os

# Jumlah worker process. Formula umum (2 x CPU core + 1) cukup untuk workload
# I/O-bound biasa, tapi untuk workload CPU-bound seperti face embedding,
# pertimbangkan worker lebih sedikit supaya tidak berebut CPU antar proses.
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() + 1))

worker_class = "uvicorn.workers.UvicornWorker"

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

accesslog = "-"   # stdout
errorlog = "-"    # stdout
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

# PENTING: setiap worker Gunicorn adalah proses terpisah, artinya model face
# recognition akan di-load ulang (warm_up()) di SETIAP worker saat startup —
# ini normal dan diharapkan (bukan bug), karena model harus ada di memory
# masing-masing proses. Face index juga dimuat per-worker dari
# data/face_index/index.json (file yang sama, dibaca oleh semua worker).
