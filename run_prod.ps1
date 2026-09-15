# run_prod.ps1 - Jalankan server multi-worker (production-style) di Windows.
#
# CATATAN: Gunicorn TIDAK jalan di Windows (bergantung pada fcntl/os.fork
# yang cuma ada di Unix). Untuk Windows, uvicorn punya opsi --workers sendiri
# yang memakai multiprocessing - ini setara secara fungsi (multi-process,
# tanpa auto-reload), meski implementasinya beda dari gunicorn_conf.py.
$ErrorActionPreference = "Stop"
& .\.venv\Scripts\Activate.ps1

$workers = if ($env:UVICORN_WORKERS) { $env:UVICORN_WORKERS } else { 4 }

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers $workers
