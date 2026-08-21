#!/usr/bin/env python3
"""Run a real sparse SfM probe on strict-deduplicated AUMARA Drive frames."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pycolmap

import reconstruction_preflight as base
from reconstruction_preflight_strict import collect_strict


def main() -> None:
    base.download_sources()
    records, exact_dupes, near_dupes = collect_strict()
    records = [record for record in records if not record.get("decode_error")]

    work = base.ROOT / "colmap_probe"
    images = work / "images"
    sparse = work / "sparse"
    database = work / "database.db"
    if work.exists():
        shutil.rmtree(work)
    images.mkdir(parents=True)
    sparse.mkdir(parents=True)

    source_map: dict[str, dict] = {}
    for record in records:
        suffix = Path(record["path"]).suffix.lower() or ".jpg"
        name = f"{record['id']:03d}_{record['source']}_{record['name']}"
        if not name.lower().endswith(suffix):
            name += suffix
        shutil.copy2(record["path"], images / name)
        source_map[name] = record

    print(f"AUMARA_COLMAP_INPUTS={len(source_map)}", flush=True)
    pycolmap.extract_features(
        database_path=database,
        image_path=images,
        camera_mode=pycolmap.CameraMode.AUTO,
    )
    pycolmap.match_exhaustive(database_path=database)

    options = pycolmap.IncrementalPipelineOptions()
    options.min_model_size = 3
    options.multiple_models = True
    options.max_num_models = 12
    reconstructions = pycolmap.incremental_mapping(
        database_path=database,
        image_path=images,
        output_path=sparse,
        options=options,
    )

    models = []
    for model_id, reconstruction in reconstructions.items():
        reg_ids = reconstruction.reg_image_ids()
        registered = [reconstruction.image(image_id).name for image_id in reg_ids]
        model = {
            "model_id": int(model_id),
            "registered_images": reconstruction.num_reg_images(),
            "points3D": reconstruction.num_points3D(),
            "observations": reconstruction.compute_num_observations(),
            "mean_track_length": round(float(reconstruction.compute_mean_track_length()), 4),
            "mean_reprojection_error_px": round(float(reconstruction.compute_mean_reprojection_error()), 4),
            "registered_names": registered,
        }
        try:
            p0, p1 = reconstruction.compute_bounding_box(0.02, 0.98)
            model["bbox_2_98"] = {"min": [round(float(x), 6) for x in p0], "max": [round(float(x), 6) for x in p1]}
        except Exception:
            pass
        models.append(model)

    models.sort(key=lambda item: (item["registered_images"], item["points3D"]), reverse=True)
    best = models[0] if models else None
    result = {
        "schema": "aumara.colmap-sparse-probe",
        "version": "1.0.0",
        "strict_unique_inputs": len(records),
        "exact_duplicates_removed": len(exact_dupes),
        "near_duplicates_removed": len(near_dupes),
        "models": models,
        "best_model": best,
        "gate": {
            "real_sparse_sfm": bool(best and best["registered_images"] >= 5 and best["points3D"] >= 500),
            "dense_mesh_authorized_by_probe": bool(best and best["registered_images"] >= 8 and best["points3D"] >= 1500 and best["mean_reprojection_error_px"] <= 2.0),
        },
        "note": "Sparse SfM remains local/unscaled. Plan/cadastre georeference is authoritative for production scale and placement.",
    }
    print("AUMARA_COLMAP_RESULT=" + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
