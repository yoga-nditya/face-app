"""
Face detection + image quality gate.

Dipisah dari embedding secara sengaja: detection harus murah dan cepat,
sedangkan embedding lebih berat. Ini juga memungkinkan model detector
diganti (mis. HOG -> CNN -> RetinaFace) tanpa menyentuh service lain.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import cv2
import face_recognition
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QualityIssue(str, Enum):
    NO_FACE = "NO_FACE"
    MULTIPLE_FACES = "MULTIPLE_FACES"
    LOW_QUALITY_BLUR = "FACE_IMAGE_LOW_QUALITY_BLUR"
    LOW_QUALITY_BRIGHTNESS = "FACE_IMAGE_LOW_QUALITY_BRIGHTNESS"
    LOW_QUALITY_SIZE = "FACE_IMAGE_LOW_QUALITY_SIZE"


@dataclass
class DetectedFace:
    location: tuple[int, int, int, int]  # (top, right, bottom, left)
    width_px: int
    height_px: int


class FaceDetectionError(Exception):
    def __init__(self, issue: QualityIssue, message: str):
        self.issue = issue
        self.message = message
        super().__init__(message)


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode raw upload bytes to an RGB numpy array. Never persisted, never logged."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FaceDetectionError(QualityIssue.NO_FACE, "Unable to decode image")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _check_brightness(rgb_image: np.ndarray, box: tuple[int, int, int, int]) -> None:
    top, right, bottom, left = box
    crop = rgb_image[max(top, 0):bottom, max(left, 0):right]
    if crop.size == 0:
        return
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    mean_brightness = float(gray.mean())
    if not (settings.MIN_BRIGHTNESS <= mean_brightness <= settings.MAX_BRIGHTNESS):
        raise FaceDetectionError(
            QualityIssue.LOW_QUALITY_BRIGHTNESS,
            f"Brightness {mean_brightness:.1f} outside acceptable range",
        )


def _check_blur(rgb_image: np.ndarray, box: tuple[int, int, int, int]) -> None:
    top, right, bottom, left = box
    crop = rgb_image[max(top, 0):bottom, max(left, 0):right]
    if crop.size == 0:
        return
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < settings.BLUR_LAPLACIAN_THRESHOLD:
        raise FaceDetectionError(
            QualityIssue.LOW_QUALITY_BLUR, f"Blur variance {variance:.1f} too low"
        )


def _check_size(box: tuple[int, int, int, int]) -> None:
    top, right, bottom, left = box
    width = right - left
    if width < settings.MIN_FACE_WIDTH_PX:
        raise FaceDetectionError(
            QualityIssue.LOW_QUALITY_SIZE, f"Face width {width}px below minimum"
        )


def detect_single_face(image_bytes: bytes, *, enforce_quality: bool = True) -> tuple[np.ndarray, DetectedFace]:
    """
    Deteksi tepat satu wajah pada gambar dan jalankan quality gate.

    Raises FaceDetectionError dengan issue code sesuai Section 11/16 spec:
    NO_FACE, MULTIPLE_FACES, atau salah satu LOW_QUALITY_*.
    """
    rgb_image = _decode_image(image_bytes)

    locations = face_recognition.face_locations(rgb_image, model=settings.FACE_DETECTION_MODEL)

    if len(locations) == 0:
        raise FaceDetectionError(QualityIssue.NO_FACE, "No face detected in image")
    if len(locations) > 1:
        raise FaceDetectionError(QualityIssue.MULTIPLE_FACES, "More than one face detected")

    box = locations[0]  # (top, right, bottom, left)

    if enforce_quality:
        _check_size(box)
        _check_brightness(rgb_image, box)
        _check_blur(rgb_image, box)

    top, right, bottom, left = box
    face = DetectedFace(location=box, width_px=right - left, height_px=bottom - top)
    return rgb_image, face
