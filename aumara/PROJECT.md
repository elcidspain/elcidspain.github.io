# AUMARA — PROJECT ENTRYPOINT

Repository: `elcidspain/elcidspain.github.io`
Branch: `main`
Owner: Ilia
Lead / product architecture / QA: GPT
Build executor: Grok
Visual reconstruction / generative completion: Meta / Grok Imagine

## What this project is

AUMARA is one continuous georeferenced guest world:

`EARTH / REAL 3D WORLD -> SPAIN -> BENIDOLEIG -> AUMARA PARCEL -> LOCAL SPATIAL TWIN -> 3.5–4.0 m AGL FLIGHT -> WORLD-ANCHORED AR -> HOUSE / CONTENT / BOOKING`.

This is not a video slider, not a static landing-page project, and not a collection of AI concept images. Photos, videos, plans, cadastral geometry, terrain data and generated material are reconstruction inputs for one spatial world.

## Read these files first, in this order

1. `aumara/AUMARA_CONTROL_PLANE.md`
2. `aumara/world/AUMARA_SOURCE_REGISTRY.json`
3. `aumara/AUMARA_WORLD_GEOREFERENCE_v1.json`
4. `aumara/jobs/AUMARA_REALITY_TERMINOLOGY_LOCK.json`
5. `aumara/jobs/AUMARA_WORLD_V2_1_REALITY_GROK.json`
6. `aumara/world/AUMARA_TWIN_SOURCE_MANIFEST.json`
7. `aumara/world/flight-path.json`

These files are the project truth. Do not replace them with chat assumptions.

## Current project state

V2.1 local layer: CLOSED (see `aumara/jobs/AUMARA_WORLD_V2_1_1_RECEIPT.json`).

Accepted:

- current `aumara/` project tree;
- canonical georeference and parcel;
- six A–F house positions;
- current flight-path scaffold;
- world-anchored A–F AR wiring;
- six Booking interactions;
- local-twin fallback when global Google/Ion tiles are unavailable;
- source-purged local twin `aumara-site-v2_1.glb`;
- live-browser raw AGL 3.5–4.0 m on WP0–27.

Not final yet:

- P0 mobile Safari render hotfix (`aumara/jobs/AUMARA_MOBILE_RENDER_HOTFIX_GROK.json`).
  Restore last owner-proven Google tile policy. Do not optimize quality until iPhone render is crash-free.

## Active job

Current execution job:

`aumara/jobs/AUMARA_WP27_ENDSTOP_HOTFIX_GROK.json`

Restore the last owner-proven Google Photorealistic render policy on iPhone Safari. Do not optimize tile quality until the crash is gone.

Use:

- `geodesic house`
- `geodesic dome`
- `AUMARA house`
- `Casa A–F`

Do not call the houses `tents` or `glamping tents`.

Do not assert doors, glass, frames, decks, facade materials, window systems, vegetation species or construction details unless the exact feature is backed by a source file / Drive ID / plan reference for that house or parcel region.

Unseen geometry may be completed only as `generated-completion` and must be marked as such in the source manifest.

## Canonical spatial truth

- Cadastral reference: `8982501YH5988S`
- Control point: `38.7936312, -0.0194621` — verification anchor only, not site origin or house centre.
- Six physical houses A–F.
- Current product instruction: all six are bookable.
- Guided local-flight target: `3.75 m AGL`, valid band `3.5–4.0 m`.
- Never reuse legacy React-artifact coordinates or legacy inventory pins.

## Canonical code / assets

- Guest entry: `aumara/index.html`
- Georeference: `aumara/AUMARA_WORLD_GEOREFERENCE_v1.json`
- Current twin: `aumara/world/aumara-site-v2.glb`
- Next twin target: `aumara/world/aumara-site-v2_1.glb`
- Flight path: `aumara/world/flight-path.json`
- Source registry: `aumara/world/AUMARA_SOURCE_REGISTRY.json`
- Source manifest: `aumara/world/AUMARA_TWIN_SOURCE_MANIFEST.json`

## Canonical reconstruction sources

Use the Drive sources already indexed in `AUMARA_SOURCE_REGISTRY.json`, including:

- `PHOTOS AUMARA`
- Katia house folders
- `AUMARA_DAY_WALK_001_EXPORT`
- `AUMARA_OUTDOOR_AR_001`
- Puchol plans
- cadastral / georeference data
- verified heightmap / PNOA terrain

Do not create parallel truth folders unless explicitly instructed.

## Active job

Current execution job:

`aumara/jobs/AUMARA_WP27_ENDSTOP_HOTFIX_GROK.json`

Restore the last owner-proven Google Photorealistic render policy on iPhone Safari. Do not optimize tile quality until the crash is gone.

## Hard freezes

Do not:

- rewrite the full `aumara/index.html`;
- redesign landing HTML/CSS/copy;
- move house A–F coordinates;
- create another project or repository;
- create another status/dashboard UI;
- call generic hemispheres or billboards final reconstructed reality;
- fake, clamp or relabel telemetry;
- block local-twin progress on unavailable Google/Ion global tiles.

## Definition of progress

A technical report is not progress by itself.

Progress means committed artifacts in the current project tree that are visibly present in runtime.

For V2.1 this means:

- `aumara-site-v2_1.glb` visibly contains the reconstructed parcel, paths and six houses;
- every modeled feature has provenance or is explicitly marked generated-completion;
- one clean WP0→WP27 run;
- timestamps and waypoints monotonic;
- raw ground clearance sampled from actual terrain/mesh or explicitly labeled LOCAL_DEM;
- no clamp;
- desktop and mobile uncut evidence;
- current build committed to `main`.

## Execution rule for Grok

When this file is provided as the project entrypoint:

`READ PROJECT.md -> READ ACTIVE JOB -> PATCH CURRENT BUILD -> BUILD REALITY -> RUN -> MEASURE -> FIX -> RECORD -> COMMIT -> RECEIPT`.

Do not stop to restate the architecture. Do not create a new project. Do not wait for another prompt unless a genuinely non-resolvable external credential or physical source is missing.
