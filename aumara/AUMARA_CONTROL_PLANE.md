# AUMARA CONTROL PLANE

Status: ACTIVE
Owner: Ilia
Lead: GPT
Build executor: Grok
Visual/reconstruction worker: Meta/Grok Imagine

## Product objective

Build one continuous guest experience:

EARTH / REAL 3D WORLD -> SPAIN -> BENIDOLEIG -> AUMARA PARCEL -> LOCAL SPATIAL TWIN -> 3.5-4.0 m AGL FLIGHT -> WORLD-ANCHORED AR -> HOUSE / CONTENT / BOOKING INTERACTION.

This is not a video slider and not a collection of AI concept images. Real photos, video, plans, cadastral geometry and generated frames are reconstruction inputs for one georeferenced world.

## Current truth

- Brand: AUMARA.
- Site: Rincón del Silencio, Benidoleig, Alicante.
- Cadastral reference: 8982501YH5988S.
- Control point: 38.7936312, -0.0194621. This is a verification anchor, not the site origin or a house centre.
- Six physical houses.
- Current product instruction: all six houses are bookable.
- Guided local flight target: 3.75 m AGL, allowed 3.5-4.0 m.
- Do not reuse coordinates from legacy React artifacts or legacy L9 inventory pins.

## Canonical code/data paths

Repository: elcidspain/elcidspain.github.io
Branch: main

- Guest entry: /aumara/index.html
- Georeference: /aumara/AUMARA_WORLD_GEOREFERENCE_v1.json
- Local twin GLB: /aumara/world/aumara-site-v2_1.glb
- Twin source manifest: /aumara/world/AUMARA_TWIN_SOURCE_MANIFEST.json
- Flight path: /aumara/world/flight-path.json
- Machine source registry: /aumara/world/AUMARA_SOURCE_REGISTRY.json

## Canonical Drive sources

Do not move originals. Read and index them as reconstruction sources.

- 00_AUMARA_COMMAND_CENTER — folder id 1z5oWIeRoyWT6YSw3_S73qxtcjmqfNOLv
- AUMARA — folder id 14qJX_hy-4Jrj12_xWxSN5YctlEnK8Fzf
- WEB working/ingestion root — folder id 1csfG7ehFiNUZEYD75EpEiCqmEsdwbY-b
- NEW_PHOTOS — folder id 1apf9xnyInfhZSI0NfNA3n0OhEgiN8HXS
- AUMARA_MOREPHOTOS — folder id 1dUiI_xwzBpGxEhV3VlZK38LqHzMyf8wu
- BEDS24_READY_MANUAL_UPLOAD_2026-08-19 — folder id 1W_4IlgI2wJs_wWE0k-69ppe-QTWJvtw5
- PHOTOS AUMARA — folder id 1KrN5gmDnhmhvMTZt6s9CKBFCuAUoCGa2
- Katia in house copy 1 — folder id 15ns7kKd5D4Ws5n940PZh-uM-gNPmhwsX
- Katia in house copy 2 — folder id 1KvMJvnaMC466lKMs2NvE9RlJqvcKKBFl
- 00_AUMARA_CONTENT_FACTORY — folder id 1j7AjGTjAsrxPoP5AOMYm4JZlV_dLk9be
- AUMARA_OUTDOOR_AR_001 — folder id 1HMqmvUEi51gzflKHpDCmaWmAca3AMNQz
- AUMARA_DAY_WALK_001_EXPORT — folder id 1IEBw2SHBEnxIraQV6vDykkSyLi5YLtOv
- AUMARA Fotos AI Edited — folder id 1Vm9kWSQZMHbAXEyRNB4Nww-KDNpPQbxO

## Roles

### GPT
Owns product architecture, truth-lock, routing of work, acceptance criteria and final QA.

### Grok Build
Owns code execution and runtime integration. It must patch the current build, not create another parallel product unless explicitly ordered.

### Meta / Imagine
Owns reconstruction inputs: perspective-complete exterior frames, textures, environmental extensions, lighting/day-night states and ad/content derivatives. Generated material must be geospatially and visually reconciled before becoming site truth.

## Build order

1. Keep guest entry stable and non-blocking.
2. Load the global real-world layer (Google Photorealistic 3D Tiles when the authorized key is available).
3. Use the authoritative georeference to place the parcel and houses A-F.
4. Replace placeholder/flat geometry with the reconstructed local twin using the Drive source registry.
5. Fly the local route continuously at measured 3.5-4.0 m AGL.
6. Add world-anchored AR labels/cards with Cesium world-to-screen synchronization.
7. Bind all six houses to guest content and booking actions.
8. Add cinematic Earth-to-AUMARA descent and mobile controls.
9. Move the accepted public experience to aumara.me.

## Runtime rules

- A guest must never land on an internal EL CID portal, Ops, TGSS, Sabadell, KYP or debug interface.
- Cesium/WebGL failure must degrade to a real AUMARA media surface; no black/grey dead screen.
- Engineering HUD only under ?debug=1.
- Do not call a build LIVE/READY before firstFrameRendered=true.
- No fake AGL telemetry: use production terrain sampling or raycast the loaded local terrain/mesh.
- Keep raw unclamped telemetry.
- Google/tiles credentials are runtime configuration only; never commit or print secret values.

## Current public surfaces

- elcidspain.com/aumara — temporary public guest surface; may not represent the latest spatial twin.
- grok.me previews — temporary build previews, never canonical.
- chatgpt.site previews — temporary QA/checkpoint surfaces, never canonical.
- aumara.me — target canonical public domain after DNS/TLS/hosting cutover.

## Single next production objective

Build AUMARA_WORLD_V2 from the real source registry: real parcel landscape, six reconstructed houses, paths, vegetation and spatial content, then prove one continuous mobile/desktop flight through waypoint 0 -> 27 with world-anchored AR and six booking interactions.
