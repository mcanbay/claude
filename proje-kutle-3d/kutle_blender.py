"""
plan_geometri.json'dan Blender'da 3B kütle modeli kurar, render alır ve dışa aktarır.

    python kutle_blender.py --json plan_geometri.json --out cikti

Gereken: `pip install bpy shapely pillow` (bpy = Blender'ın Python modülü, Python 3.13).
Blender kuruluysa:  blender -b -P kutle_blender.py -- --json plan_geometri.json

Kat kotları (varsayılan):
  Zemin kat (dükkanlar)   ±0.00 → +4.50
  1.–7. normal katlar     her biri 3.30 m → çatı döşemesi üstü +27.60
  Çatı parapeti           +28.60 (1.00 m, varsayım)
  Merdiven/asansör kulesi +30.60 (3.00 m, varsayım)
"""

import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector, geometry
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

# ------------------------------------------------------------------ ayarlar

ZEMIN_H = 4.50
KAT_H = 3.30
KAT_SAYISI = 7
DOSEME = 0.30            # döşeme kalınlığı (cephede açık gri bant)
PARAPET = 1.00
KULE = 3.00
TERAS_PARAPET = 0.60
CAM_DERINLIK = 0.18      # pencere boşluğunun cepheden içeri girişi

TOPLAM_H = ZEMIN_H + KAT_SAYISI * KAT_H


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="plan_geometri.json")
    ap.add_argument("--out", default="cikti")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--scale", type=float, default=1.0, help="Render çözünürlük çarpanı (deneme için 0.5)")
    ap.add_argument("--only", default="", help="Yalnızca bu görünümler (virgülle): cadde,otopark,goz,ust,kesit,kil")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--no-kule", action="store_true", help="Çatıdaki merdiven/asansör kulesini koyma")
    return ap.parse_args(argv)


# --------------------------------------------------------------- geometri

def P(d):
    """JSON {outer, holes} -> shapely Polygon"""
    return Polygon(d["outer"], d.get("holes") or [])


def parts(g):
    if g is None or g.is_empty:
        return []
    if hasattr(g, "geoms"):
        out = []
        for x in g.geoms:
            out += parts(x)
        return out
    return [g] if isinstance(g, Polygon) and g.area > 1e-4 else []


def clean_ring(coords, tol=0.005):
    pts = []
    for c in coords:
        if not pts or math.dist(pts[-1], c) > tol:
            pts.append(tuple(c))
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) <= tol:
        pts.pop()
    return pts


def prism_data(poly, z0, z1):
    """Shapely poligonu z0..z1 arasında katı (manifold) prizmaya çevirir."""
    poly = orient(poly.simplify(0.003), sign=1.0)
    rings = [clean_ring(poly.exterior.coords)] + [clean_ring(r.coords) for r in poly.interiors]
    rings = [r for r in rings if len(r) >= 3]
    flat = [p for r in rings for p in r]
    n = len(flat)
    verts = [(x, y, z0) for x, y in flat] + [(x, y, z1) for x, y in flat]
    faces = []
    tris = geometry.tessellate_polygon([[Vector((x, y, 0)) for x, y in r] for r in rings])
    for a, b, c in tris:
        pa, pb, pc = (Vector(flat[i] + (0,)) for i in (a, b, c))
        if (pb - pa).cross(pc - pa).z < 0:
            b, c = c, b
        faces.append((a + n, b + n, c + n))    # üst
        faces.append((c, b, a))                # alt
    off = 0
    for r in rings:
        m = len(r)
        for i in range(m):
            j = (i + 1) % m
            faces.append((off + i, off + j, off + j + n, off + i + n))
        off += m
    return verts, faces


class MeshBuilder:
    """Aynı malzemeli parçaları tek nesnede toplar."""

    def __init__(self):
        self.verts, self.faces = [], []

    def add(self, verts, faces):
        o = len(self.verts)
        self.verts += verts
        self.faces += [tuple(i + o for i in f) for f in faces]

    def prism(self, poly, z0, z1):
        for p in parts(poly):
            self.add(*prism_data(p, z0, z1))

    def box(self, center, size, rot=0.0):
        cx, cy, cz = center
        sx, sy, sz = (s / 2 for s in size)
        c, s = math.cos(rot), math.sin(rot)
        vs = []
        for z in (-sz, sz):
            for x, y in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
                vs.append((cx + x * c - y * s, cy + x * s + y * c, cz + z))
        fs = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(vs, fs)

    def segment_box(self, a, b, z0, z1, thick, offset=0.0):
        """a-b doğrusu boyunca, sola 'offset' kaydırılmış ince kutu."""
        ax, ay = a
        bx, by = b
        L = math.dist(a, b)
        if L < 1e-3:
            return
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        cx, cy = (ax + bx) / 2 + nx * offset, (ay + by) / 2 + ny * offset
        self.box((cx, cy, (z0 + z1) / 2), (L, thick, z1 - z0), math.atan2(uy, ux))

    def build(self, name, mat, coll=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.validate()
        me.update()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        if mat:
            ob.data.materials.append(mat)
        for p in me.polygons:
            p.use_smooth = False
        return ob


# --------------------------------------------------------------- malzemeler

def material(name, color, rough=0.6, metal=0.0, transmission=0.0, ior=1.45, alpha=1.0, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*color, alpha)
    return m


def make_materials():
    return {
        "duvar": material("Duvar_Beyaz", (0.80, 0.78, 0.74), 0.85),
        "bant": material("Doseme_Bandi", (0.50, 0.51, 0.52), 0.7),
        "zemin_kaplama": material("Zemin_Kat_Antrasit", (0.06, 0.065, 0.07), 0.45),
        "cam": material("Cam", (0.03, 0.045, 0.06), 0.04, ior=1.6),
        "korkuluk_cam": material("Korkuluk_Cami", (0.75, 0.85, 0.88), 0.03, transmission=1.0, ior=1.5, alpha=0.35),
        "metal": material("Metal", (0.12, 0.12, 0.13), 0.35, metal=1.0),
        "cati": material("Cati", (0.36, 0.36, 0.35), 0.95),
        "parke": material("Parke_Tasi", (0.50, 0.48, 0.45), 0.9),
        "asfalt": material("Asfalt", (0.07, 0.07, 0.075), 0.95),
        "cizgi": material("Yol_Cizgisi", (0.85, 0.85, 0.82), 0.8),
        "cim": material("Cim", (0.16, 0.24, 0.09), 1.0),
        "cevre": material("Cevre_Zemin", (0.17, 0.20, 0.12), 1.0),
        "kaldirim": material("Kaldirim", (0.55, 0.53, 0.50), 0.9),
        "agac": material("Agac_Tac", (0.10, 0.20, 0.06), 0.9),
        "govde": material("Agac_Govde", (0.17, 0.12, 0.08), 0.9),
        "kil": material("Kil", (0.78, 0.77, 0.75), 0.9),
        "kil_cam": material("Kil_Cam", (0.20, 0.24, 0.28), 0.1),
    }


CAR_COLORS = [(0.80, 0.80, 0.80), (0.55, 0.56, 0.58), (0.03, 0.03, 0.035), (0.25, 0.26, 0.28),
              (0.06, 0.10, 0.22), (0.45, 0.05, 0.04), (0.75, 0.73, 0.68)]


# ------------------------------------------------------------------- sahne

def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def edge_list(poly):
    """Kenarlar; iç taraf her zaman solda kalır (dış normal sağda)."""
    poly = orient(poly, sign=1.0)
    for r in [poly.exterior] + list(poly.interiors):
        cs = clean_ring(r.coords)
        for i in range(len(cs)):
            yield cs[i], cs[(i + 1) % len(cs)]


def outward_normal(poly, a, b):
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    n = (uy, -ux)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if poly.contains(Point(mid[0] + n[0] * 0.05, mid[1] + n[1] * 0.05)):
        n = (-n[0], -n[1])
    return n


def add_boolean(target, cutter):
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    mod = target.modifiers.new("Bosluklar", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    try:
        mod.solver = "MANIFOLD"
    except Exception:
        mod.solver = "EXACT"
    return mod


def street_frame(D):
    st = D["cadde"]
    smid = ((st["a"][0] + st["b"][0]) / 2, (st["a"][1] + st["b"][1]) / 2)
    sl = math.dist(st["a"], st["b"])
    su = ((st["b"][0] - st["a"][0]) / sl, (st["b"][1] - st["a"][1]) / sl)
    sn = (su[1], -su[0])
    if Polygon(D["parsel"]).contains(Point(smid[0] + sn[0] * 2, smid[1] + sn[1] * 2)):
        sn = (-sn[0], -sn[1])
    return smid, su, sn


def eye_camera_pos(D):
    smid, su, sn = street_frame(D)
    return (smid[0] + sn[0] * 19.6 - su[0] * 24, smid[1] + sn[1] * 19.6 - su[1] * 24, 1.65)


def build_scene(D, M, args):
    rnd = random.Random(7)
    bina = collection("Bina")
    cevre = collection("Cevre")
    yardimci = collection("Yardimci")
    yardimci.hide_render = True

    parcel = Polygon(D["parsel"])
    zemin = D["zemin"]
    normal = D["normal"]
    ground_fp = unary_union([P(p) for p in zemin["ayak_izi"]])
    body = P(zemin["govde"])
    fins = [P(p) for p in zemin["teras_bolmeleri"]]
    tower = unary_union([P(p) for p in normal["doseme"]])
    enclosed = P(normal["kapali"])
    balconies = [P(b) for b in normal["balkonlar"]]
    gap = P(normal["giris_boslugu"]) if normal.get("giris_boslugu") else None
    core = P(normal["cekirdek"])

    # ------------------------------------------------ zemin kat (dükkanlar)
    mb = MeshBuilder()
    mb.prism(body, 0.0, ZEMIN_H - DOSEME)
    for f in fins:
        mb.prism(f, 0.0, ZEMIN_H - DOSEME)
    zemin_ob = mb.build("Zemin_Kat_Dukkanlar", M["zemin_kaplama"], bina)

    # Vitrin camları: gövdenin dış kenarları boyunca ~3 m'lik bölmeler.
    cut, glass = MeshBuilder(), MeshBuilder()
    gap_zone = gap.buffer(0.4) if gap is not None else Polygon()
    for a, b in edge_list(body):
        L = math.dist(a, b)
        if L < 1.6:
            continue
        mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        n = outward_normal(body, a, b)
        # dışarıya bakmayan (başka bir hacme dayalı) kenarları atla
        probe = Point(mid.x + n[0] * 0.3, mid.y + n[1] * 0.3)
        if any(f.buffer(0.05).contains(probe) for f in fins):
            continue
        in_gap = gap_zone.contains(mid)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        if in_gap:
            if abs(ux) > abs(uy):          # giriş geçidinin yan duvarları: kapalı
                continue
            top = 3.0                      # bina giriş kapısı
            bays = [(0.0, L)]
        else:
            top = 3.55
            nb = max(1, round(L / 3.0))
            w = L / nb
            bays = [(i * w, (i + 1) * w) for i in range(nb)]
        for s0, s1 in bays:
            s0, s1 = s0 + 0.12, s1 - 0.12
            p0 = (a[0] + ux * s0, a[1] + uy * s0)
            p1 = (a[0] + ux * s1, a[1] + uy * s1)
            # kesici: cepheden içeri CAM_DERINLIK kadar boşluk
            cut.segment_box(p0, p1, 0.12, top, CAM_DERINLIK * 2 + 0.1, offset=0.0)
            glass.segment_box(p0, p1, 0.12, top, 0.03, offset=CAM_DERINLIK)   # sol = iç taraf
    cut_ob = cut.build("Zemin_Vitrin_Kesici", None, yardimci)
    add_boolean(zemin_ob, cut_ob)
    glass.build("Zemin_Vitrin_Cam", M["cam"], bina)

    # zemin kat tavan döşemesi (teraslar dahil, saçak gibi)
    mb = MeshBuilder()
    mb.prism(ground_fp.buffer(0.05, join_style=2), ZEMIN_H - DOSEME, ZEMIN_H)
    mb.build("Zemin_Kat_Tavan_Dosemesi", M["bant"], bina)

    # gezilemeyen teras: çatı kaplaması + parapet
    roof_area = ground_fp.difference(tower.buffer(0.02, join_style=2))
    mb = MeshBuilder()
    mb.prism(roof_area, ZEMIN_H, ZEMIN_H + 0.04)
    mb.build("Gezilemeyen_Teras", M["cati"], bina)
    ring = ground_fp.buffer(0.05, join_style=2).difference(ground_fp.buffer(-0.2, join_style=2))
    ring = ring.difference(tower.buffer(0.05, join_style=2))
    mb = MeshBuilder()
    mb.prism(ring, ZEMIN_H, ZEMIN_H + TERAS_PARAPET)
    mb.build("Teras_Parapeti", M["duvar"], bina)

    # --------------------------------------------------- normal katlar 1..7
    walls, bands, wcut, wglass, rail, handrail = (MeshBuilder() for _ in range(6))
    # açıklıkların dış normalleri
    openings = []
    for o in normal["acikliklar"]:
        a, b = tuple(o["a"]), tuple(o["b"])
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        n = (uy, -ux)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if enclosed.contains(Point(mid[0] + n[0] * 0.3, mid[1] + n[1] * 0.3)):
            a, b = b, a        # dış normal sağda kalsın
        openings.append((a, b, o["tip"]))
    rail_edges = []
    for bal in balconies:
        for a, b in edge_list(bal):
            if math.dist(a, b) < 0.3:
                continue
            mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if enclosed.distance(mid) < 0.12:
                continue
            n = outward_normal(bal, a, b)
            if tower.contains(Point(mid.x + n[0] * 0.3, mid.y + n[1] * 0.3)):
                continue
            rail_edges.append((a, b, n))

    for i in range(KAT_SAYISI):
        z0 = ZEMIN_H + i * KAT_H
        z1 = z0 + KAT_H
        walls.prism(enclosed, z0, z1 - DOSEME)
        bands.prism(tower.buffer(0.04, join_style=2), z1 - DOSEME, z1)
        for a, b, tip in openings:
            sill, head = (0.0, 2.45) if tip == "door" else (0.90, 2.45)
            # sağdaki dış normal => sol-offset negatif dışarı; kesici yüzü ortalar
            cut_w = CAM_DERINLIK * 2 + 0.1
            wcut.segment_box(a, b, z0 + sill, z0 + head, cut_w, offset=0.0)
            wglass.segment_box(a, b, z0 + sill, z0 + head, 0.03, offset=CAM_DERINLIK)
        for a, b, n in rail_edges:
            L = math.dist(a, b)
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            # köşelerde çakışmasın diye biraz kısalt
            a2 = (a[0] + ux * 0.05 - n[0] * 0.08, a[1] + uy * 0.05 - n[1] * 0.08)
            b2 = (b[0] - ux * 0.05 - n[0] * 0.08, b[1] - uy * 0.05 - n[1] * 0.08)
            rail.segment_box(a2, b2, z0 + 0.05, z0 + 1.05, 0.02)
            handrail.segment_box(a2, b2, z0 + 1.05, z0 + 1.10, 0.06)

    walls_ob = walls.build("Normal_Katlar_Duvar", M["duvar"], bina)
    add_boolean(walls_ob, wcut.build("Normal_Kat_Pencere_Kesici", None, yardimci))
    wglass.build("Normal_Kat_Camlar", M["cam"], bina)
    bands.build("Normal_Kat_Doseme_Bantlari", M["bant"], bina)
    rail.build("Balkon_Korkuluk_Cam", M["korkuluk_cam"], bina)
    handrail.build("Balkon_Kupesteleri", M["metal"], bina)

    # ----------------------------------------------------------- çatı
    mb = MeshBuilder()
    mb.prism(tower.buffer(-0.2, join_style=2), TOPLAM_H, TOPLAM_H + 0.05)
    mb.build("Cati_Kaplamasi", M["cati"], bina)
    mb = MeshBuilder()
    mb.prism(tower.buffer(0.04, join_style=2).difference(tower.buffer(-0.2, join_style=2)), TOPLAM_H, TOPLAM_H + PARAPET)
    mb.build("Cati_Parapeti", M["duvar"], bina)
    if not args.no_kule:
        mb = MeshBuilder()
        mb.prism(core, TOPLAM_H, TOPLAM_H + KULE - 0.25)
        mb.build("Merdiven_Asansor_Kulesi", M["duvar"], bina)
        mb = MeshBuilder()
        mb.prism(core.buffer(0.15, join_style=2), TOPLAM_H + KULE - 0.25, TOPLAM_H + KULE)
        mb.build("Kule_Saçak", M["bant"], bina)

    # ----------------------------------------------------------- çevre
    build_site(D, M, cevre, parcel, ground_fp, rnd, avoid=[eye_camera_pos(D)])
    return bina


def build_site(D, M, coll, parcel, ground_fp, rnd, avoid=()):
    st = D["cadde"]
    a, b = st["a"], st["b"]
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (u[1], -u[0])
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if parcel.contains(Point(mid[0] + n[0] * 2, mid[1] + n[1] * 2)):
        n = (-n[0], -n[1])       # n: parselden caddeye doğru

    def strip(d0, d1, ext=1100):
        p = [(mid[0] + u[0] * s + n[0] * d, mid[1] + u[1] * s + n[1] * d)
             for s, d in ((-ext, d0), (ext, d0), (ext, d1), (-ext, d1))]
        return Polygon(p)

    world = box(-1200, -1200, 1200, 1200)
    kaldirim1, yol, kaldirim2 = strip(0, 3.5), strip(3.5, 17.5), strip(17.5, 21)
    cevre_zemin = world.difference(unary_union([parcel, kaldirim1, yol, kaldirim2]).buffer(0.01))

    mb = MeshBuilder()
    mb.prism(cevre_zemin, -0.12, 0.0)
    mb.build("Cevre_Zemin", M["cevre"], coll)
    mb = MeshBuilder()
    mb.prism(yol.intersection(world), -0.12, -0.02)
    mb.build("Odunluk_Caddesi", M["asfalt"], coll)
    mb = MeshBuilder()
    mb.prism(unary_union([kaldirim1, kaldirim2]).intersection(world).difference(parcel), -0.12, 0.13)
    mb.build("Kaldirimlar", M["kaldirim"], coll)
    # şerit çizgisi (kesikli)
    mb = MeshBuilder()
    for s in range(-400, 400, 9):
        c0 = (mid[0] + u[0] * s + n[0] * 10.5, mid[1] + u[1] * s + n[1] * 10.5)
        c1 = (c0[0] + u[0] * 4.5, c0[1] + u[1] * 4.5)
        mb.segment_box(c0, c1, -0.02, 0.0, 0.15)
    mb.build("Serit_Cizgisi", M["cizgi"], coll)

    # parsel içi: kenarlarda yeşil şerit, bina çevresinde parke, gerisi asfalt
    street_edge = LineString([a, b])
    edge_strip = parcel.difference(parcel.buffer(-1.6, join_style=2)).difference(street_edge.buffer(4.0))
    apron = ground_fp.buffer(2.0, join_style=2).intersection(parcel)
    front = parcel.intersection(street_edge.buffer(3.0))         # caddeye bakan ön bahçe/giriş parkesi
    asfalt = parcel.difference(unary_union([edge_strip, apron, front]).buffer(0.01))
    parke = unary_union([apron, front]).intersection(parcel).difference(ground_fp.buffer(-0.05))
    mb = MeshBuilder()
    mb.prism(edge_strip, -0.12, 0.05)
    mb.build("Yesil_Serit", M["cim"], coll)
    mb = MeshBuilder()
    mb.prism(asfalt, -0.12, 0.0)
    mb.build("Otopark_Asfalt", M["asfalt"], coll)
    mb = MeshBuilder()
    mb.prism(parke, -0.12, 0.03)
    mb.build("Parke_Kaplama", M["parke"], coll)

    # otopark çizgileri ve araçlar
    lines, cars_body = MeshBuilder(), {}
    for s in D["otopark"]:
        cx, cy = s["c"]
        Lp, Wp, ang = s["uzunluk"], s["genislik"], s["aci"]
        ux, uy = math.cos(ang), math.sin(ang)
        vx, vy = -uy, ux
        corners = [(cx + ux * Lp / 2 * i + vx * Wp / 2 * j, cy + uy * Lp / 2 * i + vy * Wp / 2 * j)
                   for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for k in range(4):
            lines.segment_box(corners[k], corners[(k + 1) % 4], 0.0, 0.012, 0.12)
        if rnd.random() < 0.62:
            col = rnd.randrange(len(CAR_COLORS))
            mb = cars_body.setdefault(col, MeshBuilder())
            flip = 1 if rnd.random() < 0.5 else -1
            jitter = rnd.uniform(-0.15, 0.15)
            ccx, ccy = cx + ux * jitter, cy + uy * jitter
            mb.box((ccx, ccy, 0.62), (4.35, 1.80, 0.72), ang)
            # kabin: aracın bir ucuna kaydırılmış, camlı
            ox = -0.25 * flip
            cars_body.setdefault("cam", MeshBuilder()).box(
                (ccx + ux * ox, ccy + uy * ox, 1.24), (2.30, 1.62, 0.55), ang)
            cars_body.setdefault("teker", MeshBuilder()).box((ccx, ccy, 0.2), (3.9, 1.7, 0.4), ang)
    lines.build("Otopark_Cizgileri", M["cizgi"], coll)
    for key, mb in cars_body.items():
        if key == "cam":
            mb.build("Arac_Kabin", M["cam"], coll)
        elif key == "teker":
            mb.build("Arac_Alt", M["asfalt"], coll)
        else:
            m = material(f"Arac_{key}", CAR_COLORS[key], 0.25, metal=0.4)
            mb.build(f"Arac_Govde_{key}", m, coll)

    # ağaçlar: yeşil şerit boyunca ve karşı kaldırımda
    trees = []
    ring = parcel.buffer(-0.8, join_style=2).exterior
    d = 0.0
    while d < ring.length:
        p = ring.interpolate(d)
        if street_edge.distance(p) > 5 and ground_fp.distance(p) > 4:
            trees.append((p.x, p.y, rnd.uniform(0.85, 1.2)))
        d += rnd.uniform(7.5, 10)
    for s in range(-120, 121, 11):
        p = (mid[0] + u[0] * s + n[0] * 19.3, mid[1] + u[1] * s + n[1] * 19.3)
        trees.append((p[0], p[1], rnd.uniform(0.9, 1.15)))
    for s in range(-120, 121, 13):
        p = Point(mid[0] + u[0] * s + n[0] * 1.6, mid[1] + u[1] * s + n[1] * 1.6)
        if ground_fp.distance(p) > 8 and abs(s) > 40:
            trees.append((p.x, p.y, rnd.uniform(0.8, 1.0)))
    trees = [t for t in trees if all(math.dist(t[:2], c[:2]) > 12 for c in avoid)]
    crown, trunk = MeshBuilder(), MeshBuilder()
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
    ico = bpy.context.active_object
    iv = [tuple(v.co) for v in ico.data.vertices]
    ifc = [tuple(p.vertices) for p in ico.data.polygons]
    bpy.data.objects.remove(ico)
    for x, y, s in trees:
        r = 2.1 * s
        h = 3.0 * s
        trunk.box((x, y, h / 2), (0.28 * s, 0.28 * s, h))
        crown.add([(x + vx * r, y + vy * r, h + 1.2 * s + vz * r * 1.15) for vx, vy, vz in iv], ifc)
    trunk.build("Agac_Govdeleri", M["govde"], coll)
    cob = crown.build("Agac_Taclari", M["agac"], coll)
    for p in cob.data.polygons:
        p.use_smooth = True


# ------------------------------------------------------ ışık ve render

def clay_swap(M):
    """Kil görünümü: bina beyaz, çevre gri tonlar. Eski malzemeleri döndürür."""
    grey = {}

    def g(v, r=0.9):
        if v not in grey:
            grey[v] = material(f"Kil_Gri_{v}", (v, v, v), r)
        return grey[v]
    site = {"Cevre_Zemin": g(0.30), "Odunluk_Caddesi": g(0.16), "Otopark_Asfalt": g(0.20),
            "Kaldirimlar": g(0.45), "Parke_Kaplama": g(0.42), "Yesil_Serit": g(0.33),
            "Serit_Cizgisi": g(0.6), "Otopark_Cizgileri": g(0.6)}
    saved = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.material_slots:
            continue
        old = ob.material_slots[0].material
        if ob.name in site:
            new = site[ob.name]
        elif "Korkuluk_Cam" in ob.name:
            continue
        elif "Cam" in ob.name or "Kabin" in ob.name:
            new = M["kil_cam"]
        else:
            new = M["kil"]
        saved.append((ob, old))
        ob.material_slots[0].material = new
    return saved


def setup_world(sun_az_deg, sun_el_deg):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Gok")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "MULTIPLE_SCATTERING"
    except Exception:
        pass
    sky.sun_disc = False
    sky.sun_elevation = math.radians(sun_el_deg)
    sky.sun_rotation = math.radians(sun_az_deg)
    try:
        sky.altitude = 200
        sky.air_density = 1.0
        sky.aerosol_density = 1.2
    except Exception:
        pass
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.22
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])

    sun_data = bpy.data.lights.new("Gunes", "SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(1.2)
    sun_data.color = (1.0, 0.96, 0.9)
    sun = bpy.data.objects.new("Gunes", sun_data)
    sc.collection.objects.link(sun)
    # sun_rotation: +y'den saat yönünün tersine; güneş ışığı ters yönde gelir
    az, el = math.radians(sun_az_deg), math.radians(sun_el_deg)
    d = Vector((-math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def setup_render(samples, scale):
    import addon_utils
    addon_utils.enable("cycles", default_set=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 6
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except Exception:
            pass
    sc.view_settings.exposure = -0.55
    sc.render.image_settings.file_format = "PNG"
    sc.render.resolution_percentage = int(100 * scale)


def camera(name, loc, target, lens=35, ortho=None, shift=(0, 0)):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.sensor_width = 36
    cd.shift_x, cd.shift_y = shift
    cd.clip_end = 2000
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def render(cam, path, res):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("Render:", path, flush=True)


# --------------------------------------------------------------- anotasyon

def annotate_elevation(path, cam_info, D):
    """Ortografik görünüşe kat kotlarını ve açıklamaları işler."""
    from PIL import Image, ImageDraw, ImageFont
    src = Image.open(path).convert("RGBA")
    im = Image.new("RGB", src.size, (250, 250, 248))
    im.paste(src, (0, 0), src)
    W, H = im.size
    g = ImageDraw.Draw(im)
    cx, cz, scale = cam_info
    ppm = W / scale

    def zpix(z):
        return H / 2 - (z - cz) * ppm

    def xpix(x):
        return W / 2 + (x - cx) * ppm
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", int(W / 75))
        fb = ImageFont.truetype("DejaVuSans-Bold.ttf", int(W / 60))
    except Exception:
        f = fb = ImageFont.load_default()
    xs = [p[0] for p in D["normal"]["kapali"]["outer"]] + [p[0] for g_ in D["zemin"]["ayak_izi"] for p in g_["outer"]]
    x_left, x_right = xpix(min(xs)) - 30, xpix(max(xs)) + 30
    g.line([(0, zpix(0)), (W, zpix(0))], fill=(90, 90, 90), width=3)
    u = W / 1800
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    go = ImageDraw.Draw(ov)
    levels = [(0.0, "±0.00")]
    levels += [(ZEMIN_H + i * KAT_H, f"+{ZEMIN_H + i * KAT_H:.2f}") for i in range(KAT_SAYISI + 1)]
    for z, t in levels:
        y = zpix(z)
        col = (40, 90, 160, 255)
        go.line([(x_left - 250 * u, y), (x_left, y)], fill=col, width=max(1, int(2 * u)))
        go.line([(x_left, y), (x_right + 40 * u, y)], fill=(40, 90, 160, 70), width=max(1, int(2 * u)))
        go.text((x_left - 200 * u, y - int(W / 75) - 4 * u), t, fill=col, font=f)
    for z, t in ((TOPLAM_H + PARAPET, f"+{TOPLAM_H + PARAPET:.2f}  çatı parapeti"),
                 (TOPLAM_H + KULE, f"+{TOPLAM_H + KULE:.2f}  merdiven/asansör kulesi")):
        y = zpix(z)
        go.line([(xpix(min(xs)) + 60 * u, y), (x_right + 40 * u, y)], fill=(120, 120, 120, 200), width=max(1, int(2 * u)))
        go.text((x_right + 55 * u, y - int(W / 75) - 2 * u), t, fill=(110, 110, 110, 255), font=f)
    im.paste(ov, (0, 0), ov)
    g = ImageDraw.Draw(im)
    # kat isimleri
    names = [(ZEMIN_H / 2, f"ZEMİN KAT · DÜKKAN · {ZEMIN_H:.2f} m")]
    for i in range(KAT_SAYISI):
        names.append((ZEMIN_H + i * KAT_H + KAT_H / 2, f"{i + 1}. KAT · KONUT · {KAT_H:.2f} m"))
    for z, t in names:
        g.text((x_right + 55 * u, zpix(z) - int(W / 150)), t, fill=(30, 30, 30), font=f)
    # toplam yükseklik ölçüsü
    xd = x_left - 225 * u
    g.line([(xd, zpix(0)), (xd, zpix(TOPLAM_H))], fill=(180, 40, 30), width=3)
    for z in (0, TOPLAM_H):
        g.line([(xd - 12, zpix(z)), (xd + 12, zpix(z))], fill=(180, 40, 30), width=3)
    txt = f"{TOPLAM_H:.2f} m"
    tw = g.textlength(txt, font=fb)
    lbl = Image.new("RGBA", (int(tw) + 10, int(W / 50)), (0, 0, 0, 0))
    ImageDraw.Draw(lbl).text((5, 0), txt, fill=(180, 40, 30), font=fb)
    lbl = lbl.rotate(90, expand=True)
    im.paste(lbl, (int(xd - lbl.width - 8), int(zpix(TOPLAM_H / 2) - lbl.height / 2)), lbl)
    g.text((40, 30), "KÜTLE GÖRÜNÜŞÜ VE KAT KOTLARI", fill=(20, 20, 20), font=fb)
    g.text((40, 30 + int(W / 45)), f"Zemin kat 4.50 m + {KAT_SAYISI} normal kat × 3.30 m = {TOPLAM_H:.2f} m (çatı döşemesi üstü)",
           fill=(60, 60, 60), font=f)
    g.text((40, 30 + 2 * int(W / 45)), "Parapet ve çatı kulesi yükseklikleri projede yoktur, varsayımdır.",
           fill=(60, 60, 60), font=f)
    im.save(path)


def annotate_top(path, cam_info, D):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGB")
    W, H = im.size
    g = ImageDraw.Draw(im)
    cx, cy, scale = cam_info
    ppm = W / scale

    def T(p):
        return (W / 2 + (p[0] - cx) * ppm, H / 2 - (p[1] - cy) * ppm)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", int(W / 80))
        fb = ImageFont.truetype("DejaVuSans-Bold.ttf", int(W / 60))
    except Exception:
        f = fb = ImageFont.load_default()
    pts = [T(p) for p in D["parsel"]]
    g.line(pts + [pts[0]], fill=(230, 60, 40), width=4)
    st = D["cadde"]
    a, b = T(st["a"]), T(st["b"])
    ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
    txt = "ODUNLUK CADDESİ"
    tw = g.textlength(txt, font=fb)
    lbl = Image.new("RGBA", (int(tw) + 10, int(W / 45)), (0, 0, 0, 0))
    ImageDraw.Draw(lbl).text((5, 0), txt, fill=(255, 255, 255), font=fb)
    lbl = lbl.rotate(ang, expand=True)
    mx, my = (a[0] + b[0]) / 2 + 0.035 * W, (a[1] + b[1]) / 2
    im.paste(lbl, (int(mx - lbl.width / 2), int(my - lbl.height / 2)), lbl)
    pb = [T(p) for p in D["parsel"]]
    top_y = min(p[1] for p in pb)
    g.text((W / 2 - g.textlength("OTEL BÖLGESİ", font=fb) / 2, top_y - W / 30), "OTEL BÖLGESİ", fill=(255, 255, 255), font=fb)
    g.text((40, 30), "VAZİYET · ÜSTTEN GÖRÜNÜŞ", fill=(255, 255, 255), font=fb)
    im.save(path)


# -------------------------------------------------------------------- ana

def main():
    args = parse_args()
    with open(args.json, encoding="utf-8") as fh:
        D = json.load(fh)
    os.makedirs(args.out, exist_ok=True)
    out = os.path.abspath(args.out)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = make_materials()
    bina = build_scene(D, M, args)

    # kamera hedefleri
    xs = [p[0] for p in D["parsel"]]
    ys = [p[1] for p in D["parsel"]]
    st = D["cadde"]
    smid, su, sn = street_frame(D)
    goz = eye_camera_pos(D)

    setup_world(sun_az_deg=215, sun_el_deg=38)
    setup_render(args.samples, args.scale)

    H = TOPLAM_H
    views = {
        "cadde": (camera("Kamera_Cadde_Kusbakisi", (smid[0] + 55, -62, 46), (2, 0, 10), lens=32), (1920, 1080)),
        "otopark": (camera("Kamera_Otopark_Kusbakisi", (-72, -64, 50), (-10, 2, 8), lens=30), (1920, 1080)),
        "goz": (camera("Kamera_Cadde_Goz_Hizasi", goz, (-3, 1, 12.5), lens=19, shift=(0, 0.08)), (1920, 1080)),
        "kil": (camera("Kamera_Kil_Kutle", (smid[0] + 48, 58, 44), (0, 0, 10), lens=35), (1920, 1080)),
    }
    top_scale = (max(xs) - min(xs)) * 1.12
    cx_top, cy_top = (max(xs) + min(xs)) / 2 + 4, (max(ys) + min(ys)) / 2
    views["ust"] = (camera("Kamera_Ust", (cx_top, cy_top, 200), (cx_top, cy_top, 0), ortho=top_scale), (2400, 1200))
    gxs = [p[0] for g_ in D["zemin"]["ayak_izi"] for p in g_["outer"]]
    ecx = (min(gxs) + max(gxs)) / 2 + 2
    ecz = H / 2 + 2.0
    escale = 80
    cam_el = camera("Kamera_Gorunus_Guney", (ecx, -150, ecz), (ecx, 0, ecz), ortho=escale)
    views["kesit"] = (cam_el, (1800, 1400))

    sel = [v for v in args.only.split(",") if v] or list(views)
    if not args.no_render:
        for key in sel:
            cam, res = views[key]
            path = os.path.join(out, {"cadde": "01_cadde_kusbakisi.png", "otopark": "02_otopark_kusbakisi.png",
                                      "goz": "03_cadde_goz_hizasi.png", "kil": "04_kil_kutle.png",
                                      "ust": "05_vaziyet_ustten.png", "kesit": "06_gorunus_kotlar.png"}[key])
            vl = bpy.context.view_layer
            vl.material_override = M["kil"] if key == "kesit" else None
            saved = clay_swap(M) if key == "kil" else []
            bpy.context.scene.view_settings.exposure = {"kil": -0.75, "kesit": -0.7}.get(key, -0.55)
            bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = \
                0.13 if key in ("kil", "kesit") else 0.22
            cevre_coll = bpy.data.collections["Cevre"]
            cevre_coll.hide_render = key == "kesit"
            bpy.context.scene.render.film_transparent = key == "kesit"
            render(cam, path, res)
            for ob, m in saved:
                ob.material_slots[0].material = m
            bpy.context.scene.render.film_transparent = False
            if key == "kesit":
                annotate_elevation(path, (ecx, ecz, escale), D)
            if key == "ust":
                annotate_top(path, (cx_top, cy_top, top_scale), D)
        bpy.context.view_layer.material_override = None
        bpy.data.collections["Cevre"].hide_render = False

    if not args.no_export:
        export(out)


def export(out):
    sc = bpy.context.scene
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "proje_kutle.blend"), compress=True)
    # dışa aktarımda boolean'ları uygula, yardımcı kesicileri gizle
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in list(sc.objects):
        if ob.type == "MESH" and ob.modifiers:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            ob.modifiers.clear()
            ob.data = me
    for ob in list(bpy.data.collections["Yardimci"].objects):
        bpy.data.objects.remove(ob)
    for ob in list(sc.objects):
        ob.select_set(ob.type == "MESH")
    import addon_utils
    addon_utils.enable("io_scene_gltf2", default_set=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "proje_kutle.glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True)
    bpy.ops.wm.obj_export(filepath=os.path.join(out, "proje_kutle.obj"), export_selected_objects=True,
                          apply_modifiers=True, export_materials=True, forward_axis="NEGATIVE_Z", up_axis="Y")
    try:  # SketchUp için Collada (.dae)
        import trimesh
        trimesh.load(os.path.join(out, "proje_kutle.glb")).export(os.path.join(out, "proje_kutle.dae"))
    except Exception as e:
        print("DAE dışa aktarılamadı:", e)
    print("Dışa aktarıldı:", out, flush=True)


if __name__ == "__main__":
    main()
