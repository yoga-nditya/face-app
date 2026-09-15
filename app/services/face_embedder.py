"""
Face embedding generation.

Model di-load sekali (module-level singleton via face_recognition/dlib) dan
dipakai ulang di setiap request — TIDAK load/unload per-request (Section 22).
"""
from __future__ import annotations

import face_recognition
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

EMBEDDING_DIM = 128  # dlib ResNet face encoder output size
MODEL_VERSION = settings.EMBEDDING_MODEL_VERSION


def warm_up() -> None:
    """
    Dipanggil sekali saat startup untuk memastikan model dlib ter-load ke
    memory sebelum request pertama datang (menghindari cold-start latency
    pada request user pertama).
    """
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)
    face_recognition.face_encodings(dummy, known_face_locations=[(10, 90, 90, 10)])
    logger.info("face_embedder warmed up (model_version=%s)", MODEL_VERSION)


def generate_embedding(rgb_image: np.ndarray, face_location: tuple[int, int, int, int]) -> np.ndarray:
    """
    Generate 128-d embedding vector untuk satu wajah yang sudah terdeteksi.
    `face_location` = (top, right, bottom, left), hasil dari face_detector.
    """
    encodings = face_recognition.face_encodings(
        rgb_image, known_face_locations=[face_location], num_jitters=1
    )
    if not encodings:
        raise ValueError("Failed to generate embedding for detected face")
    return encodings[0].astype(np.float32)
