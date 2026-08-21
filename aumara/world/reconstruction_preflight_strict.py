#!/usr/bin/env python3
"""Strict AUMARA preflight pass: collapse resized/cropped derivatives before overlap QA."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

import reconstruction_preflight as base


def collect_strict() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    exact_dupes: list[dict[str, Any]] = []
    near_dupes: list[dict[str, Any]] = []
    seen_sha: dict[str, str] = {}
    kept_hashes: list[tuple[int, str]] = []

    for path in sorted(base.ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in base.IMAGE_SUFFIXES:
            continue
        try:
            digest = base.sha256(path)
            if digest in seen_sha:
                exact_dupes.append({"path": str(path), "same_as": seen_sha[digest], "sha256": digest})
                continue
            with Image.open(path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
                exif = opened.getexif()
                width, height = image.size
                perceptual = base.dhash(image)
                has_gps = base.gps_from_exif(exif)
                captured = exif.get(36867) or exif.get(306)
            near_match = next(
                ((other, base.hamming(perceptual, other_hash)) for other_hash, other in kept_hashes if base.hamming(perceptual, other_hash) <= 3),
                None,
            )
            if near_match:
                near_dupes.append({"path": str(path), "near_same_as": near_match[0], "dhash_distance": near_match[1]})
                continue
            seen_sha[digest] = str(path)
            kept_hashes.append((perceptual, str(path)))
            records.append({
                "id": len(records),
                "path": str(path),
                "name": path.name,
                "source": base.source_name(path),
                "bytes": path.stat().st_size,
                "width": width,
                "height": height,
                "sha256": digest,
                "gps_exif": has_gps,
                "captured_at": str(captured) if captured else None,
            })
        except Exception as exc:
            records.append({
                "id": len(records),
                "path": str(path),
                "name": path.name,
                "source": base.source_name(path),
                "decode_error": type(exc).__name__,
            })
    return records, exact_dupes, near_dupes


if __name__ == "__main__":
    base.collect = collect_strict
    base.main()
