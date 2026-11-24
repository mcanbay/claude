# -*- coding: utf-8 -*-
"""
Bursa / Nilüfer / İrfaniye, 169 ada 1 parsel: 32 bitişik villa vaziyet planı (ön çalışma)

Çıktılar:
  vaziyet_169-1.pdf   A3 yatay, 1/400 ölçekli pafta
  vaziyet_169-1.png   önizleme
  vaziyet_169-1.dxf   TM30 (ITRF96, EPSG:5254) koordinatlı CAD çizimi

Çalıştırma: python vaziyet.py
"""
import math
import re

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, FancyArrow
from pyproj import Transformer
from shapely import affinity
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

# ---------------------------------------------------------------- parametreler
KML = "parsel-169-1.kml"
CEKME = 3.0          # parsel sınırından bina çekme mesafesi (varsayım; imar durumundan teyit edilmeli)
W = 5.85             # villa cephe genişliği
D = 12.0             # villa derinliği
OTOPARK = 5.0        # her villanın önündeki otopark derinliği
YOL = 6.0            # site içi yol genişliği (çift yön)
UST_ARKA = 51.0      # üst sıra villaların arka cephe hattı (yerel v)
N_UST, N_ALT = 18, 14
BALKON = 1.5         # arka balkon çıkması (1. kat, kesikli gösterilir)
BRUT = 165.0         # villa başı brüt alan (balkon dahil)
EKSEN_ACI = 69.6     # parsel uzun ekseninin doğudan açısı (derece)

# ---------------------------------------------------------------- parsel
txt = open(KML, encoding="utf-8").read()
def kml_data(name):
    m = re.search(r'<Data name="%s">\s*<value>(.*?)</value>' % name, txt, re.S)
    return m.group(1).strip() if m else ""
coords = re.search(r"<coordinates>(.*?)</coordinates>", txt, re.S).group(1).split()
lonlat = [tuple(map(float, c.split(",")[:2])) for c in coords][:-1]
to_tm = Transformer.from_crs(4326, 5254, always_xy=True)
tm = [to_tm.transform(*p) for p in lonlat]
P_tm = Polygon(tm)
OX, OY = P_tm.centroid.x, P_tm.centroid.y
_tmp = affinity.rotate(affinity.translate(P_tm, -OX, -OY), -EKSEN_ACI, origin=(0, 0))
MX, MY = _tmp.bounds[0], _tmp.bounds[1]
PARSEL = affinity.translate(_tmp, -MX, -MY)          # yerel: u uzun eksen, v enine


def to_world(x, y):
    """yerel (u,v) -> TM30 (sağa, yukarı)"""
    x, y = x + MX, y + MY
    a = math.radians(EKSEN_ACI)
    return (x * math.cos(a) - y * math.sin(a) + OX, x * math.sin(a) + y * math.cos(a) + OY)


BUILD = PARSEL.buffer(-CEKME, join_style=2)          # yapı yaklaşma sınırı

# ---------------------------------------------------------------- şeritler (v ekseni)
ust = (UST_ARKA - D, UST_ARKA)
ust_otp = (ust[0] - OTOPARK, ust[0])
yol = (ust_otp[0] - YOL, ust_otp[0])
alt_otp = (yol[0] - OTOPARK, yol[0])
alt = (alt_otp[0] - D, alt_otp[0])


def first_fit(v0, v1, n):
    for i in range(0, 1200):
        x = i * 0.05
        if all(BUILD.contains(box(x + k * W, v0, x + (k + 1) * W, v1)) for k in (0, n - 1)):
            if all(BUILD.contains(box(x + k * W, v0, x + (k + 1) * W, v1)) for k in range(n)):
                return round(x + 0.05, 2)   # küçük pay
    raise SystemExit("Sıra sığmadı: v=%s..%s n=%d" % (v0, v1, n))


X_UST = first_fit(*ust, N_UST)
X_ALT = first_fit(*alt, N_ALT)

villas = []   # dict: no, ev, otopark, park_yeri, yuruyus, bahce, balkon, sira
BIG = 200


def make_row(x0, n, ev, otp, bahce_side, no0, sira):
    for k in range(n):
        x = x0 + k * W
        house = box(x, ev[0], x + W, ev[1])
        front = box(x, otp[0], x + W, otp[1])
        # park yerleri çiftler halinde yan yana (ortak bordür kesimi)
        left = (k % 2 == 1)
        sx = x if left else x + W - 2.6
        stall = box(sx, otp[0], sx + 2.6, otp[1])
        wx = x + W - 1.4 if left else x + 0.2
        walk = box(wx, otp[0], wx + 1.2, otp[1])
        if bahce_side == "ust":
            g = box(x, ev[1], x + W, BIG).intersection(PARSEL)
            bal = box(x + 0.3, ev[1], x + W - 0.3, ev[1] + BALKON)
        else:
            g = box(x, -BIG, x + W, ev[0]).intersection(PARSEL)
            bal = box(x + 0.3, ev[0] - BALKON, x + W - 0.3, ev[0])
        villas.append(dict(no=no0 + k, ev=house, otopark=front, park=stall, yuruyus=walk,
                           bahce=g, balkon=bal, sira=sira))


# numaralandırma: üst sıra soldan sağa V1..V18, alt sıra sağdan sola V19..V32 (döngü sırası)
make_row(X_UST, N_UST, ust, ust_otp, "ust", 1, "A")
tmp = []
make_row(X_ALT, N_ALT, alt, alt_otp, "alt", 0, "B")
alt_list = villas[N_UST:]
for i, v in enumerate(reversed(alt_list)):
    v["no"] = N_UST + 1 + i

YOL_POLY = box(-BIG, yol[0], BIG, yol[1]).intersection(PARSEL)
SETBACK_LINE = BUILD.exterior

# ortak alan = parsel - (yol + villa lotları)
lots = unary_union([unary_union([v["ev"], v["otopark"], v["bahce"]]) for v in villas])
ORTAK = PARSEL.difference(unary_union([lots, YOL_POLY]))

# ---------------------------------------------------------------- kontroller / tablo
for v in villas:
    assert BUILD.contains(v["ev"]), v["no"]
    assert PARSEL.buffer(0.01).contains(v["otopark"]), v["no"]
tapu_alan = float(kml_data("Alan").replace(".", "").replace(",", "."))
geo_alan = PARSEL.area
oturum = W * D
taban_top = oturum * len(villas)
brut_top = BRUT * len(villas)
balkon_villa = BRUT - 2 * oturum
yol_alan = YOL_POLY.area
otopark_alan = sum(v["otopark"].area for v in villas)
bahce_alan = sum(v["bahce"].area for v in villas)
ortak_alan = ORTAK.area
bahce_min = min(v["bahce"].area for v in villas)
bahce_max = max(v["bahce"].area for v in villas)

ozet = [
    ("Parsel alanı (tapu)", f"{tapu_alan:,.2f} m²"),
    ("Villa sayısı", f"{len(villas)} adet (A sırası {N_UST} + B sırası {N_ALT})"),
    ("Villa tipi", f"{W:.2f} × {D:.2f} m, bitişik nizam, Z+1"),
    ("Taban oturumu / villa", f"{oturum:.1f} m²"),
    ("Brüt alan / villa", f"{BRUT:.0f} m² (2 × {oturum:.1f} + {balkon_villa:.1f} balkon/teras)"),
    ("Toplam taban oturumu", f"{taban_top:,.0f} m²  →  TAKS ≈ {taban_top / tapu_alan:.2f}"),
    ("Toplam brüt inşaat", f"{brut_top:,.0f} m²  →  KAKS ≈ {brut_top / tapu_alan:.2f}"),
    ("Otopark", f"{len(villas)} araç (her villanın önünde 2,6 × 5,0 m)"),
    ("Site içi yol", f"{YOL:.1f} m genişlik, {yol_alan:,.0f} m²"),
    ("Özel bahçeler", f"{bahce_alan:,.0f} m² (villa başı {bahce_min:.0f}–{bahce_max:.0f} m²)"),
    ("Ortak alan / artık", f"{ortak_alan:,.0f} m²"),
]

# ---------------------------------------------------------------- çizim (matplotlib)
C = dict(parsel="#1f2937", cekme="#dc2626", yol="#d6d3d1", otopark="#e7e5e4", park="#a8a29e",
         ev="#b45309", ev_fill="#fde68a", bahce="#dcfce7", ortak="#bbf7d0", yazi="#111827")


def draw_poly(ax, g, **kw):
    if g.is_empty:
        return
    geoms = getattr(g, "geoms", [g])
    for p in geoms:
        if p.geom_type != "Polygon":
            continue
        ax.add_patch(MPoly(list(p.exterior.coords), closed=True, **kw))


def render(path_pdf, path_png):
    A3 = (420 / 25.4, 297 / 25.4)
    fig = plt.figure(figsize=A3)
    # 1/400: 1 m = 2,5 mm
    MM = 2.5
    pad = 6.0
    x0, y0, x1, y1 = PARSEL.bounds
    wm, hm = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    ax_w, ax_h = wm * MM / 420, hm * MM / 297
    ax = fig.add_axes([20 / 420, 1 - 18 / 297 - ax_h, ax_w, ax_h])
    ax.set_xlim(x0 - pad, x1 + pad)
    ax.set_ylim(y0 - pad, y1 + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    draw_poly(ax, ORTAK, facecolor=C["ortak"], edgecolor="none", zorder=1)
    for v in villas:
        draw_poly(ax, v["bahce"], facecolor=C["bahce"], edgecolor="#86efac", lw=0.4, zorder=1)
        draw_poly(ax, v["otopark"], facecolor=C["otopark"], edgecolor="#a8a29e", lw=0.3, zorder=2)
        draw_poly(ax, v["park"], facecolor=C["park"], edgecolor="#78716c", lw=0.3, zorder=3)
        draw_poly(ax, v["yuruyus"], facecolor="#ffffff", edgecolor="#a8a29e", lw=0.3, zorder=3)
        draw_poly(ax, v["ev"], facecolor=C["ev_fill"], edgecolor=C["ev"], lw=0.8, zorder=4)
        bx = list(v["balkon"].exterior.coords)
        ax.plot([p[0] for p in bx], [p[1] for p in bx], ls=(0, (2, 1.5)), lw=0.5, color=C["ev"], zorder=5)
        c = v["ev"].centroid
        ax.text(c.x, c.y, f"V{v['no']}", ha="center", va="center", fontsize=6.2,
                fontweight="bold", color=C["yazi"], rotation=90, zorder=6)
        pc = v["park"].centroid
        ax.text(pc.x, pc.y, "P", ha="center", va="center", fontsize=4.5, color="white", zorder=6)
    draw_poly(ax, YOL_POLY, facecolor=C["yol"], edgecolor="#78716c", lw=0.5, zorder=2)
    ym = (yol[0] + yol[1]) / 2
    ax.plot([PARSEL.bounds[0], PARSEL.bounds[2]], [ym, ym], ls=(0, (6, 4)), lw=0.5, color="white", zorder=3)
    ax.plot([X_ALT, X_ALT + N_ALT * W], [ym, ym], lw=0, zorder=3)
    ax.text(60, ym, f"SİTE İÇİ YOL  ({YOL:.0f} m)", ha="center", va="center", fontsize=7,
            color="#44403c", zorder=6, bbox=dict(fc=C["yol"], ec="none", pad=0.6))

    # parsel ve çekme hattı
    px, py = PARSEL.exterior.xy
    ax.plot(px, py, color=C["parsel"], lw=1.6, zorder=8)
    sx, sy = SETBACK_LINE.xy
    ax.plot(sx, sy, color=C["cekme"], lw=0.6, ls=(0, (5, 2, 1, 2)), zorder=7)
    cen = PARSEL.centroid
    pts = list(PARSEL.exterior.coords)
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.dist(a, b)
        mx_, my_ = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L     # sola normal
        if (mx_ + nx - cen.x) ** 2 + (my_ + ny - cen.y) ** 2 < (mx_ - cen.x) ** 2 + (my_ - cen.y) ** 2:
            nx, ny = -nx, -ny
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        ax.text(mx_ + nx * 2.0, my_ + ny * 2.0, f"{L:.2f}", fontsize=5.5, color=C["parsel"],
                ha="center", va="center", rotation=ang, zorder=9)

    # ölçü: tipik villa
    v = villas[8]
    e = v["ev"].bounds
    ax.annotate("", (e[0], e[3] + 6.2), (e[2], e[3] + 6.2),
                arrowprops=dict(arrowstyle="<->", lw=0.5, color="#374151"))
    ax.text((e[0] + e[2]) / 2, e[3] + 6.9, f"{W:.2f}", fontsize=5.5, ha="center", color="#374151")

    # sıra etiketleri, giriş notları
    ax.text(X_UST + N_UST * W / 2, PARSEL.bounds[3] + 2.5, "A SIRASI · 18 VİLLA · arka bahçeler",
            fontsize=6.5, ha="center", color="#166534", zorder=9)
    ax.text(X_ALT + N_ALT * W / 2, alt[0] - 5.0, "B SIRASI · 14 VİLLA · arka bahçeler",
            fontsize=6.5, ha="center", color="#166534", zorder=9)
    gx0 = PARSEL.bounds[0]
    ax.annotate("GİRİŞ ?", (gx0 + 1.2, ym), (gx0 - 4.5, ym + 9), fontsize=7, color="#b91c1c",
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.0), zorder=10)
    gx1 = YOL_POLY.bounds[2]
    ax.annotate("GİRİŞ ?", (gx1 - 1.2, ym), (gx1 + 3.5, ym + 9), fontsize=7, color="#b91c1c",
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.0), zorder=10)

    # kuzey oku (yerel çerçevede kuzey yönü)
    a = math.radians(EKSEN_ACI)
    nxv, nyv = math.sin(a), math.cos(a)
    kx, ky = x1 - 2, y1 + 1
    ax.add_patch(FancyArrow(kx - nxv * 4, ky - nyv * 4, nxv * 8, nyv * 8, width=0.6,
                            head_width=2.4, head_length=2.6, color="#111827", zorder=10,
                            length_includes_head=True))
    ax.text(kx + nxv * 6.5, ky + nyv * 6.5, "K", fontsize=10, fontweight="bold",
            ha="center", va="center")

    # ölçek çubuğu
    sx0, sy0 = x0, y0 - 4.5
    for i in range(5):
        ax.add_patch(MPoly([(sx0 + i * 5, sy0), (sx0 + i * 5 + 5, sy0), (sx0 + i * 5 + 5, sy0 + 0.8),
                            (sx0 + i * 5, sy0 + 0.8)], fc="#111827" if i % 2 == 0 else "white",
                           ec="#111827", lw=0.4))
    for m in (0, 10, 25):
        ax.text(sx0 + m, sy0 - 1.6, f"{m} m", fontsize=5.5, ha="center")

    # başlık ve tablo
    fig.text(20 / 420, 1 - 9 / 297, "VAZİYET PLANI (ÖN ÇALIŞMA): 32 BİTİŞİK VİLLA", fontsize=15,
             fontweight="bold", color="#111827")
    fig.text(20 / 420, 1 - 14.5 / 297,
             f"{kml_data('İl')} / {kml_data('İlçe')} / {kml_data('Mahalle')} Mah. · "
             f"{kml_data('Ada')} Ada {kml_data('ParselNo')} Parsel · Mevkii: {kml_data('Mevkii')} · "
             f"Pafta: {kml_data('Pafta')} · Nitelik: {kml_data('Nitelik')}",
             fontsize=8.5, color="#374151")
    tx, ty = 20 / 420, 1 - (18 + ax_h * 297 + 10) / 297
    fig.text(tx, ty, "ALAN ÖZETİ", fontsize=9, fontweight="bold")
    for i, (k, val) in enumerate(ozet):
        yy = ty - (5 + i * 4.3) / 297
        fig.text(tx, yy, k, fontsize=7.2, color="#374151")
        fig.text(tx + 48 / 420, yy, val, fontsize=7.2, color="#111827")
    # lejant
    lx = 175 / 420
    fig.text(lx, ty, "LEJANT", fontsize=9, fontweight="bold")
    items = [(C["ev_fill"], C["ev"], "Villa (taban oturumu), kesikli: 1. kat balkon"),
             (C["park"], "#78716c", "Otopark (villa önü, 2,6 × 5,0 m)"),
             (C["otopark"], "#a8a29e", "Villa ön bahçesi / araç girişi"),
             (C["yol"], "#78716c", "Site içi yol"),
             (C["bahce"], "#86efac", "Villa özel bahçesi"),
             (C["ortak"], "none", "Ortak yeşil / artık alan")]
    for i, (fc, ec, lab) in enumerate(items):
        yy = ty - (5 + i * 4.3) / 297
        fig.patches.append(matplotlib.patches.Rectangle((lx, yy - 0.3 / 297), 6 / 420, 2.6 / 297,
                           transform=fig.transFigure, fc=fc, ec=ec, lw=0.5))
        fig.text(lx + 8 / 420, yy, lab, fontsize=7.2, color="#374151")
    yy = ty - (5 + len(items) * 4.3) / 297
    fig.lines.append(matplotlib.lines.Line2D([lx, lx + 6 / 420], [yy + 1 / 297] * 2, transform=fig.transFigure,
                                             color=C["cekme"], lw=0.8, ls=(0, (5, 2, 1, 2))))
    fig.text(lx + 8 / 420, yy, f"Yapı yaklaşma sınırı ({CEKME:.0f} m, varsayım)", fontsize=7.2, color="#374151")
    yy -= 4.3 / 297
    fig.lines.append(matplotlib.lines.Line2D([lx, lx + 6 / 420], [yy + 1 / 297] * 2, transform=fig.transFigure,
                                             color=C["parsel"], lw=1.6))
    fig.text(lx + 8 / 420, yy, "Parsel sınırı (TKGM), kenar uzunlukları metre", fontsize=7.2, color="#374151")
    # notlar
    nx_ = 290 / 420
    fig.text(nx_, ty, "NOTLAR", fontsize=9, fontweight="bold")
    notes = [
        "1. Ön çalışmadır; imar durumu (emsal, TAKS, kat adedi, çekme",
        "    mesafeleri, blok boyu) belediyeden alınıp teyit edilmelidir.",
        "2. Parsel sınırı TKGM KML'inden alınmıştır. Koordinat yuvarlaması",
        f"    nedeniyle çizim alanı {geo_alan:,.0f} m², tapu alanı {tapu_alan:,.0f} m².",
        "3. Yola cephe bilinmiyor; giriş iki uçtan biri varsayılmıştır.",
        "    Tek uçtan girişte diğer uçta dönüş cebi gerekir.",
        "4. 32 villa ancak 5,85 m cephe ve kesintisiz bloklarla sığıyor;",
        "    misafir otoparkı ve ortak alan için yer kalmıyor. A sırası",
        "    bahçeleri dar (4–6 m), balkonlar çekme hattına taşıyor.",
        "5. Ölçek 1/400 (A3). DXF dosyası TM30 / ITRF96 koordinatlıdır.",
    ]
    for i, n in enumerate(notes):
        fig.text(nx_, ty - (5 + i * 4.3) / 297, n, fontsize=6.8, color="#374151")
    fig.text(1 - 20 / 420, 8 / 297, "Ölçek 1/400 · A3", fontsize=7, ha="right", color="#6b7280")

    fig.savefig(path_pdf)
    fig.savefig(path_png, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- DXF (TM30 dünya koordinatı)
def write_dxf(path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    layers = {"PARSEL": 7, "CEKME": 1, "YOL": 8, "OTOPARK": 9, "PARK_YERI": 252, "VILLA": 30,
              "BALKON": 30, "BAHCE": 3, "ORTAK_ALAN": 82, "YAZI": 7}
    for n, col in layers.items():
        doc.layers.add(n, color=col)
    doc.layers.get("CEKME").dxf.linetype = "DASHDOT"
    doc.layers.get("BALKON").dxf.linetype = "DASHED"

    def poly(g, layer):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type == "Polygon" and not p.is_empty:
                msp.add_lwpolyline([to_world(*c) for c in p.exterior.coords[:-1]], close=True,
                                   dxfattribs={"layer": layer})

    poly(PARSEL, "PARSEL")
    poly(BUILD, "CEKME")
    poly(YOL_POLY, "YOL")
    poly(ORTAK, "ORTAK_ALAN")
    for v in villas:
        poly(v["ev"], "VILLA")
        poly(v["balkon"], "BALKON")
        poly(v["otopark"], "OTOPARK")
        poly(v["park"], "PARK_YERI")
        poly(v["bahce"], "BAHCE")
        c = v["ev"].centroid
        msp.add_text(f"V{v['no']}", height=1.2, rotation=EKSEN_ACI + 90,
                     dxfattribs={"layer": "YAZI"}).set_placement(
            to_world(c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    c = PARSEL.centroid
    msp.add_text(f"{kml_data('Ada')} ADA {kml_data('ParselNo')} PARSEL", height=2.0,
                 rotation=EKSEN_ACI, dxfattribs={"layer": "YAZI"}).set_placement(
        to_world(c.x, PARSEL.bounds[1] - 5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


if __name__ == "__main__":
    render("vaziyet_169-1.pdf", "vaziyet_169-1.png")
    write_dxf("vaziyet_169-1.dxf")
    print(f"A sırası x0={X_UST}, B sırası x0={X_ALT}")
    for k, v in ozet:
        print(f"{k:24s} {v}")
