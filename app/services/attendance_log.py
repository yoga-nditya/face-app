"""
Attendance log tanpa database.

Setiap check-in yang berhasil dicatat sebagai satu baris JSON di
data/attendance_log.jsonl (append-only, gampang dibuka lewat Excel/Sheets
kalau perlu). Pencegahan duplicate check-in beruntun dilakukan dengan
menyimpan "terakhir absen jam berapa" per nama di memory (di-load ulang
dari file log saat startup).
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_last_seen: dict[str, datetime] = {}  # name_key -> waktu absen terakhir


@dataclass
class AttendanceRecord:
    name: str
    timestamp: datetime
    confidence: float  # 0-1, makin tinggi makin yakin


class AttendanceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _log_path():
    settings.FACE_INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    return settings.FACE_INDEX_DIR.parent / "attendance_log.jsonl"


def load_last_seen() -> None:
    """Dipanggil sekali saat startup supaya aturan anti-duplicate tetap
    berlaku walau server baru saja di-restart."""
    path = _log_path()
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                ts = datetime.fromisoformat(data["timestamp"])
                key = data["name"].strip().lower()
                if key not in _last_seen or ts > _last_seen[key]:
                    _last_seen[key] = ts
            except Exception:  # noqa: BLE001 - baris rusak, lewati saja
                continue
    logger.info("Attendance log loaded: %d orang punya riwayat absen", len(_last_seen))


def record_check_in(name: str, confidence: float) -> AttendanceRecord:
    key = name.strip().lower()
    now = datetime.now(timezone.utc)

    with _lock:
        last = _last_seen.get(key)
        if last is not None:
            elapsed = (now - last).total_seconds()
            if elapsed < settings.MIN_SECONDS_BETWEEN_ATTENDANCE:
                raise AttendanceError(
                    "DUPLICATE_ATTENDANCE",
                    f"Attendance already recorded {int(elapsed)}s ago",
                )

        record = AttendanceRecord(name=name, timestamp=now, confidence=confidence)
        with _log_path().open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "name": record.name,
                        "timestamp": record.timestamp.isoformat(),
                        "confidence": round(record.confidence, 4),
                    }
                )
                + "\n"
            )
        _last_seen[key] = now

    return record
