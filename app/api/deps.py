from __future__ import annotations

from fastapi import Request

from app.services.image_index import FaceIndex


def get_face_index(request: Request) -> FaceIndex:
    """
    Index disimpan in-memory di app.state, di-load sekali saat startup dan
    hanya diperbarui lewat rebuild (startup check atau admin endpoint) —
    TIDAK pernah dihitung ulang per-request.
    """
    return request.app.state.face_index
