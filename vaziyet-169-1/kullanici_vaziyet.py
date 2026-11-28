# -*- coding: utf-8 -*-
"""
Kullanıcının vaziyet planı (girdi/vaziyet_kullanici.png) → ölçekli sayısallaştırma, 2B pafta, DXF ve 3B model.

Görseldeki parsel köşeleri tevhitli parselin yerel koordinatlarına benzerlik dönüşümüyle oturtulur
(ölçek ≈ 18,14 piksel/m, köşe hatası ≤ 0,5 m). Bina oturumları görüntüden çıkarılır:
  - 5 adet dörtlü blok (artı biçimli, 2 × 2 villa), üst yol ve iç yol cepheli
  - 13 sıra villa (5 + 8), iç yola cepheli, bahçeleri alt yola doğru
Yükseklikler bu projenin standardındadır: zemin + 1, kat 3,15 m, subasman 0,45 m, betonarme düz çatı + parapet.

Çıktılar: vaziyet_169-1-2_U.pdf/.png/.dxf, model_169-1-2_U.glb/.json (görüntüleyici: build_viewer.py U)
Çalıştırma: python kullanici_vaziyet.py
"""
import json
import math
import random
import sys

import cv2
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Polygon as MPoly, FancyArrow
from shapely import affinity
from shapely.geometry import Polygon, LineString, box, Point
from shapely.ops import unary_union

sys.argv = ["vaziyet.py", "B"]
import vaziyet as V          # noqa: E402  parsel, TM30 dönüşümü, KML verileri
import kat_plani as KP       # noqa: E402  kot standartları

GORSEL = "girdi/vaziyet_kullanici.png"
EMSAL, TAKS = 0.70, 0.35
SUB, KAT = KP.SUBASMAN, KP.KAT_H
CATI_BIT, PARAPET = KP.CATI_BITMIS, KP.PARAPET_UST

# ------------------------------------------------------------------ görüntü → yerel koordinat
IMG_PTS = [(557, 129), (2530, 129), (2605, 217), (2465, 1098), (2384, 1165), (345, 1129), (1031, 1129)]
LOC_PTS = [tuple(round(c, 2) for c in p) for p in
           [(10.89, 55.40), (119.89, 57.23), (123.99, 52.37), (116.61, 3.65), (111.95, 0.18), (0.0, 0.0), (37.47, 0.72)]]
# benzerlik dönüşümü (ölçek + dönme + öteleme), görüntünün y ekseni aşağı olduğu için yy = −y
_A, _B = [], []
for (x, y), (u, v) in zip(IMG_PTS, LOC_PTS):
    yy = -y
    _A += [[x, -yy, 1, 0], [yy, x, 0, 1]]
    _B += [u, v]
_a, _b, _tx, _ty = np.linalg.lstsq(np.array(_A, float), np.array(_B, float), rcond=None)[0]
OLCEK = 1 / math.hypot(_a, _b)


def P2L(x, y):
    """görüntü pikseli → yerel (u, v) metre"""
    yy = -y
    return (_a * x - _b * yy + _tx, _b * x + _a * yy + _ty)


HATA = max(math.dist(P2L(*p), q) for p, q in zip(IMG_PTS, LOC_PTS))


def poly_l(pts):
    return Polygon([P2L(x, y) for x, y in pts])


# ------------------------------------------------------------------ dış hat çıkarımı
IM = cv2.imread(GORSEL, cv2.IMREAD_GRAYSCALE)


def dis_hat(x0, y0, x1, y1):
    c = IM[y0:y1, x0:x1]
    d = cv2.morphologyEx((c < 170).astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    h, w = d.shape
    ff, mask = d.copy(), np.zeros((h + 2, w + 2), np.uint8)
    kenar = [(x, 1) for x in range(1, w - 1, 6)] + [(x, h - 2) for x in range(1, w - 1, 6)] + \
        [(1, y) for y in range(1, h - 1, 6)] + [(w - 2, y) for y in range(1, h - 1, 6)]
    for sx, sy in kenar:                  # dış bölgeyi pencerenin bütün kenarından doldur
        if ff[sy, sx] == 0:
            cv2.floodFill(ff, mask, (sx, sy), 128)
    b = cv2.morphologyEx((ff != 128).astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    cs, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    return (cv2.approxPolyDP(c, 2.5, True).reshape(-1, 2) + [x0, y0]).tolist()


def dik(pts):
    """yaklaşık dik açılı çokgeni tam dik yap (komşu köşelerin x / y değerlerini eşitle)"""
    pts = [list(p) for p in pts]
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if abs(a[0] - b[0]) < abs(a[1] - b[1]):
            m = (a[0] + b[0]) / 2
            a[0] = b[0] = m
        else:
            m = (a[1] + b[1]) / 2
            a[1] = b[1] = m
    return pts


# 5 dörtlü blok: merkez çizgileri görüntüde x ≈ 715, 1122, 1523, 1924, 2326; y orta çizgisi 418
DORTLU_X = [715, 1122, 1523, 1924, 2326]
ORTA_Y = 418
# sıra villalar: iç yol alt kenarı y=830; grup başlangıçları ve villa genişliği (piksel)
SIRA_GRUP = [(487, 5), (1321, 8)]
SIRA_W = (1161 - 487) / 5           # ≈ 134,8 px ≈ 7,43 m
SIRA_ON, SIRA_KIRIK, SIRA_ARKA, SIRA_L = 830, 965, 1032, 80     # ön, L kırığı, arka (y), L kolu genişliği (px)
IC_YOL = (720, 830)                 # iç yol üst ve alt kenarı (y, piksel)
UST_LOT_X = [715, 921, 1122, 1323, 1523, 1725, 1924, 2125, 2326]   # üst bölge parsel çizgileri (x)

villas = []   # dict: no, tip, poly (taban), lot, on (ön cephe orta noktası), blok
bloklar = []  # blok bileşik taban çokgenleri

no = 1
for i, cx in enumerate(DORTLU_X):
    pts = dik(dis_hat(cx - 175, 200, cx + 175, 640))
    blok = poly_l(pts)
    bloklar.append(blok)
    # villa bölme çizgileri (görüntüde dikey cx ve yatay ORTA_Y)
    yarim = {}
    for ad, (qx0, qy0, qx1, qy1) in {"ust_sol": (cx - 400, 0, cx, ORTA_Y), "ust_sag": (cx, 0, cx + 400, ORTA_Y),
                                     "alt_sol": (cx - 400, ORTA_Y, cx, 900), "alt_sag": (cx, ORTA_Y, cx + 400, 900)}.items():
        q = poly_l([(qx0, qy0), (qx1, qy0), (qx1, qy1), (qx0, qy1)])
        yarim[ad] = blok.intersection(q)
    for ad in ("ust_sol", "ust_sag", "alt_sol", "alt_sag"):
        villas.append(dict(no=None, tip="dortlu", poly=yarim[ad], blok=i, konum=ad,
                           cephe="ust_yol" if ad.startswith("ust") else "ic_yol"))
for g, (gx, n) in enumerate(SIRA_GRUP):
    pts_blok = []
    for k in range(n):
        x0 = gx + k * SIRA_W
        p = unary_union([poly_l([(x0, SIRA_ON), (x0 + SIRA_W, SIRA_ON), (x0 + SIRA_W, SIRA_KIRIK), (x0, SIRA_KIRIK)]),
                         poly_l([(x0, SIRA_KIRIK), (x0 + SIRA_L, SIRA_KIRIK), (x0 + SIRA_L, SIRA_ARKA), (x0, SIRA_ARKA)])])
        villas.append(dict(no=None, tip="sira", poly=p, blok=5 + g, konum=k, cephe="ic_yol"))
        pts_blok.append(p)
    bloklar.append(unary_union(pts_blok).buffer(0.02, join_style=2).buffer(-0.02, join_style=2))

# numaralandırma: üst yol cepheli dörtlü villalar V1–V10 (soldan sağa), iç yol cepheli dörtlüler V11–V20, sıra V21–V33
_ust = [v for v in villas if v["tip"] == "dortlu" and v["cephe"] == "ust_yol"]
_ic = [v for v in villas if v["tip"] == "dortlu" and v["cephe"] == "ic_yol"]
_sr = [v for v in villas if v["tip"] == "sira"]
for grp in (_ust, _ic, _sr):
    grp.sort(key=lambda v: v["poly"].centroid.x)
for i, v in enumerate(_ust + _ic + _sr):
    v["no"] = i + 1
villas.sort(key=lambda v: v["no"])

# ------------------------------------------------------------------ parseller (lotlar), iç yol, kamu yolları
PARSEL = V.PARSEL
IC_YOL_POLY = poly_l([(0, IC_YOL[0]), (3000, IC_YOL[0]), (3000, IC_YOL[1]), (0, IC_YOL[1])]).intersection(PARSEL)
_ust_bolge = PARSEL.intersection(poly_l([(0, 0), (3000, 0), (3000, IC_YOL[0]), (0, IC_YOL[0])]))
_alt_bolge = PARSEL.intersection(poly_l([(0, IC_YOL[1]), (3000, IC_YOL[1]), (3000, 1400), (0, 1400)]))
_xs = [0] + UST_LOT_X + [3000]
for v in _ust + _ic:
    c = v["poly"].centroid
    for xa, xb in zip(_xs[:-1], _xs[1:]):
        hucre = poly_l([(xa, 0), (xb, 0), (xb, ORTA_Y), (xa, ORTA_Y)]) if v["cephe"] == "ust_yol" else \
            poly_l([(xa, ORTA_Y), (xb, ORTA_Y), (xb, IC_YOL[0]), (xa, IC_YOL[0])])
        if hucre.contains(c):
            v["lot"] = hucre.intersection(_ust_bolge)
for g, (gx, n) in enumerate(SIRA_GRUP):
    for k in range(n):
        x0 = gx + k * SIRA_W
        hucre = poly_l([(x0, IC_YOL[1]), (x0 + SIRA_W, IC_YOL[1]), (x0 + SIRA_W, 1400), (x0, 1400)])
        vv = [v for v in _sr if v["blok"] == 5 + g and v["konum"] == k][0]
        vv["lot"] = hucre.intersection(_alt_bolge)
ORTAK = PARSEL.difference(unary_union([v["lot"] for v in villas] + [IC_YOL_POLY]))
# kamu yolları (parselin üst ve alt uzun kenarı boyunca, 12 m: 7 m taşıt + 2 × 2,5 m kaldırım varsayımı)
UST_YOL = poly_l([(-200, 129 - 12 * OLCEK), (3200, 129 - 12 * OLCEK), (3200, 129), (-200, 129)]).difference(PARSEL)
ALT_YOL = poly_l([(-200, 1129), (1031, 1129), (2384, 1165), (3200, 1187), (3200, 1187 + 12 * OLCEK),
                  (-200, 1129 + 12 * OLCEK)]).difference(PARSEL)

# ------------------------------------------------------------------ metraj
tapu = V.tapu_alan
taban = sum(v["poly"].area for v in villas)
insaat = 2 * taban                                   # zemin + 1, balkonsuz (çizimde balkon yok)
taban_d = np.mean([v["poly"].area for v in villas if v["tip"] == "dortlu"])
taban_s = np.mean([v["poly"].area for v in villas if v["tip"] == "sira"])
bahce = [v["lot"].area - v["poly"].area for v in villas]
OZET = dict(n=len(villas), taban=taban, insaat=insaat, taks=taban / tapu, emsal=insaat / tapu,
            taban_dortlu=taban_d, taban_sira=taban_s, bahce_min=min(bahce), bahce_max=max(bahce),
            lot_d=np.mean([v["lot"].area for v in villas if v["tip"] == "dortlu"]),
            lot_s=np.mean([v["lot"].area for v in villas if v["tip"] == "sira"]),
            ic_yol=IC_YOL_POLY.area, ortak=ORTAK.area)
_d0 = bloklar[0].bounds
_s0 = [v for v in _sr if v["konum"] == 0][0]["poly"].bounds
_dp = dis_hat(DORTLU_X[0] - 175, 200, DORTLU_X[0] + 175, 640)           # piksel ölçüsü (dönmeden bağımsız)
_dgen = (max(p[0] for p in _dp) - min(p[0] for p in _dp)) / OLCEK
_dder = (max(p[1] for p in _dp) - min(p[1] for p in _dp)) / OLCEK
OLCU = dict(dortlu_gen=_dgen, dortlu_der=_dder,
            sira_gen=SIRA_W / OLCEK, sira_der=(SIRA_ARKA - SIRA_ON) / OLCEK,
            sira_on_der=(SIRA_KIRIK - SIRA_ON) / OLCEK, sira_l=SIRA_L / OLCEK,
            dortlu_ara=(DORTLU_X[1] - DORTLU_X[0]) / OLCEK - _dgen,
            ic_yol=(IC_YOL[1] - IC_YOL[0]) / OLCEK)


def tr(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ 2B pafta
def ciz(pdf, png):
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    pad = 8.0
    x0, y0, x1, y1 = PARSEL.bounds
    wm, hm = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad + 8
    MM = 2.5
    ax = fig.add_axes([20 / 420, 1 - 18 / 297 - hm * MM / 297, wm * MM / 420, hm * MM / 297])
    ax.set_xlim(x0 - pad, x1 + pad)
    ax.set_ylim(y0 - pad - 4, y1 + pad + 4)
    ax.set_aspect("equal")
    ax.axis("off")

    def P(g, **kw):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type == "Polygon" and not p.is_empty:
                ax.add_patch(MPoly(list(p.exterior.coords), closed=True, **kw))
    P(UST_YOL.intersection(box(x0 - pad, y0 - pad - 4, x1 + pad, y1 + pad + 4)), fc="#d6d3d1", ec="none")
    P(ALT_YOL.intersection(box(x0 - pad, y0 - pad - 4, x1 + pad, y1 + pad + 4)), fc="#d6d3d1", ec="none")
    P(ORTAK, fc="#bbf7d0", ec="none")
    for v in villas:
        P(v["lot"], fc="#dcfce7", ec="#4d7c0f", lw=0.5)
    P(IC_YOL_POLY, fc="#d6d3d1", ec="#78716c", lw=0.5)
    for b in bloklar:
        P(b, fc="#fde68a", ec="#b45309", lw=1.0)
    for v in villas:
        P(v["poly"], fc="none", ec="#b45309", lw=0.5)
        c = v["poly"].representative_point()
        ax.text(c.x, c.y, f"V{v['no']}", ha="center", va="center", fontsize=5.5, fontweight="bold", color="#111827")
    px, py = PARSEL.exterior.xy
    ax.plot(px, py, color="#1f2937", lw=1.6)
    ax.text((x0 + x1) / 2, y1 + 4.5, "Y O L", ha="center", va="center", fontsize=10, color="#44403c")
    ax.text((x0 + x1) / 2, y0 - 5.5, "Y O L", ha="center", va="center", fontsize=10, color="#44403c")
    yb = IC_YOL_POLY.centroid
    ax.text(yb.x, yb.y, f"İÇ YOL ({tr(OLCU['ic_yol'], 1)} m)", ha="center", va="center", fontsize=7, color="#44403c")
    # ölçüler: bir dörtlü ve bir sıra villa
    b0 = bloklar[0].bounds
    ax.annotate("", (b0[0], b0[1] - 1.2), (b0[2], b0[1] - 1.2), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text((b0[0] + b0[2]) / 2, b0[1] - 2.6, tr(OLCU["dortlu_gen"]), ha="center", fontsize=5.5)
    ax.annotate("", (b0[0] - 1.2, b0[1]), (b0[0] - 1.2, b0[3]), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text(b0[0] - 2.4, (b0[1] + b0[3]) / 2, tr(OLCU["dortlu_der"]), ha="center", va="center", fontsize=5.5,
            rotation=90)
    s0 = _sr[0]["poly"].bounds
    ax.annotate("", (s0[0], s0[1] - 1.2), (s0[2], s0[1] - 1.2), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text((s0[0] + s0[2]) / 2, s0[1] - 2.6, tr(OLCU["sira_gen"]), ha="center", fontsize=5.5)
    # kuzey oku
    a_ = math.radians(V.EKSEN_ACI)
    nx, ny = math.sin(a_), math.cos(a_)
    kx, ky = x1 + 2, y1 + 2
    ax.add_patch(FancyArrow(kx - nx * 4, ky - ny * 4, nx * 8, ny * 8, width=0.6, head_width=2.4, head_length=2.6,
                            color="#111827", length_includes_head=True))
    ax.text(kx + nx * 6.5, ky + ny * 6.5, "K", fontsize=10, fontweight="bold", ha="center", va="center")
    fig.text(20 / 420, 1 - 9 / 297, "VAZİYET PLANI: KULLANICI ÇALIŞMASI, ÖLÇEKLİ SAYISALLAŞTIRMA", fontsize=14,
             fontweight="bold", color="#111827")
    fig.text(20 / 420, 1 - 14.5 / 297, "Bursa / Nilüfer / İrfaniye Mah. · 169 Ada 1 + 2 Parseller · "
             f"5 dörtlü blok (20 villa) + 13 sıra villa = {len(villas)} villa · iki uzun kenarı kamu yoluna cepheli",
             fontsize=8.5, color="#374151")
    rows = [
        ("Parsel alanı (tapu)", f"{tr(tapu)} m²"),
        ("Villa sayısı", f"{len(villas)} (dörtlü 20 + sıra 13)"),
        ("Dörtlü blok", f"{tr(OLCU['dortlu_gen'])} × {tr(OLCU['dortlu_der'])} m, bloklar arası {tr(OLCU['dortlu_ara'])} m"),
        ("Dörtlü villa taban alanı", f"{tr(taban_d)} m² (Z+1: {tr(2 * taban_d)} m²)"),
        ("Sıra villa", f"{tr(OLCU['sira_gen'])} × {tr(OLCU['sira_der'])} m (L), taban {tr(taban_s)} m² (Z+1: {tr(2 * taban_s)} m²)"),
        ("Toplam taban alanı", f"{tr(taban, 0)} m² → TAKS {tr(taban / tapu, 3)} (sınır {tr(TAKS)}: {tr(TAKS * tapu, 0)} m²)"),
        ("Toplam inşaat (Z+1)", f"{tr(insaat, 0)} m² → emsal {tr(insaat / tapu, 3)} (sınır {tr(EMSAL)}: {tr(EMSAL * tapu, 0)} m²)"),
        ("Özel bahçe (lot − taban)", f"villa başı {tr(min(bahce), 0)}–{tr(max(bahce), 0)} m²"),
        ("Lot (ortalama)", f"dörtlü {tr(OZET['lot_d'], 0)} m², sıra {tr(OZET['lot_s'], 0)} m²"),
        ("İç yol", f"{tr(OLCU['ic_yol'], 1)} m genişlik, {tr(IC_YOL_POLY.area, 0)} m²"),
    ]
    ty = 1 - (18 + hm * MM + 6) / 297
    fig.text(20 / 420, ty, "ÖLÇÜ VE ALAN ÖZETİ", fontsize=9, fontweight="bold")
    for i, (k, v) in enumerate(rows):
        fig.text(20 / 420, ty - (5 + i * 4.3) / 297, k, fontsize=7.2, color="#374151")
        fig.text(75 / 420, ty - (5 + i * 4.3) / 297, v, fontsize=7.2, color="#111827")
    notlar = [
        "1. Görselden sayısallaştırılmıştır (ölçek ≈ %.2f px/m, köşe hatası ≤ %.1f m); ölçüler ±0,3 m" % (OLCEK, HATA),
        "    hassasiyetlidir. Kesin ölçü için DWG/DXF dosyası gerekir.",
        "2. Taban alanı villa dış hattından (balkonlar hariç), inşaat alanı zemin + 1 kabulüyle hesaplanmıştır.",
        "3. Otopark ve iç yolun kamu yoluna bağlantısı çizimde yok; ayrıca çözülmelidir.",
        "4. Yükseklikler proje standardı: subasman 0,45, kat 3,15 m, betonarme düz çatı, parapet +7,65.",
    ]
    for i, n in enumerate(notlar):
        fig.text(230 / 420, ty - (5 + i * 4.3) / 297, n, fontsize=6.8, color="#374151")
    fig.text(230 / 420, ty, "NOTLAR", fontsize=9, fontweight="bold")
    fig.text(1 - 20 / 420, 8 / 297, "Ölçek 1/400 · A3", fontsize=7, ha="right", color="#6b7280")
    fig.savefig(pdf)
    fig.savefig(png, dpi=200)
    plt.close(fig)


def dxf(path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    for n, c in {"PARSEL": 7, "LOT": 3, "VILLA": 30, "BLOK": 30, "IC_YOL": 8, "YAZI": 7}.items():
        doc.layers.add(n, color=c)

    def p(g, layer):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon" and not q.is_empty:
                msp.add_lwpolyline([V.to_world(*c) for c in q.exterior.coords[:-1]], close=True,
                                   dxfattribs={"layer": layer})
    p(PARSEL, "PARSEL")
    p(IC_YOL_POLY, "IC_YOL")
    for b in bloklar:
        p(b, "BLOK")
    for v in villas:
        p(v["poly"], "VILLA")
        p(v["lot"], "LOT")
        c = v["poly"].representative_point()
        msp.add_text(f"V{v['no']}", height=1.0, dxfattribs={"layer": "YAZI"}).set_placement(
            V.to_world(c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


# ------------------------------------------------------------------ 3B model
MAT = {
    "duvar": ((0.93, 0.91, 0.86), 0.9, 0.0), "duvar2": ((0.80, 0.74, 0.66), 0.9, 0.0),
    "subasman": ((0.55, 0.53, 0.50), 0.9, 0.0), "cam": ((0.16, 0.22, 0.27), 0.15, 0.3),
    "asfalt": ((0.24, 0.24, 0.25), 0.95, 0.0), "cizgi": ((0.95, 0.95, 0.92), 0.8, 0.0),
    "kaldirim": ((0.72, 0.70, 0.66), 0.9, 0.0), "cim": ((0.42, 0.62, 0.30), 1.0, 0.0),
    "ortak": ((0.36, 0.56, 0.28), 1.0, 0.0), "zemin": ((0.78, 0.75, 0.66), 1.0, 0.0),
    "bahce_duv": ((0.80, 0.78, 0.73), 0.9, 0.0), "cit": ((0.24, 0.42, 0.20), 1.0, 0.0),
    "govde": ((0.40, 0.29, 0.20), 1.0, 0.0), "yaprak": ((0.27, 0.48, 0.22), 1.0, 0.0),
    "yaprak2": ((0.36, 0.54, 0.25), 1.0, 0.0), "harpusta": ((0.62, 0.60, 0.56), 0.8, 0.0),
    "cakil": ((0.66, 0.65, 0.62), 1.0, 0.0), "teras": ((0.62, 0.50, 0.38), 0.85, 0.0),
    "dograma": ((0.25, 0.25, 0.26), 0.6, 0.2),
}
parts = {}


def add(g, m, mesh):
    if mesh is not None:
        parts.setdefault((g, m), []).append(mesh)


def slab(poly, h0, h1):
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


def kenarlar(poly):
    c = list(poly.exterior.coords)
    return list(zip(c[:-1], c[1:]))


def model(glb, meta_path):
    rng = random.Random(33)
    minu, minv, maxu, maxv = PARSEL.bounds
    add("zemin", "zemin", slab(box(minu - 60, minv - 45, maxu + 60, maxv + 45).difference(
        unary_union([PARSEL, UST_YOL, ALT_YOL])), -0.10, -0.02))
    for yol in (UST_YOL, ALT_YOL):
        y = yol.intersection(box(minu - 60, minv - 45, maxu + 60, maxv + 45))
        add("yol", "asfalt", slab(y, -0.05, 0.0))
    add("peyzaj", "cim", slab(PARSEL, -0.10, 0.0))
    add("peyzaj", "ortak", slab(ORTAK, 0.0, 0.02))
    add("yol", "asfalt", slab(IC_YOL_POLY, 0.0, 0.05))
    # çevre duvarı (yol cephelerinde alçak duvar + çit), lot sınırlarında çit
    ring = PARSEL.difference(PARSEL.buffer(-0.25, join_style=2))
    ring = ring.difference(IC_YOL_POLY.buffer(0.3))
    add("peyzaj", "bahce_duv", slab(ring, 0.0, 0.6))
    add("peyzaj", "cit", slab(ring.buffer(-0.05), 0.6, 1.3))
    ic = PARSEL.buffer(-0.25, join_style=2)
    cizgiler = unary_union([v["lot"].boundary for v in villas]).intersection(ic)
    cizgiler = cizgiler.difference(unary_union([v["poly"] for v in villas]).buffer(0.05))
    cizgiler = cizgiler.difference(IC_YOL_POLY.buffer(0.3))
    add("peyzaj", "cit", slab(cizgiler.buffer(0.12, cap_style=2), 0.0, 1.2))
    # binalar
    for b in bloklar:
        add("villa", "subasman", slab(b, 0.0, SUB))
        add("villa", "duvar", slab(b, SUB, CATI_BIT))
        add("villa", "duvar2", slab(b.buffer(0.08, join_style=2).difference(b), SUB + KAT - 0.05, SUB + KAT + 0.25))
        add("villa", "duvar2", slab(b.buffer(0.04, join_style=2).difference(b), KP.CATI_DOSEME, CATI_BIT))
        add("villa", "cakil", slab(b.buffer(-0.25, join_style=2), CATI_BIT, CATI_BIT + 0.03))
        par = b.difference(b.buffer(-0.25, join_style=2))
        add("villa", "duvar", slab(par, CATI_BIT, PARAPET - 0.05))
        add("villa", "harpusta", slab(par.buffer(0.04, join_style=2), PARAPET - 0.05, PARAPET))
        # pencereler: blok dış kenarlarında, her katta
        for (xa, ya), (xb, yb) in kenarlar(b.simplify(0.05)):
            L = math.dist((xa, ya), (xb, yb))
            if L < 2.2:
                continue
            ux, uy = (xb - xa) / L, (yb - ya) / L
            nx, ny = uy, -ux                       # dış normal (dış hat saat yönünün tersi)
            if b.contains(Point((xa + xb) / 2 + nx * 0.2, (ya + yb) / 2 + ny * 0.2)):
                nx, ny = -nx, -ny
            n_w = max(1, int(L // 3.6))
            for j in range(n_w):
                cxm = xa + ux * L * (j + 0.5) / n_w
                cym = ya + uy * L * (j + 0.5) / n_w
                wl = min(1.6, L / n_w * 0.55)
                for z0, z1 in ((SUB + 0.9, SUB + 2.3), (SUB + KAT + 0.6, SUB + KAT + 2.3)):
                    q = Polygon([(cxm - ux * wl / 2, cym - uy * wl / 2), (cxm + ux * wl / 2, cym + uy * wl / 2),
                                 (cxm + ux * wl / 2 + nx * 0.04, cym + uy * wl / 2 + ny * 0.04),
                                 (cxm - ux * wl / 2 + nx * 0.04, cym - uy * wl / 2 + ny * 0.04)])
                    add("villa", "cam", slab(q, z0, z1))
    # villa aralarındaki yangın duvarı çıkıntısı (parapet hizasına kadar)
    for b_i, b in enumerate(bloklar):
        vs = [v for v in villas if v["blok"] == b_i]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                s = vs[i]["poly"].buffer(0.02).intersection(vs[j]["poly"].buffer(0.02))
                if s.is_empty or s.area < 0.05:
                    continue
                cizgi = s.minimum_rotated_rectangle
                add("villa", "duvar2", slab(cizgi.buffer(0.10, join_style=2).difference(
                    b.buffer(-0.01)), SUB, PARAPET))
    # ağaçlar: her lotun bahçesinde bir ağaç
    for v in villas:
        bah = v["lot"].difference(v["poly"].buffer(2.0)).buffer(-1.2)
        if bah.is_empty:
            continue
        p = bah.representative_point()
        h = rng.uniform(4.0, 6.0)
        t = trimesh.creation.cylinder(radius=0.14, height=h * 0.45, sections=8)
        t.apply_translation((p.x, p.y, h * 0.225))
        add("agac", "govde", t)
        c = trimesh.creation.icosphere(subdivisions=1, radius=h * 0.28)
        c.apply_scale((1, 1, 1.15))
        c.apply_translation((p.x, p.y, h * 0.62))
        add("agac", rng.choice(["yaprak", "yaprak2"]), c)
    # glTF
    cu, cv = PARSEL.centroid.x, PARSEL.centroid.y
    T = np.array([[1, 0, 0, -cu], [0, 0, 1, 0], [0, -1, 0, cv], [0, 0, 0, 1]], float)
    scene = trimesh.Scene()
    for (g, m), ms in sorted(parts.items()):
        ms = [x for x in ms if x is not None]
        if not ms:
            continue
        mesh = trimesh.util.concatenate(ms)
        mesh.apply_transform(T)
        mesh.unmerge_vertices()
        col, ro, me = MAT[m]
        mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name=m, baseColorFactor=[*col, 1.0], roughnessFactor=ro, metallicFactor=me))
        scene.add_geometry(mesh, node_name=f"{g}__{m}", geom_name=f"{g}__{m}")
    with open(glb, "wb") as fh:
        fh.write(trimesh.exchange.gltf.export_glb(scene, include_normals=True))

    def g_(u, v):
        return [round(u - cu, 2), round(-(v - cv), 2)]
    a_ = math.radians(V.EKSEN_ACI)
    yc = IC_YOL_POLY.centroid.y
    meta = dict(
        varyant="U", kuzey=[round(math.sin(a_), 4), round(-math.cos(a_), 4)],
        dogu=[round(math.cos(a_), 4), round(math.sin(a_), 4)], cati=CATI_BIT, ust=PARAPET,
        giris=g_(IC_YOL_POLY.bounds[2] + 4, yc), yol_sol=g_(IC_YOL_POLY.bounds[0] + 4, yc),
        meydan=None, park=None, parsel=[g_(x, y) for x, y in PARSEL.exterior.coords],
        villalar=[dict(no=v["no"], sira=v["tip"], p=g_(*v["poly"].representative_point().coords[0])) for v in villas],
        ozet=dict(W=round(OLCU["sira_gen"], 2), D=round(OLCU["sira_der"], 2), n=len(villas), tapu=tapu,
                  brut=round(2 * float(np.mean([v["poly"].area for v in villas])), 0),
                  taks=round(taban / tapu, 2), kaks=round(insaat / tapu, 2), blok="5 dörtlü + 5 + 8 sıra"),
    )
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False)


if __name__ == "__main__":
    ciz("vaziyet_169-1-2_U.pdf", "vaziyet_169-1-2_U.png")
    dxf("vaziyet_169-1-2_U.dxf")
    model("model_169-1-2_U.glb", "model_169-1-2_U.json")
    print(f"ölçek {OLCEK:.3f} px/m, köşe hatası ≤ {HATA:.2f} m")
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in OLCU.items()})
    print({k: (round(float(v), 3) if not isinstance(v, int) else v) for k, v in OZET.items()})
