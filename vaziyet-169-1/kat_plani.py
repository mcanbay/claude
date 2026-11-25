# -*- coding: utf-8 -*-
"""
4+1 tip villa kat planları (Varyant B: 6,60 × 11,00 m, zemin + 1 kat)

Çıktılar:
  kat_plani_4+1.pdf / .png   A2 yatay, 1/50 ölçek: zemin kat, 1. kat, metraj tablosu
  kat_plani_4+1.dxf          CAD çizimi (yerel koordinat, metre; köken: villanın ön-sol aks köşesi)

Koordinatlar: x = cephe boyunca (0 ve 6,60 yangın duvarı aksları), y = derinlik (0 ön/yol cephesi,
11,00 arka/bahçe cephesi). Yangın duvarları aksa ortalı 25 cm, ön ve arka dış duvarlar 25 cm,
iç bölmeler 10 cm. Plan girişi sağda olan villa içindir; komşu tip bunun aynalanmışıdır.
"""
import math

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Arc
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

GEN, DER = 6.60, 11.00           # aks ölçüleri
YD, DD = 0.125, 0.25             # yangın duvarı yarı kalınlığı, dış duvar kalınlığı
KAT_H = 3.15
SUBASMAN = 0.45                  # zemin kat döşeme kotu (±0,00 bahçe / otopark)
BALKON_ON, BALKON_ARKA = 1.60, 1.50
BRUT_HEDEF = 165.0


def B(x0, y0, x1, y1):
    """iç ölçü çerçevesinden (0..6,35 × 0..10,50) aks çerçevesine"""
    return box(x0 + YD, y0 + DD, x1 + YD, y1 + DD)


def P(x, y):
    return (x + YD, y + DD)


# ------------------------------------------------------------------ mahaller
# (ad, kutu(lar), net alana dahil mi). Aynı "grup" değerine sahip mahaller arasında duvar yoktur.
ZEMIN = [
    dict(ad="MİSAFİR / ÇALIŞMA\nODASI (YATAK 4)", kisa="Misafir/çalışma (yatak 4)", g=[B(0, 0, 3.10, 3.40)]),
    dict(ad="WC / DUŞ", kisa="WC / duş", g=[B(3.20, 0, 4.45, 2.20)]),
    dict(ad="KİLER", kisa="Kiler", g=[B(3.20, 2.30, 4.45, 3.40)]),
    dict(ad="ANTRE", kisa="Antre", g=[B(4.55, 0, 6.35, 3.40)], grup="acik"),
    dict(ad="HOL", kisa="Hol", g=[B(3.10, 3.50, 6.35, 4.40), B(4.55, 3.40, 6.35, 3.50)], grup="acik"),
    dict(ad="AMERİKAN\nMUTFAK", kisa="Amerikan mutfak", g=[B(0, 3.50, 3.10, 6.70)], grup="acik"),
    dict(ad="SALON + YEMEK", kisa="Salon + yemek", g=[B(0, 6.70, 6.35, 10.50)], grup="acik"),
    dict(ad="MERDİVEN", kisa="Merdiven", g=[B(3.10, 4.40, 6.35, 6.60)], grup="acik", etiket=False),
]
KAT1 = [
    dict(ad="YATAK ODASI 2", kisa="Yatak odası 2", g=[B(0, 0, 3.10, 3.40)]),
    dict(ad="YATAK ODASI 3", kisa="Yatak odası 3", g=[B(3.20, 0, 6.35, 3.40)]),
    dict(ad="BANYO", kisa="Banyo (ortak)", g=[B(0, 3.50, 1.75, 6.60)]),
    dict(ad="HOL", kisa="Hol", g=[B(1.85, 3.50, 3.10, 6.60), B(3.10, 3.50, 6.35, 4.40)], grup="hol"),
    dict(ad="MERDİVEN", kisa="Merdiven", g=[B(3.10, 4.40, 6.35, 6.60)], grup="hol", etiket=False),
    dict(ad="EBEVEYN\nYATAK ODASI", kisa="Ebeveyn yatak odası", g=[B(0, 6.70, 3.80, 10.50)]),
    dict(ad="GİYİNME\nODASI", kisa="Giyinme odası", g=[B(3.90, 6.70, 6.35, 8.40)]),
    dict(ad="EBEVEYN\nBANYOSU", kisa="Ebeveyn banyosu", g=[B(3.90, 8.50, 6.35, 10.50)]),
]


# ------------------------------------------------------------------ kapı / pencere tanımları
def kapi(hx, hy, kapali, acik, w, surgu=False):
    """hx,hy: menteşe (iç çerçeve); kapali: duvar boyunca birim vektör; acik: açılma yönü"""
    return dict(h=P(hx, hy), k=kapali, a=acik, w=w, surgu=surgu)


ZEMIN_KAPI = [
    kapi(6.15, 0.0, (-1, 0), (0, 1), 1.00),                 # dış kapı (antreye)
    kapi(3.00, 3.40, (-1, 0), (0, -1), 0.80),               # misafir odası
    kapi(4.45, 1.95, (0, -1), (1, 0), 0.75),                # WC / duş (antreye açılır)
    kapi(4.15, 3.40, (-1, 0), (0, -1), 0.70),               # kiler
]
KAT1_KAPI = [
    kapi(3.00, 3.40, (-1, 0), (0, -1), 0.80),               # yatak 2
    kapi(4.00, 3.40, (1, 0), (0, -1), 0.80),                # yatak 3
    kapi(1.75, 5.35, (0, -1), (-1, 0), 0.75),               # banyo
    kapi(2.10, 6.60, (1, 0), (0, 1), 0.85),                 # ebeveyn
    kapi(3.80, 7.00, (0, 1), (1, 0), 0.80),                 # giyinme
    kapi(4.10, 8.40, (1, 0), (0, 1), 0.75),                 # ebeveyn banyosu
]
# pencere: (cephe 'on'/'arka', x0, x1 [iç çerçeve], tür)
ZEMIN_PENC = [("on", 0.60, 2.50, "p"), ("on", 3.45, 4.20, "p"), ("arka", 0.45, 5.90, "surgu")]
KAT1_PENC = [("on", 0.50, 2.60, "surgu"), ("on", 3.75, 5.85, "surgu"),
             ("arka", 0.50, 3.30, "surgu"), ("arka", 4.55, 5.75, "p")]


def cephe_aciklari(cephe):
    """Cephedeki açıklıklar, plan aks koordinatında (x: 0..6,60, girişi sağda olan tip) ve kotlarıyla.
    Görünüş, 3B model ve kat planı aynı tanımı kullanır. Döner: dict(x0, x1, z0, z1, tur)
    tur: 'kapi' (dış kapı), 'surgu' (sürme cam kapı / balkon kapısı), 'pencere', 'yuksek' (WC/banyo)."""
    out = []
    for kat, liste in ((0, ZEMIN_PENC), (1, KAT1_PENC)):
        zf = SUBASMAN + kat * KAT_H
        for c, x0, x1, tur in liste:
            if c != cephe:
                continue
            if tur == "surgu":
                z0, z1, t = zf + 0.05, zf + 2.50, "surgu"
            elif (x1 - x0) < 1.0 or kat == 1:       # WC / banyo: yüksek denizlik
                z0, z1, t = zf + 1.50, zf + 2.30, "yuksek"
            else:
                z0, z1, t = zf + 0.90, zf + 2.30, "pencere"
            out.append(dict(x0=x0 + YD, x1=x1 + YD, z0=z0, z1=z1, tur=t))
    if cephe == "on":
        k = ZEMIN_KAPI[0]
        x1 = k["h"][0]
        out.append(dict(x0=x1 - k["w"], x1=x1, z0=SUBASMAN, z1=SUBASMAN + 2.35, tur="kapi"))
    return out


# ------------------------------------------------------------------ duvar kütlesi
def duvarlar(mahaller, kapilar, pencereler):
    dis = box(-YD, 0, GEN + YD, DER)
    ic_parcalar = []
    gruplar = {}
    for m in mahaller:
        u = unary_union(m["g"])
        if m.get("grup"):
            gruplar.setdefault(m["grup"], []).append(u)
        ic_parcalar.append(u)
    ic = unary_union(ic_parcalar)
    # aynı gruptaki mahaller arasındaki ince bölmeleri kaldır (açık plan)
    for g in gruplar.values():
        ic = unary_union([ic, unary_union([x.buffer(0.06, join_style=2) for x in g]).buffer(-0.06, join_style=2)])
    w = dis.difference(ic)
    kesik = []
    for k in kapilar:
        hx, hy = k["h"]
        ex, ey = hx + k["k"][0] * k["w"], hy + k["k"][1] * k["w"]
        if k["k"][0]:   # yatay duvar
            kesik.append(box(min(hx, ex), hy - 0.3, max(hx, ex), hy + 0.3))
        else:
            kesik.append(box(hx - 0.3, min(hy, ey), hx + 0.3, max(hy, ey)))
    for cephe, x0, x1, _ in pencereler:
        y0, y1 = (0, DD) if cephe == "on" else (DER - DD, DER)
        kesik.append(box(x0 + YD, y0, x1 + YD, y1))
    # kapı kesikleri dış kabuğun dışına taşmasın
    return w.difference(unary_union(kesik)), ic


# ------------------------------------------------------------------ mobilya (çizgi/poligon listesi)
def r(x0, y0, x1, y1):
    return [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1), P(x0, y0)]


def yatak(x0, y0, w, l, yon):
    """yon: başucunun olduğu duvar 'sol'/'sag'; yatak x boyunca uzanır"""
    out = [r(x0, y0, x0 + l, y0 + w)]
    if yon == "sol":
        out += [r(x0 + 0.05, y0 + 0.1, x0 + 0.45, y0 + w / 2 - 0.05), r(x0 + 0.05, y0 + w / 2 + 0.05, x0 + 0.45, y0 + w - 0.1)]
        out += [r(x0 + 0.55, y0, x0 + 0.55, y0 + w)]
    else:
        e = x0 + l
        out += [r(e - 0.45, y0 + 0.1, e - 0.05, y0 + w / 2 - 0.05), r(e - 0.45, y0 + w / 2 + 0.05, e - 0.05, y0 + w - 0.1)]
        out += [r(e - 0.55, y0, e - 0.55, y0 + w)]
    return out


def dolap(x0, y0, x1, y1):
    out = [r(x0, y0, x1, y1)]
    out.append([P(x0, y0), P(x1, y1)])
    return out


def wc(x, y, yon):
    """klozet; yon: duvarın olduğu taraf ('sol','sag','alt','ust')"""
    if yon in ("sol", "sag"):
        s = 1 if yon == "sol" else -1
        bx0 = x if yon == "sol" else x - 0.2
        out = [r(bx0, y - 0.2, bx0 + 0.2, y + 0.2)]
        cx = x + s * 0.45
        out.append([P(cx + 0.25 * math.cos(t) * s, y + 0.18 * math.sin(t)) for t in [i / 20 * 2 * math.pi for i in range(21)]])
        return out
    s = 1 if yon == "alt" else -1
    by0 = y if yon == "alt" else y - 0.2
    out = [r(x - 0.2, by0, x + 0.2, by0 + 0.2)]
    cy = y + s * 0.45
    out.append([P(x + 0.18 * math.cos(t), cy + 0.25 * math.sin(t) * s) for t in [i / 20 * 2 * math.pi for i in range(21)]])
    return out


def lavabo(x0, y0, x1, y1):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2 - 0.08, (y1 - y0) / 2 - 0.08
    return [r(x0, y0, x1, y1), [P(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in [i / 20 * 2 * math.pi for i in range(21)]]]


def dus(x0, y0, x1, y1):
    return [r(x0, y0, x1, y1), [P(x0, y0), P(x1, y1)], [P(x0, y1), P(x1, y0)]]


def kuvet(x0, y0, x1, y1):
    return [r(x0, y0, x1, y1), r(x0 + 0.08, y0 + 0.08, x1 - 0.08, y1 - 0.08)]


def cizgi(*pts):
    return [P(*p) for p in pts]


def merdiven(kat):
    """U dönüşlü merdiven: kol genişliği 1,05 m, 2 × 9 rıht (17,5 cm), basamak 27 cm.
    1. kol (arka, y 5,55–6,60) zeminden x=3,10'da başlar, +x yönünde sahanlığa (x 5,30–6,35) çıkar;
    2. kol (ön, y 4,40–5,45) sahanlıktan -x yönünde x=3,10'da 1. kata varır."""
    out, kesik = [], []
    x0, xs = 3.10, 3.10 + 8 * 0.27        # sahanlık başlangıcı ≈ 5,26
    for i in range(9):
        x = x0 + i * 0.27
        out.append(cizgi((x, 5.55), (x, 6.60)) if kat == 0 else [])
        kesik.append(cizgi((x, 5.55), (x, 6.60)))
        out.append(cizgi((x, 4.40), (x, 5.45)))
    out.append(cizgi((x0, 5.45), (xs, 5.45)))
    out.append(cizgi((x0, 5.55), (xs, 5.55)))
    out.append(cizgi((xs, 4.40), (xs, 6.60)))
    if kat == 0:
        kesik = []
    else:
        out = [o for o in out if o]
    return out, kesik


ZEMIN_MOB = (
    yatak(0.0, 1.00, 1.40, 2.00, "sol") + dolap(0.0, 2.80, 2.00, 3.40)
    + dolap(2.50, 0.0, 3.10, 1.20)                                      # çalışma masası
    + wc(3.20, 1.40, "sol") + lavabo(3.75, 1.65, 4.45, 2.20) + dus(3.20, 0.0, 4.10, 0.90)
    + dolap(5.95, 1.20, 6.35, 3.30)                                     # vestiyer / ayakkabılık
    + dolap(3.20, 2.30, 3.60, 3.40)                                     # kiler rafı
    # mutfak: L tezgah, buzdolabı, ocak, eviye
    + [r(0.0, 3.50, 0.62, 6.70), r(0.62, 3.50, 2.05, 4.12)] + dolap(0.0, 3.50, 0.70, 4.20)
    + [r(0.10, 4.90, 0.55, 5.50)] + lavabo(0.08, 5.80, 0.56, 6.40)
    # yemek masası (6 kişilik) ve sandalyeler
    + [r(0.90, 7.20, 1.80, 9.00)]
    + sum([[r(0.45, y, 0.85, y + 0.4), r(1.85, y, 2.25, y + 0.4)] for y in (7.35, 7.90, 8.45)], [])
    # oturma grubu: kanepe (sırtı merdiven duvarına), sehpa, berjerler
    + [r(3.40, 6.70, 6.20, 7.60), r(3.40, 6.70, 6.20, 6.95), r(4.20, 8.10, 5.40, 8.70),
       r(3.40, 9.20, 4.20, 9.90), r(5.40, 9.20, 6.20, 9.90)]

)
KAT1_MOB = (
    yatak(0.0, 1.00, 1.20, 2.00, "sol") + dolap(0.0, 2.80, 2.10, 3.40) + dolap(2.50, 0.30, 3.10, 1.50)
    + yatak(4.35, 1.00, 1.20, 2.00, "sag") + dolap(4.90, 2.80, 6.35, 3.40) + dolap(3.20, 0.30, 3.80, 1.50)
    + lavabo(0.0, 3.60, 0.55, 4.40) + wc(0.0, 4.95, "sol") + kuvet(0.0, 5.85, 1.75, 6.60)
    + dolap(5.55, 3.50, 6.35, 4.40)                                     # çamaşır / keten dolabı
    + yatak(0.0, 7.75, 1.60, 2.10, "sol") + [r(0.0, 7.25, 0.45, 7.70), r(0.0, 9.40, 0.45, 9.85)]
    + dolap(5.75, 6.70, 6.35, 8.40) + dolap(4.75, 6.70, 5.75, 7.30)      # giyinme dolapları (L)
    + [r(3.90, 9.35, 4.80, 10.50)] + dus(5.25, 9.30, 6.35, 10.50)        # çift lavabo tezgahı, duş
    + wc(5.80, 8.50, "alt")
)

# ------------------------------------------------------------------ metraj
def alan(m):
    return unary_union(m["g"]).area


def metraj(mahaller):
    return [(m["kisa"], alan(m)) for m in mahaller]


MZ, M1 = metraj(ZEMIN), metraj(KAT1)
BRUT_KAT = GEN * DER
BAL_ON = (GEN - 0.20) * BALKON_ON
BAL_ARKA = (GEN - 0.20) * BALKON_ARKA


def tr(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ çizim
INK = "#1c1917"
POCHE = "#3f3a36"
FILL = {"acik": "#faf6ee"}


def ciz_kat(ax, baslik, mahaller, kapilar, pencereler, mobilya, kat):
    w, ic = duvarlar(mahaller, kapilar, pencereler)
    # zemin dolgusu
    for m in mahaller:
        for g in m["g"]:
            renk = "#f4efe6" if "BANYO" in m["ad"] or "WC" in m["ad"] else "#fbf8f2"
            ax.add_patch(MPoly(list(g.exterior.coords), closed=True, fc=renk, ec="none", zorder=0))
    # balkonlar
    if kat == 1:
        for y0, y1, ad, a in ((-BALKON_ON, 0, "ÖN BALKON", BAL_ON), (DER, DER + BALKON_ARKA, "ARKA BALKON", BAL_ARKA)):
            bp = box(0.10, y0, GEN - 0.10, y1)
            ax.add_patch(MPoly(list(bp.exterior.coords), closed=True, fc="#eef2f3", ec=INK, lw=0.6, zorder=1))
            ye = y0 + 0.04 if y0 < 0 else y1 - 0.04
            ax.plot([0.12, GEN - 0.12], [ye, ye], color="#5b8aa6", lw=1.4, zorder=2)        # cam korkuluk
            ax.text(GEN / 2, (y0 + y1) / 2, f"{ad}\n{tr(a)} m²", ha="center", va="center", fontsize=7.5, color=INK)
            for fx in (-0.10, GEN - 0.10):                                                       # mahremiyet duvarları
                f = box(fx, min(y0, y1) - (0.10 if y0 < 0 else 0), fx + 0.20, max(y0, y1) + (0.10 if y1 > DER else 0))
                ax.add_patch(MPoly(list(f.exterior.coords), closed=True, fc=POCHE, ec="none", zorder=3))
    else:   # zemin: arka teras ve ön bahçe izi
        t = box(0.10, DER, GEN - 0.10, DER + 3.0)
        ax.add_patch(MPoly(list(t.exterior.coords), closed=True, fc="#f1ebe0", ec=INK, lw=0.4, ls=(0, (4, 2)), zorder=1))
        ax.text(GEN / 2, DER + 1.9, "TERAS (bahçe)", ha="center", va="center", fontsize=7.5, color="#57534e")
        for fx in (-0.10, GEN - 0.10):
            f = box(fx, DER, fx + 0.20, DER + 3.5)
            ax.add_patch(MPoly(list(f.exterior.coords), closed=True, fc=POCHE, ec="none", zorder=3))
        ax.text(GEN / 2, -1.2, "ÖN BAHÇE / OTOPARK", ha="center", va="center", fontsize=7.5, color="#57534e")
    # duvarlar
    for p in getattr(w, "geoms", [w]):
        ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=POCHE, ec=INK, lw=0.4, zorder=5))
        for hole in p.interiors:
            ax.add_patch(MPoly(list(hole.coords), closed=True, fc="#fbf8f2", ec=INK, lw=0.4, zorder=5))
    # yangın duvarı aksları
    for ax_x in (0, GEN):
        ax.plot([ax_x, ax_x], [-2.2 if kat else -0.6, DER + 2.2], color="#b91c1c", lw=0.5, ls=(0, (8, 2, 1, 2)), zorder=6)
    # pencereler
    for cephe, x0, x1, tur in pencereler:
        y0, y1 = (0, DD) if cephe == "on" else (DER - DD, DER)
        for yy in (y0, (y0 + y1) / 2, y1):
            ax.plot([x0 + YD, x1 + YD], [yy, yy], color=INK, lw=0.6, zorder=6)
        if tur == "surgu":
            m_ = (x0 + x1) / 2 + YD
            ax.plot([x0 + YD, m_ + 0.1], [(y0 + y1) / 2 - 0.04] * 2, color=INK, lw=1.2, zorder=6)
            ax.plot([m_ - 0.1, x1 + YD], [(y0 + y1) / 2 + 0.04] * 2, color=INK, lw=1.2, zorder=6)
    # kapılar
    for k in kapilar:
        hx, hy = k["h"]
        w_ = k["w"]
        ax.plot([hx, hx + k["a"][0] * w_], [hy, hy + k["a"][1] * w_], color=INK, lw=0.9, zorder=7)
        a0 = math.degrees(math.atan2(k["k"][1], k["k"][0]))
        a1 = math.degrees(math.atan2(k["a"][1], k["a"][0]))
        lo, hi = (a0, a1) if (a1 - a0) % 360 <= 180 else (a1, a0)
        ax.add_patch(Arc((hx, hy), 2 * w_, 2 * w_, theta1=lo, theta2=hi, color=INK, lw=0.4, zorder=7))
    # mobilya
    for pl in mobilya:
        ax.plot([p[0] for p in pl], [p[1] for p in pl], color="#78716c", lw=0.45, zorder=4)
    # merdiven
    mc, mk = merdiven(kat)
    for pl in mc:
        ax.plot([p[0] for p in pl], [p[1] for p in pl], color=INK, lw=0.5, zorder=6)
    for pl in mk:
        ax.plot([p[0] for p in pl], [p[1] for p in pl], color=INK, lw=0.4, ls=(0, (3, 2)), zorder=6)
    if kat == 0:   # çıkış oku: 1. kol başlangıcından sahanlığa, 2. kolda kesme çizgisi
        ax.annotate("", P(5.10, 6.07), P(3.25, 6.07), arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK), zorder=8)
        ax.text(*P(3.25, 6.30), "ÇIKIŞ", fontsize=6, color=INK, zorder=8)
        ax.plot(*zip(P(4.10, 4.40), P(4.40, 5.45)), color=INK, lw=0.6, zorder=8)
        ax.text(*P(4.55, 4.62), "merdiven altı dolap", fontsize=5.5, color="#57534e", zorder=8,
                bbox=dict(fc="#fbf8f2", ec="none", pad=0.3))
        ax.plot(*zip(P(3.10, 4.40), P(6.35, 4.40)), color=INK, lw=0.4, ls=(0, (2, 2)), zorder=6)
    else:          # varış oku ve korkuluklar (boşluk kenarı)
        ax.annotate("", P(3.25, 4.92), P(5.10, 4.92), arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK), zorder=8)
        ax.text(*P(3.55, 5.12), "VARIŞ", fontsize=6, color=INK, zorder=8)
        for a, b in (((3.10, 4.40), (6.35, 4.40)), ((3.10, 5.50), (3.10, 6.60))):
            ax.plot(*zip(P(*a), P(*b)), color="#5b8aa6", lw=1.3, zorder=8)
        ax.text(*P(3.85, 6.07), "BOŞLUK", fontsize=6, color="#57534e", zorder=8)
    # mahal etiketleri
    for m in mahaller:
        if m.get("etiket", True) is False:
            continue
        g = m["g"][0] if len(m["g"]) == 1 else max(m["g"], key=lambda q: q.area)
        c = g.centroid
        dx, dy = m.get("et", (0, 0))
        bx = g.bounds
        w_, h_ = bx[2] - bx[0], bx[3] - bx[1]
        olcu = "" if len(m["g"]) > 1 else f"\n{tr(w_ , 2)} × {tr(h_, 2)}"
        ax.text(c.x + dx, c.y + dy, f"{m['ad']}\n{tr(alan(m))} m²{olcu}", ha="center", va="center",
                fontsize=7.2, color=INK, zorder=9, linespacing=1.15,
                bbox=dict(fc="#fbf8f2", ec="none", pad=0.6, alpha=0.85))
    # ölçü zincirleri
    def olcu_yatay(xs, y, txt_dy=0.18):
        ax.plot([xs[0], xs[-1]], [y, y], color=INK, lw=0.4, zorder=8)
        for x in xs:
            ax.plot([x - 0.08, x + 0.08], [y - 0.08, y + 0.08], color=INK, lw=0.7, zorder=8)
            ax.plot([x, x], [y - 0.15, y + 0.15], color=INK, lw=0.3, zorder=8)
        for a, b in zip(xs[:-1], xs[1:]):
            ax.text((a + b) / 2, y + txt_dy, f"{(b - a) * 100:.0f}", ha="center", va="bottom", fontsize=6.2, color=INK)

    def olcu_dusey(ys, x):
        ax.plot([x, x], [ys[0], ys[-1]], color=INK, lw=0.4, zorder=8)
        for y in ys:
            ax.plot([x - 0.08, x + 0.08], [y - 0.08, y + 0.08], color=INK, lw=0.7, zorder=8)
            ax.plot([x - 0.15, x + 0.15], [y, y], color=INK, lw=0.3, zorder=8)
        for a, b in zip(ys[:-1], ys[1:]):
            ax.text(x - 0.18, (a + b) / 2, f"{(b - a) * 100:.0f}", ha="right", va="center", fontsize=6.2,
                    color=INK, rotation=90)

    yb = -2.3 if kat else -2.0
    olcu_yatay([0, GEN], yb - 0.7)
    olcu_yatay([0, YD + 3.10, YD + 3.20, YD + 4.45, YD + 4.55, GEN] if kat == 0 else
               [0, YD + 3.10, YD + 3.20, GEN], yb)
    olcu_dusey([0, DER], -1.6)
    olcu_dusey([0, DD + 3.40, DD + 3.50, DD + 6.60, DD + 6.70, DER], -0.9)
    ax.text(GEN / 2, DER + 4.1, baslik, ha="center", va="bottom", fontsize=13, fontweight="bold", color=INK)
    ax.text(GEN / 2, DER + 3.45, "BAHÇE CEPHESİ", ha="center", va="bottom", fontsize=6.5, color="#57534e")
    ax.text(GEN / 2, yb - 1.45, "YOL / OTOPARK CEPHESİ", ha="center", va="top", fontsize=6.5, color="#57534e")


def render(pdf, png):
    A2 = (594 / 25.4, 420 / 25.4)
    fig = plt.figure(figsize=A2)
    MM = 20.0          # 1/50: 1 m = 20 mm
    # çizim pencereleri (metre cinsinden kapsam)
    x_min, x_max = -2.4, GEN + 1.0
    y_min, y_max = -4.4, DER + 5.3
    wmm, hmm = (x_max - x_min) * MM, (y_max - y_min) * MM
    for i, (bas, mah, kap, pen, mob) in enumerate((
            ("ZEMİN KAT PLANI", ZEMIN, ZEMIN_KAPI, ZEMIN_PENC, ZEMIN_MOB),
            ("1. KAT PLANI", KAT1, KAT1_KAPI, KAT1_PENC, KAT1_MOB))):
        left = 18 + i * (wmm + 8)
        ax = fig.add_axes([left / 594, (420 - 30 - hmm) / 420, wmm / 594, hmm / 420])
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect("equal")
        ax.axis("off")
        ciz_kat(ax, bas, mah, kap, pen, mob, i)

    fig.text(18 / 594, 1 - 14 / 420, "TİP VİLLA 4+1 · KAT PLANLARI (ÖN ÇALIŞMA)", fontsize=18, fontweight="bold", color=INK)
    fig.text(18 / 594, 1 - 21 / 420,
             "Bursa / Nilüfer / İrfaniye Mah. · 169 Ada 1 + 2 Parseller · Varyant B · villa 6,60 × 11,00 m, zemin + 1 kat",
             fontsize=10, color="#44403c")

    # metraj tablosu
    tx = (18 + 2 * (wmm + 8) + 4) / 594
    ty = 1 - 34 / 420
    lh = 5.0 / 420
    fig.text(tx, ty, "METRAJ (net alanlar)", fontsize=11, fontweight="bold", color=INK)
    y = ty - 1.6 * lh
    cw = 52 / 594

    def satir(a, b, bold=False, renk=INK):
        nonlocal y
        fig.text(tx, y, a, fontsize=8.2, color=renk, fontweight="bold" if bold else "normal")
        fig.text(tx + cw, y, b, fontsize=8.2, color=renk, ha="right", fontweight="bold" if bold else "normal",
                 family="DejaVu Sans Mono")
        y -= lh

    for bas, mm in (("ZEMİN KAT", MZ), ("1. KAT", M1)):
        satir(bas, "m²", bold=True)
        for ad, a in mm:
            satir("  " + ad, tr(a))
        satir("  Net toplam", tr(sum(a for _, a in mm)), bold=True)
        satir("  Brüt (aks içi)", tr(BRUT_KAT))
        y -= 0.5 * lh
    satir("BALKONLAR", "", bold=True)
    satir("  Ön balkon (1. kat)", tr(BAL_ON))
    satir("  Arka balkon (1. kat)", tr(BAL_ARKA))
    y -= 0.5 * lh
    net = sum(a for _, a in MZ) + sum(a for _, a in M1)
    brut = 2 * BRUT_KAT + BAL_ON + BAL_ARKA
    satir("TOPLAM", "", bold=True)
    satir("  Net kapalı alan", tr(net))
    satir("  Brüt kapalı alan", tr(2 * BRUT_KAT))
    satir("  Brüt + balkonlar", tr(brut), bold=True)
    y -= lh
    fig.text(tx, y, "NOTLAR", fontsize=11, fontweight="bold", color=INK)
    y -= 1.4 * lh
    notlar = [
        "Ölçüler cm, alanlar m². Ölçek 1/50 (A2).",
        "Duvar: yangın duvarı aksa ortalı 25 cm,",
        "dış duvar 25 cm, iç bölme 10 cm.",
        "Kat yüksekliği 315 cm. Merdiven U dönüşlü,",
        "2 × 9 rıht 17,5 cm, basamak 27 cm, kol 105 cm.",
        "Plan girişi sağda olan villa içindir;",
        "komşu villa aynalanmış tiptir.",
        "Bahçe, teras ve balkon kenarındaki koyu",
        "parçalar mahremiyet duvarlarıdır.",
        "Banyo/WC havalandırması mekaniktir",
        "(ortak banyo penceresizdir).",
        "Ön çalışmadır; statik ve tesisat projesiyle",
        "değişebilir.",
    ]
    for n in notlar:
        fig.text(tx, y, n, fontsize=7.6, color="#44403c")
        y -= 0.85 * lh
    fig.text(1 - 14 / 594, 8 / 420, "Ölçek 1/50 · A2", fontsize=8, ha="right", color="#78716c")
    fig.savefig(pdf)
    fig.savefig(png, dpi=150)
    plt.close(fig)
    return net, brut


# ------------------------------------------------------------------ DXF
def write_dxf(path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    for n, c in {"DUVAR": 7, "KAPI": 4, "PENCERE": 5, "MOBILYA": 8, "MERDIVEN": 7, "MAHAL": 3,
                 "BALKON": 30, "AKS": 1}.items():
        doc.layers.add(n, color=c)
    doc.layers.get("AKS").dxf.linetype = "DASHDOT"
    for i, (mah, kap, pen, mob) in enumerate(((ZEMIN, ZEMIN_KAPI, ZEMIN_PENC, ZEMIN_MOB),
                                              (KAT1, KAT1_KAPI, KAT1_PENC, KAT1_MOB))):
        ox = i * (GEN + 6)            # iki kat yan yana

        def T(p):
            return (p[0] + ox, p[1])
        w, _ = duvarlar(mah, kap, pen)
        for p in getattr(w, "geoms", [w]):
            msp.add_lwpolyline([T(c) for c in p.exterior.coords], close=True, dxfattribs={"layer": "DUVAR"})
            h = msp.add_hatch(color=8, dxfattribs={"layer": "DUVAR"})
            h.paths.add_polyline_path([T(c) for c in p.exterior.coords[:-1]], is_closed=True)
        for k in kap:
            hx, hy = k["h"]
            msp.add_line(T((hx, hy)), T((hx + k["a"][0] * k["w"], hy + k["a"][1] * k["w"])), dxfattribs={"layer": "KAPI"})
            a0 = math.degrees(math.atan2(k["k"][1], k["k"][0]))
            a1 = math.degrees(math.atan2(k["a"][1], k["a"][0]))
            lo, hi = (a0, a1) if (a1 - a0) % 360 <= 180 else (a1, a0)
            msp.add_arc(T((hx, hy)), k["w"], lo, hi, dxfattribs={"layer": "KAPI"})
        for cephe, x0, x1, _ in pen:
            y0, y1 = (0, DD) if cephe == "on" else (DER - DD, DER)
            for yy in (y0, (y0 + y1) / 2, y1):
                msp.add_line(T((x0 + YD, yy)), T((x1 + YD, yy)), dxfattribs={"layer": "PENCERE"})
        for pl in mob:
            msp.add_lwpolyline([T(p) for p in pl], dxfattribs={"layer": "MOBILYA"})
        mc, mk = merdiven(i)
        for pl in mc + mk:
            msp.add_lwpolyline([T(p) for p in pl], dxfattribs={"layer": "MERDIVEN"})
        for m in mah:
            if m.get("etiket", True) is False:
                continue
            g = max(m["g"], key=lambda q: q.area)
            c = g.centroid
            msp.add_text(f"{m['ad'].replace(chr(10), ' ')} {tr(alan(m))} m2", height=0.16,
                         dxfattribs={"layer": "MAHAL"}).set_placement(
                T((c.x, c.y)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        for ax_x in (0, GEN):
            msp.add_line(T((ax_x, -2)), T((ax_x, DER + 2)), dxfattribs={"layer": "AKS"})
        if i == 1:
            for y0, y1 in ((-BALKON_ON, 0), (DER, DER + BALKON_ARKA)):
                msp.add_lwpolyline([T(c) for c in box(0.10, y0, GEN - 0.10, y1).exterior.coords], close=True,
                                   dxfattribs={"layer": "BALKON"})
        msp.add_text("ZEMIN KAT" if i == 0 else "1. KAT", height=0.35, dxfattribs={"layer": "MAHAL"}).set_placement(
            T((GEN / 2, DER + 3.2)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


if __name__ == "__main__":
    net, brut = render("kat_plani_4+1.pdf", "kat_plani_4+1.png")
    write_dxf("kat_plani_4+1.dxf")
    for bas, mm in (("ZEMİN", MZ), ("1. KAT", M1)):
        print(bas)
        for ad, a in mm:
            print(f"   {ad:32s} {a:6.2f}")
        print(f"   {'net toplam':32s} {sum(a for _, a in mm):6.2f}")
    print(f"balkon ön {BAL_ON:.2f} arka {BAL_ARKA:.2f}  net {net:.2f}  brüt+balkon {brut:.2f}")
