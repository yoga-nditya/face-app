"""
Liveness / anti-spoofing.

MVP: recognition-only, TIDAK melakukan liveness check nyata (Section 17).
Module ini sengaja diletakkan sebagai seam terpisah supaya model
anti-spoofing (mis. passive liveness dari single frame, atau challenge-response)
bisa ditambahkan nanti tanpa mengubah recognition/attendance flow.

Ancaman yang perlu ditangani ketika liveness diaktifkan:
- printed photo
- screenshot / foto dari layar HP lain
- replay video
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LivenessResult:
    is_live: bool
    score: float
    enabled: bool


def check_liveness(image_bytes: bytes) -> LivenessResult:
    """
    Stub MVP: selalu meloloskan sebagai "live" dengan enabled=False supaya
    caller dapat membedakan "belum diimplementasi" vs "gagal liveness check".
    Ganti isi fungsi ini dengan model anti-spoofing tanpa mengubah signature.
    """
    return LivenessResult(is_live=True, score=1.0, enabled=False)
