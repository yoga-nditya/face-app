from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import get_face_index
from app.api.schemas import ErrorResponse, PersonOut, RecognizeSuccess
from app.core.logging import get_logger
from app.services import face_embedder, face_matcher
from app.services.face_detector import FaceDetectionError, detect_single_face
from app.services.image_index import FaceIndex

router = APIRouter(prefix="/api/v1/face", tags=["recognition"])
logger = get_logger(__name__)

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB


@router.post(
    "/recognize",
    response_model=RecognizeSuccess,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def recognize_face(
    image: UploadFile = File(...),
    index: FaceIndex = Depends(get_face_index),
):
    """
    Recognition murni, tanpa database sama sekali: ambil wajah dari foto
    yang diupload, bandingkan langsung ke seluruh foto di folder images/.
    Kalau cocok -> kembalikan nama (diambil dari nama file gambar itu).
    Endpoint ini TIDAK menulis attendance - lihat /api/v1/attendance/check-in.
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

    query_embedding = face_embedder.generate_embedding(rgb_image, face.location)
    match = face_matcher.find_best_match(query_embedding, index)

    if not match.matched:
        logger.info("Face not recognized (best_distance=%.4f)", match.distance)
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                code=404, reason="FACE_NOT_RECOGNIZED", message="Face was not recognized"
            ).model_dump(),
        )

    return RecognizeSuccess(
        person=PersonOut(name=match.name),
        confidence=match.confidence,
    )