#!/usr/bin/env python3
"""AUMARA reconstruction source preflight.

Downloads the two active Drive photo-ingest folders, removes exact/near duplicates,
extracts basic image/EXIF evidence, and builds a SIFT/RANSAC overlap graph. The
output is intentionally geometry-neutral: it tells the next reconstruction stage
which real frames actually overlap before any mesh or splat is generated.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import cv2
import gdown
import numpy as np
from PIL import Image, ImageOps

FOLDERS = {
    "NEW_PHOTOS": "https://drive.google.com/drive/folders/1apf9xnyInfhZSI0NfNA3n0OhEgiN8HXS",
    "AUMARA_MOREPHOTOS": "https://drive.google.com/drive/folders/1dUiI_xwzBpGxEhV3VlZK38LqHzMyf8wu",
}
ROOT = Path(os.environ.get("AUMARA_SOURCE_DIR", "/tmp/aumara-reconstruction-preflight"))
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dhash(image: Image.Image, size: int = 8) -> int:
    gray = ImageOps.grayscale(image).resize((size + 1, size), Image.Resampling.LANCZOS)
    a = np.asarray(gray, dtype=np.int16)
    bits = a[:, 1:] > a[:, :-1]
    value = 0
    for bit in bits.ravel():
        value = (value << 1) | int(bit)
    return value


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def gps_from_exif(exif: Any) -> bool:
    try:
        return bool(exif.get(34853))
    except Exception:
        return False


def source_name(path: Path) -> str:
    for name in FOLDERS:
        if name in path.parts:
            return name
    return "unknown"


def download_sources() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for name, url in FOLDERS.items():
        out = ROOT / name
        out.mkdir(parents=True, exist_ok=True)
        print(f"AUMARA_DOWNLOAD_START {name}", flush=True)
        gdown.download_folder(
            url=url,
            output=str(out) + os.sep,
            quiet=False,
            use_cookies=False,
            remaining_ok=True,
        )
        print(f"AUMARA_DOWNLOAD_DONE {name}", flush=True)


def collect() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    exact_dupes: list[dict[str, Any]] = []
    near_dupes: list[dict[str, Any]] = []
    seen_sha: dict[str, str] = {}
    kept_hashes: list[tuple[int, str, tuple[int, int]]] = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        try:
            digest = sha256(path)
            if digest in seen_sha:
                exact_dupes.append({"path": str(path), "same_as": seen_sha[digest], "sha256": digest})
                continue
            with Image.open(path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
                exif = opened.getexif()
                width, height = image.size
                perceptual = dhash(image)
                has_gps = gps_from_exif(exif)
                captured = exif.get(36867) or exif.get(306)
            near = next(
                (
                    other
                    for other_hash, other, dims in kept_hashes
                    if dims == (width, height) and hamming(perceptual, other_hash) <= 2
                ),
                None,
            )
            if near:
                near_dupes.append({"path": str(path), "near_same_as": near, "dhash_distance_max": 2})
                continue
            seen_sha[digest] = str(path)
            kept_hashes.append((perceptual, str(path), (width, height)))
            records.append(
                {
                    "id": len(records),
                    "path": str(path),
                    "name": path.name,
                    "source": source_name(path),
                    "bytes": path.stat().st_size,
                    "width": width,
                    "height": height,
                    "sha256": digest,
                    "gps_exif": has_gps,
                    "captured_at": str(captured) if captured else None,
                }
            )
        except Exception as exc:
            records.append(
                {
                    "id": len(records),
                    "path": str(path),
                    "name": path.name,
                    "source": source_name(path),
                    "decode_error": type(exc).__name__,
                }
            )
    return records, exact_dupes, near_dupes


def feature_graph(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sift = cv2.SIFT_create(nfeatures=1400, contrastThreshold=0.03, edgeThreshold=12)
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    features: dict[int, tuple[list[Any], Any]] = {}

    for record in records:
        if record.get("decode_error"):
            continue
        image = cv2.imread(record["path"], cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        scale = min(1.0, 1400.0 / max(image.shape[:2]))
        if scale < 1.0:
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        keypoints, descriptors = sift.detectAndCompute(image, None)
        record["sift_keypoints"] = len(keypoints or [])
        if descriptors is not None and len(keypoints) >= 12:
            features[record["id"]] = (keypoints, descriptors)

    edges: list[dict[str, Any]] = []
    ids = sorted(features)
    for pos, left_id in enumerate(ids):
        kp1, des1 = features[left_id]
        for right_id in ids[pos + 1 :]:
            kp2, des2 = features[right_id]
            raw = matcher.knnMatch(des1, des2, k=2)
            good = [m for m, n in raw if m.distance < 0.72 * n.distance]
            if len(good) < 12:
                continue
            src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            _, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
            inliers = int(mask.sum()) if mask is not None else 0
            if inliers >= 10:
                edges.append(
                    {
                        "a": left_id,
                        "b": right_id,
                        "good_matches": len(good),
                        "ransac_inliers": inliers,
                        "inlier_ratio": round(inliers / max(1, len(good)), 3),
                    }
                )

    strong = [edge for edge in edges if edge["ransac_inliers"] >= 25]
    adjacency = {record["id"]: set() for record in records if not record.get("decode_error")}
    for edge in strong:
        adjacency[edge["a"]].add(edge["b"])
        adjacency[edge["b"]].add(edge["a"])

    components: list[list[int]] = []
    unseen = set(adjacency)
    while unseen:
        start = unseen.pop()
        stack = [start]
        component = [start]
        while stack:
            node = stack.pop()
            for neighbor in adjacency[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)
        components.append(sorted(component))
    components.sort(key=len, reverse=True)

    summary = {
        "feature_images": len(features),
        "pair_edges_ransac_10_plus": len(edges),
        "strong_edges_ransac_25_plus": len(strong),
        "largest_strong_component": len(components[0]) if components else 0,
        "strong_components": [len(component) for component in components[:10]],
        "isolated_images": sum(1 for component in components if len(component) == 1),
    }
    edges.sort(key=lambda item: (item["ransac_inliers"], item["inlier_ratio"]), reverse=True)
    return edges[:80], summary


def main() -> None:
    download_sources()
    records, exact_dupes, near_dupes = collect()
    valid = [record for record in records if not record.get("decode_error")]
    edges, graph = feature_graph(records)
    report = {
        "schema": "aumara.reconstruction-preflight",
        "version": "1.0.0",
        "source_folders": FOLDERS,
        "downloaded_image_candidates": len(valid) + len(exact_dupes) + len(near_dupes),
        "unique_images": len(valid),
        "exact_duplicates_removed": len(exact_dupes),
        "near_duplicates_removed": len(near_dupes),
        "gps_exif_images": sum(bool(record.get("gps_exif")) for record in valid),
        "captured_at_images": sum(bool(record.get("captured_at")) for record in valid),
        "graph": graph,
        "reconstruction_gate": {
            "sparse_multiview_candidate": graph["largest_strong_component"] >= 8,
            "dense_reconstruction_candidate": graph["largest_strong_component"] >= 12 and graph["strong_edges_ransac_25_plus"] >= 18,
            "rule": "Proceed only with real overlapping frames; keep plan/cadastre georeference authoritative for scale and placement.",
        },
        "images": valid,
        "exact_duplicates": exact_dupes,
        "near_duplicates": near_dupes,
        "top_overlap_pairs": edges,
    }
    output = ROOT / "AUMARA_RECONSTRUCTION_PREFLIGHT.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("AUMARA_PREFLIGHT_SUMMARY=" + json.dumps({
        "downloaded_image_candidates": report["downloaded_image_candidates"],
        "unique_images": report["unique_images"],
        "exact_duplicates_removed": report["exact_duplicates_removed"],
        "near_duplicates_removed": report["near_duplicates_removed"],
        "gps_exif_images": report["gps_exif_images"],
        "captured_at_images": report["captured_at_images"],
        **graph,
        **report["reconstruction_gate"],
    }, sort_keys=True), flush=True)
    print("AUMARA_PREFLIGHT_REPORT=" + output.read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
