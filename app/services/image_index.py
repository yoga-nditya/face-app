"""
Face Index: pipeline images/ -> detect -> embed -> persisted index.

PERUBAHAN UTAMA (versi tanpa database):
- Identitas seseorang (nama) diambil LANGSUNG dari nama file di folder
  images/, bukan dari tabel database. Folder images/ adalah satu-satunya
  sumber kebenaran, baik untuk biometric (wajah) maupun nama.
- Tidak ada lagi "employee_code" yang harus dicocokkan ke baris database.
  Cukup: ada foto di images/ + ada wajah terdeteksi di foto itu = orang itu
  otomatis dikenali dengan nama dari nama filenya.

Index TIDAK pernah dihitung ulang penuh setiap request. Perubahan pada
folder images/ (file baru, berubah, dihapus) terdeteksi lewat SHA-256 hash
per file sehingga rebuild hanya dilakukan untuk orang yang benar-benar
berubah fotonya.

Konvensi penamaan file di images/:
    budi.jpg                -> nama: "Budi"
    budi_santoso.jpg        -> nama: "Budi Santoso"
    budi-santoso.jpg        -> nama: "Budi Santoso"
    budi_santoso_1.jpg      -> nama: "Budi Santoso" (foto kedua orang yang sama)
    budi_santoso (2).jpg    -> nama: "Budi Santoso" (foto ketiga orang yang sama)

Boleh taruh beberapa foto untuk orang yang sama (disarankan, hasil lebih
akurat) selama nama dasarnya sama - cukup tambahkan angka/urutan di
belakang nama.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.services import face_embedder
from app.services.face_detector import FaceDetectionError, detect_single_face

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Menghapus akhiran angka/urutan foto: "_1", "-2", " (3)", " 4" di ujung nama file
# sehingga "budi_1.jpg" dan "budi_2.jpg" dianggap orang yang sama: "budi".
_TRAILING_INDEX_PATTERN = re.compile(r"[\s_\-]*\(?\d+\)?$")


@dataclass
class PersonIndexEntry:
    """Satu orang di dalam index, diidentifikasi dari nama file gambar."""

    name: str  # nama tampilan, contoh: "Budi Santoso"
    embeddings: list[np.ndarray] = field(default_factory=list)
    source_files: dict[str, str] = field(default_factory=dict)  # filename -> sha256 hash
    model_version: str = face_embedder.MODEL_VERSION


@dataclass
class FaceIndex:
    # key = nama dinormalisasi lowercase, dipakai untuk grouping antar file
    entries: dict[str, PersonIndexEntry] = field(default_factory=dict)
    built_at: float = 0.0


def _extract_name(filename: str) -> str | None:
    """
    Ambil nama orang dari nama file.
    Contoh: "budi_santoso_1.jpeg" -> "Budi Santoso"
    """
    stem = Path(filename).stem.strip()
    if not stem:
        return None

    # Buang akhiran angka/urutan foto (mis. "_1", "-02", " (3)")
    without_index = _TRAILING_INDEX_PATTERN.sub("", stem).strip()
    base = without_index if without_index else stem

    # Normalisasi pemisah kata (_ dan -) jadi spasi, lalu Title Case tiap kata
    normalized = re.sub(r"[_\-]+", " ", base).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    if not normalized:
        return None

    name = " ".join(word.capitalize() for word in normalized.split(" "))
    return name


def _name_key(name: str) -> str:
    """Key untuk grouping antar-file milik orang yang sama."""
    return name.strip().lower()


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _scan_images_dir() -> dict[str, tuple[str, list[Path]]]:
    """Return {name_key: (display_name, [image_paths])} dari folder images/."""
    grouped: dict[str, tuple[str, list[Path]]] = {}
    if not settings.IMAGES_DIR.exists():
        return grouped

    for path in sorted(settings.IMAGES_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        name = _extract_name(path.name)
        if not name:
            logger.warning("Skipping file with unparseable name: %s", path.name)
            continue
        key = _name_key(name)
        if key not in grouped:
            grouped[key] = (name, [])
        grouped[key][1].append(path)

    return grouped


def _embed_image_file(path: Path) -> np.ndarray | None:
    try:
        image_bytes = path.read_bytes()
        rgb_image, face = detect_single_face(image_bytes, enforce_quality=False)
        embedding = face_embedder.generate_embedding(rgb_image, face.location)
        return embedding
    except FaceDetectionError as exc:
        logger.error("Reference image failed quality/detection check: %s (%s)", path.name, exc.issue)
        return None
    except Exception:  # noqa: BLE001 - log dan skip, jangan crash seluruh build
        logger.exception("Unexpected error embedding reference image: %s", path.name)
        return None


def build_or_update_index(existing: FaceIndex | None = None) -> tuple[FaceIndex, dict]:
    """
    Scan images/, bandingkan hash terhadap index lama, dan hanya
    generate ulang embedding untuk file yang baru/berubah. Orang yang
    seluruh file gambarnya sudah hilang akan otomatis hilang dari index
    (tidak akan pernah terdeteksi lagi sampai fotonya ditambahkan lagi).
    """
    grouped = _scan_images_dir()
    old_entries = existing.entries if existing else {}

    new_entries: dict[str, PersonIndexEntry] = {}
    stats = {"total_images": 0, "processed": 0, "failed": 0, "unchanged": 0}

    for name_key, (display_name, paths) in grouped.items():
        old_entry = old_entries.get(name_key)
        entry = PersonIndexEntry(name=display_name)

        for path in paths:
            stats["total_images"] += 1
            current_hash = _file_hash(path)
            old_hash = old_entry.source_files.get(path.name) if old_entry else None

            if old_entry and old_hash == current_hash and old_entry.model_version == face_embedder.MODEL_VERSION:
                # Tidak berubah -> reuse embedding lama, jangan compute ulang.
                idx = list(old_entry.source_files.keys()).index(path.name)
                entry.embeddings.append(old_entry.embeddings[idx])
                entry.source_files[path.name] = current_hash
                stats["unchanged"] += 1
                continue

            embedding = _embed_image_file(path)
            if embedding is None:
                stats["failed"] += 1
                continue

            entry.embeddings.append(embedding)
            entry.source_files[path.name] = current_hash
            stats["processed"] += 1

        if entry.embeddings:
            new_entries[name_key] = entry
        else:
            logger.warning("%s has no valid embeddings, excluded from index", display_name)

    removed = set(old_entries.keys()) - set(new_entries.keys())
    if removed:
        removed_names = [old_entries[k].name for k in removed]
        logger.info("Removed from index (image deleted/invalid): %s", sorted(removed_names))

    index = FaceIndex(entries=new_entries, built_at=time.time())
    return index, stats


def save_index(index: FaceIndex) -> None:
    payload = {
        "built_at": index.built_at,
        "model_version": face_embedder.MODEL_VERSION,
        "people": {
            key: {
                "name": entry.name,
                "embeddings": [emb.tolist() for emb in entry.embeddings],
                "source_files": entry.source_files,
                "model_version": entry.model_version,
            }
            for key, entry in index.entries.items()
        },
    }
    settings.FACE_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = settings.FACE_INDEX_FILE.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload))
    tmp_path.replace(settings.FACE_INDEX_FILE)  # atomic write


def load_index() -> FaceIndex:
    if not settings.FACE_INDEX_FILE.exists():
        return FaceIndex()

    raw = json.loads(settings.FACE_INDEX_FILE.read_text())
    entries: dict[str, PersonIndexEntry] = {}
    for key, data in raw.get("people", {}).items():
        entries[key] = PersonIndexEntry(
            name=data.get("name", key),
            embeddings=[np.array(e, dtype=np.float32) for e in data["embeddings"]],
            source_files=data["source_files"],
            model_version=data.get("model_version", face_embedder.MODEL_VERSION),
        )
    return FaceIndex(entries=entries, built_at=raw.get("built_at", 0.0))
