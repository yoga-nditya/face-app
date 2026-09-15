"""
Unit test untuk ekstraksi nama dari filename (tanpa database) dan logika
face_matcher (memakai face_recognition.face_distance, sama seperti versi
kamera). Test end-to-end recognition (butuh model dlib + sample face
images) sebaiknya dijalankan terpisah sebagai integration test dengan
dataset di tests/fixtures/.
"""
from __future__ import annotations

import numpy as np

from app.services.image_index import _extract_name


def test_extract_name_simple():
    assert _extract_name("budi.jpg") == "Budi"


def test_extract_name_with_underscore():
    assert _extract_name("budi_santoso.jpg") == "Budi Santoso"


def test_extract_name_with_dash():
    assert _extract_name("budi-santoso.jpg") == "Budi Santoso"


def test_extract_name_strips_trailing_photo_index():
    assert _extract_name("budi_santoso_1.jpg") == "Budi Santoso"
    assert _extract_name("budi_santoso-02.jpg") == "Budi Santoso"
    assert _extract_name("budi_santoso (3).jpg") == "Budi Santoso"


def test_find_best_match_picks_closest_person():
    from app.services import face_matcher
    from app.services.image_index import FaceIndex, PersonIndexEntry

    # Encoding "dummy" 3 dimensi hanya untuk uji logika argmin, bukan
    # encoding wajah sungguhan (yang asli 128 dimensi dari dlib).
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    index = FaceIndex(
        entries={
            "budi": PersonIndexEntry(name="Budi", embeddings=[np.array([1.0, 0.05, 0.0], dtype=np.float32)]),
            "siti": PersonIndexEntry(name="Siti", embeddings=[np.array([0.0, 1.0, 0.0], dtype=np.float32)]),
        }
    )
    match = face_matcher.find_best_match(query, index)
    assert match.matched is True
    assert match.name == "Budi"
