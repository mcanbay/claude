# -*- coding: utf-8 -*-
"""
Bursa / Nilüfer / İrfaniye, 169 ada 1 + 2 parseller (tevhit): bitişik villa vaziyet planı (ön çalışma)

Varyantlar (VARYANTLAR sözlüğü):
  A: 32 villa, iki kesintisiz blok (16+16), sol uçta dönüş cebi
  B: 32 villa, iki kesintisiz blok (16+16), dönüş cebi yok, villa cephesi en geniş
  C: 32 villa, her sırada 2 blok (8+8), bloklar arası 6 m
  D: 30 villa, her sırada 2 blok (8+7), bloklar arası 6 m
  E: 28 villa, her sırada 3 blok (5+4+5), bloklar arası 6 m
Çıktılar: vaziyet_169-1-2_<V>.pdf / .png / .dxf
PDF: A3 yatay 1/400 pafta. DXF: TM30 (ITRF96, EPSG:5254) koordinatlı.

Çalıştırma: python vaziyet.py          (tüm varyantları üretir)
            python vaziyet.py C
"""
import sys
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
KMLS = ["parsel-169-1.kml", "parsel-169-2.kml"]   # tevhit edilecek parseller
CEKME = 3.0          # parsel sınırından bina çekme mesafesi (varsayım; imar durumundan teyit edilmeli)
OTOPARK = 5.0        # her villanın önündeki otopark derinliği
YOL = 6.0            # site içi yol genişliği (çift yön)
BLOK_ARA = 6.0       # ayrık bloklar arasındaki asgari mesafe (iki kütle arası)
W_MAX = 6.60         # villa cephesi üst sınırı (4+1 tip kat planı bu genişliğe göre çizildi)
VARYANTLAR = {
    # ad: (villa derinliği D, sol uçta dönüş cebi, A sırası blokları, B sırası blokları, açıklama)
    "A": (11.5, 6.0, [16], [16], "sol uçta dönüş cebi var"),
    "B": (11.0, 0.0, [16], [16], "dönüş cebi yok, villa cephesi en geniş"),
    "C": (11.0, 0.0, [8, 8], [8, 8], "32 villa, her sırada 2 blok (8+8), bloklar arası 6 m"),
    "D": (11.0, 0.0, [8, 7], [7, 8], "30 villa, her sırada 2 blok (8+7), bloklar arası 6 m"),
    "E": (11.0, 0.0, [5, 4, 5], [5, 4, 5], "28 villa, her sırada 3 blok (5+4+5), bloklar arası 6 m"),
}
VARYANT = sys.argv[1] if len(sys.argv) > 1 else "A"
D, CEP, BLOK_UST, BLOK_ALT, VARYANT_ACIKLAMA = VARYANTLAR[VARYANT]
N_UST, N_ALT = sum(BLOK_UST), sum(BLOK_ALT)
ARA_UST, ARA_ALT = (len(BLOK_UST) - 1) * BLOK_ARA, (len(BLOK_ALT) - 1) * BLOK_ARA
BALKON = 1.5         # arka balkon çıkması (1. kat, kesikli gösterilir)
BALKON_ON = 1.6      # ön balkon çıkması (1. kat, otopark üstüne; girişe saçak olur)
BRUT = 165.0         # villa başı brüt alan (balkon dahil)
EKSEN_ACI = 69.6     # parsel uzun ekseninin doğudan açısı (derece)

# ---------------------------------------------------------------- parsel
to_tm = Transformer.from_crs(4326, 5254, always_xy=True)
TXTS = [open(k, encoding="utf-8").read() for k in KMLS]


def kml_data(name, txt=None):
    m = re.search(r'<Data name="%s">\s*<value>(.*?)</value>' % name, txt or TXTS[0], re.S)
    return m.group(1).strip() if m else ""


def kml_poly(txt):
    coords = re.search(r"<coordinates>(.*?)</coordinates>", txt, re.S).group(1).split()
    return Polygon([to_tm.transform(*map(float, c.split(",")[:2])) for c in coords])


P_tm = unary_union([kml_poly(t) for t in TXTS]).simplify(0.05)
PARSEL_NO = " + ".join(kml_data("ParselNo", t) for t in TXTS)
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
def seritler(ust_arka):
    ust = (ust_arka - D, ust_arka)
    ust_otp = (ust[0] - OTOPARK, ust[0])
    yol = (ust_otp[0] - YOL, ust_otp[0])
    alt_otp = (yol[0] - OTOPARK, yol[0])
    alt = (alt_otp[0] - D, alt_otp[0])
    return ust, ust_otp, yol, alt_otp, alt


def sol_kenar(v):
    """parsel sol (giriş karşısı) kenarının v yüksekliğindeki x değeri"""
    s = PARSEL.intersection(LineString([(-1, v), (BIG, v)]))
    return s.bounds[0]


def bant(v0, v1, xmin):
    """[v0,v1] bandında yapı yaklaşma sınırı içindeki en sol/en sağ x"""
    xs = [x * 0.05 for x in range(int(xmin / 0.05), 3000)]
    ok = [x for x in xs if BUILD.contains(box(x, v0, x + 0.05, v1))]
    return ok[0], ok[-1] + 0.05


BIG = 200
# en geniş villa cephesini ve iki yandaki bahçeleri dengeleyen yol konumunu ara
_best = None
for _t10 in range(400, 560, 5):
    _ua = _t10 / 10
    _u, _uo, _y, _ao, _a = seritler(_ua)
    _cep_x = (sol_kenar(_uo[1]) + CEP) if CEP else 0.0
    try:
        _su, _sa = bant(*_u, _cep_x), bant(*_a, _cep_x)
    except IndexError:
        continue
    _w = math.floor(min((_su[1] - _su[0] - ARA_UST) / N_UST, (_sa[1] - _sa[0] - ARA_ALT) / N_ALT) * 20) / 20
    _w = min(_w, W_MAX)
    _ust_bahce = PARSEL.bounds[3] - 1.0 - _ua
    _denge = abs(_ust_bahce - _a[0])
    _key = (_w, -_denge)
    if _best is None or _key > _best[0]:
        _best = (_key, _ua, _su, _sa, _cep_x)
(W, _), UST_ARKA, SU, SA, CEP_X = _best
ust, ust_otp, yol, alt_otp, alt = seritler(UST_ARKA)
# sıraları giriş (sağ) ucuna yaslamak yerine bant içinde ortala
L_UST, L_ALT = N_UST * W + ARA_UST, N_ALT * W + ARA_ALT          # sıra boyları (bloklar + aralar)
X_UST = round(SU[0] + ((SU[1] - SU[0]) - L_UST) / 2, 2)
X_ALT = round(SA[0] + ((SA[1] - SA[0]) - L_ALT) / 2, 2)

villas = []   # dict: no, ev, otopark, park_yeri, yuruyus, bahce, balkon, sira, blok, blok_bas, blok_son
ARALAR = []   # dict: sira, u0, u1 (bloklar arası 6 m boşluk)
MISAFIR = []  # misafir otoparkı yerleri (bloklar arasındaki boşluğun ön şeridinde)


def make_row(x0, n, ev, otp, bahce_side, no0, sira, blok=0):
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
            bal = box(x + 0.1, ev[1], x + W - 0.1, ev[1] + BALKON)
            bal_on = box(x + 0.1, ev[0] - BALKON_ON, x + W - 0.1, ev[0])
        else:
            g = box(x, -BIG, x + W, ev[0]).intersection(PARSEL)
            bal = box(x + 0.1, ev[0] - BALKON, x + W - 0.1, ev[0])
            bal_on = box(x + 0.1, ev[1], x + W - 0.1, ev[1] + BALKON_ON)
        villas.append(dict(no=no0 + k, ev=house, otopark=front, park=stall, yuruyus=walk,
                           bahce=g, balkon=bal, balkon_on=bal_on, sira=sira, blok=blok,
                           blok_bas=(k == 0), blok_son=(k == n - 1)))


def make_bloklar(x0, bloklar, ev, otp, bahce_side, no0, sira):
    """Sırayı bloklara böler; bloklar arasında BLOK_ARA boşluk bırakır. Boşluğun yarısı komşu uç
    villanın yan bahçesi olur, ön şeridine iki misafir otoparkı konur."""
    x = x0
    for b, n in enumerate(bloklar):
        make_row(x, n, ev, otp, bahce_side, no0, sira, blok=b)
        no0 += n
        x += n * W
        if b < len(bloklar) - 1:
            gu0, gu1 = x, x + BLOK_ARA
            gc = (gu0 + gu1) / 2
            ARALAR.append(dict(sira=sira, u0=gu0, u1=gu1))
            for a0 in (gc - 2.55, gc + 0.05):
                MISAFIR.append(box(a0, otp[0], a0 + 2.5, otp[1]))
            # yan bahçeler: uç villanın yanında, ön cephe hizasından bahçe sonuna kadar
            for vv in villas:
                if vv["sira"] != sira:
                    continue
                hu0, hv0, hu1, hv1 = vv["ev"].bounds
                if abs(hu1 - gu0) < 1e-6:          # boşluğun solundaki villa
                    yan = box(hu1, hv0, gc, hv1)
                    arka = box(hu1, hv1, gc, BIG) if bahce_side == "ust" else box(hu1, -BIG, gc, hv0)
                    vv["bahce"] = unary_union([vv["bahce"], yan, arka.intersection(PARSEL)])
                    vv["lot_u1"] = gc
            x += BLOK_ARA
    # boşluğun sağındaki villalar (bir sonraki bloğun ilk villası)
    for a in [a for a in ARALAR if a["sira"] == sira]:
        gc = (a["u0"] + a["u1"]) / 2
        for vv in villas:
            hu0, hv0, hu1, hv1 = vv["ev"].bounds
            if vv["sira"] == sira and abs(hu0 - a["u1"]) < 1e-6:
                yan = box(gc, hv0, hu0, hv1)
                arka = box(gc, hv1, hu0, BIG) if bahce_side == "ust" else box(gc, -BIG, hu0, hv0)
                vv["bahce"] = unary_union([vv["bahce"], yan, arka.intersection(PARSEL)])
                vv["lot_u0"] = gc


# numaralandırma girişten (sağ uç) başlar: A sırası sağdan sola V1.., B sırası soldan sağa
make_bloklar(X_UST, BLOK_UST, ust, ust_otp, "ust", 1, "A")
for i, v in enumerate(reversed(villas)):
    v["no"] = i + 1
make_bloklar(X_ALT, BLOK_ALT, alt, alt_otp, "alt", N_UST + 1, "B")

YOL_POLY = box(-BIG, yol[0], BIG, yol[1]).intersection(PARSEL)
CEP_POLY = box(-BIG, alt_otp[0], min(X_UST, X_ALT), ust_otp[1]).intersection(PARSEL) if CEP else Polygon()
if CEP:
    YOL_POLY = unary_union([YOL_POLY, CEP_POLY])
SETBACK_LINE = BUILD.exterior

# ortak alan = parsel - (yol + villa lotları + misafir otoparkları)
lots = unary_union([unary_union([v["ev"], v["otopark"], v["bahce"]]) for v in villas])
ORTAK = PARSEL.difference(unary_union([lots, YOL_POLY] + MISAFIR))

# ---------------------------------------------------------------- mahremiyet duvarları
# Komşu villalar arasında: arka bahçede teras boyunca yüksek, bahçe sonuna kadar alçak duvar;
# 1. katta balkonlar arasında saçağa kadar yan duvar; önde iki giriş yolu yan yana gelen sınırda alçak duvar.
MAH_T = 0.20            # duvar kalınlığı
MAH_TERAS = 3.5         # arka cepheden itibaren yüksek (teras) duvar boyu
MAH_H_TERAS, MAH_H_BAHCE, MAH_H_ON = 2.4, 1.9, 1.4
MAH_ON_BOY = 4.0        # ön bahçede giriş yolları arasındaki duvar boyu
CEVRE_DUVAR_KAL = 0.25  # parsel çevre duvarı kalınlığı
MAH = []                # dict: tip (teras / bahce / on / balkon), poly, h (yükseklik; balkon için saçağa kadar)


def _vband(a, b, u0, u1):
    return box(u0, min(a, b), u1, max(a, b))


def _mahremiyet_duvarlari():
    ic = PARSEL.buffer(-CEVRE_DUVAR_KAL, join_style=2)
    for row, blok in sorted({(v["sira"], v["blok"]) for v in villas}):
        vs = sorted([v for v in villas if v["sira"] == row and v["blok"] == blok], key=lambda v: v["ev"].bounds[0])
        for i, v in enumerate(vs):
            u0, v0, u1, v1 = v["ev"].bounds
            arka, on = (v1, v0) if row == "A" else (v0, v1)
            dis = 1 if row == "A" else -1           # arka cepheden bahçeye doğru v yönü
            # blok sonundaki villanın dış yanında boşluk varsa yan bahçe duvarı boşluğun ortasındadır
            for lot_key, uh in (("lot_u0", u0), ("lot_u1", u1)):
                if lot_key in v:
                    gc = v[lot_key]
                    ln = LineString([(gc, on), (gc, arka + dis * 500)]).intersection(ic)
                    MAH.append(dict(tip="bahce", poly=ln.buffer(MAH_T / 2, cap_style=2), h=MAH_H_BAHCE))
                    MAH.append(dict(tip="on", poly=box(min(uh, gc), on - MAH_T / 2, max(uh, gc), on + MAH_T / 2),
                                    h=MAH_H_ON))
            for uu in [u0] + ([u1] if i == len(vs) - 1 else []):
                if (uu == u0 and "lot_u0" in v) or (uu == u1 and "lot_u1" in v):
                    # yan bahçeli uç: zeminde duvar boşlukta; 1. katta balkon yan duvarı yine var
                    MAH.append(dict(tip="balkon", poly=_vband(arka, arka + dis * (BALKON + 0.1),
                                                              uu - MAH_T / 2, uu + MAH_T / 2), h=None))
                    MAH.append(dict(tip="balkon", poly=_vband(on, on - dis * (BALKON_ON + 0.1),
                                                              uu - MAH_T / 2, uu + MAH_T / 2), h=None))
                    continue
                ln = LineString([(uu, arka), (uu, arka + dis * 500)]).intersection(ic)
                if not ln.is_empty:
                    duvar = ln.buffer(MAH_T / 2, cap_style=2)
                    teras = _vband(arka, arka + dis * MAH_TERAS, uu - 1, uu + 1)
                    MAH.append(dict(tip="teras", poly=duvar.intersection(teras), h=MAH_H_TERAS))
                    MAH.append(dict(tip="bahce", poly=duvar.difference(teras), h=MAH_H_BAHCE))
                MAH.append(dict(tip="balkon", poly=_vband(arka, arka + dis * (BALKON + 0.1),
                                                          uu - MAH_T / 2, uu + MAH_T / 2), h=None))
                MAH.append(dict(tip="balkon", poly=_vband(on, on - dis * (BALKON_ON + 0.1),
                                                          uu - MAH_T / 2, uu + MAH_T / 2), h=None))
            if i > 0:
                once = vs[i - 1]
                ou0, _, ou1, _ = once["ev"].bounds
                if v["yuruyus"].centroid.x < (u0 + u1) / 2 and once["yuruyus"].centroid.x > (ou0 + ou1) / 2:
                    MAH.append(dict(tip="on", poly=_vband(on, on - dis * MAH_ON_BOY,
                                                          u0 - MAH_T / 2, u0 + MAH_T / 2), h=MAH_H_ON))


_mahremiyet_duvarlari()

# ---------------------------------------------------------------- kontroller / tablo
for v in villas:
    assert BUILD.contains(v["ev"]), v["no"]
    assert PARSEL.buffer(0.01).contains(v["otopark"]), v["no"]
tapu_alanlar = [float(kml_data("Alan", t).replace(".", "").replace(",", ".")) for t in TXTS]
tapu_alan = sum(tapu_alanlar)
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
    ("Parsel alanı (tapu)", f"{tapu_alan:,.2f} m² ({' + '.join(f'{a:,.2f}' for a in tapu_alanlar)})"),
    ("Villa sayısı", f"{len(villas)} adet (A sırası {N_UST} + B sırası {N_ALT})"),
    ("Villa tipi", f"{W:.2f} × {D:.2f} m, " + ("blok içinde bitişik" if ARALAR else "bitişik nizam") + ", Z+1"),
    ("Taban oturumu / villa", f"{oturum:.1f} m²"),
    ("Brüt alan / villa", f"{BRUT:.0f} m² (2 × {oturum:.1f} + {balkon_villa:.1f} balkon/teras)"),
    ("Toplam taban oturumu", f"{taban_top:,.0f} m²  →  TAKS ≈ {taban_top / tapu_alan:.2f}"),
    ("Toplam brüt inşaat", f"{brut_top:,.0f} m²  →  KAKS ≈ {brut_top / tapu_alan:.2f}"),
    ("Blok düzeni", f"A: {'+'.join(map(str, BLOK_UST))}, B: {'+'.join(map(str, BLOK_ALT))}"
                    + (f", bloklar arası {BLOK_ARA:.0f} m" if ARALAR else ", kesintisiz")),
    ("Otopark", f"{len(villas)} villa önünde" + (f" + {len(MISAFIR)} misafir" if MISAFIR else "")
                + " (2,6 × 5,0 m)"),
    ("Site içi yol", f"{YOL:.1f} m genişlik, {yol_alan:,.0f} m²" + (" (dönüş cebi dahil)" if CEP else "")),
    ("Özel bahçeler", f"{bahce_alan:,.0f} m² (villa başı {bahce_min:.0f}–{bahce_max:.0f} m²)"),
    ("Ortak alan / artık", f"{ortak_alan:,.0f} m²"),
]

# ---------------------------------------------------------------- çizim (matplotlib)
C = dict(parsel="#1f2937", cekme="#dc2626", yol="#d6d3d1", otopark="#e7e5e4", park="#a8a29e",
         ev="#b45309", ev_fill="#fde68a", bahce="#dcfce7", ortak="#bbf7d0", yazi="#111827",
         mah="#44403c")


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
    for mp in MISAFIR:
        draw_poly(ax, mp, facecolor="#cbd5e1", edgecolor="#64748b", lw=0.4, zorder=3)
        c_ = mp.centroid
        ax.text(c_.x, c_.y, "M", ha="center", va="center", fontsize=4.5, color="#334155", zorder=6)
    for a in ARALAR:                       # bloklar arası mesafe ölçüsü
        vv = (ust[0] + ust[1]) / 2 if a["sira"] == "A" else (alt[0] + alt[1]) / 2
        ax.annotate("", (a["u0"], vv), (a["u1"], vv), arrowprops=dict(arrowstyle="<->", lw=0.6, color="#b91c1c"),
                    zorder=9)
        ax.text((a["u0"] + a["u1"]) / 2, vv + 0.6, f"{BLOK_ARA:.2f}".replace(".", ","), ha="center",
                fontsize=6, color="#b91c1c", zorder=9)
    for m in MAH:   # balkon yan duvarları zemindeki teras duvarıyla aynı izde, ayrıca çizilmez
        if m["tip"] != "balkon":
            draw_poly(ax, m["poly"], facecolor=C["mah"], edgecolor="none", zorder=6)
    for v in villas:
        for bk in ("balkon", "balkon_on"):
            bx = list(v[bk].exterior.coords)
            ax.plot([p[0] for p in bx], [p[1] for p in bx], ls=(0, (2, 1.5)), lw=0.5, color=C["ev"], zorder=5)
        c = v["ev"].centroid
        ax.text(c.x, c.y, f"V{v['no']}", ha="center", va="center", fontsize=6.2,
                fontweight="bold", color=C["yazi"], rotation=90, zorder=6)
        pc = v["park"].centroid
        ax.text(pc.x, pc.y, "P", ha="center", va="center", fontsize=4.5, color="white", zorder=6)
    draw_poly(ax, YOL_POLY, facecolor=C["yol"], edgecolor="#78716c", lw=0.5, zorder=2)
    ym = (yol[0] + yol[1]) / 2
    ax.plot([PARSEL.bounds[0], PARSEL.bounds[2]], [ym, ym], ls=(0, (6, 4)), lw=0.5, color="white", zorder=3)
    ax.text(X_ALT + L_ALT / 2, ym, f"SİTE İÇİ YOL  ({YOL:.0f} m)", ha="center", va="center", fontsize=7,
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
        tt = 0.5
        if yol[0] - 3 < (a[1] + b[1]) / 2 < yol[1] + 3:     # yol ağzındaki kenar: ölçüyü kaydır
            tt = 0.8 if a[1] < b[1] else 0.2
        mx_, my_ = a[0] + (b[0] - a[0]) * tt, a[1] + (b[1] - a[1]) * tt
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L     # sola normal
        if (mx_ + nx - cen.x) ** 2 + (my_ + ny - cen.y) ** 2 < (mx_ - cen.x) ** 2 + (my_ - cen.y) ** 2:
            nx, ny = -nx, -ny
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        ax.text(mx_ + nx * 2.0, my_ + ny * 2.0, f"{L:.2f}", fontsize=5.5, color=C["parsel"],
                ha="center", va="center", rotation=ang, zorder=9)

    # ölçü: tipik villa
    v = villas[N_UST // 2]
    e = v["ev"].bounds
    ax.annotate("", (e[0], e[3] + 6.2), (e[2], e[3] + 6.2),
                arrowprops=dict(arrowstyle="<->", lw=0.5, color="#374151"))
    ax.text((e[0] + e[2]) / 2, e[3] + 6.9, f"{W:.2f}", fontsize=5.5, ha="center", color="#374151")

    # sıra etiketleri, giriş notları
    ax.text(X_UST + L_UST / 2, PARSEL.bounds[3] + 2.5, f"A SIRASI · {N_UST} VİLLA · arka bahçeler",
            fontsize=6.5, ha="center", color="#166534", zorder=9)
    ax.text(X_ALT + L_ALT / 2, alt[0] - BALKON - 1.6, f"B SIRASI · {N_ALT} VİLLA · arka bahçeler",
            fontsize=6.5, ha="center", color="#166534", zorder=9)
    gx1 = YOL_POLY.bounds[2]
    ax.annotate("SİTE GİRİŞİ", (gx1 - 1.0, ym), (gx1 + 9.5, ym), fontsize=7.5, color="#b91c1c",
                fontweight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#b91c1c", lw=1.4), zorder=10)
    if CEP:
        cc = CEP_POLY.centroid
        ax.text(cc.x + 1.0, (alt_otp[0] + alt_otp[1]) / 2, "DÖNÜŞ\nCEBİ", fontsize=6, ha="center",
                va="center", color="#44403c", zorder=6)

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
    fig.text(20 / 420, 1 - 9 / 297, (f"VAZİYET PLANI (ÖN ÇALIŞMA): {len(villas)} VİLLA, {len(BLOK_UST) + len(BLOK_ALT)} BLOK · VARYANT {VARYANT}"
              if ARALAR else f"VAZİYET PLANI (ÖN ÇALIŞMA): {len(villas)} BİTİŞİK VİLLA · VARYANT {VARYANT}"), fontsize=15,
             fontweight="bold", color="#111827")
    fig.text(20 / 420, 1 - 14.5 / 297,
             f"{kml_data('İl')} / {kml_data('İlçe')} / {kml_data('Mahalle')} Mah. · "
             f"{kml_data('Ada')} Ada {PARSEL_NO} Parseller (tevhit) · Mevkii: {kml_data('Mevkii')} · "
             f"Pafta: {kml_data('Pafta')} · Varyant {VARYANT}: {VARYANT_ACIKLAMA}",
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
    items = [(C["ev_fill"], C["ev"], "Villa (taban oturumu), kesikli: 1. kat ön ve arka balkon"),
             (C["park"], "#78716c", "Otopark (villa önü, 2,6 × 5,0 m)"),
             (C["otopark"], "#a8a29e", "Villa ön bahçesi / araç girişi"),
             (C["yol"], "#78716c", "Site içi yol"),
             (C["bahce"], "#86efac", "Villa özel bahçesi"),
             (C["ortak"], "none", "Ortak yeşil / artık alan"),
             ("#cbd5e1", "#64748b", "Misafir otoparkı (M)"),
             (C["mah"], C["mah"], "Mahremiyet duvarı (h: teras {}, bahçe {}, giriş {} m) + 1. kat balkon yan duvarı"
              .format(*(f"{h:.1f}".replace(".", ",") for h in (MAH_H_TERAS, MAH_H_BAHCE, MAH_H_ON))))]
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
        "2. Sınır TKGM KML'lerinden alınmış, 1 ve 2 parseller birleştirilmiştir.",
        f"    Koordinat yuvarlaması: çizim {geo_alan:,.0f} m², tapu {tapu_alan:,.0f} m².",
        "3. Site girişi sağ (kuzeydoğu) uçtan; yol sol uçta çıkmaz.",
        ("    Sol uçta 16 m × 6 m dönüş cebi bırakılmıştır." if CEP else
         "    Dönüş cebi YOK: itfaiye erişimi için uygun değildir."),
        (f"4. Bloklar arası {BLOK_ARA:.0f} m: önde 2 misafir otoparkı, arkada" if ARALAR else
         f"4. Villalar kesintisiz iki blok ({N_UST}+{N_ALT}); misafir otoparkı"),
        ("    uç villaların yan bahçeleri (ortada mahremiyet duvarı)." if ARALAR else
         "    ve ortak alan için yer kalmıyor."),
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
              "BALKON": 30, "BAHCE": 3, "ORTAK_ALAN": 82, "YAZI": 7, "MAHREMIYET_DUVARI": 251,
              "MAHREMIYET_BALKON": 251, "MISAFIR_OTOPARK": 5}
    for n, col in layers.items():
        doc.layers.add(n, color=col)
    doc.layers.get("CEKME").dxf.linetype = "DASHDOT"
    doc.layers.get("BALKON").dxf.linetype = "DASHED"
    doc.layers.get("MAHREMIYET_BALKON").dxf.linetype = "DASHED"

    def poly(g, layer):
        for p in getattr(g, "geoms", [g]):
            if p.geom_type == "Polygon" and not p.is_empty:
                msp.add_lwpolyline([to_world(*c) for c in p.exterior.coords[:-1]], close=True,
                                   dxfattribs={"layer": layer})

    poly(PARSEL, "PARSEL")
    poly(BUILD, "CEKME")
    poly(YOL_POLY, "YOL")
    poly(ORTAK, "ORTAK_ALAN")
    for m in MAH:
        poly(m["poly"], "MAHREMIYET_BALKON" if m["tip"] == "balkon" else "MAHREMIYET_DUVARI")
    for mp in MISAFIR:
        poly(mp, "MISAFIR_OTOPARK")
    for v in villas:
        poly(v["ev"], "VILLA")
        poly(v["balkon"], "BALKON")
        poly(v["balkon_on"], "BALKON")
        poly(v["otopark"], "OTOPARK")
        poly(v["park"], "PARK_YERI")
        poly(v["bahce"], "BAHCE")
        c = v["ev"].centroid
        msp.add_text(f"V{v['no']}", height=1.2, rotation=EKSEN_ACI + 90,
                     dxfattribs={"layer": "YAZI"}).set_placement(
            to_world(c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    c = PARSEL.centroid
    msp.add_text(f"{kml_data('Ada')} ADA {PARSEL_NO} PARSEL", height=2.0,
                 rotation=EKSEN_ACI, dxfattribs={"layer": "YAZI"}).set_placement(
        to_world(c.x, PARSEL.bounds[1] - 5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


if __name__ == "__main__":
    if len(sys.argv) == 1:      # varsayılan: her iki varyantı ayrı süreçte üret
        import subprocess
        for k in VARYANTLAR:
            subprocess.run([sys.executable, __file__, k], check=True)
        raise SystemExit
    ad = f"vaziyet_169-1-2_{VARYANT}"
    render(ad + ".pdf", ad + ".png")
    write_dxf(ad + ".dxf")
    print(f"--- Varyant {VARYANT}: W={W:.2f} D={D:.2f} üst arka={UST_ARKA} A x0={X_UST} B x0={X_ALT}")
    for k, v in ozet:
        print(f"{k:24s} {v}")
