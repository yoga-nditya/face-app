#!/usr/bin/env bash
# run_prod.sh - Jalankan server pakai Gunicorn + Uvicorn worker (multi-process,
# tanpa auto-reload) - lebih mendekati kondisi production daripada uvicorn saja.
set -euo pipefail

source .venv/bin/activate
gunicorn -c gunicorn_conf.py app.main:app
