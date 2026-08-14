#!/usr/bin/env python3
"""AUMARA site twin v2.1 — source-derived reality, not generic hemispheres."""
from __future__ import annotations

import io
import json
import math
import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUB = Path("/workspace/public/aumara")
OUT = ROOT / "world" / "aumara-site-v2_1.glb"
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


def jpg_bytes(im: Image.Image, size, quality=82):
    im = im.convert("RGB")
    im.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (40, 42, 36))
    canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def load_rgb(path):
    return Image.open(path).convert("RGB")


def crop_frac(im, box):
    w, h = im.size
    x0, y0, x1, y1 = box
    return im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))


def fabric_from_photo(im):
    """Tent membrane only — not the whole photo (avoids billboard wrap)."""
    tent = crop_frac(im, (0.28, 0.12, 0.78, 0.62))
    tent = ImageEnhance.Color(tent).enhance(0.45)
    tent = ImageEnhance.Brightness(tent).enhance(1.18)
    tent = ImageEnhance.Contrast(tent).enhance(0.85)
    return tent


def wood_swatch(im, box, warm=(72, 48, 28)):
    sw = crop_frac(im, box)
    sw = ImageEnhance.Color(sw).enhance(0.7)
    return sw


def enu(e, n, h):
    return (float(e), float(h), float(-n))


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add3(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(v):
    L = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / L, v[1] / L, v[2] / L)


def rot_yaw(x, z, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return x * c - z * s, x * s + z * c


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

    def quad(self, p00, p10, p11, p01, n, uv00=(0, 0), uv10=(1, 0), uv11=(1, 1), uv01=(0, 1)):
        self.tri(p00, p10, p11, n, uv00, uv10, uv11)
        self.tri(p00, p11, p01, n, uv00, uv11, uv01)

    def box(self, a, b, r, up=(0, 1, 0)):
        d = sub(b, a)
        L = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1
        dn = (d[0] / L, d[1] / L, d[2] / L)
        side = norm(cross(dn, up))
        if abs(side[0]) + abs(side[1]) + abs(side[2]) < 0.2:
            side = norm(cross(dn, (1, 0, 0)))
        lift = norm(cross(side, dn))
        corners_a = [
            add3(add3(a, side, r), lift, r),
            add3(add3(a, side, -r), lift, r),
            add3(add3(a, side, -r), lift, -r),
            add3(add3(a, side, r), lift, -r),
        ]
        corners_b = [add3(p, dn, L) for p in corners_a]
        faces = (
            (corners_a[0], corners_a[1], corners_a[2], corners_a[3]),
            (corners_b[0], corners_b[3], corners_b[2], corners_b[1]),
            (corners_a[0], corners_b[0], corners_b[1], corners_a[1]),
            (corners_a[1], corners_b[1], corners_b[2], corners_a[2]),
            (corners_a[2], corners_b[2], corners_b[3], corners_a[3]),
            (corners_a[3], corners_b[3], corners_b[0], corners_a[0]),
        )
        for q in faces:
            nrm = norm(cross(sub(q[1], q[0]), sub(q[3], q[0])))
            self.quad(q[0], q[1], q[2], q[3], nrm)

    def disc(self, cx, cy, cz, rx, rz, y, segs, uv_scale=1.0):
        for i in range(segs):
            t0, t1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
            p0 = (cx, y, cz)
            p1 = (cx + rx * math.cos(t0), y, cz + rz * math.sin(t0))
            p2 = (cx + rx * math.cos(t1), y, cz + rz * math.sin(t1))
            self.tri(p0, p1, p2, (0, 1, 0), (0.5, 0.5), (0.5 + 0.5 * math.cos(t0), 0.5 + 0.5 * math.sin(t0)), (0.5 + 0.5 * math.cos(t1), 0.5 + 0.5 * math.sin(t1)))

    def cylinder(self, e, n, y0, y1, rad, segs=8):
        for i in range(segs):
            t0, t1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
            x0, z0 = rad * math.cos(t0), rad * math.sin(t0)
            x1, z1 = rad * math.cos(t1), rad * math.sin(t1)
            p00 = enu(e + x0, n + z0, y0)
            p10 = enu(e + x1, n + z1, y0)
            p11 = enu(e + x1, n + z1, y1)
            p01 = enu(e + x0, n + z0, y1)
            nrm = norm((math.cos((t0 + t1) / 2), 0, math.sin((t0 + t1) / 2)))
            self.quad(p00, p10, p11, p01, nrm, (0, 0), (1, 0), (1, 1), (0, 1))

    def ellipsoid(self, e, n, cy, rx, ry, rz, segs=9, stacks=6):
        def pt(u, v):
            th = u * math.pi
            ph = v * 2 * math.pi
            x = rx * math.sin(th) * math.cos(ph)
            y = ry * math.cos(th)
            z = rz * math.sin(th) * math.sin(ph)
            return enu(e + x, n + z, cy + y), (v, 1 - u)

        for i in range(stacks):
            for j in range(segs):
                u0, u1 = i / stacks, (i + 1) / stacks
                v0, v1 = j / segs, (j + 1) / segs
                a, ua = pt(u0, v0)
                b, ub = pt(u1, v0)
                c, uc = pt(u1, v1)
                d, ud = pt(u0, v1)
                nrm = norm(sub(a, enu(e, n, cy)))
                self.quad(a, b, c, d, nrm, ua, ub, uc, ud)


def icosahedron():
    t = PHI
    raw = [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
        (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
        (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
    ]
    verts = [norm(p) for p in raw]
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    return verts, faces


def subdivide(verts, faces, n):
    cache = {}

    def mid(i, j):
        key = tuple(sorted((i, j)))
        if key in cache:
            return cache[key]
        m = norm(((verts[i][0] + verts[j][0]) * 0.5, (verts[i][1] + verts[j][1]) * 0.5, (verts[i][2] + verts[j][2]) * 0.5))
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


def unit_to_world(x, y, z, east, north, base, r, height, yaw):
    y = max(y, -0.08)
    yn = (y + 0.08) / 1.08
    px, pz = x * r, z * r
    py = yn * height
    rx, rz = rot_yaw(px, pz, yaw)
    return enu(east + rx, north - rz, base + py), yn, math.atan2(z, x)


def in_door_sector(ang, door_ang, half=0.28):
    d = (ang - door_ang + math.pi) % (2 * math.pi) - math.pi
    return abs(d) < half


def house_parts(hid, east, north, base, diameter, height, facing):
    """Framed geodesic + path-facing door/windows + timber deck. Not a photo sphere."""
    r = diameter / 2.0
    verts, faces = icosahedron()
    verts, faces = subdivide(verts, faces, 2)
    canvas, timber, deck, glass = Mesh("house_" + hid), Mesh("frame_" + hid), Mesh("deck_" + hid), Mesh("glass_" + hid)
    yaw = facing
    door_ang = 0.0  # local +X after yaw? we apply yaw in unit_to_world; door faces +local Z toward path
    # facing is atan2(de, dn) in east/north. Door should sit at that world direction.
    # unit sphere: we treat local +Z (south in glTF after ENU? ) — bake door in unrotated sphere at angle 0
    # then rotate the whole house by facing.

    kept = []
    edges = set()
    for a, b, c in faces:
        pa, pb, pc = verts[a], verts[b], verts[c]
        if pa[1] < -0.12 and pb[1] < -0.12 and pc[1] < -0.12:
            continue
        kept.append((a, b, c))
        for i, j in ((a, b), (b, c), (c, a)):
            edges.add(tuple(sorted((i, j))))

    for a, b, c in kept:
        pts, uvs, angs, yns = [], [], [], []
        skip = False
        for i in (a, b, c):
            p, yn, ang = unit_to_world(*verts[i], east, north, base, r, height, yaw)
            pts.append(p)
            yns.append(yn)
            angs.append(ang)
            uvs.append((0.5 + math.atan2(verts[i][2], verts[i][0]) / (2 * math.pi), 1.0 - yn))
            if yn < 0.48 and in_door_sector(ang, 0.0, 0.22):
                skip = True
        if skip:
            continue
        nrm = norm(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
        canvas.tri(pts[0], pts[1], pts[2], nrm, uvs[0], uvs[1], uvs[2])

    for i, j in edges:
        pa, pb = verts[i], verts[j]
        if pa[1] < -0.1 and pb[1] < -0.1:
            continue
        a, _, _ = unit_to_world(*pa, east, north, base, r, height, yaw)
        b, _, _ = unit_to_world(*pb, east, north, base, r, height, yaw)
        timber.box(a, b, 0.045)

    # base ring
    segs = 28
    for i in range(segs):
        t0, t1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
        a = enu(east + r * math.cos(t0), north + r * math.sin(t0), base + 0.06)
        b = enu(east + r * math.cos(t1), north + r * math.sin(t1), base + 0.06)
        timber.box(a, b, 0.05)

    # path-facing deck sector (photos: timber deck + rail in front of glass door)
    deck_r0, deck_r1 = r * 0.15, r + 1.15
    span = math.radians(150)
    dsegs = 14
    for i in range(dsegs):
        a0 = facing - span / 2 + span * i / dsegs
        a1 = facing - span / 2 + span * (i + 1) / dsegs
        p00 = enu(east + deck_r0 * math.sin(a0), north + deck_r0 * math.cos(a0), base + 0.07)
        p10 = enu(east + deck_r1 * math.sin(a0), north + deck_r1 * math.cos(a0), base + 0.07)
        p11 = enu(east + deck_r1 * math.sin(a1), north + deck_r1 * math.cos(a1), base + 0.07)
        p01 = enu(east + deck_r0 * math.sin(a1), north + deck_r0 * math.cos(a1), base + 0.07)
        deck.quad(p00, p10, p11, p01, (0, 1, 0), (0, 0), (1, 0), (1, 1), (0, 1))
    # posts + rail
    for i in range(dsegs + 1):
        ang = facing - span / 2 + span * i / dsegs
        px = east + deck_r1 * math.sin(ang)
        pn = north + deck_r1 * math.cos(ang)
        timber.box(enu(px, pn, base + 0.07), enu(px, pn, base + 1.02), 0.035)
    for i in range(dsegs):
        a0 = facing - span / 2 + span * i / dsegs
        a1 = facing - span / 2 + span * (i + 1) / dsegs
        p0 = enu(east + deck_r1 * math.sin(a0), north + deck_r1 * math.cos(a0), base + 1.00)
        p1 = enu(east + deck_r1 * math.sin(a1), north + deck_r1 * math.cos(a1), base + 1.00)
        timber.box(p0, p1, 0.03)

    # glass door facing path (photos: dark-framed glass entrance)
    door_w, door_h = 1.15 if diameter > 8 else 1.02, 2.15
    de, dn = math.sin(facing), math.cos(facing)
    pe, pn = east + de * (r * 0.96), north + dn * (r * 0.96)
    sx, sn = -dn, de
    y0, y1 = base + 0.08, base + door_h
    g00 = enu(pe - sx * door_w / 2, pn - sn * door_w / 2, y0)
    g10 = enu(pe + sx * door_w / 2, pn + sn * door_w / 2, y0)
    g11 = enu(pe + sx * door_w / 2, pn + sn * door_w / 2, y1)
    g01 = enu(pe - sx * door_w / 2, pn - sn * door_w / 2, y1)
    gn = norm((de, 0, -dn))
    glass.quad(g00, g10, g11, g01, gn)
    timber.box(g00, g01, 0.04)
    timber.box(g10, g11, 0.04)
    timber.box(g01, g11, 0.04)
    timber.box(g00, g10, 0.04)
    # mid mullion
    mid0 = enu(pe, pn, y0)
    mid1 = enu(pe, pn, y1)
    timber.box(mid0, mid1, 0.03)

    # side windows at ±62°
    for side in (-1, 1):
        ang = facing + side * math.radians(62)
        de, dn = math.sin(ang), math.cos(ang)
        pe, pn = east + de * (r * 0.97), north + dn * (r * 0.97)
        sx, sn = -dn, de
        ww, wh, wb = 0.95, 0.95, base + 1.15
        w00 = enu(pe - sx * ww / 2, pn - sn * ww / 2, wb)
        w10 = enu(pe + sx * ww / 2, pn + sn * ww / 2, wb)
        w11 = enu(pe + sx * ww / 2, pn + sn * ww / 2, wb + wh)
        w01 = enu(pe - sx * ww / 2, pn - sn * ww / 2, wb + wh)
        glass.quad(w00, w10, w11, w01, norm((de, 0, -dn)))
        timber.box(w00, w01, 0.03)
        timber.box(w10, w11, 0.03)
        timber.box(w00, w10, 0.03)
        timber.box(w01, w11, 0.03)

    return [
        ("canvas_" + hid, canvas, "canvas_" + hid),
        ("timber_" + hid, timber, "timber"),
        ("deck_" + hid, deck, "deck"),
        ("glass_" + hid, glass, "glass"),
    ]


def pack_glb(entries, images):
    """entries: list of (node_name, Mesh, mat_name). images: name -> jpeg bytes."""
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

    mat_index = {}

    def ensure_mat(name):
        if name in mat_index:
            return mat_index[name]
        if name == "glass":
            materials.append({
                "name": "glass",
                "alphaMode": "BLEND",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.18, 0.28, 0.30, 0.55],
                    "metallicFactor": 0.2,
                    "roughnessFactor": 0.12,
                },
            })
        elif name == "veg_lod":
            materials.append({
                "name": "veg_lod",
                "pbrMetallicRoughness": {"baseColorFactor": [0.22, 0.34, 0.16, 1], "metallicFactor": 0, "roughnessFactor": 0.95},
            })
        elif name in img_tex:
            materials.append({
                "name": name,
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": img_tex[name]},
                    "metallicFactor": 0,
                    "roughnessFactor": 0.86,
                },
            })
        else:
            materials.append({
                "name": name,
                "pbrMetallicRoughness": {"baseColorFactor": [0.4, 0.4, 0.35, 1], "metallicFactor": 0, "roughnessFactor": 0.9},
            })
        mat_index[name] = len(materials) - 1
        return mat_index[name]

    def add_acc(raw, typ, comp, mn, mx, target):
        off = sum(len(p) for p in bin_parts)
        bin_parts.append(align4(raw))
        bufferViews.append({"buffer": 0, "byteOffset": off, "byteLength": len(raw), "target": target})
        stride = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[typ]
        bpe = 2 if comp == 5123 else 4
        accessors.append({
            "bufferView": len(bufferViews) - 1,
            "componentType": comp,
            "count": len(raw) // (bpe * stride),
            "type": typ,
            "min": mn,
            "max": mx,
        })
        return len(accessors) - 1

    def mn_mx(arr, dim):
        cols = [arr[i::dim] for i in range(dim)]
        return [min(c) for c in cols], [max(c) for c in cols]

    # group house parts under one node name house_X
    grouped = {}
    order = []
    for node_name, mesh, mat in entries:
        key = node_name
        if node_name.startswith("house_") or node_name.startswith("canvas_") or node_name.startswith("timber_") or node_name.startswith("deck_") or node_name.startswith("glass_"):
            hid = node_name.split("_")[1]
            key = "house_" + hid
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((mesh, mat))

    for key in order:
        prims = []
        for mesh, mat in grouped[key]:
            if not mesh.idx:
                continue
            if max(mesh.idx) > 65535:
                raise SystemExit(f"index overflow {key} {mesh.name}")
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
            prims.append({
                "attributes": {"POSITION": ai, "NORMAL": ni, "TEXCOORD_0": ui},
                "indices": ii,
                "material": ensure_mat(mat),
                "mode": 4,
            })
        if not prims:
            continue
        gltf_meshes.append({"name": key, "primitives": prims})
        nodes.append({"name": key, "mesh": len(gltf_meshes) - 1})

    blob = b"".join(bin_parts)
    gltf = {
        "asset": {"version": "2.0", "generator": "aumara-v2.1-reality"},
        "scene": 0,
        "scenes": [{"name": "AUMARA_SITE_V2_1", "nodes": list(range(len(nodes)))}],
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
    return OUT.stat().st_size, [n["name"] for n in nodes]


def main():
    hm = json.loads((ROOT / "world" / "heightmap.json").read_text())
    geo = json.loads((ROOT / "AUMARA_WORLD_GEOREFERENCE_v1.json").read_text())
    fp = json.loads((ROOT / "world" / "flight-path.json").read_text())
    wps = fp["waypoints"]

    photos = {
        "A": PUB / "houses/chalet-1/houses_real_1B6A8852.jpg",
        "B": PUB / "houses/superior-1/houses_real_1B6A9875.jpg",
        "C": PUB / "houses/chalet-2/houses_real_1B6A8803.jpg",
        "D": PUB / "houses/superior-2/houses_real_1B6A9866.jpg",
        "E": PUB / "houses/chalet-3/houses_real_1B6A8857.jpg",
        "F": PUB / "houses/private-6/exterior.jpg",
    }
    images = {
        "ground": jpg_bytes(load_rgb(PUB / "twin/pnoa_25cm.jpg"), 1024, 84),
        "path": jpg_bytes(load_rgb(PUB / "site/path_day_v1.jpg"), 384, 80),
        "timber": jpg_bytes(wood_swatch(load_rgb(photos["A"]), (0.05, 0.62, 0.45, 0.92)), 256, 78),
        "deck": jpg_bytes(wood_swatch(load_rgb(photos["B"]), (0.15, 0.70, 0.70, 0.98)), 256, 78),
        "canopy": jpg_bytes(crop_frac(load_rgb(photos["A"]), (0.55, 0.00, 0.98, 0.45)), 256, 76),
        "bark": jpg_bytes(crop_frac(load_rgb(photos["C"]), (0.02, 0.35, 0.18, 0.85)), 128, 74),
    }
    for hid, p in photos.items():
        images["canvas_" + hid] = jpg_bytes(fabric_from_photo(load_rgb(p)), 384, 80)

    # denser terrain: bilinear upsample of verified heightmap so raycast ≈ DEM
    terrain = Mesh("terrain")
    cols, rows = hm["cols"], hm["rows"]
    e0, n0, cell = hm["east0"], hm["north0"], hm["cell"]
    up = 2
    fcell = cell / up
    fcols = (cols - 1) * up + 1
    frows = (rows - 1) * up + 1
    grid = []
    for ri in range(frows):
        row = []
        for ci in range(fcols):
            e = e0 + ci * fcell
            n = n0 + ri * fcell
            row.append((e, n, hm_at(hm, e, n)))
        grid.append(row)
    umin, umax = e0, e0 + (fcols - 1) * fcell
    vmin, vmax = n0, n0 + (frows - 1) * fcell
    for ri in range(frows - 1):
        for ci in range(fcols - 1):
            a, b = grid[ri][ci], grid[ri][ci + 1]
            c, d = grid[ri + 1][ci + 1], grid[ri + 1][ci]

            def uv(p):
                return ((p[0] - umin) / (umax - umin), 1 - (p[1] - vmin) / (vmax - vmin))

            pA, pB, pC, pD = enu(*a), enu(*b), enu(*c), enu(*d)
            nrm = norm(cross(sub(pB, pA), sub(pD, pA)))
            terrain.quad(pA, pB, pC, pD, nrm, uv(a), uv(b), uv(c), uv(d))

    # gravel path from DAY_WALK / path_day — ~2.2 m recognizable walk
    path = Mesh("path")
    half = 1.15
    for i in range(len(wps) - 1):
        a, b = wps[i]["local"], wps[i + 1]["local"]
        e0_, n0_ = a["east"], a["north"]
        e1, n1 = b["east"], b["north"]
        dx, dy = e1 - e0_, n1 - n0_
        L = math.hypot(dx, dy) or 1
        px, py = -dy / L * half, dx / L * half
        h0 = hm_at(hm, e0_, n0_) + 0.06
        h1 = hm_at(hm, e1, n1) + 0.06
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
        nearest = min(wps, key=lambda w: (w["local"]["east"] - e) ** 2 + (w["local"]["north"] - n) ** 2)
        facing = math.atan2(nearest["local"]["east"] - e, nearest["local"]["north"] - n)
        height = 5.50 if h["diameterMetres"] == 9 else 4.86
        houses[h["spatialId"]] = house_parts(
            h["spatialId"], e, n, hm_at(hm, e, n), h["diameterMetres"], height, facing
        )

    # source-guided pines along the real walk (DAY_WALK / outdoor photos: pines line the gravel)
    veg = Mesh("veg")
    bark = Mesh("bark")
    occ = [(h["localMetres"]["east"], h["localMetres"]["north"], h["diameterMetres"] / 2 + 2.0) for h in geo["houses"]]

    def blocked(e, n, rad=1.2):
        if any((e - oe) ** 2 + (n - on) ** 2 < (rr + rad) ** 2 for oe, on, rr in occ):
            return True
        # keep path clear
        for i in range(len(wps) - 1):
            a, b = wps[i]["local"], wps[i + 1]["local"]
            ax, ay, bx, by = a["east"], a["north"], b["east"], b["north"]
            abx, aby = bx - ax, by - ay
            t = ((e - ax) * abx + (n - ay) * aby) / ((abx * abx + aby * aby) or 1)
            t = max(0, min(1, t))
            if math.hypot(e - (ax + abx * t), n - (ay + aby * t)) < 2.0:
                return True
        return False

    def pine(e, n, ht):
        base = hm_at(hm, e, n)
        trunk_h = ht * 0.38
        bark.cylinder(e, n, base, base + trunk_h + 0.4, 0.14 + ht * 0.012, 7)
        # layered umbrella canopies — Aleppo/stone-pine volumes from photos
        layers = ((0.42, 0.55, 1.6), (0.62, 0.38, 1.25), (0.80, 0.24, 0.85))
        for frac, ry, rx in layers:
            veg.ellipsoid(e, n, base + ht * frac, rx * (0.7 + ht * 0.06), ry * ht * 0.35, rx * (0.7 + ht * 0.06), 8, 5)

    rng = 11

    def rnd():
        nonlocal rng
        rng = (1103515245 * rng + 12345) & 0x7FFFFFFF
        return rng / 0x7FFFFFFF

    n_pine = 0
    for i in range(len(wps) - 1):
        a, b = wps[i]["local"], wps[i + 1]["local"]
        dx, dy = b["east"] - a["east"], b["north"] - a["north"]
        L = math.hypot(dx, dy) or 1
        px, py = -dy / L, dx / L
        for side, dist, ht in ((1, 3.6 + rnd() * 1.4, 8.5 + rnd() * 4), (-1, 3.3 + rnd() * 1.8, 7.2 + rnd() * 3.5)):
            if (i + side) % 2 != 0:
                continue
            e = a["east"] + dx * 0.5 + px * side * dist
            n = a["north"] + dy * 0.5 + py * side * dist
            if blocked(e, n, 1.6):
                continue
            pine(e, n, ht)
            n_pine += 1

    # a few more from photo-guided pockets north of the cluster (wooded CV-733 edge)
    pockets = [
        (40, 12, 11), (48, 14, 10), (58, 18, 12), (70, 16, 9),
        (78, 18, 11), (30, 8, 8), (88, 10, 9), (55, -10, 7),
        (72, -9, 8), (42, -8, 7), (20, 6, 10), (92, 6, 8),
    ]
    for e, n, ht in pockets:
        if blocked(e, n, 1.8):
            continue
        pine(e, n, ht)
        n_pine += 1

    # distant schematic LOD cones — marked generated
    veg_lod = Mesh("veg_lod")
    for e, n, ht, rad in ((8, 22, 9, 1.4), (15, 24, 8, 1.2), (95, 22, 10, 1.5), (102, 8, 7, 1.1), (10, -18, 6, 1.0)):
        base = hm_at(hm, e, n)
        apex = enu(e, n, base + ht)
        for i in range(6):
            t0, t1 = 2 * math.pi * i / 6, 2 * math.pi * (i + 1) / 6
            p0 = enu(e + rad * math.cos(t0), n + rad * math.sin(t0), base)
            p1 = enu(e + rad * math.cos(t1), n + rad * math.sin(t1), base)
            veg_lod.tri(p0, p1, apex, (0, 1, 0), (0, 1), (1, 1), (0.5, 0))

    entries = [
        ("terrain", terrain, "ground"),
        ("path", path, "path"),
        ("veg", veg, "canopy"),
        ("bark", bark, "bark"),
        ("veg_lod", veg_lod, "veg_lod"),
    ]
    for hid in "ABCDEF":
        entries.extend((name, mesh, mat) for name, mesh, mat in houses[hid])

    size, names = pack_glb(entries, images)
    print("GLB", size, "nodes", names, "pines", n_pine, "terrain_tris", len(terrain.idx) // 3)


if __name__ == "__main__":
    main()
