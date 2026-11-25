# -*- coding: utf-8 -*-
"""
Tip villa cephe görünüşleri (Varyant B, 4+1, 6,60 × 11,00 m, zemin + 1 kat)

Çıktılar:
  cephe_gorunusleri.pdf / .png   A1 yatay: ön, arka ve yan cephe 1/50, A sırası ön cephesi 1/200
  cephe_gorunusleri.dxf          CAD çizimi (metre; her görünüş ayrı yerde)

Açıklıklar kat_plani.cephe_aciklari()'ndan gelir; 3B model de aynı tanımı kullanır.
Kotlar: ±0,00 bahçe / otopark, +0,45 zemin kat döşemesi, +3,60 1. kat döşemesi, +6,75 saçak, +8,40 mahya.
"""
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MPoly

import kat_plani as KP

GEN, DER = KP.GEN, KP.DER
SUB, KAT = KP.SUBASMAN, KP.KAT_H
SACAK = SUB + 2 * KAT                       # 6,75
EGIM, TASMA, CATI_KAL = 0.30, 0.50, 0.18
MAHYA = SACAK + DER / 2 * EGIM              # 8,40
SACAK_UC = SACAK - TASMA * EGIM             # 6,60 (saçak ucu alt kotu)
YD_TEPE = MAHYA + 0.45                      # yangın duvarı tepe kotu
BAL_ALT, BAL_UST = SUB + KAT - 0.20, SUB + KAT          # balkon döşemesi
KORK = 1.00
BANT = (SUB + KAT - 0.05, SUB + KAT + 0.25)             # kat bandı
H_GIRIS, H_TERAS, H_BAHCE = 1.40, 2.40, 1.90

R = dict(siva="#efe9df", bant="#d8ccb8", sub="#8d8780", cati="#a9563c", cati_cizgi="#7e3c28",
         cam="#a9bfcc", kapi="#45484c", kork="#cfe2ea", perde="#cdbfa8", perde_kenar="#8a7b66",
         kont="#1c1917", zemin="#57534e", soluk="#a8a29e")

DXF = []      # (katman, [(x, z), ...], kapalı)  — her görünüşün öteleme ile eklenir


# ------------------------------------------------------------------ çizim yardımcıları
class Gorunus:
    """Bir görünüşün çizim tuvali: matplotlib ekseni + DXF ötelemesi"""

    def __init__(self, ax, dx, soluk=False):
        self.ax, self.dx, self.soluk = ax, dx, soluk

    def kutu(self, x0, z0, x1, z1, fc, ec=None, lw=0.5, z=1, alpha=1.0, hatch=None, katman="CEPHE"):
        ec = ec or R["kont"]
        if self.soluk:
            ec, alpha = R["soluk"], alpha * 0.45
        self.ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha,
                                    hatch=hatch))
        DXF.append((katman, [(x0 + self.dx, z0), (x1 + self.dx, z0), (x1 + self.dx, z1), (x0 + self.dx, z1)], True))

    def poly(self, pts, fc, ec=None, lw=0.5, z=1, katman="CEPHE", hatch=None):
        ec = ec or R["kont"]
        alpha = 1.0
        if self.soluk:
            ec, alpha = R["soluk"], 0.45
        self.ax.add_patch(MPoly(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, hatch=hatch))
        DXF.append((katman, [(x + self.dx, y) for x, y in pts], True))

    def cizgi(self, pts, lw=0.4, z=2, renk=None, ls="-", katman="CEPHE"):
        renk = R["soluk"] if self.soluk else (renk or R["kont"])
        self.ax.plot([p[0] for p in pts], [p[1] for p in pts], color=renk, lw=lw, zorder=z, ls=ls)
        DXF.append((katman, [(x + self.dx, y) for x, y in pts], False))


def aciklik(g, ac, ayna, x_off, olcek=1.0):
    x0, x1 = (GEN - ac["x1"], GEN - ac["x0"]) if ayna else (ac["x0"], ac["x1"])
    x0, x1 = x0 + x_off, x1 + x_off
    z0, z1 = ac["z0"], ac["z1"]
    lw = 0.7 * olcek
    if ac["tur"] == "kapi":
        g.kutu(x0, z0, x1, z1, R["kapi"], lw=lw, z=3, katman="DOGRAMA")
        g.kutu(x0 + 0.38, z0 + 0.55, x1 - 0.38, z1 - 0.15, R["cam"], lw=0.3 * olcek, z=4, katman="DOGRAMA")
        hx = x0 + 0.12 if ayna else x1 - 0.12
        g.cizgi([(hx, z0 + 1.0), (hx, z0 + 1.25)], lw=1.2 * olcek, z=5, renk="#d6d3d1", katman="DOGRAMA")
        return
    g.kutu(x0, z0, x1, z1, R["cam"], lw=lw, z=3, katman="DOGRAMA")
    # kayıt (orta kayıtlar) ve cam yansıması
    if ac["tur"] == "surgu":
        n = max(2, round((x1 - x0) / 1.4))
        for i in range(1, n):
            xm = x0 + (x1 - x0) * i / n
            g.cizgi([(xm, z0), (xm, z1)], lw=0.5 * olcek, z=4, katman="DOGRAMA")
    elif ac["tur"] == "pencere":
        xm = (x0 + x1) / 2
        g.cizgi([(xm, z0), (xm, z1)], lw=0.5 * olcek, z=4, katman="DOGRAMA")
        g.cizgi([(x0, z1 - 0.45), (x1, z1 - 0.45)], lw=0.35 * olcek, z=4, katman="DOGRAMA")
    else:   # yüksek (buzlu cam)
        g.cizgi([(x0, (z0 + z1) / 2), (x1, (z0 + z1) / 2)], lw=0.3 * olcek, z=4, katman="DOGRAMA")
    if olcek >= 1 and not g.soluk:
        w, h = x1 - x0, z1 - z0
        g.ax.plot([x0 + 0.15 * w, x0 + 0.15 * w + 0.35 * h], [z0 + 0.25 * h, z0 + 0.6 * h], color="white", lw=0.5,
                  alpha=0.8, zorder=4)
        g.ax.plot([x0 + 0.25 * w, x0 + 0.25 * w + 0.25 * h], [z0 + 0.25 * h, z0 + 0.5 * h], color="white", lw=0.5,
                  alpha=0.8, zorder=4)


def villa_on_arka(g, x_off, cephe, ayna, sol_uc=False, sag_uc=False, olcek=1.0, giris_duvari=()):
    """Tek villanın ön veya arka görünüşü. ayna: görünüşte kapı solda mı (aynalanmış tip).
    sol_uc/sag_uc: sıranın ucu (çatı yandan taşar, yangın duvarı başlığı yok)."""
    x0, x1 = x_off, x_off + GEN
    lw = 0.6 * olcek
    # çatı (saçak ucu kotundan mahyaya görünen yüzey)
    cx0, cx1 = x0 - (0.30 if sol_uc else 0), x1 + (0.30 if sag_uc else 0)
    g.kutu(cx0, SACAK_UC + CATI_KAL, cx1, MAHYA + CATI_KAL, R["cati"], lw=lw, z=2, katman="CATI")
    if olcek >= 1:
        z = SACAK_UC + CATI_KAL + 0.22
        while z < MAHYA + CATI_KAL - 0.05:
            g.cizgi([(cx0, z), (cx1, z)], lw=0.25, z=2, renk=R["cati_cizgi"], katman="CATI")
            z += 0.22
    g.kutu(cx0, SACAK_UC, cx1, SACAK_UC + CATI_KAL, "#6b4a3c", lw=lw, z=3, katman="CATI")       # saçak alnı
    # duvar, subasman, kat bandı
    g.kutu(x0, SUB, x1, SACAK_UC, R["siva"], lw=lw, z=1)
    g.kutu(x0, 0, x1, SUB, R["sub"], lw=lw, z=1, hatch="////" if olcek >= 1 else None)
    g.kutu(x0, BANT[0], x1, BANT[1], R["bant"], lw=0.4 * olcek, z=2)
    # açıklıklar
    for ac in KP.cephe_aciklari(cephe):
        aciklik(g, ac, ayna, x_off, olcek)
    # balkon döşemesi ve cam korkuluk (ön ve arkada, 1. katta)
    g.kutu(x0 + 0.10, BAL_ALT, x1 - 0.10, BAL_UST, "#ddd5c8", lw=lw, z=6)
    g.kutu(x0 + 0.10, BAL_UST, x1 - 0.10, BAL_UST + KORK, R["kork"], lw=0.5 * olcek, z=7, alpha=0.55,
           katman="KORKULUK")
    g.cizgi([(x0 + 0.10, BAL_UST + KORK), (x1 - 0.10, BAL_UST + KORK)], lw=0.9 * olcek, z=8, katman="KORKULUK")
    # aks üzerindeki perdeler: yangın duvarı çıkıntısı + balkon yan duvarı (mahremiyet), başlık çatı üstünde
    for ax_x, uc in ((x0, sol_uc), (x1, sag_uc)):
        if uc:
            g.kutu(ax_x - 0.10, BAL_ALT, ax_x + 0.10, SACAK_UC, R["perde"], ec=R["perde_kenar"], lw=lw, z=9,
                   katman="MAHREMIYET")
        else:
            g.kutu(ax_x - 0.12, SUB, ax_x + 0.12, SACAK_UC, R["perde"], ec=R["perde_kenar"], lw=lw, z=9,
                   katman="YANGIN_DUVARI")
            g.kutu(ax_x - 0.12, SACAK_UC, ax_x + 0.12, YD_TEPE, R["perde"], ec=R["perde_kenar"], lw=lw, z=9,
                   katman="YANGIN_DUVARI")
        # zemin: arka cephede teras duvarı her aksta; ön cephede yalnız girişlerin yan yana geldiği aksta
        if cephe == "arka":
            g.kutu(ax_x - 0.10, 0, ax_x + 0.10, H_TERAS, "#bfb19a", ec=R["perde_kenar"], lw=lw, z=10,
                   katman="MAHREMIYET")
        elif ax_x in giris_duvari:
            g.kutu(ax_x - 0.10, 0, ax_x + 0.10, H_GIRIS, "#bfb19a", ec=R["perde_kenar"], lw=lw, z=10,
                   katman="MAHREMIYET")


def insan(g, x, renk="#78716c"):
    """1,75 m ölçek figürü"""
    pts = [(x - 0.11, 0), (x - 0.06, 0.85), (x - 0.22, 0.88), (x - 0.24, 1.40), (x - 0.10, 1.48), (x - 0.09, 1.55),
           (x - 0.11, 1.68), (x, 1.75), (x + 0.11, 1.68), (x + 0.09, 1.55), (x + 0.10, 1.48), (x + 0.24, 1.40),
           (x + 0.22, 0.88), (x + 0.06, 0.85), (x + 0.11, 0), (x + 0.02, 0), (x, 0.80), (x - 0.02, 0)]
    g.ax.add_patch(MPoly(pts, closed=True, fc="none", ec=renk, lw=0.6, zorder=11))


def kotlar(g, x, liste, sag=True, fs=6.5):
    for z, etiket in liste:
        g.ax.plot([x - 0.18, x, x + 0.18, x - 0.18], [z + 0.25, z, z + 0.25, z + 0.25], color=R["kont"], lw=0.5,
                  zorder=12)
        g.ax.plot([x - 0.4, x + 1.3] if sag else [x - 1.3, x + 0.4], [z, z], color=R["kont"], lw=0.3, zorder=12)
        g.ax.text(x + 0.28 if sag else x - 0.28, z + 0.08, etiket, fontsize=fs, ha="left" if sag else "right",
                  va="bottom", color=R["kont"], zorder=12)


def olcu_dusey(g, x, zs, fs=6):
    g.ax.plot([x, x], [zs[0], zs[-1]], color=R["kont"], lw=0.4, zorder=12)
    for z in zs:
        g.ax.plot([x - 0.08, x + 0.08], [z - 0.08, z + 0.08], color=R["kont"], lw=0.7, zorder=12)
    for a, b in zip(zs[:-1], zs[1:]):
        g.ax.text(x - 0.15, (a + b) / 2, f"{(b - a) * 100:.0f}", fontsize=fs, rotation=90, ha="right",
                  va="center", color=R["kont"], zorder=12)


def olcu_yatay(g, z, xs, fs=6):
    g.ax.plot([xs[0], xs[-1]], [z, z], color=R["kont"], lw=0.4, zorder=12)
    for x in xs:
        g.ax.plot([x - 0.08, x + 0.08], [z - 0.08, z + 0.08], color=R["kont"], lw=0.7, zorder=12)
    for a, b in zip(xs[:-1], xs[1:]):
        g.ax.text((a + b) / 2, z + 0.12, f"{(b - a) * 100:.0f}", fontsize=fs, ha="center", va="bottom",
                  color=R["kont"], zorder=12)


KOTLAR = [(0.0, "±0,00"), (SUB, "+0,45"), (SUB + KAT, "+3,60"), (SACAK, "+6,75"), (MAHYA, "+8,40")]


# ------------------------------------------------------------------ görünüşler
def on_veya_arka(ax, cephe, dx):
    """Tip villa (girişi sağda) ve iki yanında komşu villaların birer parçası"""
    g = Gorunus(ax, dx)
    gs = Gorunus(ax, dx, soluk=True)
    # ön cephede tip villa girişi sağda; arkadan bakınca görünüş aynalanır
    ayna_ana = False if cephe == "on" else True
    # komşular aynalanmış tiptir; giriş duvarı: ön cephede ana villa ile sağ komşu arasında (x = 6,60)
    if cephe == "on":
        villa_on_arka(gs, -GEN, cephe, not ayna_ana)
        villa_on_arka(gs, GEN, cephe, not ayna_ana)
        villa_on_arka(g, 0, cephe, ayna_ana, giris_duvari=(GEN,))
    else:
        # arkadan bakınca sol/sağ yer değiştirir; çizim tip villayı yine 0..6,60 arasına koyar
        villa_on_arka(gs, -GEN, cephe, not ayna_ana)
        villa_on_arka(gs, GEN, cephe, not ayna_ana)
        villa_on_arka(g, 0, cephe, ayna_ana)
    ax.plot([-3.0, GEN + 3.0], [0, 0], color=R["kont"], lw=1.6, zorder=13)
    ax.add_patch(Rectangle((-3.0, -0.35), GEN + 6, 0.35, fc="#e7e2d8", ec="none", hatch="..", zorder=0))
    insan(g, 4.55 if cephe == "on" else 2.0)
    kotlar(g, -1.15, KOTLAR, sag=False)
    olcu_dusey(g, -2.05, [0, SUB, SUB + KAT, SACAK, MAHYA])
    olcu_yatay(g, -0.95, [0, GEN])
    # açıklık genişlikleri (tip villa)
    xs = []
    for ac in KP.cephe_aciklari(cephe):
        a, b = (GEN - ac["x1"], GEN - ac["x0"]) if (cephe == "arka") else (ac["x0"], ac["x1"])
        if ac["z0"] < SUB + KAT:      # zemin kat
            xs += [a, b]
    olcu_yatay(g, -0.60, sorted(set([0] + [round(x, 3) for x in xs] + [GEN])))


def yan(ax, dx):
    """Sıra sonu villanın yan (alın) cephesi: solda yol/otopark, sağda bahçe"""
    g = Gorunus(ax, dx)
    lw = 0.6
    # ön bahçe ve araç
    arac = [(-4.95, 0.30), (-4.95, 0.85), (-4.55, 0.95), (-3.85, 1.42), (-1.95, 1.45), (-1.25, 0.98),
            (-0.75, 0.90), (-0.65, 0.30)]
    ax.add_patch(MPoly(arac, closed=True, fc="#d6d3d1", ec=R["zemin"], lw=0.6, zorder=8))
    for cx in (-4.15, -1.45):
        ax.add_patch(plt.Circle((cx, 0.32), 0.32, fc="#44403c", ec="none", zorder=9))
    # çatı (beşik, mahya cepheye dik), alın üçgeni, duvar, subasman
    g.poly([(0, SACAK), (DER, SACAK), (DER / 2, MAHYA)], R["siva"], lw=lw, z=1)
    g.kutu(0, SUB, DER, SACAK, R["siva"], lw=lw, z=1)
    g.kutu(0, 0, DER, SUB, R["sub"], lw=lw, z=1, hatch="////")
    for s in (-1, 1):
        e = -TASMA if s < 0 else DER + TASMA
        g.poly([(e, SACAK_UC), (DER / 2, MAHYA), (DER / 2, MAHYA + CATI_KAL), (e, SACAK_UC + CATI_KAL)],
               R["cati"], lw=lw, z=3, katman="CATI")
    # kat bandı uçları (ön ve arka cephede, yandan kesit gibi görünür)
    for xb in (-0.12, DER):
        g.kutu(xb, BANT[0], xb + 0.12, BANT[1], R["bant"], lw=0.4, z=2)
    # balkonların yan mahremiyet duvarları (sıra sonunda da var)
    g.kutu(-(KP.BALKON_ON + 0.10), BAL_ALT, 0, SACAK_UC, R["perde"], ec=R["perde_kenar"], lw=lw, z=4,
           katman="MAHREMIYET")
    g.kutu(DER, BAL_ALT, DER + KP.BALKON_ARKA + 0.10, SACAK_UC, R["perde"], ec=R["perde_kenar"], lw=lw, z=4,
           katman="MAHREMIYET")
    # bahçe: teras duvarı 2,40 (3,50 m) ve bahçe duvarı 1,90
    g.kutu(DER, 0, DER + 3.5, H_TERAS, "#d9cfbf", ec=R["perde_kenar"], lw=lw, z=5, katman="MAHREMIYET")
    g.kutu(DER - 0.02, H_TERAS, DER + 3.52, H_TERAS + 0.06, "#9b958c", lw=0.4, z=6, katman="MAHREMIYET")
    g.kutu(DER + 3.5, 0, DER + 8.3, H_BAHCE, "#d9cfbf", ec=R["perde_kenar"], lw=lw, z=5, katman="MAHREMIYET")
    g.kutu(DER + 3.48, H_BAHCE, DER + 8.32, H_BAHCE + 0.06, "#9b958c", lw=0.4, z=6, katman="MAHREMIYET")
    ax.plot([-6.0, DER + 9.0], [0, 0], color=R["kont"], lw=1.6, zorder=13)
    ax.add_patch(Rectangle((-6.0, -0.35), DER + 15, 0.35, fc="#e7e2d8", ec="none", hatch="..", zorder=0))
    insan(g, DER + 1.6)
    kotlar(g, DER + 8.9, KOTLAR, sag=True)
    olcu_dusey(g, -5.4, [0, SUB, SUB + KAT, SACAK, MAHYA])
    olcu_yatay(g, -1.0, [-(KP.BALKON_ON + 0.10), 0, DER / 2, DER, DER + KP.BALKON_ARKA + 0.10, DER + 3.5,
                         DER + 8.3])
    ax.text(-3.0, -1.9, "YOL / OTOPARK", ha="center", fontsize=6.5, color=R["zemin"])
    ax.text(DER + 4.5, -1.9, "BAHÇE", ha="center", fontsize=6.5, color=R["zemin"])
    ax.text(DER / 2, MAHYA - 1.0, "%30", ha="center", fontsize=6.5, color=R["kont"])


def sira(ax, dx):
    """A sırası ön cephesi: 16 villa; tipler dönüşümlü aynalanır (giriş solda / sağda)"""
    g = Gorunus(ax, dx)
    n = 16
    for k in range(n):
        ayna = (k % 2 == 0)                     # çift sıradaki villada giriş solda
        giris = ((k + 1) * GEN,) if (k % 2 == 1 and k < n - 1) else ()
        villa_on_arka(g, k * GEN, "on", ayna, sol_uc=(k == 0), sag_uc=(k == n - 1), olcek=0.45,
                      giris_duvari=giris)
        ax.text(k * GEN + GEN / 2, -1.3, f"V{16 - k}", fontsize=5.5, ha="center", va="top", color=R["kont"])
    ax.plot([-2, n * GEN + 2], [0, 0], color=R["kont"], lw=1.0, zorder=13)
    olcu_yatay(g, -3.2, [0, n * GEN], fs=5.5)
    ax.text(n * GEN + 1.0, 0.2, "SİTE GİRİŞİ →", fontsize=6, color="#b91c1c", va="bottom")


# ------------------------------------------------------------------ pafta
def render(pdf, png):
    W_, H_ = 841, 594
    fig = plt.figure(figsize=(W_ / 25.4, H_ / 25.4))

    def ax_mm(left, top, xlim, zlim, olcek):
        w = (xlim[1] - xlim[0]) * 1000 / olcek
        h = (zlim[1] - zlim[0]) * 1000 / olcek
        ax = fig.add_axes([left / W_, 1 - (top + h) / H_, w / W_, h / H_])
        ax.set_xlim(*xlim)
        ax.set_ylim(*zlim)
        ax.set_aspect("equal")
        ax.axis("off")
        return ax, w, h

    fig.text(18 / W_, 1 - 14 / H_, "TİP VİLLA 4+1 · CEPHE GÖRÜNÜŞLERİ (ÖN ÇALIŞMA)", fontsize=18,
             fontweight="bold", color=R["kont"])
    fig.text(18 / W_, 1 - 21 / H_, "Bursa / Nilüfer / İrfaniye Mah. · 169 Ada 1 + 2 Parseller · Varyant B · "
             "villa 6,60 × 11,00 m, zemin + 1 kat, çatı %30 beşik", fontsize=10, color="#44403c")

    zl = (-1.2, YD_TEPE + 0.5)
    top1 = 40
    ax1, w1, h1 = ax_mm(16, top1, (-2.6, GEN + 1.2), zl, 50)
    on_veya_arka(ax1, "on", 0)
    ax2, w2, _ = ax_mm(16 + w1 + 6, top1, (-2.6, GEN + 1.2), zl, 50)
    on_veya_arka(ax2, "arka", 30)
    for left, w, ad in ((16, w1, "ÖN CEPHE (yol / otopark)"), (16 + w1 + 6, w2, "ARKA CEPHE (bahçe)")):
        fig.text((left + w / 2) / W_, 1 - (top1 - 3) / H_, ad, ha="center", fontsize=12, fontweight="bold",
                 color=R["kont"])
        fig.text((left + w / 2) / W_, 1 - (top1 + h1 + 4) / H_, "1/50", ha="center", fontsize=8, color="#57534e")

    top2 = top1 + h1 + 20
    ax3, w3, h3 = ax_mm(16, top2, (-6.0, DER + 10.4), (-2.2, YD_TEPE + 0.4), 50)
    yan(ax3, 60)
    fig.text((16 + w3 / 2) / W_, 1 - (top2 - 3) / H_, "YAN CEPHE (sıra sonu, V1 · site girişi tarafı)",
             ha="center", fontsize=12, fontweight="bold", color=R["kont"])
    fig.text((16 + w3 / 2) / W_, 1 - (top2 + h3 + 3) / H_, "1/50", ha="center", fontsize=8, color="#57534e")

    top3 = top2 + h3 + 16
    ax4, w4, h4 = ax_mm(16, top3, (-1.5, 16 * GEN + 9.5), (-3.8, YD_TEPE + 0.5), 200)
    sira(ax4, 100)
    fig.text(16 / W_, 1 - (top3 - 3) / H_, "A SIRASI ÖN CEPHESİ (16 villa, girişler dönüşümlü sağ / sol)",
             fontsize=12, fontweight="bold", color=R["kont"])
    fig.text((16 + w4) / W_, 1 - (top3 - 3) / H_, "1/200", ha="right", fontsize=8, color="#57534e")

    # malzeme lejantı ve notlar (sağ sütun)
    lx = (16 + w1 + 6 + w2 + 18) / W_
    ly = 1 - (top1 + 4) / H_
    fig.text(lx, ly, "MALZEME", fontsize=11, fontweight="bold", color=R["kont"])
    items = [
        (R["siva"], None, "Dış cephe: ısı yalıtımlı mantolama, açık bej ince sıva"),
        (R["bant"], None, "Kat bandı ve balkon döşeme alnı: bej, hafif koyu ton"),
        (R["sub"], "////", "Subasman (45 cm): gri doğal taş kaplama"),
        (R["cati"], None, "Çatı: %30 beşik, kiremit; saçak 50 cm, alın 30 cm"),
        (R["cam"], None, "Doğrama: antrasit alüminyum, ısıcam; banyo/WC buzlu"),
        (R["kapi"], None, "Dış kapı: antrasit çelik kapı, dar camlı"),
        (R["kork"], None, "Balkon korkuluğu: 100 cm temperli lamine cam"),
        (R["perde"], None, "Yangın duvarı çıkıntısı ve balkon yan duvarları (mahremiyet)"),
        ("#bfb19a", None, "Bahçe / teras / giriş mahremiyet duvarları, harpuştalı"),
    ]
    y = ly - 9 / H_
    for fc, hatch, txt in items:
        fig.patches.append(Rectangle((lx, y - 0.6 / H_), 8 / W_, 3.4 / H_, transform=fig.transFigure, fc=fc,
                                     ec=R["kont"], lw=0.5, hatch=hatch))
        fig.text(lx + 11 / W_, y, txt, fontsize=7.6, color="#292524", va="bottom")
        y -= 6.0 / H_
    y -= 4 / H_
    fig.text(lx, y, "KOTLAR", fontsize=11, fontweight="bold", color=R["kont"])
    y -= 7 / H_
    for kot, txt in (("±0,00", "bahçe, teras ve otopark"), ("+0,45", "zemin kat döşemesi"),
                     ("+3,60", "1. kat döşemesi (kat yüksekliği 315 cm)"), ("+6,75", "saçak"),
                     ("+8,40", "mahya"), (f"+{YD_TEPE:.2f}".replace(".", ","), "yangın duvarı başlığı")):
        fig.text(lx, y, kot, fontsize=7.6, color=R["kont"], family="DejaVu Sans Mono")
        fig.text(lx + 16 / W_, y, txt, fontsize=7.6, color="#292524")
        y -= 5.0 / H_
    lx = (16 + w3 + 18) / W_
    y = 1 - (top2 + 4) / H_
    fig.text(lx, y, "NOTLAR", fontsize=11, fontweight="bold", color=R["kont"])
    y -= 7 / H_
    for n in ("Ön ve arka cephe girişi sağda olan tiptir; komşu",
              "villalar (soluk) aynalanmış tiptir.",
              "Ön balkon 160 cm, arka balkon 150 cm çıkmalıdır;",
              "girişin ve otoparkın üstünü örter.",
              "Ön cephede giriş duvarı (140 cm) yalnızca iki",
              "girişin yan yana geldiği akstadır.",
              "Arka cephede her aksta 240 cm teras duvarı vardır.",
              "Sıra sonu villaların yan cephesine pencere açılması",
              "mümkündür; bu çalışmada sağır bırakılmıştır.",
              "Ölçüler cm. Ön çalışmadır; uygulama projesiyle",
              "değişebilir."):
        fig.text(lx, y, n, fontsize=7.4, color="#44403c")
        y -= 4.4 / H_
    fig.text(1 - 14 / W_, 8 / H_, "Ölçekler: 1/50 · 1/200 · A1", fontsize=8, ha="right", color="#78716c")
    fig.savefig(pdf)
    fig.savefig(png, dpi=150)
    plt.close(fig)


def write_dxf(path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    renk = {"CEPHE": 7, "CATI": 1, "DOGRAMA": 5, "KORKULUK": 4, "MAHREMIYET": 30, "YANGIN_DUVARI": 32}
    for k, c in renk.items():
        doc.layers.add(k, color=c)
    for katman, pts, kapali in DXF:
        msp.add_lwpolyline(pts, close=kapali, dxfattribs={"layer": katman})
    for dx, txt in ((0, "ON CEPHE"), (30, "ARKA CEPHE"), (60, "YAN CEPHE"), (100, "A SIRASI ON CEPHESI")):
        msp.add_text(txt, height=0.4, dxfattribs={"layer": "CEPHE"}).set_placement((dx, -2.5))
    doc.saveas(path)


if __name__ == "__main__":
    render("cephe_gorunusleri.pdf", "cephe_gorunusleri.png")
    write_dxf("cephe_gorunusleri.dxf")
    print("cephe_gorunusleri.pdf / .png / .dxf")
