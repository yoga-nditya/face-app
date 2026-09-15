"""
Auth dependency sederhana untuk endpoint admin (Section 9/21/27).
Untuk production, ganti dengan mekanisme auth organisasi yang sesungguhnya
(OAuth2/JWT, mTLS, dsb.) - API key di sini adalah baseline minimum, bukan
solusi akhir.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_admin(x_api_key: str = Header(default="")) -> None:
    if not x_api_key or x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
