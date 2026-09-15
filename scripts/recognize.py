"""
CLI recognition tanpa server, untuk debugging / uji cepat model & threshold.

Usage:
    python scripts/recognize.py path/to/photo.jpg
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import face_embedder, face_matcher, image_index  # noqa: E402
from app.services.face_detector import FaceDetectionError, detect_single_face  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/recognize.py <image_path>")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"File not found: {image_path}")
        sys.exit(1)

    index = image_index.load_index()
    if not index.entries:
        print("Face index is empty. Run scripts/build_face_index.py first.")
        sys.exit(1)

    image_bytes = image_path.read_bytes()
    try:
        rgb_image, face = detect_single_face(image_bytes)
    except FaceDetectionError as exc:
        print(f"Result: {exc.issue.value} - {exc.message}")
        sys.exit(1)

    embedding = face_embedder.generate_embedding(rgb_image, face.location)
    match = face_matcher.find_best_match(embedding, index)

    if match.matched:
        print(f"Name: {match.name}")
        print(f"Distance: {match.distance:.4f}  (tolerance: <= {face_matcher.settings.FACE_MATCH_TOLERANCE})")
        print(f"Confidence: {match.confidence:.4f}")
        print("Result: MATCHED")
    else:
        print(f"Distance: {match.distance:.4f}  (tolerance: <= {face_matcher.settings.FACE_MATCH_TOLERANCE})")
        print("Result: NOT_MATCHED")


if __name__ == "__main__":
    main()
