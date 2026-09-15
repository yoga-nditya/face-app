# Face Recognition Attendance API (tanpa database)

Versi ini **tidak memakai database sama sekali**. Satu-satunya sumber
kebenaran adalah folder `images/`:

- Nama file = nama orang.
- Ada wajah yang cocok dengan salah satu foto di `images/` → terdeteksi,
  dan nama yang dikembalikan diambil langsung dari nama file itu.
- Tidak ada wajah yang cocok → tidak terdeteksi.

Tidak ada lagi tabel `employees`, tidak ada `employee_code`, tidak ada
SQLite/SQLAlchemy. Absen (`/attendance/check-in`) dicatat ke file teks
sederhana (`data/attendance_log.jsonl`), bukan ke database.

## Konvensi nama file di `images/`

```
images/
  agoy.jpeg              -> dikenali sebagai "Agoy"
  satrio.jpeg             -> dikenali sebagai "Satrio"
  budi_santoso.jpg        -> "Budi Santoso"
  budi_santoso_1.jpg      -> foto ke-2 utk orang yang sama "Budi Santoso"
  budi_santoso (2).jpg    -> foto ke-3 utk orang yang sama "Budi Santoso"
```

Boleh (dan disarankan) taruh 2–3 foto per orang untuk akurasi lebih baik —
tambahkan angka/urutan di belakang nama file, sistem otomatis menganggapnya
foto orang yang sama.

## Flow

```
images/ (kamu kelola manual, tambah/hapus/replace foto)
   │  SHA-256 hash per file → deteksi file baru/berubah/dihapus
   ▼
Face Index Builder (scripts/build_face_index.py, atau startup/admin rebuild)
   │  nama orang = diambil dari nama file (lihat konvensi di atas)
   ▼
data/face_index/index.json   (cache embedding, tidak pernah diexpose via API)

Client → POST foto ──▶ FastAPI
                           ├─ face_detector    (deteksi wajah + quality gate)
                           ├─ liveness_service (stub, MVP pass-through)
                           ├─ face_embedder    (128-d embedding, model loaded once)
                           ├─ face_matcher     (face_distance/Euclidean vs index, tolerance)
                           └─ (opsional) attendance_log (file .jsonl, bukan DB)
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # dlib butuh waktu lebih lama jika wheel prebuilt tidak tersedia

cp .env.example .env
# edit .env, WAJIB ganti ADMIN_API_KEY

# taruh foto referensi di images/, contoh:
#   images/budi.jpg
#   images/siti_aminah.jpg
```

## Jalankan (dev)

```bash
chmod +x run_dev.sh
./run_dev.sh
# atau manual:
uvicorn app.main:app --reload --port 8000
```

Saat startup, server otomatis scan `images/`, bangun/refresh face index, lalu
siap menerima request.

## Endpoint

### `POST /api/v1/face/recognize`
Upload satu foto (`multipart/form-data`, field `image`). Kembalikan nama
orang yang cocok (dari nama file di `images/`) + confidence score. Tidak
menulis apapun ke log/attendance — murni "siapa ini?".

Contoh:
```bash
curl -X POST http://localhost:8000/api/v1/face/recognize \
  -F "image=@/path/ke/foto.jpg"
```

Respons sukses:
```json
{
  "success": true,
  "code": "FACE_MATCHED",
  "person": { "name": "Satrio" },
  "confidence": 0.7231
}
```

Respons kalau tidak dikenali (404):
```json
{ "success": false, "code": "FACE_NOT_RECOGNIZED", "message": "Face was not recognized" }
```

### `POST /api/v1/attendance/check-in`
Sama seperti `/recognize`, tapi kalau cocok akan dicatat ke
`data/attendance_log.jsonl` (bukan database). Ada jeda minimum antar-absen
(`MIN_SECONDS_BETWEEN_ATTENDANCE` di `.env`) untuk mencegah duplikat.

### `POST /api/v1/admin/face-index/rebuild`
Header `X-API-Key: <ADMIN_API_KEY>`. Scan ulang `images/` (tambah/hapus/
ubah foto langsung kedeteksi tanpa restart server).

## CLI tanpa server

```bash
python scripts/build_face_index.py       # build/refresh index dari images/
python scripts/recognize.py foto.jpg      # cek satu foto langsung dari terminal
```

## Metode matching (disamakan dengan versi kamera)

Sekarang pakai fungsi bawaan library `face_recognition`: `face_distance()`
(jarak Euclidean antar-encoding 128 dimensi), **bukan** cosine similarity
custom seperti versi sebelumnya. Ini metode yang sama persis dipakai versi
kamera (`recognition_engine.py`), dan memang cara yang direkomendasikan
oleh pembuat library-nya — jauh lebih toleran terhadap variasi wajar
seperti gaya rambut beda, pakai/lepas kacamata, atau sudut wajah sedikit
berbeda, karena modelnya sendiri dilatih & dikalibrasi berbasis jarak ini.

`FACE_MATCH_TOLERANCE` di `.env` (default `0.5`, sama seperti versi kamera)
menentukan batas jarak maksimum sebelum dianggap "cocok" — **makin KECIL
nilainya, makin ketat**:
- Orang beda sering ketuker jadi orang lain → turunkan (mis. `0.45`).
- Orang yang benar sering gagal terdeteksi (misal gara-gara ganti gaya
  rambut/kacamata) → naikkan sedikit (mis. `0.55` atau `0.6`).

Cara mengecek jarak sebenarnya untuk satu foto: `python scripts/recognize.py foto.jpg`
— akan menampilkan `Distance` dan `Confidence` mentahnya.

Tips tambahan untuk daya tahan terhadap perubahan penampilan: taruh 2-3
foto per orang di `images/` dengan variasi (pakai kacamata / tidak,
gaya rambut beda) — sistem otomatis pilih jarak terkecil dari semua foto
referensi orang itu, jadi makin banyak variasi foto referensi, makin
toleran hasil deteksinya.

## Yang dihapus dari versi sebelumnya

- `app/models/`, `app/repositories/` (SQLAlchemy models + repo) → dihapus.
- `DATABASE_URL`, `sqlalchemy` di `requirements.txt` → dihapus.
- Konsep `employee_code` yang harus match ke baris database → diganti
  langsung dengan nama dari nama file gambar.
- Attendance sekarang disimpan sebagai file `.jsonl`, bukan tabel SQL.
- Matching diganti dari cosine similarity custom ke `face_recognition.face_distance()`
  (Euclidean, standar library, sama seperti versi kamera) — lebih toleran
  terhadap variasi gaya rambut/kacamata/sudut wajah.
