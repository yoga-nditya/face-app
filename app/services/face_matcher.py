"""
Face matching — pakai metode BAWAAN library `face_recognition`
(face_distance / Euclidean distance antar 128-d encoding), sama persis
seperti yang dipakai versi kamera (recognition_engine.py).

Kenapa ganti dari cosine similarity ke ini:
- Model dlib_resnet_v1 yang dipakai `face_recognition` dilatih & dikalibrasi
  memakai jarak Euclidean, bukan cosine similarity. Threshold yang umum
  dipakai komunitas (dan versi kamera kamu) adalah tolerance ~0.5-0.6.
- Hasilnya jauh lebih toleran terhadap variasi wajar: gaya rambut beda,
  pakai/lepas kacamata, sedikit beda sudut/ekspresi — karena memang begitu
  cara model ini "dimaksudkan" untuk dipakai.
- Tidak perlu kalibrasi manual yang rumit seperti cosine similarity kemarin.

Cara kerja: distance 0.0 = identik, semakin besar semakin beda. Kalau
distance <= FACE_MATCH_TOLERANCE -> dianggap orang yang sama.
"""
from __future__ import annotations

from dataclasses import dataclass

import face_recognition
import numpy as np

from app.core.config import settings
from app.services.image_index import FaceIndex


@dataclass
class MatchResult:
    matched: bool
    name: str | None
    distance: float  # 0.0 = identik, makin besar makin beda
    confidence: float  # nilai 0-1 untuk ditampilkan ke user (bukan dasar keputusan)


def find_best_match(query_embedding: np.ndarray, index: FaceIndex) -> MatchResult:
    """
    Bandingkan satu wajah query ke SEMUA foto referensi di index (semua
    orang, semua foto per orang) sekaligus, ambil yang jaraknya paling
    kecil (paling mirip) — persis seperti alur di versi kamera.
    """
    all_encodings: list[np.ndarray] = []
    all_names: list[str] = []

    for entry in index.entries.values():
        for emb in entry.embeddings:
            all_encodings.append(emb)
            all_names.append(entry.name)

    if not all_encodings:
        return MatchResult(matched=False, name=None, distance=1.0, confidence=0.0)

    distances = face_recognition.face_distance(all_encodings, query_embedding)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])
    confidence = round(max(0.0, 1.0 - best_distance), 4)

    if best_distance <= settings.FACE_MATCH_TOLERANCE:
        return MatchResult(
            matched=True, name=all_names[best_idx], distance=best_distance, confidence=confidence
        )

    return MatchResult(matched=False, name=None, distance=best_distance, confidence=confidence)
