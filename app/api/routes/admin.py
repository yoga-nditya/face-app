from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.api.schemas import RebuildResponse
from app.core.logging import get_logger
from app.core.security import require_admin
from app.services import image_index

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])
logger = get_logger(__name__)


@router.post("/face-index/rebuild", response_model=RebuildResponse)
async def rebuild_face_index(request: Request):
    """
    Manual rebuild trigger. Protected via X-API-Key header. Scan ulang
    folder images/ dan cocokkan dengan index lama (hash-based), bukan
    full recompute.
    """
    started = time.perf_counter()
    existing = request.app.state.face_index
    new_index, stats = image_index.build_or_update_index(existing)
    image_index.save_index(new_index)
    request.app.state.face_index = new_index
    duration_ms = int((time.perf_counter() - started) * 1000)

    logger.info("Face index rebuilt: %s (duration_ms=%d)", stats, duration_ms)

    return RebuildResponse(
        total_images=stats["total_images"],
        processed=stats["processed"] + stats["unchanged"],
        failed=stats["failed"],
        people_in_index=len(new_index.entries),
        duration_ms=duration_ms,
    )
