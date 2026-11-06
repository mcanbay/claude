"""
Ekran üstü öğeler: konuşma ve düşünce balonları, altyazılar, hedef uyarısı
(HUD), nişangâh ve kapanış kartı. Hepsi ekran koordinatlarında çizilir.
"""

import math

from cizim import (OUT, WHITE, H, W, TAU, about, back_out, brokoli, catmull, ease_out, ellipse_pts,
                   mixc, parilti, rgba, roket_ikon, rrect_pts, S, smooth, span, T, text_w, wrap)

INK = (60, 40, 58)


def _lines_box(text, size, max_w, weight):
    lines = wrap(text, size, max_w, weight)
    lh = size * 1.2
    tw = max(text_w(l, size, weight) for l in lines)
    return lines, lh, tw


def _draw_lines(cv, lines, cx, cy, lh, size, fill, weight, width=100):
    y = cy - (len(lines) - 1) * lh / 2
    for line in lines:
        cv.text(cx, y, line, size, fill, weight=weight, width=width, anchor="mm")
        y += lh


def konusma_balonu(cv, text, cx, cy, tip, appear, alpha=1.0, size=54, max_w=760, weight=600):
    """Kuyruklu konuşma balonu. appear: 0..1 açılma ilerlemesi (esneyerek büyür)."""
    if appear <= 0 or alpha <= 0.01:
        return
    lines, lh, tw = _lines_box(text, size, max_w, weight)
    pw, ph = tw / 2 + 44, len(lines) * lh / 2 + 30
    sc = 0.55 + 0.45 * back_out(appear, 2.2)
    line_c, fill_c = rgba(OUT, alpha), rgba(WHITE, alpha)
    with cv.screen(), cv.push(about(S(sc), cx, cy)):
        box = rrect_pts(cx - pw, cy - ph, cx + pw, cy + ph, min(44, ph))
        dx, dy = tip[0] - cx, tip[1] - cy
        L = math.hypot(dx, dy) or 1.0
        ux, uy = dx / L, dy / L
        k = min(pw / max(abs(ux), 1e-6), ph / max(abs(uy), 1e-6))
        bx, by = cx + ux * (k - 26), cy + uy * (k - 26)
        nx, ny = -uy, ux
        mid = (bx + (tip[0] - bx) * 0.55 + nx * 14, by + (tip[1] - by) * 0.55 + ny * 14)
        tail = catmull([(bx + nx * 34, by + ny * 34), mid, tip, (bx - nx * 26, by - ny * 26)], k=5, closed=False)
        cv.stroke(box, line_c, 14, closed=True)
        cv.stroke(tail, line_c, 14, closed=True)
        cv.poly(tail, fill=fill_c)
        cv.poly(box, fill=fill_c)
        _draw_lines(cv, lines, cx, cy + 2, lh, size, rgba(INK, alpha), weight)


def dusunce_balonu(cv, text, cx, cy, toward, appear, alpha=1.0, size=54, max_w=720, weight=600):
    """Bulut biçimli düşünce balonu; küçük baloncuklar 'toward' noktasına iner."""
    if appear <= 0 or alpha <= 0.01:
        return
    lines, lh, tw = _lines_box(text, size, max_w, weight)
    pw, ph = tw / 2 + 50, len(lines) * lh / 2 + 34
    sc = 0.55 + 0.45 * back_out(appear, 2.0)
    line_c, fill_c = rgba(OUT, alpha), rgba(WHITE, alpha)
    bumps = []
    nb = max(8, int((pw + ph) / 38))
    for i in range(nb):
        a = i / nb * TAU
        bumps.append((cx + math.cos(a) * pw * 0.98, cy + math.sin(a) * ph * 0.98, 0.42 * ph + 18))
    trail = []
    for i, r in enumerate((24, 16, 10)):
        u = 0.25 + i * 0.26
        trail.append((lerp2(cx, toward[0], u), lerp2(cy + ph * 0.8, toward[1], u), r))
    with cv.screen(), cv.push(about(S(sc), cx, cy)):
        for x, y, r in bumps + trail:
            cv.circle(x, y, r + 7, fill=line_c)
        cv.ellipse(cx, cy, pw + 7, ph + 7, fill=line_c)
        for x, y, r in bumps + trail:
            cv.circle(x, y, r, fill=fill_c)
        cv.ellipse(cx, cy, pw, ph, fill=fill_c)
        _draw_lines(cv, lines, cx, cy + 2, lh, size, rgba(INK, alpha), weight)


def lerp2(a, b, u):
    return a + (b - a) * u


def altyazi(cv, text, cy, alpha, size=50, max_w=880, weight=600, label=None, tone=(24, 18, 46),
            color=WHITE):
    """Anlatıcı (iç ses) altyazısı: yarı saydam koyu hap üzerinde beyaz yazı."""
    if alpha <= 0.01:
        return
    lines, lh, tw = _lines_box(text, size, max_w, weight)
    pw, ph = tw / 2 + 40, len(lines) * lh / 2 + 24
    rise = (1 - ease_out(alpha)) * 24
    cx = W / 2
    with cv.screen(), cv.push(T(0, rise)):
        cv.rrect(cx - pw, cy - ph, cx + pw, cy + ph, min(36, ph), fill=rgba(tone, 0.78 * alpha))
        if label:
            lw_ = text_w(label, 26, 700, 110) / 2 + 18
            cv.rrect(cx - lw_, cy - ph - 22, cx + lw_, cy - ph + 14, 16, fill=rgba((255, 196, 84), alpha))
            cv.text(cx, cy - ph - 4, label, 26, rgba(INK, alpha), weight=700, width=110)
        _draw_lines(cv, lines, cx, cy + 2, lh, size, rgba(color, alpha), weight)


def nisangah(cv, x, y, t, lock, alpha=1.0):
    """Hedefe kilitlenen dönen nişangâh."""
    if alpha <= 0.01:
        return
    r = 46 + 150 * (1 - ease_out(lock))
    col = rgba((255, 90, 100), alpha)
    rot = t * 2.2 + (1 - lock) * 3
    with cv.screen():
        for i in range(4):
            a0 = rot + i * TAU / 4
            cv.stroke(ellipse_pts(x, y, r, r, a0=a0 + 0.25, a1=a0 + TAU / 4 - 0.25, n=14), col, 6, caps=False)
            c, s = math.cos(a0 + TAU / 8), math.sin(a0 + TAU / 8)
            cv.stroke([(x + c * (r - 16), y + s * (r - 16)), (x + c * (r + 16), y + s * (r + 16))], col, 6)
        if lock > 0.95:
            p = 0.5 + 0.5 * math.sin(t * 16)
            rr = r + 14 + 8 * p
            cv.stroke(ellipse_pts(x, y, rr, rr, n=48), rgba((255, 90, 100), alpha * 0.5 * p), 4, closed=True)


def hud_uyari(cv, t, t0, alpha=1.0):
    """'HEDEF TESPİT EDİLDİ: BROKOLİ GEZEGENİ' uyarı paneli."""
    if alpha <= 0.01:
        return
    u = t - t0
    glitch = 1 - span(u, 0.0, 0.3)
    jx = glitch * 30 * math.sin(u * 91) * (1 if int(u * 40) % 3 else -1)
    vis = alpha * (0.35 + 0.65 * (1 - glitch * (int(u * 30) % 2)))
    blink = 0.55 + 0.45 * math.sin(u * 14)
    cx, cy, pw, ph = W / 2 + jx, 300, 450, 128
    red = (255, 70, 90)
    with cv.screen():
        cv.glow(cx, cy, 520, red, 0.35 * vis * blink)
        cv.rrect(cx - pw, cy - ph, cx + pw, cy + ph, 26, fill=rgba((36, 6, 20), 0.86 * vis))
        for y in range(int(cy - ph + 10), int(cy + ph - 6), 9):
            cv.stroke([(cx - pw + 12, y), (cx + pw - 12, y)], rgba(red, 0.07 * vis), 2, caps=False)
        cv.stroke(rrect_pts(cx - pw, cy - ph, cx + pw, cy + ph, 26), rgba(red, vis * (0.5 + 0.5 * blink)), 6,
                  closed=True)
        for sx in (-1, 1):
            for sy in (-1, 1):
                x0, y0 = cx + sx * (pw + 16), cy + sy * (ph + 16)
                cv.stroke([(x0, y0 - sy * 46), (x0, y0), (x0 - sx * 46, y0)], rgba((255, 214, 102), vis), 7)
        # uyarı üçgenleri
        for sx in (-1, 1):
            tx = cx + sx * 375
            tri = [(tx, cy - 92), (tx + 40, cy - 22), (tx - 40, cy - 22)]
            cv.poly(tri, fill=rgba((255, 214, 102), vis * blink), line=rgba((36, 6, 20), vis), lw=4)
            cv.text(tx, cy - 46, "!", 46, rgba((36, 6, 20), vis), weight=700)
        cv.text(cx, cy - 56, "HEDEF TESPİT EDİLDİ:", 54, rgba((255, 214, 102), vis), weight=700, width=112)
        label = "BROKOLİ GEZEGENİ"
        lw_ = text_w(label, 66, 700, 108)
        lx = cx - 38
        cv.text(lx, cy + 46, label, 66, rgba(WHITE, vis), weight=700, width=108)
        if vis > 0.3:
            brokoli(cv, lx + lw_ / 2 + 60, cy + 62, 0.48)


# --------------------------------------------------------------- kapanış --

def _fit(s, size, max_w, weight):
    w = text_w(s, size, weight)
    return size if w <= max_w else size * max_w / w


_BOKEH = [(120, 1500, 70), (930, 1640, 90), (820, 260, 60), (200, 420, 44), (980, 980, 40), (70, 980, 54),
          (560, 1780, 64), (420, 180, 36), (700, 1420, 30)]


def kapanis_karti(cv, t, t0):
    """Sıcak renkli kapanış kartı, yazılar ve uçan küçük roket."""
    u = t - t0
    top, mid, bot = (255, 222, 196), (255, 196, 206), (214, 196, 246)
    with cv.screen():
        n = 32
        for i in range(n):
            a = i / n
            c = mixc(top, mid, a * 2) if a < 0.5 else mixc(mid, bot, (a - 0.5) * 2)
            cv.rrect(-10, H * a - 1, W + 10, H * (a + 1 / n) + 2, 0, fill=c)
        for i, (x, y, r) in enumerate(_BOKEH):
            yy = y - u * (18 + 6 * (i % 3))
            cv.circle(x + 10 * math.sin(u * 0.8 + i), yy, r, fill=rgba(WHITE, 0.22))
        for i in range(16):
            x = (i * 167 + 60) % W
            y = (i * 293 + 140) % 1500 + 120
            tw = 0.5 + 0.5 * math.sin(u * 3 + i * 1.7)
            parilti(cv, x, y, 10 + 10 * tw, WHITE, 0.4 + 0.5 * tw, rot=u * 0.5)

        # uçan roket ve noktalı iz
        fly = span(u, 0.15, 2.4)
        if 0 < fly:
            def path(v):
                return (lerp2(-120, 1200, v), 1320 - 820 * v + 260 * math.sin(v * math.pi) * -0.6)

            for k in range(1, 26):
                v = fly - k * 0.03
                if v <= 0:
                    break
                px, py = path(v)
                cv.circle(px, py, 7 * (1 - k / 26) + 2, fill=rgba(WHITE, 0.8 * (1 - k / 26)))
            if fly < 1:
                x, y = path(fly)
                x2, y2 = path(min(1, fly + 0.01))
                ang = math.atan2(y2 - y, x2 - x) + math.pi / 2
                roket_ikon(cv, x, y, 0.8, ang=ang, flame=1.0, t=t)

        a1 = smooth(span(u, 0.4, 1.0))
        a2 = smooth(span(u, 1.2, 1.8))
        a3 = smooth(span(u, 2.0, 2.6))
        plum, coral = (92, 56, 108), (232, 84, 112)
        s1 = _fit("sıradan bir gün…", 80, 900, 500)
        s2 = _fit("kocaman bir macera.", 108, 960, 700)
        with cv.push(T(0, (1 - a1) * 30)):
            cv.text(W / 2, 520, "Sizin için", s1, rgba(plum, a1), weight=500)
            cv.text(W / 2, 520 + s1 * 1.15, "sıradan bir gün…", s1, rgba(plum, a1), weight=500)
        y2 = 820
        with cv.push(about(S(0.85 + 0.15 * back_out(a2)), W / 2, y2 + s2 * 0.6)):
            cv.text(W / 2, y2, "Onlar için", s2, rgba(coral, a2), weight=700, stroke=7,
                    stroke_fill=rgba(WHITE, a2))
            cv.text(W / 2, y2 + s2 * 1.15, "kocaman bir macera.", s2, rgba(coral, a2), weight=700, stroke=7,
                    stroke_fill=rgba(WHITE, a2))
        if a2 > 0.05:
            iy = y2 + s2 * 1.15 + 190
            roket_ikon(cv, W / 2 - 70, iy, 0.9 * a2, ang=0.45, flame=a2, t=t)
            for i, (dx, dy, r) in enumerate(((40, -50, 34), (120, 0, 24), (80, 70, 18))):
                tw = 0.6 + 0.4 * math.sin(u * 5 + i * 2)
                parilti(cv, W / 2 + dx, iy + dy, r * a2 * tw + 5 * a2, (255, 214, 102), a2)
        if a3 > 0.01:
            title = "BEBEĞİN DÜNYASINDA BİR GÜN"
            tw_ = text_w(title, 38, 700, 112)
            ep = "BÖLÜM 1"
            ew = text_w(ep, 38, 700, 112)
            total = tw_ + 46 + ew
            x0 = W / 2 - total / 2
            y = 1390 + (1 - a3) * 20
            cv.rrect(x0 - 34, y - 44, x0 + total + 34, y + 44, 44, fill=rgba(WHITE, 0.85 * a3))
            cv.text(x0, y, title, 38, rgba(plum, a3), weight=700, width=112, anchor="lm")
            cv.rrect(x0 + tw_ + 21, y - 24, x0 + tw_ + 25, y + 24, 2, fill=rgba(coral, a3))
            cv.text(x0 + tw_ + 46, y, ep, 38, rgba(coral, a3), weight=700, width=112, anchor="lm")
