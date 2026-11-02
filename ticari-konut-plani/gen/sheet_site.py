"""Vaziyet planı (yerleşim planı)."""
import math
from geom import *

def _road_pts(off_a, off_b, ya=-8, yb=40):
    dx, dy = NE[0] - SE[0], NE[1] - SE[1]; L = math.hypot(dx, dy)
    nx, ny = dy / L, -dx / L                   # dışa (yol yönü) normal
    def on(y, off):
        x = SE[0] + (y - SE[1]) * dx / dy
        return (x + nx * off, y + ny * off)
    return [on(ya, off_a), on(yb, off_a), on(yb, off_b), on(ya, off_b)], on

def tree(s, x, y, r=1.4):
    s.raw(f'<circle cx="{s.X(x):.1f}" cy="{s.Y(y):.1f}" r="{r*s.s:.1f}" class="tree"/>')

def site_plan(saw=False):
    s = Svg(-5, -10, 118, 40, 10, pad=30)
    # yol ve kaldırım
    road, on = _road_pts(3.5, 17)
    walk, _ = _road_pts(0, 3.5)
    s.poly(walk, class_="walk"); s.poly(road, class_="road")
    c, _ = _road_pts(10.25, 10.25)
    s.line(c[0], c[1], class_="laneline")
    for y in range(-6, 40, 6):
        tree(s, *on(y + 2, 1.75), r=1.1)
    # komşu bilgileri
    s.text(45, -5.5, "GÜNEY KOMŞU PARSEL (mevcut yapı + açık alan)", 11, class_="nb")
    s.text(45, 36.5, "KUZEY KOMŞU PARSEL (boş arsa)", 11, class_="nb")
    s.text(-3, 15.5, "ARKA KOMŞU (çok katlı yapı)", 11, rot=-90, class_="nb")
    rp, _ = _road_pts(12, 12)
    s.text(*on(15.5, 12), "CADDE", 16, rot=-74, class_="roadt")
    # parsel
    s.poly(PLOT, class_="plot")
    # yeşil alanlar (yan/arka bahçeler)
    s.poly([(x_rear(Y_N, 0), Y_N), (x_front(Y_N, 0), Y_N), NE, NW], class_="green")
    s.poly([SW, (x_rear(Y_N, 0), Y_N), (X0, Y_N), (X0, 0)], class_="green")
    s.poly([(X0, 0), (x_front(0, 0), 0), (x_front(0.8, 0), 0.8), (X0, 0.8)], class_="green")
    # asfalt: araç yolu + giriş
    s.poly([(X0, 6.0), (x_front(6.0, 0), 6.0), (x_front(12.0, 0), 12.0), (X0, 12.0)], class_="asph")
    s.poly([(83.5, 0.8), (x_front(0.8, 0), 0.8), (x_front(6.0, 0), 6.0), (83.5, 6.0)], class_="asph")
    # otopark sırası
    n = 0
    x = 8.0
    while x + 2.5 <= 58.01:
        s.rect(x, 0.8, x + 2.5, 6.0, class_="stall"); n += 1; x += 2.5
    s.text(33, 3.4, f"AÇIK OTOPARK  ({n} araç)", 10, class_="lbls")
    # rampa
    s.rect(59.5, 0.8, 83.5, 6.0, class_="ramp")
    for xx in [64, 70, 76]:
        s.raw(f'<path d="M{s.X(xx+3):.1f},{s.Y(3.4):.1f} L{s.X(xx):.1f},{s.Y(3.4):.1f}" class="arrow"/>')
    s.text(71.5, 5.0, "RAMPA %15 → BODRUM OTOPARK", 9, class_="lbls")
    # dükkan önü yaya / revak + ön meydan
    s.poly([(X0, 12.0), (x_front(12.0, 0), 12.0), (x_front(Y_N, 0), Y_N), (X1, Y_N),
            (X1, Y_GF_S), (X0, Y_GF_S)], class_="pave")
    s.text(45, 13.6, "DÜKKAN ÖNÜ YAYA AKSI / REVAK (4.5 m)", 9, class_="lbls")
    s.text(48, 9.0, "ARAÇ YOLU (6 m)", 10, class_="lbls")
    for (x, y) in [(90.5, 21.5), (93.0, 26.5), (88.5, 13.5), (20, 29.6), (40, 29.6), (60, 29.6), (75, 29.6)]:
        tree(s, x, y, 1.0)
    s.text(96.2, 25.0, "ÖN MEYDAN", 10, rot=-74, class_="lbls")
    # bina
    s.rect(X0, Y_GF_S, X1, Y_N, class_="bldg")
    for name, a, b in GF_MODULES:
        cls = "shop" if name.startswith("DK") else ("lobby" if name.startswith("LOBI") else "tech")
        s.rect(a, Y_GF_S, b, Y_N, class_=cls)
        t = name.replace("LOBI_", "LOBİ ").replace("TEKNIK", "T").replace("DK", "DK")
        s.text((a + b) / 2, Y_GF_S + 2.0, t, 9, class_="lbl")
    s.rect(X0, Y_UP_S, X1, Y_N, class_="slab")
    if saw:
        for name, x0, _ in UP_MODULES:
            if name.startswith("D"):
                s.poly([(x0 + px, Y_UP_S + py) for px, py in SAW_BALC], class_="balc")
    s.text((X0 + X1) / 2, (Y_UP_S + Y_N) / 2 + 1.5, "ZEMİN: 7 DÜKKAN (770 m²)  ·  1.–5. KAT: KAT BAŞI 7 DAİRE = 35 DAİRE", 11, class_="lblb")
    # yapı yaklaşma sınırı
    s.poly(ENVELOPE, class_="env")
    # ölçüler
    s.dim(NW, NE, 2.6, "100 m")
    s.dim(SE, SW, 6.6, "94.1 m")
    s.dim(SW, NW, 2.4, "31.2 m")
    s.dim(NE, SE, 14.5, "32.3 m")
    # çekme ölçüleri
    s.dim((x_front(22), 22), (x_front(22, 0), 22), -1.2, "10 m")
    s.dim((50, H), (50, Y_N), 1.5, "3 m")
    s.dim((58.75, 0), (58.75, 3), -1.2, "3 m")
    s.dim((x_rear(24, 0), 24), (x_rear(24), 24), 1.2, "3 m*")
    # giriş okları
    ax, ay = x_front(9, 0) + 5, 9
    s.raw(f'<path d="M{s.X(ax):.1f},{s.Y(ay):.1f} L{s.X(ax-6):.1f},{s.Y(ay):.1f}" class="arrowb"/>')
    s.text(ax + 0.5, ay + 2.2, "ARAÇ GİRİŞİ", 9, anchor="start", class_="lbl")
    # kuzey oku (görüntüye göre yaklaşık; parsel ekseni ~13° dönük)
    cx, cy = s.X(112), s.Y(35.5)
    s.raw(f'<g transform="translate({cx:.0f},{cy:.0f}) rotate(-12.9)"><path d="M0,-22 L7,8 L0,3 L-7,8 Z" class="north"/>'
          f'<text y="-28" font-size="12" text-anchor="middle" class="lblb">K</text></g>')
    s.text(45, -8.2, "Yapı yaklaşma sınırı (kesikli mavi)  ·  * arka çekme 3 m varsayılmıştır", 9, class_="note")
    return s.svg("Vaziyet planı"), n
