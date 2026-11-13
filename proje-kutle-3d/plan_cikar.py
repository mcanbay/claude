"""
AutoCAD'den basılmış PDF kat planlarından 3B kütle için geometri çıkarır.

Girdi:
  --zemin  Zemin kat + vaziyet planı PDF'i (parsel sınırı, dükkanlar, teraslar, otopark)
  --normal Normal kat planı PDF'i (daireler, balkonlar, pencereler)

Çıktı: metre cinsinden, zemin kat binasının ortası (0,0) olan bir JSON.
  x: plan sağa (Odunluk Caddesi yönü), y: plan yukarı (Otel bölgesi yönü)

Yöntem:
  * Kalın kırmızı duvar katmanındaki çizgiler poligonlara dönüştürülür (shapely polygonize).
  * Ölçek, AutoCAD'in yazdığı oda alanlarıyla (ör. "Alan:10.67m²") poligon alanları
    karşılaştırılarak bulunur. Bu çizimlerde 1 pt = ~3.30 cm (yaklaşık 1/107 baskı).
  * İki plan aynı ölçekte; sayfadaki kaymaları asansör kuyularının merkezleri
    üst üste getirilerek giderilir.
  * Pencereler (camgöbeği katman) ve kapı katmanında dış cepheye denk gelen açıklıklar
    cephe açıklığı olarak alınır.
  * Otopark yerleri, otopark katmanı rasterize edilip kapalı hücreler bulunarak çıkarılır.
"""

import argparse
import json
import math
import re
from collections import defaultdict

import cv2
import numpy as np
import pymupdf
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import polygonize, unary_union

WALL = ((0.87, 0.22, 0.0), 1.08)
PARK_COLOR = (0.72, 0.45, 0.36)
WINDOW_COLOR = (0.0, 0.75, 1.0)
DOOR_KEY = ((0.62, 0.5, 1.0), 0.6)


# ------------------------------------------------------------------ PDF okuma

def read_pdf(path):
    page = pymupdf.open(path)[0]
    M = page.rotation_matrix  # sayfayı ekranda görüldüğü yöne çevir
    layers = defaultdict(list)  # (renk, kalınlık) -> [her path için segment listesi]
    quads = defaultdict(list)   # renk -> [4 köşe]
    for d in page.get_drawings():
        color = tuple(round(c, 2) for c in (d.get("color") or ()))
        width = round(d.get("width") or 0, 2)
        segs = []
        for it in d["items"]:
            if it[0] == "l":
                segs.append((it[1] * M, it[2] * M))
            elif it[0] == "c":
                segs.append((it[1] * M, it[4] * M))
            elif it[0] == "qu":
                q = it[1]
                P = [p * M for p in (q.ul, q.ur, q.lr, q.ll)]
                segs += [(P[i], P[(i + 1) % 4]) for i in range(4)]
                quads[color].append([(p.x, p.y) for p in P])
            elif it[0] == "re":
                r = it[1]
                P = [pymupdf.Point(r.x0, r.y0) * M, pymupdf.Point(r.x1, r.y0) * M,
                     pymupdf.Point(r.x1, r.y1) * M, pymupdf.Point(r.x0, r.y1) * M]
                segs += [(P[i], P[(i + 1) % 4]) for i in range(4)]
        layers[(color, width)].append([((a.x, a.y), (b.x, b.y)) for a, b in segs])
    words = []
    for w in page.get_text("words"):
        p = pymupdf.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2) * M
        words.append((p.x, p.y, w[4]))
    return layers, words, quads


def wall_polygons(layers, words):
    segs = [s for path in layers[WALL] for s in path]
    polys = list(polygonize(unary_union([LineString(s) for s in segs if s[0] != s[1]])))
    out = []
    for g in polys:
        inside = sorted([(y, x, t) for (x, y, t) in words if g.contains(Point(x, y))])
        out.append((g, " ".join(t for _, _, t in inside)))
    return out


def scale_from_room_areas(polys):
    """Etiketli oda alanlarından metre/pt ölçeği."""
    ratios = []
    for g, lab in polys:
        m = re.findall(r"Alan:([\d.]+)m", lab)
        if len(m) == 1 and float(m[0]) > 3 and g.area > 1000:
            ratios.append(math.sqrt(float(m[0]) / g.area))
    ratios = np.array(ratios)
    med = np.median(ratios)
    ratios = ratios[np.abs(ratios - med) / med < 0.02]
    return float(np.mean(ratios)), len(ratios)


def clusters(paths, pad=1.5):
    """Path'lerin sınır kutularını birleştirip kümeler (pencere/kapı sembolleri)."""
    boxes = []
    for segs in paths:
        if not segs:
            continue
        xs = [p[0] for s in segs for p in s]
        ys = [p[1] for s in segs for p in s]
        boxes.append(box(min(xs), min(ys), max(xs) + 0.01, max(ys) + 0.01))
    u = unary_union([b.buffer(pad, join_style=2) for b in boxes])
    geoms = list(u.geoms) if hasattr(u, "geoms") else [u]
    return [g.buffer(-pad, join_style=2).envelope for g in geoms if not g.is_empty]


def parking_stalls(quads, k):
    """Otopark katmanındaki ~2.5x5 m dörtgenler (her biri bir otopark yeri)."""
    out = []
    for q in quads.get(PARK_COLOR, []):
        P = np.array(q)
        e1, e2 = P[1] - P[0], P[2] - P[1]
        a, b = np.linalg.norm(e1) * k, np.linalg.norm(e2) * k
        if 4.2 < max(a, b) < 5.8 and 2.0 < min(a, b) < 3.0:
            ax = e1 if a >= b else e2
            out.append({"c": tuple(P.mean(0)), "len": max(a, b), "wid": min(a, b),
                        "ang": math.atan2(ax[1], ax[0])})
    return out


def fit_scale_shift(src_pts, dst_pts):
    """dst ≈ s * src + t (dönmesiz benzerlik), en küçük kareler."""
    A, B = np.asarray(src_pts, float), np.asarray(dst_pts, float)
    ca, cb = A.mean(0), B.mean(0)
    s = float(((A - ca) * (B - cb)).sum() / ((A - ca) ** 2).sum())
    return s, cb - s * ca


# ---------------------------------------------------------------- yardımcılar

def clean(g, eps):
    return g.buffer(eps, join_style=2).buffer(-eps, join_style=2).simplify(eps * 0.5)


def as_list(g):
    if g.is_empty:
        return []
    if isinstance(g, (MultiPolygon,)) or hasattr(g, "geoms"):
        return [p for p in g.geoms if isinstance(p, Polygon) and not p.is_empty]
    return [g] if isinstance(g, Polygon) else []


# ------------------------------------------------------------------- ana akış

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zemin", required=True)
    ap.add_argument("--normal", required=True)
    ap.add_argument("--out", default="plan_geometri.json")
    ap.add_argument("--debug", default=None, help="Kontrol için plan görseli (PNG)")
    args = ap.parse_args()

    Lz, Wz, Qz = read_pdf(args.zemin)
    Ln, Wn, Qn = read_pdf(args.normal)
    Pz = wall_polygons(Lz, Wz)
    Pn = wall_polygons(Ln, Wn)

    # Ana koordinat sistemi: normal kat planının sayfası. Ölçek oda etiketlerinden.
    k, nr = scale_from_room_areas(Pn)
    print(f"Ölçek (normal kat): 1 pt = {k * 100:.3f} cm ({nr} oda etiketinden), yaklaşık 1/{k / (0.0254 / 72):.1f}")

    # --- zemin kat planı -> normal kat planı (ölçek + kaydırma)
    # Kaba hizalama asansör kuyularıyla, ince hizalama iki planda da çizili
    # 46 otopark yerinin merkezleriyle yapılır.
    def lifts(P):
        c = [g.centroid for g, lab in P if "ASANS" in lab and g.area < 6000]
        return np.array([[p.x, p.y] for p in sorted(c, key=lambda p: p.y)])
    s, t = 1.0, (lifts(Pn) - lifts(Pz)).mean(0)
    sz, sn = parking_stalls(Qz, k), parking_stalls(Qn, k)
    for _ in range(3):
        pairs = []
        for a in sz:
            pa = s * np.array(a["c"]) + t
            b = min(sn, key=lambda b: math.dist(pa, b["c"]))
            if math.dist(pa, b["c"]) * k < 1.5:
                pairs.append((a["c"], b["c"]))
        s, t = fit_scale_shift([p[0] for p in pairs], [p[1] for p in pairs])
    res = max(math.dist(s * np.array(a) + t, b) for a, b in pairs) * k
    lift_err = np.abs(s * lifts(Pz) + t - lifts(Pn)).max() * k
    print(f"Zemin kat planı ölçek düzeltmesi: x{s:.4f}, {len(pairs)} ortak otopark yeri "
          f"(en büyük sapma {res:.2f} m, asansör sapması {lift_err:.2f} m)")

    from shapely.affinity import affine_transform

    def Z(g):  # zemin kat planı geometrisini ana sisteme taşı
        return affine_transform(g, [s, 0, 0, s, t[0], t[1]])

    Pz = [(Z(g), lab) for g, lab in Pz]
    Wz = [(s * x + t[0], s * y + t[1], w) for x, y, w in Wz]
    for st in sz:
        st["c"] = tuple(s * np.array(st["c"]) + t)
        st["len"] *= s
        st["wid"] *= s

    big = 50 / k  # parsel boyutundaki poligonlar
    eps = 0.04 / k

    # --- parsel (zemin/vaziyet planından)
    parcel_poly = max((g for g, _ in Pz), key=lambda g: g.area)
    parcel = Polygon(parcel_poly.exterior).simplify(0.3 / k)

    def is_site(g):
        b = g.bounds
        return (b[2] - b[0]) > big or (b[3] - b[1]) > big

    # --- zemin kat
    gpolys = [(g, lab) for g, lab in Pz if not is_site(g)]
    ground_fp = clean(unary_union([g for g, _ in gpolys]), eps)
    terraces = [g for g, lab in gpolys if "TERAS" in lab]
    ground_body_all = as_list(clean(ground_fp.difference(unary_union([t_.buffer(0.01) for t_ in terraces])), eps * 0.5))
    ground_body_all.sort(key=lambda g: -g.area)
    ground_body, ground_fins = ground_body_all[0], [g for g in ground_body_all[1:] if g.area * k * k > 0.2]
    terrace_zone = clean(unary_union([t_.buffer(0.2 / k, join_style=2) for t_ in terraces]).intersection(ground_fp), eps)

    # --- normal kat
    npolys = [(g, lab) for g, lab in Pn if not is_site(g)]
    roof_terrace = [g for g, lab in npolys if "GEZİLEMEYEN" in lab]
    tower_polys = [(g, lab) for g, lab in npolys if "GEZİLEMEYEN" not in lab]
    tower_fp = clean(unary_union([g for g, _ in tower_polys]), eps)
    tower_fp = max(as_list(tower_fp), key=lambda g: g.area)
    balconies = [clean(g, eps) for g, lab in tower_polys if "Balkon" in lab]
    stair = [g for g, lab in tower_polys if "RIHT" in lab and len(g.interiors) == 0]
    lift_n = [g for g, lab in tower_polys if "ASANS" in lab or "AFTLAR" in lab]
    slab = tower_fp
    enclosed = clean(slab.difference(unary_union([b.buffer(0.01) for b in balconies])), eps)
    enclosed = max(as_list(enclosed), key=lambda g: g.area)
    # İki kanat arasındaki, batı cephesine açık boşluk (zemin katta bina girişi)
    hull = tower_fp.envelope
    notch = [g for g in as_list(hull.difference(tower_fp.buffer(0.01)))
             if g.area * k * k > 8 and g.bounds[0] <= tower_fp.bounds[0] + 0.5 / k]
    gap = max(notch, key=lambda g: g.area) if notch else None
    core = unary_union(stair + lift_n).envelope.buffer(0.25 / k, join_style=2)

    # --- cephe açıklıkları (normal kat)
    ext = enclosed.exterior
    bal_u = unary_union(balconies)
    openings = []
    cand = [("window", c) for c in clusters(Ln[(WINDOW_COLOR, 0.72)])]
    cand += [("door", c) for c in clusters(Ln[DOOR_KEY])]
    for kind, c in cand:
        b = c.bounds
        w, h = b[2] - b[0], b[3] - b[1]
        span = max(w, h) * k
        if span < 0.6 or span > 4.0 or min(w, h) * k > 0.6:
            continue
        if ext.distance(c.centroid) * k > 0.35:
            continue
        horiz = w > h  # açıklık yatay bir duvar üzerinde
        cx, cy = c.centroid.x, c.centroid.y
        p = ext.interpolate(ext.project(Point(cx, cy)))  # duvar çizgisine oturt
        if horiz:
            a, bb = (b[0], p.y), (b[2], p.y)
        else:
            a, bb = (p.x, b[1]), (p.x, b[3])
        to_balcony = bal_u.distance(Point(cx, cy)) * k < 0.4
        openings.append({"a": a, "b": bb, "type": "door" if to_balcony else "window"})
    uniq = []
    for o in openings:
        m = ((o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2)
        if all(math.dist(m, ((u["a"][0] + u["b"][0]) / 2, (u["a"][1] + u["b"][1]) / 2)) * k > 0.5 for u in uniq):
            uniq.append(o)
    openings = uniq

    # --- otopark: normal kat planındakiler (bina önündeki açılı yerler dahil) + zemin plandaki farklılar
    stalls = list(sn)
    for st in sz:
        if all(math.dist(st["c"], u["c"]) * k > 1.5 for u in stalls):
            stalls.append(st)
    stalls = [st for st in stalls if not ground_fp.buffer(0.5 / k).contains(Point(st["c"]))]

    # --- yol (Odunluk Caddesi): parselin yazıya en yakın kenarı
    street_word = [(x, y) for x, y, w in Wz if "ODUNLUK" in w][0]
    ring = list(parcel.exterior.coords)
    edges = [(ring[i], ring[i + 1]) for i in range(len(ring) - 1)]
    se = min(edges, key=lambda e: LineString(e).distance(Point(street_word)) - LineString(e).length * 1e-3)

    # --- dünya koordinatı: x sağa, y yukarı, metre; orijin zemin kat ortası
    gb = ground_fp.bounds
    ox, oy = (gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2

    def W(pt):
        return [round((pt[0] - ox) * k, 3), round(-(pt[1] - oy) * k, 3)]

    def ring_w(r):
        pts = [W(p) for p in list(r.coords)[:-1]]
        # saat yönünün tersine (y yukarı)
        a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        return pts if a > 0 else pts[::-1]

    def poly_w(g):
        return {"outer": ring_w(g.exterior), "holes": [ring_w(h) for h in g.interiors]}

    def polys_w(g):
        return [poly_w(p) for p in as_list(g)]

    labels_w = []
    for g, lab in gpolys:
        for key in ("DÜKKAN", "TERAS"):
            if key in lab:
                m = re.findall(r"Alan:([\d.]+)m", lab)
                labels_w.append({"text": key.title(), "area": m[0] if m else "", "at": W((g.centroid.x, g.centroid.y))})

    data = {
        "olcek_m_per_pt": k,
        "parsel": ring_w(parcel.exterior),
        "zemin": {
            "ayak_izi": polys_w(ground_fp),
            "govde": poly_w(ground_body),
            "teras_bolmeleri": [poly_w(f) for f in ground_fins],
            "teraslar": [poly_w(t) for t in terraces],
            "teras_alani": polys_w(terrace_zone),
            "etiketler": labels_w,
        },
        "normal": {
            "ayak_izi": polys_w(tower_fp),
            "doseme": polys_w(slab),
            "kapali": poly_w(enclosed),
            "balkonlar": [poly_w(b) for b in balconies],
            "giris_boslugu": poly_w(gap) if gap is not None else None,
            "cekirdek": poly_w(core),
            "acikliklar": [{"a": W(o["a"]), "b": W(o["b"]), "tip": o["type"]} for o in openings],
            "gezilemeyen_teras": polys_w(unary_union(roof_terrace)) if roof_terrace else [],
        },
        "otopark": [{"c": W(s["c"]), "uzunluk": round(s["len"], 2), "genislik": round(s["wid"], 2),
                     "aci": round(-s["ang"], 4)} for s in stalls],
        "cadde": {"a": W(se[0]), "b": W(se[1]), "ad": "Odunluk Caddesi"},
    }

    def area(g):
        return g.area * k * k
    print(f"Parsel alanı: {area(parcel):.0f} m²")
    print(f"Zemin kat oturumu: {area(ground_fp):.0f} m² (kapalı gövde {area(ground_body):.0f} m², {len(terraces)} teras)")
    print(f"Normal kat: döşeme {area(slab):.0f} m², kapalı {area(enclosed):.0f} m², {len(balconies)} balkon, "
          f"giriş boşluğu {area(gap) if gap is not None else 0:.1f} m², {len(openings)} cephe açıklığı")
    print(f"Otopark yeri: {len(stalls)}")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Yazıldı:", args.out)

    if args.debug:
        draw_debug(data, args.debug)


def draw_debug(d, path):
    from PIL import Image, ImageDraw
    pts = np.array(d["parsel"])
    x0, y0 = pts.min(0) - 25
    x1, y1 = pts.max(0) + 25
    S = 14
    im = Image.new("RGB", (int((x1 - x0) * S), int((y1 - y0) * S)), "white")
    g = ImageDraw.Draw(im)

    def T(p):
        return ((p[0] - x0) * S, (y1 - p[1]) * S)

    def poly(pp, **kw):
        g.polygon([T(p) for p in pp["outer"]], **kw)
        for h in pp["holes"]:
            g.polygon([T(p) for p in h], fill="white", outline=kw.get("outline"))
    g.polygon([T(p) for p in d["parsel"]], outline=(200, 0, 0), width=3)
    for p in d["zemin"]["ayak_izi"]:
        poly(p, fill=(230, 230, 230), outline=(0, 0, 0))
    poly(d["zemin"]["govde"], fill=(120, 120, 130))
    for p in d["zemin"]["teras_bolmeleri"]:
        poly(p, fill=(60, 60, 60))
    for p in d["normal"]["doseme"]:
        poly(p, fill=(250, 220, 160), outline=(150, 100, 0))
    poly(d["normal"]["kapali"], fill=(250, 250, 250), outline=(0, 0, 0))
    for b in d["normal"]["balkonlar"]:
        poly(b, fill=(160, 210, 255))
    if d["normal"]["giris_boslugu"]:
        poly(d["normal"]["giris_boslugu"], fill=(255, 160, 160))
    poly(d["normal"]["cekirdek"], outline=(0, 150, 0), width=3)
    for o in d["normal"]["acikliklar"]:
        g.line([T(o["a"]), T(o["b"])], fill=(0, 90, 255) if o["tip"] == "window" else (255, 0, 200), width=6)
    for s in d["otopark"]:
        c, L, Wd, a = s["c"], s["uzunluk"], s["genislik"], s["aci"]
        u = np.array([math.cos(a), math.sin(a)])
        v = np.array([-u[1], u[0]])
        cs = [np.array(c) + u * L / 2 * i + v * Wd / 2 * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        g.polygon([T(p) for p in cs], outline=(0, 120, 0))
    g.line([T(d["cadde"]["a"]), T(d["cadde"]["b"])], fill=(0, 0, 0), width=8)
    im.save(path)


if __name__ == "__main__":
    main()
