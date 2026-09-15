#!/usr/bin/env bash
# setup.sh - Setup environment tanpa Docker, khusus macOS/Linux.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3.11}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.11 tidak ditemukan sebagai '$PYTHON_BIN'."
    echo "Install Python 3.11.2 dulu, atau set PYTHON_BIN ke path python3.11 kamu."
    echo "Contoh: PYTHON_BIN=/usr/local/bin/python3.11 ./setup.sh"
    exit 1
fi

echo "Menggunakan: $("$PYTHON_BIN" --version)"

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "File .env dibuat dari .env.example - WAJIB edit ADMIN_API_KEY sebelum production."
fi

mkdir -p images data/face_index

echo ""
echo "Setup selesai. Selanjutnya:"
echo "  1) Taruh foto karyawan di folder images/ (format EMP001.jpg dst.)"
echo "  2) Jalankan: ./run_dev.sh   (development, auto-reload)"
echo "     atau:      ./run_prod.sh  (gunicorn, multi-worker)"
