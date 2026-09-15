"""
Central configuration. Semua nilai wajib dapat di-override lewat environment
variable (.env) — jangan hardcode secret / path di kode lain.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Paths ---
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    IMAGES_DIR: Path = BASE_DIR / "images"
    FACE_INDEX_DIR: Path = BASE_DIR / "data" / "face_index"
    FACE_INDEX_FILE: Path = FACE_INDEX_DIR / "index.json"

    # --- Face recognition model ---
    # "hog" = CPU only, cepat tapi recall lebih rendah.
    # "cnn" = lebih akurat, butuh GPU untuk performa layak.
    FACE_DETECTION_MODEL: str = "hog"
    EMBEDDING_MODEL_VERSION: str = "dlib_resnet_v1"

    # --- Matching ---
    # Metode SAMA seperti versi kamera: face_recognition.face_distance()
    # (Euclidean distance antar-encoding), BUKAN cosine similarity.
    # Semakin KECIL nilainya -> semakin ketat. Default 0.5 sama seperti
    # versi kamera, cukup toleran terhadap gaya rambut/kacamata berbeda.
    # Kalau orang yang benar sering gagal terdeteksi -> naikkan ke 0.55-0.6.
    # Kalau orang beda sering ketuker -> turunkan ke 0.45.
    FACE_MATCH_TOLERANCE: float = 0.5

    # --- Image quality gates ---
    MIN_FACE_WIDTH_PX: int = 80
    MIN_BRIGHTNESS: float = 40.0
    MAX_BRIGHTNESS: float = 220.0
    BLUR_LAPLACIAN_THRESHOLD: float = 25.0

    # --- Attendance rules ---
    MIN_SECONDS_BETWEEN_ATTENDANCE: int = 60  # cegah duplicate check-in beruntun
    TIMEZONE: str = "Asia/Jakarta"

    # --- Security ---
    ADMIN_API_KEY: str = "change-me-in-env"
    LOG_LEVEL: str = "INFO"


settings = Settings()

# Pastikan direktori penting selalu ada.
settings.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
settings.FACE_INDEX_DIR.mkdir(parents=True, exist_ok=True)