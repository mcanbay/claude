# -*- coding: utf-8 -*-
"""
Varyant B vaziyet planından 3B kütle modeli üretir (GLB).

Villalar Z+1, kırma yerine sıra boyunca uzanan beşik çatı, 1. katta arka balkon,
villa önünde otopark ve araç, arka bahçelerde çit ve ağaç. Temsili kütle modelidir;
cephe ve pencere düzeni mimari projeyle değişecektir.

Çalıştırma: python model3d.py [A|B]   (varsayılan B)
Çıktı:      model_169-1-2_B.glb
"""
import math
import random
import sys

VARYANT = sys.argv[1] if len(sys.argv) > 1 else "B"
sys.argv = ["vaziyet.py", VARYANT]
import vaziyet as V  # noqa: E402  (plan geometrisi buradan gelir)
import kat_plani as KP  # noqa: E402  (cephe açıklıkları buradan gelir)

import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from shapely.geometry import Polygon, LineString, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

# ------------------------------------------------------------ ölçüler (m)
SUBASMAN = 0.45      # zemin kat döşeme kotu (bahçeden)
KAT = 3.15           # kat yüksekliği
SACAK = SUBASMAN + 2 * KAT          # saçak kotu
EGIM = 0.30          # çatı eğimi (%30)
SACAK_TASMA = 0.50
CATI_KAL = 0.18
DUVAR_KAL = 0.25     # bahçe duvarı
CIT_H = 1.0

# ------------------------------------------------------------ malzemeler
MAT = {
    "duvar":     ((0.93, 0.91, 0.86), 0.9, 0.0),
    "duvar2":    ((0.80, 0.74, 0.66), 0.9, 0.0),   # yangın duvarı / bant
    "subasman":  ((0.55, 0.53, 0.50), 0.9, 0.0),
    "cati":      ((0.52, 0.22, 0.14), 0.8, 0.0),
    "cam":       ((0.16, 0.22, 0.27), 0.15, 0.3),
    "korkuluk":  ((0.70, 0.82, 0.88), 0.1, 0.0),
    "dograma":   ((0.25, 0.25, 0.26), 0.6, 0.2),
    "asfalt":    ((0.24, 0.24, 0.25), 0.95, 0.0),
    "cizgi":     ((0.95, 0.95, 0.92), 0.8, 0.0),
    "parke":     ((0.72, 0.70, 0.66), 0.9, 0.0),
    "park":      ((0.55, 0.54, 0.52), 0.9, 0.0),
    "yuruyus":   ((0.85, 0.82, 0.76), 0.9, 0.0),
    "teras":     ((0.62, 0.50, 0.38), 0.85, 0.0),
    "cim":       ((0.42, 0.62, 0.30), 1.0, 0.0),
    "ortak":     ((0.36, 0.56, 0.28), 1.0, 0.0),
    "zemin":     ((0.78, 0.75, 0.66), 1.0, 0.0),
    "bahce_duv": ((0.80, 0.78, 0.73), 0.9, 0.0),
    "perde":     ((0.84, 0.79, 0.70), 0.9, 0.0),   # mahremiyet duvarları
    "harpusta":  ((0.62, 0.60, 0.56), 0.8, 0.0),
    "cit":       ((0.24, 0.42, 0.20), 1.0, 0.0),
    "govde":     ((0.40, 0.29, 0.20), 1.0, 0.0),
    "yaprak":    ((0.27, 0.48, 0.22), 1.0, 0.0),
    "yaprak2":   ((0.36, 0.54, 0.25), 1.0, 0.0),
    "lastik":    ((0.08, 0.08, 0.08), 0.9, 0.0),
}
ARAC_RENK = [(0.92, 0.92, 0.92), (0.55, 0.57, 0.60), (0.10, 0.11, 0.12),
             (0.14, 0.22, 0.38), (0.62, 0.12, 0.12), (0.80, 0.80, 0.78)]

parts = {}   # (grup, malzeme) -> [trimesh]


def add(group, mat, mesh):
    parts.setdefault((group, mat), []).append(mesh)


# ------------------------------------------------------------ geometri yardımcıları
# Model (u, v, h) yerel plan çerçevesinde kurulur; en sonda glTF'nin Y-yukarı eksenine çevrilir.
def slab(poly, h0, h1):
    """yatay poligonu h0..h1 arasında katı yap"""
    out = []
    for p in getattr(poly, "geoms", [poly]):
        if p.geom_type != "Polygon" or p.area < 1e-4:
            continue
        m = trimesh.creation.extrude_polygon(p, h1 - h0)
        m.apply_translation((0, 0, h0))
        out.append(m)
    return trimesh.util.concatenate(out) if out else None


def bx(u0, v0, h0, u1, v1, h1):
    return slab(box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1)), h0, h1)


def prism_u(profile_vh, u0, u1):
    """(v, h) düzlemindeki profili u ekseni boyunca u0..u1 arası uzat"""
    m = trimesh.creation.extrude_polygon(Polygon(profile_vh), u1 - u0)
    # extrude: (a=v, b=h, c=u)  ->  (u, v, h)
    T = np.array([[0, 0, 1, u0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
    m.apply_transform(T)
    if m.volume < 0:
        m.invert()
    return m


def wall_ring(poly, thick, h):
    ring = poly.difference(poly.buffer(-thick, join_style=2))
    return ring


# ------------------------------------------------------------ zemin ve peyzaj
P = V.PARSEL
minu, minv, maxu, maxv = P.bounds
add("zemin", "zemin", slab(box(minu - 60, minv - 45, maxu + 60, maxv + 45).difference(P), -0.10, -0.02))
add("peyzaj", "cim", slab(P, -0.10, 0.0))
add("peyzaj", "ortak", slab(V.ORTAK, 0.0, 0.02))
add("yol", "asfalt", slab(V.YOL_POLY, 0.0, 0.05))
ym = (V.yol[0] + V.yol[1]) / 2
u = V.YOL_POLY.bounds[0] + 1.0
while u + 3 < V.YOL_POLY.bounds[2] - 1:
    seg = box(u, ym - 0.06, u + 3, ym + 0.06).intersection(V.YOL_POLY)
    if not seg.is_empty:
        add("yol", "cizgi", slab(seg, 0.05, 0.06))
    u += 6

# bahçe duvarı (giriş ağzı açık) ve kapı babaları
duvar = wall_ring(P, DUVAR_KAL, 1.2)
giris = box(V.YOL_POLY.bounds[2] - 8, V.yol[0], maxu + 5, V.yol[1])
duvar = duvar.difference(giris)
add("peyzaj", "bahce_duv", slab(duvar, 0.0, 0.6))
# duvar üstü hafif çit görünümü
add("peyzaj", "cit", slab(duvar.buffer(-0.05), 0.6, 1.4))
for vv in (V.yol[0] - 0.45, V.yol[1] + 0.45):     # kapı babaları
    uu = P.intersection(LineString([(-1, vv), (500, vv)])).bounds[2]
    add("peyzaj", "bahce_duv", bx(uu - 0.9, vv - 0.45, 0, uu - 0.1, vv + 0.45, 2.2))

rng = random.Random(1692)

# ------------------------------------------------------------ villalar
for row in ("A", "B"):
    vs = [v for v in V.villas if v["sira"] == row]
    for v in vs:
        u0, v0, u1, v1 = v["ev"].bounds
        on_v = v0 if row == "A" else v1          # yola bakan cephe
        arka_v = v1 if row == "A" else v0
        dn = -1 if row == "A" else 1             # ön cephenin dış normal yönü (v)
        W = u1 - u0
        # gövde
        add("villa", "subasman", bx(u0, v0, 0, u1, v1, SUBASMAN))
        add("villa", "duvar", bx(u0, v0, SUBASMAN, u1, v1, SACAK))
        # kat bandı
        add("villa", "duvar2", bx(u0, on_v, SUBASMAN + KAT - 0.05, u1, on_v + dn * 0.12, SUBASMAN + KAT + 0.25))
        add("villa", "duvar2", bx(u0, arka_v, SUBASMAN + KAT - 0.05, u1, arka_v - dn * 0.12, SUBASMAN + KAT + 0.25))
        # çatı arası üçgen (beşik çatı, mahya sıra boyunca)
        vm = (v0 + v1) / 2
        rise = (v1 - v0) / 2 * EGIM
        add("villa", "duvar", prism_u([(v0, SACAK), (v1, SACAK), (vm, SACAK + rise)], u0, u1))
        # çatı örtüsü, iki yüz
        for side in (-1, 1):
            e = v0 - SACAK_TASMA if side < 0 else v1 + SACAK_TASMA
            he = SACAK - SACAK_TASMA * EGIM
            hr = SACAK + rise
            prof = [(e, he), (vm, hr), (vm, hr + CATI_KAL), (e, he + CATI_KAL)]
            if side > 0:
                prof = prof[::-1]
            first, last = (v is vs[0]), (v is vs[-1])
            ua = u0 - (0.3 if first else 0)
            ub = u1 + (0.3 if last else 0)
            add("villa", "cati", prism_u(prof, ua, ub))
        # yangın duvarı (bitişik villalar arasında, çatıdan taşan)
        if v is not vs[0]:
            add("villa", "duvar2", prism_u([(v0 - 0.15, SACAK - 0.1), (v1 + 0.15, SACAK - 0.1),
                                            (v1 + 0.15, SACAK + 0.35), (vm, SACAK + rise + 0.45),
                                            (v0 - 0.15, SACAK + 0.35)], u0 - 0.12, u0 + 0.12))
            add("villa", "duvar2", bx(u0 - 0.12, on_v, SUBASMAN, u0 + 0.12, on_v + dn * 0.25, SACAK))
            add("villa", "duvar2", bx(u0 - 0.12, arka_v, SUBASMAN, u0 + 0.12, arka_v - dn * 0.25, SACAK))

        # ---- cephe açıklıkları: kat_plani.py'deki tanım (girişi sağda olan tip, plan aks x'i)
        # plan x'i -> u: A sırasında ön cephe v0'da (u artar), B sırasında v1'de (u azalır);
        # giriş yürüyüş yolunun tarafında olacak şekilde gerekirse aynalanır.
        def plan_u(px, _row=row, _u0=u0, _u1=u1):
            return _u0 + px if _row == "A" else _u1 - px
        wcx = v["yuruyus"].centroid.x
        kapi_px = (wcx - u0) if row == "A" else (u1 - wcx)
        ayna = kapi_px < W / 2

        def u_araligi(x0, x1):
            if ayna:
                x0, x1 = W - x1, W - x0
            a, b = plan_u(x0), plan_u(x1)
            return min(a, b), max(a, b)
        f = on_v + dn * 0.03
        for ac in KP.cephe_aciklari("on"):
            ua, ub = u_araligi(ac["x0"], ac["x1"])
            if ac["tur"] == "kapi":
                add("villa", "dograma", bx(ua, on_v, ac["z0"], ub, f + dn * 0.02, ac["z1"]))
                add("villa", "cam", bx(ua + 0.42, on_v, ac["z0"] + 0.55, ub - 0.42, f + dn * 0.03, ac["z1"] - 0.15))
            else:
                add("villa", "cam", bx(ua, on_v, ac["z0"], ub, f, ac["z1"]))
        # ön balkon (girişe saçak olur)
        fu0, fv0, fu1, fv1 = v["balkon_on"].bounds
        bh_on = SUBASMAN + KAT
        add("villa", "duvar", bx(fu0, fv0, bh_on - 0.2, fu1, fv1, bh_on))
        fo0, fo1 = (fv0, fv0 + 0.06) if row == "A" else (fv1 - 0.06, fv1)
        add("villa", "korkuluk", bx(fu0, fo0, bh_on, fu1, fo1, bh_on + 1.0))

        # ---- arka cephe: zeminde sürme cam, 1. katta balkon kapısı
        r = arka_v - dn * 0.03
        for ac in KP.cephe_aciklari("arka"):
            ua, ub = u_araligi(ac["x0"], ac["x1"])
            add("villa", "cam", bx(ua, arka_v, ac["z0"], ub, r, ac["z1"]))
        # arka balkon (1. kat döşemesi seviyesinde) ve cam korkuluk
        bu0, bv0, bu1, bv1 = v["balkon"].bounds
        bh = SUBASMAN + KAT
        add("villa", "duvar", bx(bu0, bv0, bh - 0.2, bu1, bv1, bh))
        ov0, ov1 = (bv1 - 0.06, bv1) if row == "A" else (bv0, bv0 + 0.06)
        add("villa", "korkuluk", bx(bu0, ov0, bh, bu1, ov1, bh + 1.0))   # yanlar mahremiyet duvarı
        # arka teras (zeminde, balkonun altında)
        t1 = arka_v - dn * 3.0
        add("peyzaj", "teras", bx(u0, arka_v, 0, u1, t1, 0.12))

        # ---- ön bahçe: otopark, yürüyüş yolu
        add("peyzaj", "parke", slab(v["otopark"], 0.0, 0.06))
        add("peyzaj", "park", slab(v["park"], 0.06, 0.08))
        add("peyzaj", "yuruyus", slab(v["yuruyus"], 0.06, 0.10))

        # ---- araç (park yerlerinin çoğunda)
        if rng.random() < 0.8:
            pu0, pv0, pu1, pv1 = v["park"].bounds
            cu = (pu0 + pu1) / 2
            cv = (pv0 + pv1) / 2 + dn * 0.2
            L, Wc = 4.3, 1.8
            col = rng.choice(ARAC_RENK)
            key = "arac_%d_%d_%d" % tuple(int(c * 100) for c in col)
            MAT.setdefault(key, (col, 0.35, 0.4))
            add("arac", key, bx(cu - Wc / 2, cv - L / 2, 0.30, cu + Wc / 2, cv + L / 2, 0.95))
            # kabin, arkaya doğru (burun eve dönük)
            c0 = cv - dn * 0.1
            add("arac", "cam", bx(cu - 0.78, c0 - 1.1, 0.95, cu + 0.78, c0 + 1.1, 1.45))
            for su in (-1, 1):
                for sv in (-1, 1):
                    wh = trimesh.creation.cylinder(radius=0.32, height=0.22, sections=12)
                    wh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 1, 0)))
                    wh.apply_translation((cu + su * 0.8, cv + sv * 1.35, 0.32))
                    add("arac", "lastik", wh)

        # ---- arka bahçe: ağaç
        g = v["bahce"]
        if g.area > 15:
            far = box(u0, -500, u1, 500).intersection(g).buffer(-1.4)
            if not far.is_empty:
                fu0, fv0, fu1, fv1 = far.bounds
                tu = (fu1 - 0.3) if v["no"] % 2 == 0 else (fu0 + 0.3)     # bahçenin dip köşesine, villa numarasına göre
                tv = (fv0 + 0.6) if row == "B" else (fv1 - 0.6)
                if far.contains(Polygon([(tu - .1, tv - .1), (tu + .1, tv - .1), (tu + .1, tv + .1)])):
                    hgt = rng.uniform(4.0, 6.0)
                    trunk = trimesh.creation.cylinder(radius=0.14, height=hgt * 0.45, sections=8)
                    trunk.apply_translation((tu, tv, hgt * 0.225))
                    add("agac", "govde", trunk)
                    crown = trimesh.creation.icosphere(subdivisions=1, radius=hgt * 0.28)
                    crown.apply_scale((1, 1, 1.15))
                    crown.apply_translation((tu, tv, hgt * 0.62))
                    add("agac", rng.choice(["yaprak", "yaprak2"]), crown)

# ------------------------------------------------------------ mahremiyet duvarları (vaziyet.py'deki MAH)
for m in V.MAH:
    if m["poly"].is_empty:
        continue
    if m["tip"] == "balkon":     # 1. kat: balkon döşemesinden saçağa kadar
        add("villa", "perde", slab(m["poly"], SUBASMAN + KAT - 0.2, SACAK))
    else:                        # zemin: bahçe, teras ve giriş duvarları + harpuşta
        add("peyzaj", "perde", slab(m["poly"], 0.0, m["h"]))
        add("peyzaj", "harpusta", slab(m["poly"].buffer(0.04, join_style=2), m["h"], m["h"] + 0.06))

# ortak alanlarda birkaç ağaç
for p in getattr(V.ORTAK, "geoms", [V.ORTAK]):
    q = p.buffer(-1.6)
    if q.is_empty or q.area < 3:
        continue
    q0, q1, q2, q3 = q.bounds
    n = max(1, int(q.area / 25))
    for _ in range(n * 6):
        if n <= 0:
            break
        tu, tv = rng.uniform(q0, q2), rng.uniform(q1, q3)
        if not q.contains(box(tu - .05, tv - .05, tu + .05, tv + .05)):
            continue
        n -= 1
        hgt = rng.uniform(4.5, 7.0)
        trunk = trimesh.creation.cylinder(radius=0.16, height=hgt * 0.45, sections=8)
        trunk.apply_translation((tu, tv, hgt * 0.225))
        add("agac", "govde", trunk)
        crown = trimesh.creation.icosphere(subdivisions=1, radius=hgt * 0.27)
        crown.apply_scale((1, 1, 1.2))
        crown.apply_translation((tu, tv, hgt * 0.62))
        add("agac", rng.choice(["yaprak", "yaprak2"]), crown)

# ------------------------------------------------------------ glTF sahnesi
cu, cv = P.centroid.x, P.centroid.y
# (u, v, h) -> glTF (x, y, z) = (u - cu, h, -(v - cv))  : sağ el, Y yukarı
TO_GLTF = np.array([[1, 0, 0, -cu], [0, 0, 1, 0], [0, -1, 0, cv], [0, 0, 0, 1]], float)

scene = trimesh.Scene()
for (group, mat), meshes in sorted(parts.items()):
    meshes = [m for m in meshes if m is not None]
    if not meshes:
        continue
    m = trimesh.util.concatenate(meshes)
    m.apply_transform(TO_GLTF)
    m.unmerge_vertices()          # köşeleri ayır: düz (keskin kenarlı) gölgelendirme için yüz normali
    col, rough, metal = MAT[mat]
    alpha = 0.45 if mat == "korkuluk" else 1.0
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=mat, baseColorFactor=[*col, alpha], roughnessFactor=rough, metallicFactor=metal,
        alphaMode="BLEND" if alpha < 1 else "OPAQUE", doubleSided=False))
    scene.add_geometry(m, node_name=f"{group}__{mat}", geom_name=f"{group}__{mat}")

out = f"model_169-1-2_{VARYANT}.glb"
with open(out, "wb") as fh:
    fh.write(trimesh.exchange.gltf.export_glb(scene, include_normals=True))
# kuzey yönü (glTF düzleminde) ve özet, görüntüleyici için
a = math.radians(V.EKSEN_ACI)
nu, nv = math.sin(a), math.cos(a)
print(f"{out}: {sum(len(g.faces) for g in scene.geometry.values())} üçgen")
print(f"kuzey (x,z) = ({nu:.4f}, {-nv:.4f})  saçak {SACAK:.2f} m  mahya {SACAK + (V.D / 2) * EGIM:.2f} m")

# ------------------------------------------------------------ görüntüleyici için meta veri
import json  # noqa: E402


def g(u_, v_):
    return [round(u_ - cu, 2), round(-(v_ - cv), 2)]


meta = dict(
    varyant=VARYANT,
    kuzey=[round(nu, 4), round(-nv, 4)],                     # (x, z)
    dogu=[round(math.cos(a), 4), round(math.sin(a), 4)],
    sacak=SACAK, mahya=round(SACAK + V.D / 2 * EGIM, 2),
    giris=g(V.YOL_POLY.bounds[2] + 4, ym),
    yol_sol=g(V.YOL_POLY.bounds[0] + 4, ym),
    parsel=[g(x_, y_) for x_, y_ in P.exterior.coords],
    villalar=[dict(no=v["no"], sira=v["sira"], p=g(*v["ev"].centroid.coords[0])) for v in V.villas],
    ozet=dict(W=V.W, D=V.D, n=len(V.villas), tapu=V.tapu_alan, brut=V.BRUT,
              taks=round(V.taban_top / V.tapu_alan, 2), kaks=round(V.brut_top / V.tapu_alan, 2)),
)
with open(f"model_169-1-2_{VARYANT}.json", "w", encoding="utf-8") as fh:
    json.dump(meta, fh, ensure_ascii=False)
