from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import admin, attendance, recognition
from app.core.logging import get_logger, setup_logging
from app.services import attendance_log, face_embedder, image_index

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup (tanpa database sama sekali):
    1. load model face recognition
    2. load face index dari disk (cache)
    3. scan folder images/, validasi & incremental-rebuild berdasarkan
       hash file (foto baru/berubah/dihapus otomatis terdeteksi)
    4. load riwayat absen dari file log (untuk aturan anti-duplicate)
    5. ready menerima request
    """
    logger.info("Starting up: warming up face embedding model")
    face_embedder.warm_up()

    logger.info("Starting up: loading face index from disk")
    existing_index = image_index.load_index()

    logger.info("Starting up: validating index against images/ (hash check, incremental rebuild)")
    fresh_index, stats = image_index.build_or_update_index(existing_index)
    image_index.save_index(fresh_index)

    app.state.face_index = fresh_index
    logger.info(
        "Startup complete. Face index stats: %s | people recognized: %d",
        stats,
        len(fresh_index.entries),
    )

    attendance_log.load_last_seen()

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="Face Recognition Attendance API (tanpa database)",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(recognition.router)
app.include_router(attendance.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
