#!/usr/bin/env python3
"""Rebuild aumara-site.glb: geodesic Ø7/Ø9 from Puchol plans + real photos."""
from __future__ import annotations
import io, json, math, struct
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TEX = Path("/tmp/tex")
OUT = ROOT / "world" / "aumara-site.glb"

PHI = (1 + math.sqrt(5)) / 2


def hm_at(hm, e, n):
    u = (e - hm["east0"]) / hm["cell"]
    v = (n - hm["north0"]) / hm["cell"]
    c0, r0 = int(math.floor(u)), int(math.floor(v))
    tx, ty = u - c0, v - r0

    def at(c, r):
        cc = max(0, min(hm["cols"] - 1, c))
        rr = max(0, min(hm["rows"] - 1, r))
        return hm["heights_m"][rr * hm["cols"] + cc]

    return (
        at(c0, r0) * (1 - tx) * (1 - ty)
        + at(c0 + 1, r0) * tx * (1 - ty)
        + at(c0, r0 + 1) * (1 - tx) * ty
        + at(c0 + 1, r0 + 1) * tx * ty
    )


def jpg(path, size):
    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (48, 52, 40))
    canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=80, optimize=True)
    return buf.getvalue()


def enu(e, n, h):
    return (float(e), float(h), float(-n))


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(v):
    L = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / L, v[1] / L, v[2] / L)


def add3(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s)


class Mesh:
    def __init__(self, name):
        self.name = name
        self.pos, self.nrm, self.uv, self.idx = [], [], [], []

    def tri(self, p0, p1, p2, n, uv0, uv1, uv2):
        i = len(self.pos) // 3
        for p, u in ((p0, uv0), (p1, uv1), (p2, uv2)):
            self.pos.extend(p)
            self.nrm.extend(n)
            self.uv.extend(u)
        self.idx.extend([i, i + 1, i + 2])

    def quad(self, p00, p10, p11, p01, n, uv00, uv10, uv11, uv01):
        self.tri(p00, p10, p11, n, uv00, uv10, uv11)
        self.tri(p00, p11, p01, n, uv00, uv11, uv01)


def icosahedron():
    verts = []
    for a, b in (
        (-1, -PHI),
        (-1, PHI),
        (1, -PHI),
        (1, PHI),
    ):
        verts.append(norm((-1 if a < 0 else 1, b, 0)) if False else None)
    v = []
    for x, y in ((-1, -PHI), (-1, PHI), (1, -PHI), (1, PHI)):
        v.append(norm((0, x, y)))
        v.append(norm((x, y, 0)))
        v.append(norm((y, 0, x)))
    # unique via standard 12
    t = PHI
    raw = [
        (-1, t, 0),
        (1, t, 0),
        (-1, -t, 0),
        (1, -t, 0),
        (0, -1, t),
        (0, 1, t),
        (0, -1, -t),
        (0, 1, -t),
        (t, 0, -1),
        (t, 0, 1),
        (-t, 0, -1),
        (-t, 0, 1),
    ]
    verts = [norm(p) for p in raw]
    faces = [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    ]
    return verts, faces


def subdivide(verts, faces, n):
    cache = {}

    def mid(i, j):
        key = tuple(sorted((i, j)))
        if key in cache:
            return cache[key]
        m = norm(
            (
                (verts[i][0] + verts[j][0]) * 0.5,
                (verts[i][1] + verts[j][1]) * 0.5,
                (verts[i][2] + verts[j][2]) * 0.5,
            )
        )
        cache[key] = len(verts)
        verts.append(m)
        return cache[key]

    for _ in range(n):
        nf = []
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = nf
    return verts, faces


def dome_mesh(name, east, north, base, diameter, height, facing):
    """Geodesic hemisphere, plan heights Ø7=4.86 / Ø9=5.50."""
    r = diameter / 2.0
    verts, faces = icosahedron()
    verts, faces = subdivide(verts, faces, 2)
    m = Mesh(name)
    # keep upper hemisphere (y>=-0.08)
    kept = []
    for a, b, c in faces:
        pa, pb, pc = verts[a], verts[b], verts[c]
        if pa[1] < -0.12 and pb[1] < -0.12 and pc[1] < -0.12:
            continue
        kept.append((a, b, c))
    yaw = facing
    cy, sy = math.cos(yaw), math.sin(yaw)
    for a, b, c in kept:
        pts = []
        uvs = []
        for i in (a, b, c):
            x, y, z = verts[i]
            y = max(y, -0.08)
            # sphere to dome: xz * r, y mapped 0..height
            yn = (y + 0.08) / (1.08)
            px = x * r
            pz = z * r
            py = yn * height
            # rotate around Y by facing
            rx = px * cy - pz * sy
            rz = px * sy + pz * cy
            pts.append(enu(east + rx, north - rz, base + py))
            u = 0.5 + math.atan2(z, x) / (2 * math.pi)
            v = 1.0 - yn
            uvs.append((u, v))
        n = norm(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
        m.tri(pts[0], pts[1], pts[2], n, uvs[0], uvs[1], uvs[2])
    # timber deck ring
    segs = 24
    deck_r = r + 0.55
    for i in range(segs):
        t0, t1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
        p00 = enu(east + r * 0.2 * math.cos(t0), north + r * 0.2 * math.sin(t0), base + 0.04)
        p10 = enu(east + deck_r * math.cos(t0), north + deck_r * math.sin(t0), base + 0.04)
        p11 = enu(east + deck_r * math.cos(t1), north + deck_r * math.sin(t1), base + 0.04)
        p01 = enu(east + r * 0.2 * math.cos(t1), north + r * 0.2 * math.sin(t1), base + 0.04)
        m.quad(p00, p10, p11, p01, (0, 1, 0), (0, 0), (1, 0), (1, 1), (0, 1))
    return m


def pack_glb(meshes, images, mat_of):
    bin_parts = []

    def align4(b):
        return b + b"\x00" * ((4 - len(b) % 4) % 4)

    accessors, bufferViews, gltf_meshes, nodes = [], [], [], []
    materials, gltf_images, textures = [], [], []
    samplers = [{"magFilter": 9729, "minFilter": 9729, "wrapS": 10497, "wrapT": 10497}]

    img_tex = {}
    for name, data in images.items():
        off = sum(len(p) for p in bin_parts)
        bin_parts.append(align4(data))
        bufferViews.append({"buffer": 0, "byteOffset": off, "byteLength": len(data)})
        gltf_images.append({"bufferView": len(bufferViews) - 1, "mimeType": "image/jpeg", "name": name})
        textures.append({"sampler": 0, "source": len(gltf_images) - 1})
        img_tex[name] = len(textures) - 1

    materials.append(
        {
            "name": "veg",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.20, 0.36, 0.16, 1],
                "metallicFactor": 0,
                "roughnessFactor": 0.92,
            },
        }
    )
    mat_index = {None: 0}
    for name, texi in img_tex.items():
        materials.append(
            {
                "name": name,
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": texi},
                    "metallicFactor": 0,
                    "roughnessFactor": 0.82,
                },
            }
        )
        mat_index[name] = len(materials) - 1

    def add_acc(raw, typ, comp, mn, mx, target):
        off = sum(len(p) for p in bin_parts)
        bin_parts.append(align4(raw))
        bufferViews.append(
            {"buffer": 0, "byteOffset": off, "byteLength": len(raw), "target": target}
        )
        stride = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[typ]
        bpe = 2 if comp == 5123 else 4
        accessors.append(
            {
                "bufferView": len(bufferViews) - 1,
                "componentType": comp,
                "count": len(raw) // (bpe * stride),
                "type": typ,
                "min": mn,
                "max": mx,
            }
        )
        return len(accessors) - 1

    def mn_mx(arr, dim):
        cols = [arr[i::dim] for i in range(dim)]
        return [min(c) for c in cols], [max(c) for c in cols]

    for key, mesh in meshes:
        pos = struct.pack("<%sf" % len(mesh.pos), *mesh.pos)
        nrm = struct.pack("<%sf" % len(mesh.nrm), *mesh.nrm)
        uv = struct.pack("<%sf" % len(mesh.uv), *mesh.uv)
        idx = struct.pack("<%sH" % len(mesh.idx), *mesh.idx)
        pmin, pmax = mn_mx(mesh.pos, 3)
        nmin, nmax = mn_mx(mesh.nrm, 3)
        umin, umax = mn_mx(mesh.uv, 2)
        ai = add_acc(pos, "VEC3", 5126, pmin, pmax, 34962)
        ni = add_acc(nrm, "VEC3", 5126, nmin, nmax, 34962)
        ui = add_acc(uv, "VEC2", 5126, umin, umax, 34962)
        ii = add_acc(idx, "SCALAR", 5123, [min(mesh.idx)], [max(mesh.idx)], 34963)
        mat = mat_of.get(key)
        gltf_meshes.append(
            {
                "name": mesh.name,
                "primitives": [
                    {
                        "attributes": {"POSITION": ai, "NORMAL": ni, "TEXCOORD_0": ui},
                        "indices": ii,
                        "material": mat_index[mat],
                        "mode": 4,
                    }
                ],
            }
        )
        nodes.append({"name": mesh.name, "mesh": len(gltf_meshes) - 1})

    blob = b"".join(bin_parts)
    gltf = {
        "asset": {"version": "2.0", "generator": "aumara-geodesic-v2"},
        "scene": 0,
        "scenes": [{"name": "AUMARA_SITE_V2", "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": gltf_meshes,
        "materials": materials,
        "textures": textures,
        "images": gltf_images,
        "samplers": samplers,
        "accessors": accessors,
        "bufferViews": bufferViews,
        "buffers": [{"byteLength": len(blob)}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = bytearray()
    total = 12 + 8 + len(js) + 8 + len(blob)
    out += struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(js), b"JSON")
    out += js
    out += struct.pack("<I4s", len(blob), b"BIN\x00")
    out += blob
    OUT.write_bytes(out)
    return OUT.stat().st_size


def main():
    hm = json.loads((ROOT / "world" / "heightmap.json").read_text())
    geo = json.loads((ROOT / "AUMARA_WORLD_GEOREFERENCE_v1.json").read_text())
    fp = json.loads((ROOT / "world" / "flight-path.json").read_text())

    images = {
        "ground": jpg("/workspace/public/aumara/twin/pnoa_25cm.jpg", 1024),
        "path": jpg("/workspace/public/aumara/site/path_day_v1.jpg", 256),
        "A": jpg("/workspace/public/aumara/houses/chalet-1/houses_real_1B6A8852.jpg", 512),
        "B": jpg("/workspace/public/aumara/houses/superior-1/houses_real_1B6A9875.jpg", 512),
        "C": jpg("/workspace/public/aumara/houses/chalet-2/houses_real_1B6A8803.jpg", 512),
        "D": jpg("/workspace/public/aumara/houses/superior-2/houses_real_1B6A9866.jpg", 512),
        "E": jpg("/workspace/public/aumara/houses/chalet-3/houses_real_1B6A8857.jpg", 512),
        "F": jpg("/workspace/public/aumara/houses/private-6/exterior.jpg", 512),
    }

    terrain = Mesh("terrain")
    cols, rows = hm["cols"], hm["rows"]
    e0, n0, cell = hm["east0"], hm["north0"], hm["cell"]
    grid = []
    for ri in range(rows):
        row = []
        for ci in range(cols):
            e = e0 + ci * cell
            n = n0 + ri * cell
            row.append((e, n, hm["heights_m"][ri * cols + ci]))
        grid.append(row)
    umin, umax = e0, e0 + (cols - 1) * cell
    vmin, vmax = n0, n0 + (rows - 1) * cell
    for ri in range(rows - 1):
        for ci in range(cols - 1):
            a, b = grid[ri][ci], grid[ri][ci + 1]
            c, d = grid[ri + 1][ci + 1], grid[ri + 1][ci]

            def uv(p):
                return ((p[0] - umin) / (umax - umin), 1 - (p[1] - vmin) / (vmax - vmin))

            pA, pB, pC, pD = enu(*a), enu(*b), enu(*c), enu(*d)
            nrm = norm(cross(sub(pB, pA), sub(pD, pA)))
            terrain.quad(pA, pB, pC, pD, nrm, uv(a), uv(b), uv(c), uv(d))

    path = Mesh("path")
    half = 1.05
    wps = fp["waypoints"]
    for i in range(len(wps) - 1):
        a, b = wps[i]["local"], wps[i + 1]["local"]
        e0_, n0_ = a["east"], a["north"]
        e1, n1 = b["east"], b["north"]
        dx, dy = e1 - e0_, n1 - n0_
        L = math.hypot(dx, dy) or 1
        px, py = -dy / L * half, dx / L * half
        h0 = hm_at(hm, e0_, n0_) + 0.07
        h1 = hm_at(hm, e1, n1) + 0.07
        path.quad(
            enu(e0_ + px, n0_ + py, h0),
            enu(e1 + px, n1 + py, h1),
            enu(e1 - px, n1 - py, h1),
            enu(e0_ - px, n0_ - py, h0),
            (0, 1, 0),
            (0, 0),
            (1, 0),
            (1, 1),
            (0, 1),
        )

    houses = {}
    for h in geo["houses"]:
        e, n = h["localMetres"]["east"], h["localMetres"]["north"]
        # face nearest path segment
        nearest = min(wps, key=lambda w: (w["local"]["east"] - e) ** 2 + (w["local"]["north"] - n) ** 2)
        facing = math.atan2(nearest["local"]["east"] - e, nearest["local"]["north"] - n)
        height = 5.50 if h["diameterMetres"] == 9 else 4.86
        houses[h["spatialId"]] = dome_mesh(
            "house_" + h["spatialId"],
            e,
            n,
            hm_at(hm, e, n),
            h["diameterMetres"],
            height,
            facing,
        )

    veg = Mesh("veg")
    rng = 7

    def rnd():
        nonlocal rng
        rng = (1103515245 * rng + 12345) & 0x7FFFFFFF
        return rng / 0x7FFFFFFF

    occ = [
        (h["localMetres"]["east"], h["localMetres"]["north"], h["diameterMetres"] / 2 + 1.4)
        for h in geo["houses"]
    ]
    n = 0
    tries = 0
    while n < 64 and tries < 1200:
        tries += 1
        e = e0 + 6 + rnd() * 96
        nn = n0 + 5 + rnd() * 46
        if any((e - oe) ** 2 + (nn - on) ** 2 < (rr + 1.6) ** 2 for oe, on, rr in occ):
            continue
        base = hm_at(hm, e, nn)
        ht = 1.8 + rnd() * 3.0
        rad = 0.4 + rnd() * 0.7
        apex = enu(e, nn, base + ht)
        for i in range(7):
            t0, t1 = 2 * math.pi * i / 7, 2 * math.pi * (i + 1) / 7
            p0 = enu(e + rad * math.cos(t0), nn + rad * math.sin(t0), base)
            p1 = enu(e + rad * math.cos(t1), nn + rad * math.sin(t1), base)
            veg.tri(p0, p1, apex, (0, 1, 0), (0, 1), (1, 1), (0.5, 0))
        n += 1

    meshes = [("ground", terrain), ("path", path), ("veg", veg)]
    mat_of = {"ground": "ground", "path": "path", "veg": None}
    for k in "ABCDEF":
        meshes.append((k, houses[k]))
        mat_of[k] = k
    size = pack_glb(meshes, images, mat_of)
    print("GLB", size, "terrain", len(terrain.idx) // 3, "A", len(houses["A"].idx) // 3)


if __name__ == "__main__":
    main()
