# run_dev.ps1 - Jalankan server pakai uvicorn dengan auto-reload (development).
$ErrorActionPreference = "Stop"
& .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
