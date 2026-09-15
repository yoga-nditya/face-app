# setup.ps1 - Setup environment tanpa Docker, khusus Windows.
#
# Usage (PowerShell):
#   .\setup.ps1
#
# Kalau muncul error "execution of scripts is disabled", jalankan dulu (sekali saja, per user):
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

$ErrorActionPreference = "Stop"

$pythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }

$versionOutput = & $pythonBin --version
Write-Host "Menggunakan: $versionOutput"
if ($versionOutput -notmatch "3\.11") {
    Write-Warning "Python yang terdeteksi bukan 3.11.x ($versionOutput). Pastikan Python 3.11.2 terinstall dan ada di PATH, atau set env var PYTHON_BIN ke path python.exe yang benar."
}

& $pythonBin -m venv .venv

& .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "File .env dibuat dari .env.example - WAJIB edit ADMIN_API_KEY sebelum production."
}

New-Item -ItemType Directory -Force -Path images | Out-Null
New-Item -ItemType Directory -Force -Path data\face_index | Out-Null

Write-Host ""
Write-Host "Setup selesai. Selanjutnya:"
Write-Host "  1) Taruh foto karyawan di folder images\ (format EMP001.jpg dst.)"
Write-Host "  2) Jalankan: .\run_dev.ps1   (development, auto-reload)"
Write-Host "     atau:      .\run_prod.ps1  (gunicorn, multi-worker)"
