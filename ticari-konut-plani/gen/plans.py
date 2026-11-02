"""Zemin kat, normal kat ve tip daire planları."""
from geom import *

def _stair_core(s, a, y_bot, y_top, landing_south=True):
    """Merdiven (2 kollu) + asansör + tesisat şaftı. a: modül batı x'i."""
    s0, s1 = y_bot + 0.3, y_top - 0.1
    s.rect(a + 0.3, s0, a + 2.9, s1, class_="stairbox")
    s.line((a + 1.6, s0 + 1.3), (a + 1.6, s1 - 1.0), class_="thin")
    y = s0 + 1.3
    while y < s1 - 1.0:
        s.line((a + 0.3, y), (a + 2.9, y), class_="tread"); y += 0.3
    s.line((a + 0.3, s0 + 1.3), (a + 2.9, s0 + 1.3), class_="thin")
    s.raw(f'<path d="M{s.X(a+0.95):.1f},{s.Y(s1-1.2):.1f} L{s.X(a+0.95):.1f},{s.Y(s0+0.8):.1f} '
          f'L{s.X(a+2.25):.1f},{s.Y(s0+0.8):.1f} L{s.X(a+2.25):.1f},{s.Y(s1-1.2):.1f}" class="stairarrow"/>')
    e0, e1 = y_top - 2.5, y_top - 0.3
    s.rect(a + 3.3, e0, a + 5.1, e1, class_="lift")
    s.line((a + 3.3, e0), (a + 5.1, e1), class_="thin"); s.line((a + 3.3, e1), (a + 5.1, e0), class_="thin")
    s.rect(a + 3.3, s0, a + 5.1, s0 + 1.4, class_="shaft")
    s.text(a + 4.2, s0 + 0.7, "şaft", 7, class_="lbls")
    s.text(a + 4.2, e0 - 0.6, "asansör", 7, class_="lbls")

def _win(s, a, b, y=None, x=None):
    if y is not None: s.line((a, y), (b, y), class_="win")
    else: s.line((x, a), (x, b), class_="win")

def ground_floor():
    s = Svg(3, 11.2, 91, 30.5, 13, pad=30)
    s.rect(X0, 12.0, X1, Y_GF_S, class_="pave")
    s.text((X0 + X1) / 2, 13.2, "DÜKKAN ÖNÜ YAYA AKSI / REVAK — üstteki balkonlar saçak görevi görür", 10, class_="lbls")
    for name, a, b in GF_MODULES:
        if name.startswith("DK"):
            s.rect(a, Y_GF_S, b, Y_N, class_="shop")
            area = (b - a) * GF_DEPTH
            s.text((a + b) / 2, Y_GF_S + 6.5, name.replace("DK", "DÜKKAN "), 12, class_="lblb")
            s.text((a + b) / 2, Y_GF_S + 4.8, f"{area:.1f} m²", 11, class_="lbl")
            s.rect(b - 1.8, Y_N - 1.6, b - 0.1, Y_N - 0.1, class_="wet")
            s.text(b - 0.95, Y_N - 0.85, "WC", 7, class_="lbls")
            _win(s, a + 0.6, b - 0.6, y=Y_GF_S)
            if name == "DK1":
                _win(s, Y_GF_S + 0.6, Y_N - 0.6, x=b)
        elif name.startswith("LOBI"):
            s.rect(a, Y_GF_S, b, Y_N, class_="lobby")
            _stair_core(s, a, Y_GF_S + 1.5, Y_N)
            s.text((a + b) / 2, Y_GF_S + 0.8, "KONUT GİRİŞİ " + name[-1], 8, class_="lblb")
            s.raw(f'<path d="M{s.X(a+4.2):.1f},{s.Y(12.6):.1f} L{s.X(a+4.2):.1f},{s.Y(Y_GF_S-0.2):.1f}" class="arrowb"/>')
        else:
            s.rect(a, Y_GF_S, b, Y_N, class_="tech")
            for i, t in enumerate(["Çöp", "Elektrik", "Su/Sayaç"]):
                yy = Y_N - (i + 0.5) * GF_DEPTH / 3
                s.text((a + b) / 2, yy, t, 8, class_="lbls")
                if i: s.line((a, Y_N - i * GF_DEPTH / 3), (b, Y_N - i * GF_DEPTH / 3), class_="thin")
    s.rect(X0, Y_GF_S, X1, Y_N, class_="outline")
    s.line((X0, Y_UP_S), (X1, Y_UP_S), class_="hidden")
    s.text(X0 + 3.3, Y_UP_S + 0.45, "üst kat cephe hattı", 7, anchor="start", class_="note")
    # ölçüler
    for name, a, b in GF_MODULES:
        s.dim((a, Y_GF_S), (b, Y_GF_S), -2.2, f"{b - a:.1f}".rstrip("0").rstrip("."), 9)
    s.dim((X0, Y_N), (X1, Y_N), 1.0, f"{X1 - X0:.1f} m", 10)
    s.dim((X1, Y_GF_S), (X1, Y_N), -1.4, f"{GF_DEPTH} m", 10)
    s.text(X1 + 2.6, (Y_GF_S + Y_N) / 2, "CADDE TARAFI →", 10, rot=-90, class_="lblb")
    return s.svg("Zemin kat planı")

def _flat(s, x0, label=None, small=True, corner=False, saw=False):
    yb = Y_UP_S
    if saw:
        (ax, ay), (bx, by), (cx, cy) = SAW_BALC
        s.poly([(x0 + ax, yb + ay), (x0 + bx, yb + by), (x0 + cx, yb + cy)], class_="balc")
        s.line((x0 + ax, yb + ay), (x0 + bx, yb + by), class_="privwall")
        s.line((x0 + bx, yb + by), (x0 + cx, yb + cy), class_="rail")
        mx, my = (bx + cx) / 2, (by + cy) / 2
        s.raw(f'<path d="M{s.X(x0+mx):.1f},{s.Y(yb+my):.1f} L{s.X(x0+mx+SAW_VIEW[0]):.1f},{s.Y(yb+my+SAW_VIEW[1]):.1f}" class="viewarrow"/>')
    else:
        bx0, by0, bx1, by1 = BALCONY
        s.rect(x0 + bx0, yb + by0, x0 + bx1, yb + by1, class_="balc")
    for name, a, b, c, d in FLAT_ROOMS:
        cls = "wet" if name in ("Banyo", "WC", "Kiler") else ("kitchen" if "Mutfak" in name else "room")
        s.rect(x0 + a, yb + b, x0 + c, yb + d, class_=cls)
        if small:
            if name in ("Yatak 1", "Yatak 2", "Salon"):
                s.text(x0 + (a + c) / 2, yb + (b + d) / 2, name, 8, class_="lbls")
        else:
            net = (c - a - 0.15) * (d - b - 0.15)
            lx, ly = LABEL_POS.get(name, ((a + c) / 2, (b + d) / 2))
            s.text(x0 + lx, yb + ly + 0.22, name, 13 if c - a > 2 else 10, class_="lblb")
            s.text(x0 + lx, yb + ly - 0.22, f"{net:.1f} m²", 11 if c - a > 2 else 9, class_="lbl")
            continue
            s.text(x0 + (a + c) / 2, yb + (b + d) / 2 + 0.22, name, 13 if c - a > 2 else 10, class_="lblb")
            s.text(x0 + (a + c) / 2, yb + (b + d) / 2 - 0.3, f"{net:.1f} m²", 11 if c - a > 2 else 9, class_="lbl")
    s.rect(x0, yb, x0 + FLAT_W, Y_CORR, class_="outline")
    _win(s, x0 + 0.5, x0 + 2.3, y=yb); _win(s, x0 + 3.3, x0 + 5.3, y=yb); _win(s, x0 + 6.3, x0 + 9.5, y=yb)
    if corner:
        _win(s, yb + 1.0, yb + 5.0, x=x0 + FLAT_W)
    # daire kapısı (koridordan antreye)
    d0, d1 = x0 + 4.3, x0 + 5.3
    s.line((d0, Y_CORR), (d1, Y_CORR), class_="gap")
    r = (d1 - d0) * s.s
    s.raw(f'<path d="M{s.X(d0):.1f},{s.Y(Y_CORR):.1f} L{s.X(d0):.1f},{s.Y(Y_CORR)+r:.1f} '
          f'A{r:.1f},{r:.1f} 0 0 0 {s.X(d1):.1f},{s.Y(Y_CORR):.1f}" class="door"/>')
    if label:
        s.text(x0 + 3.0, yb - 0.75, label, 10, class_="lblb")

def typical_floor(saw=False):
    s = Svg(3, 11.6 if saw else 13.5, 91, 30.5, 13, pad=30)
    s.rect(X0, Y_CORR, X1, Y_N, class_="corr")
    s.text(50.0, Y_CORR + 1.0, "KAT KORİDORU (2.0 m) — kuzey cephede doğal ışık/duman tahliye pencereleri", 9, class_="lbls")
    i = 0
    for name, a, b in UP_MODULES:
        if name.startswith("D"):
            i += 1
            _flat(s, a, f"DAİRE {i} · 2+1", corner=(name == "D7"), saw=saw)
        else:
            s.rect(a, Y_UP_S, b, Y_N, class_="lobby")
            _stair_core(s, a, Y_UP_S, Y_CORR)
            s.text((a + b) / 2, Y_UP_S - 0.75, "ÇEKİRDEK " + name[-1], 9, class_="lblb")
    YD = Y_UP_S - (SAW_DEPTH + 0.3 if saw else BALC_D)
    for x in range(int(X0) + 3, int(X1), 6):
        _win(s, x, x + 1.6, y=Y_N)
    s.rect(X0, Y_UP_S, X1, Y_N, class_="outline")
    for name, a, b in UP_MODULES:
        s.dim((a, YD), (b, YD), -0.8, f"{b - a:.1f}".rstrip("0").rstrip("."), 9)
    s.dim((X0, Y_N), (X1, Y_N), 1.0, f"{X1 - X0:.1f} m", 10)
    s.dim((X1, Y_UP_S), (X1, Y_N), -1.4, "10 m", 10)
    s.text(X1 + 2.6, (Y_UP_S + Y_N) / 2, "CADDE TARAFI →", 10, rot=-90, class_="lblb")
    s.text(50.0, YD - 2.0, ("Testere dişi balkonlar: açık yüzler yola doğru (≈35°) döner, batı yanları sağır mahremiyet duvarı" if saw else "Tüm salon + balkonlar güney-güneybatı ana cepheye ve yol tarafındaki köşeye bakar") + "  ·  1.–5. katlar aynı (5 × 7 = 35 daire)", 10, class_="note")
    return s.svg("Normal kat planı")

LABEL_POS = {"Yatak 2": (2.05, 1.6), "Yatak 1": (4.3, 3.0), "Salon": (8.4, 1.6),
             "Açık Mutfak": (7.9, 6.75), "Banyo": (1.55, 5.3), "WC": (3.1, 6.55), "Antre": (4.8, 6.5)}

def _furn(s, x0, yb):
    R = lambda a, b, c, d, k="furn": s.rect(x0 + a, yb + b, x0 + c, yb + d, class_=k)
    R(3.4, 0.5, 5.0, 2.5)            # çift kişilik yatak
    R(0.3, 0.4, 1.3, 2.4)            # tek kişilik yatak
    R(0.3, 3.4, 2.5, 4.0)            # dolap Y2
    R(3.2, 3.5, 5.6, 4.1)            # dolap Y1
    R(6.2, 2.4, 6.9, 4.8)            # kanepe
    R(7.6, 3.0, 8.8, 4.2)            # sehpa
    R(5.9, 7.35, 9.9, 7.95)          # tezgah
    R(8.4, 4.6, 9.6, 5.6)            # yemek masası
    R(0.15, 4.35, 0.85, 5.95)        # duş
    R(1.7, 6.0, 2.25, 6.5)           # lavabo
    R(2.55, 7.3, 3.1, 7.9)           # wc

def unit_plan(saw=False):
    dy = SAW_DEPTH - BALC_D if saw else 0
    s = Svg(-1.2, Y_UP_S - 2.9 - dy, 11.8, Y_N + 0.4, 52, pad=24)
    x0 = 0.0
    s.rect(-1.2, Y_CORR, 11.6, Y_N, class_="corr")
    s.text(5.0, Y_CORR + 1.0, "KAT KORİDORU", 11, class_="lbls")
    _flat(s, x0, small=False, saw=saw)
    _furn(s, x0, Y_UP_S)
    if saw:
        s.text(6.9, Y_UP_S - 0.75, "BALKON", 12, class_="lblb")
        s.text(6.9, Y_UP_S - 1.2, f"{saw_balc_area():.1f} m²", 11, class_="lbl")
        s.text(9.3, Y_UP_S - 2.6, "yol yönü bakış", 11, anchor="start", class_="note")
        s.text(5.6, Y_UP_S - 1.6, "sağır duvar", 9, rot=-90, class_="note")
    else:
        s.text(7.9, Y_GF_S + 0.6, f"BALKON {(BALCONY[2]-BALCONY[0])*BALC_D:.1f} m²", 12, class_="lblb")
    s.dim((0, Y_UP_S), (FLAT_W, Y_UP_S), -2.5 - dy, "10.00 m", 11)
    s.dim((FLAT_W, Y_UP_S), (FLAT_W, Y_CORR), -0.9, "8.00 m", 11)
    for a, b in [(0, 2.8), (2.8, 5.8), (5.8, 10.0)]:
        s.dim((a, Y_UP_S), (b, Y_UP_S), -1.85 - dy, f"{b - a:.2f}", 10)
    s.text(-0.8, Y_UP_S + 4, "← ARKA (komşu tarafı)", 10, rot=-90, class_="note")
    s.text(11.35, Y_UP_S + 4, "CADDE TARAFI →", 10, rot=-90, class_="lblb")
    return s.svg("Tip daire planı")

def flat_net():
    return sum((c - a - 0.15) * (d - b - 0.15) for _, a, b, c, d in FLAT_ROOMS)

def saw_balc_area():
    (ax, ay), (bx, by), (cx, cy) = SAW_BALC
    return abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2
