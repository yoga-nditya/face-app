from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import get_face_index
from app.api.schemas import AttendanceOut, CheckInSuccess, ErrorResponse, PersonOut
from app.core.logging import get_logger
from app.services import attendance_log, face_embedder, face_matcher
from app.services.attendance_log import AttendanceError
from app.services.face_detector import FaceDetectionError, detect_single_face
from app.services.image_index import FaceIndex
from app.services.liveness_service import check_liveness

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])
logger = get_logger(__name__)

MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@router.post(
    "/check-in",
    response_model=CheckInSuccess,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def check_in(
    image: UploadFile = File(...),
    index: FaceIndex = Depends(get_face_index),
):
    """
    Flow: upload -> detect -> quality -> liveness -> embed -> match
    ke folder images/ -> catat absen (file log, tanpa database).
    """
    image_bytes = await image.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                code=422, reason="IMAGE_TOO_LARGE", message="Image exceeds max upload size"
            ).model_dump(),
        )

    try:
        rgb_image, face = detect_single_face(image_bytes)
    except FaceDetectionError as exc:
        status_code = 422 if "LOW_QUALITY" in exc.issue.value else 400
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=status_code, reason=exc.issue.value, message=exc.message).model_dump(),
        )

    liveness = check_liveness(image_bytes)
    if liveness.enabled and not liveness.is_live:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(code=400, reason="LIVENESS_FAILED", message="Liveness check failed").model_dump(),
        )

    query_embedding = face_embedder.generate_embedding(rgb_image, face.location)
    match = face_matcher.find_best_match(query_embedding, index)

    if not match.matched:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                code=404, reason="FACE_NOT_RECOGNIZED", message="Face was not recognized"
            ).model_dump(),
        )

    try:
        record = attendance_log.record_check_in(match.name, match.confidence)
    except AttendanceError as exc:
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(code=409, reason=exc.code, message=exc.message).model_dump(),
        )

    return CheckInSuccess(
        person=PersonOut(name=record.name),
        attendance=AttendanceOut(timestamp=record.timestamp.isoformat(), confidence=record.confidence),
    )