"""
CLI untuk build/rebuild face index tanpa menjalankan server.

Usage:
    python scripts/build_face_index.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import image_index  # noqa: E402


def main() -> None:
    print(f"Scanning images from: {image_index.settings.IMAGES_DIR}")
    existing = image_index.load_index()
    started = time.perf_counter()
    new_index, stats = image_index.build_or_update_index(existing)
    image_index.save_index(new_index)
    duration_ms = int((time.perf_counter() - started) * 1000)

    print(f"Total images   : {stats['total_images']}")
    print(f"Processed (new): {stats['processed']}")
    print(f"Unchanged      : {stats['unchanged']}")
    print(f"Failed         : {stats['failed']}")
    print(f"People in index  : {len(new_index.entries)}")
    print(f"Duration       : {duration_ms}ms")
    print(f"Index saved to : {image_index.settings.FACE_INDEX_FILE}")


if __name__ == "__main__":
    main()
