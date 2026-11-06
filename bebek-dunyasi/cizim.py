"""
Bebeğin Dünyasında Bir Gün: çizim altyapısı ve karakterler.

Her şey 1080×1920 "tasarım" koordinatlarında çizilir. Canvas bu koordinatları
süper örneklemeli (varsayılan 2×) bir piksel ızgarasına çevirir. Kare sonunda
görüntü küçültülerek kenarlar yumuşatılır. Şekiller nokta listesi olarak
üretilir ve bir afin dönüşümden (kamera, ölçek, dönme) geçirilir. Bu sayede
aynı karakter çizimi her ölçekte ve açıda kullanılabilir.
"""

import math
import os
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "fontlar", "Fredoka.ttf")

W, H = 1080, 1920
TAU = 2 * math.pi

# ------------------------------------------------------------------ renkler --

OUT = (74, 50, 66)            # çizgi rengi (koyu mürdüm)
WHITE = (255, 255, 255)
SKIN = (255, 216, 188)
SKIN_SH = (244, 182, 152)
CHEEK = (255, 128, 146)
HAIR = (122, 82, 58)
IRIS = (52, 36, 44)
MOUTH = (150, 50, 70)
TONGUE = (255, 132, 150)
ONESIE = (124, 198, 232)
BIB = (255, 253, 247)
BIB_TRIM = (255, 196, 84)

CHAIR = (255, 251, 244)
CUSHION = (186, 230, 212)
WOOD = (240, 204, 152)
WOOD_DK = (214, 170, 116)
TRAY_FRONT = (186, 230, 212)

HULL = (60, 66, 116)
HULL_DK = (36, 40, 76)
METAL = (150, 160, 204)
NEON = (96, 232, 236)

SLEEVE = (242, 132, 122)
SLEEVE_CUFF = (255, 184, 160)
MOM_SKIN = (244, 196, 166)
SPOON = (214, 222, 236)

BROC = (78, 160, 64)
BROC_DK = (52, 122, 50)
BROC_LT = (130, 200, 92)
BROC_STEM = (170, 214, 116)


# --------------------------------------------------------------- yardımcılar --

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ease_in_out(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def back_out(t, k=1.7):
    t = clamp(t)
    t1 = t - 1
    return 1 + (k + 1) * t1 ** 3 + k * t1 ** 2


def span(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def window(t, t0, t1, fin=0.25, fout=0.25):
    """t0..t1 arasında görünür, kenarlarda yumuşak geçişli 0..1 zarf."""
    return min(span(t, t0, t0 + fin), 1 - span(t, t1 - fout, t1))


def mixc(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def rgba(c, a=1.0):
    return (c[0], c[1], c[2], int(round(255 * clamp(a))))


def keys(t, frames, fn=smooth):
    """Anahtar kare ara değerlemesi. frames: [(zaman, değer), ...]."""
    if t <= frames[0][0]:
        return frames[0][1]
    for (ta, va), (tb, vb) in zip(frames, frames[1:]):
        if t <= tb:
            u = fn((t - ta) / (tb - ta)) if tb > ta else 1.0
            if isinstance(va, tuple):
                return tuple(lerp(a, b, u) for a, b in zip(va, vb))
            return lerp(va, vb, u)
    return frames[-1][1]


# ------------------------------------------------------------ afin dönüşüm --

class Xf:
    """x' = a·x + b·y + c,  y' = d·x + e·y + f"""

    __slots__ = ("a", "b", "c", "d", "e", "f")

    def __init__(self, a=1.0, b=0.0, c=0.0, d=0.0, e=1.0, f=0.0):
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

    def __matmul__(self, o):
        return Xf(self.a * o.a + self.b * o.d, self.a * o.b + self.b * o.e, self.a * o.c + self.b * o.f + self.c,
                  self.d * o.a + self.e * o.d, self.d * o.b + self.e * o.e, self.d * o.c + self.e * o.f + self.f)

    def apply(self, P):
        x, y = P[:, 0], P[:, 1]
        return np.column_stack((self.a * x + self.b * y + self.c, self.d * x + self.e * y + self.f))

    def pt(self, x, y):
        return self.a * x + self.b * y + self.c, self.d * x + self.e * y + self.f

    def inv(self):
        det = self.a * self.e - self.b * self.d
        a, b, d, e = self.e / det, -self.b / det, -self.d / det, self.a / det
        return Xf(a, b, -(a * self.c + b * self.f), d, e, -(d * self.c + e * self.f))

    @property
    def s(self):
        return math.sqrt(abs(self.a * self.e - self.b * self.d))

    @property
    def axis_aligned(self):
        return abs(self.b) < 1e-9 and abs(self.d) < 1e-9


def T(tx, ty):
    return Xf(1, 0, tx, 0, 1, ty)


def S(sx, sy=None):
    return Xf(sx, 0, 0, 0, sx if sy is None else sy, 0)


def R(ang):
    c, s = math.cos(ang), math.sin(ang)
    return Xf(c, -s, 0, s, c, 0)


def about(xf, cx, cy):
    return T(cx, cy) @ xf @ T(-cx, -cy)


# ------------------------------------------------------------- şekil üretimi --

def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=64, a0=0.0, a1=TAU):
    full = (a1 - a0) >= TAU - 1e-6
    a = np.linspace(a0, a1, n, endpoint=not full)
    x, y = rx * np.cos(a), ry * np.sin(a)
    if rot:
        c, s = math.cos(rot), math.sin(rot)
        x, y = c * x - s * y, s * x + c * y
    return np.column_stack((x + cx, y + cy))


def rrect_pts(x0, y0, x1, y1, r, n=10):
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    out = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0.0),
                       (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
        a = np.linspace(a0, a0 + math.pi / 2, n)
        out.append(np.column_stack((cx + r * np.cos(a), cy + r * np.sin(a))))
    return np.vstack(out)


def star_pts(cx, cy, r_out, r_in, n=4, rot=0.0):
    a = np.arange(2 * n) * math.pi / n + rot - math.pi / 2
    r = np.where(np.arange(2 * n) % 2 == 0, r_out, r_in)
    return np.column_stack((cx + r * np.cos(a), cy + r * np.sin(a)))


def catmull(pts, k=8, closed=True):
    """Kontrol noktalarından yumuşak eğri (Catmull-Rom)."""
    P = np.asarray(pts, float)
    n = len(P)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed or i > 0 else P[0]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed or i + 2 < n else P[-1]
        u = np.linspace(0, 1, k, endpoint=False)[:, None]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    if not closed:
        out.append(P[-1:])
    return np.vstack(out)


# -------------------------------------------------------------------- yazı --

_fonts = {}


def font(size, weight=600, width=100):
    key = (max(4, int(round(size))), int(weight), int(width))
    f = _fonts.get(key)
    if f is None:
        f = ImageFont.truetype(FONT_PATH, key[0])
        try:
            f.set_variation_by_axes([weight, width])
        except Exception:
            pass
        _fonts[key] = f
    return f


def text_w(s, size, weight=600, width=100):
    return font(size, weight, width).getlength(s)


def wrap(s, size, max_w, weight=600, width=100):
    lines, cur = [], ""
    for word in s.split():
        cand = (cur + " " + word).strip()
        if cur and text_w(cand, size, weight, width) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------------- tuval --

_glow_masks = {}


def _glow_mask(R, level):
    key = (R, level)
    m = _glow_masks.get(key)
    if m is None:
        if len(_glow_masks) > 600:
            _glow_masks.clear()
        y, x = np.ogrid[-R:R + 1, -R:R + 1]
        d = np.sqrt(x * x + y * y) / R
        a = np.clip(1 - d, 0, 1) ** 2 * (level / 20.0) * 255
        m = Image.fromarray(a.astype(np.uint8), "L")
        _glow_masks[key] = m
    return m


class Canvas:
    def __init__(self, out_w, out_h, ss=2, img=None, bg=(0, 0, 0)):
        self.ss = ss
        self.out_w, self.out_h = out_w, out_h
        self.img = img if img is not None else Image.new("RGB", (out_w * ss, out_h * ss), bg)
        self.dr = ImageDraw.Draw(self.img, "RGBA")
        self.k = out_w / W * ss          # tasarım birimi -> piksel
        self.stack = [S(self.k)]

    # dönüşüm yığını
    @property
    def xf(self):
        return self.stack[-1]

    @contextmanager
    def push(self, xf):
        self.stack.append(self.stack[-1] @ xf)
        try:
            yield
        finally:
            self.stack.pop()

    @contextmanager
    def screen(self):
        """Kameradan bağımsız, ekran koordinatlarında çizim."""
        self.stack.append(S(self.k))
        try:
            yield
        finally:
            self.stack.pop()

    def _flat(self, pts):
        return self.xf.apply(np.asarray(pts, float)).ravel().tolist()

    def _lw(self, lw):
        return max(1, int(round(lw * self.xf.s)))

    # temel şekiller
    def poly(self, pts, fill=None, line=None, lw=0):
        flat = self._flat(pts)
        if len(flat) < 6:
            return
        if fill is not None:
            self.dr.polygon(flat, fill=fill)
        if line is not None and lw > 0:
            self.dr.line(flat + flat[:2], fill=line, width=self._lw(lw), joint="curve")

    def stroke(self, pts, color, lw, closed=False, caps=True):
        flat = self._flat(pts)
        if len(flat) < 4:
            return
        if closed:
            flat = flat + flat[:2]
        w = self._lw(lw)
        self.dr.line(flat, fill=color, width=w, joint="curve")
        if caps and not closed and w > 2:
            r = w / 2.0
            for x, y in ((flat[0], flat[1]), (flat[-2], flat[-1])):
                self.dr.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def ellipse(self, cx, cy, rx, ry=None, fill=None, line=None, lw=0, rot=0.0):
        ry = rx if ry is None else ry
        if rx <= 0 or ry <= 0:
            return
        xf = self.xf
        if xf.axis_aligned and not rot:
            px, py = xf.pt(cx, cy)
            sx, sy = rx * abs(xf.a), ry * abs(xf.e)
            if line is not None and lw > 0:
                h = lw * xf.s / 2
                self.dr.ellipse((px - sx - h, py - sy - h, px + sx + h, py + sy + h), fill=line)
                if fill is not None and sx > h + 0.5 and sy > h + 0.5:
                    self.dr.ellipse((px - sx + h, py - sy + h, px + sx - h, py + sy - h), fill=fill)
            elif fill is not None:
                self.dr.ellipse((px - sx, py - sy, px + sx, py + sy), fill=fill)
            return
        n = int(clamp(max(rx, ry) * xf.s * 0.35, 24, 220))
        self.poly(ellipse_pts(cx, cy, rx, ry, rot, n), fill, line, lw)

    def circle(self, cx, cy, r, fill=None, line=None, lw=0):
        self.ellipse(cx, cy, r, r, fill, line, lw)

    def rrect(self, x0, y0, x1, y1, r, fill=None, line=None, lw=0):
        self.poly(rrect_pts(x0, y0, x1, y1, r), fill, line, lw)

    def capsule(self, x0, y0, x1, y1, r, fill, line=None, lw=0):
        """Uçları yuvarlak kalın çubuk (kol, bacak)."""
        if line is not None and lw > 0:
            self.stroke([(x0, y0), (x1, y1)], line, 2 * r + lw)
        self.stroke([(x0, y0), (x1, y1)], fill, 2 * r - lw if line is not None else 2 * r)

    def glow(self, x, y, r, color, alpha=1.0):
        px, py = self.xf.pt(x, y)
        Rp = min(r * self.xf.s, 1100.0)
        level = int(round(clamp(alpha) * 20))
        if Rp < 3 or level <= 0:
            return
        Rp = int(1.05 ** round(math.log(Rp) / math.log(1.05)))
        m = _glow_mask(Rp, level)
        x0, y0 = int(px) - Rp, int(py) - Rp
        self.img.paste(color, (x0, y0, x0 + m.width, y0 + m.height), m)

    def text(self, x, y, s, size, fill, weight=600, width=100, anchor="mm", stroke=0, stroke_fill=None):
        px, py = self.xf.pt(x, y)
        k = self.xf.s
        f = font(size * k, weight, width)
        kw = {}
        if stroke > 0:
            kw = dict(stroke_width=max(1, int(round(stroke * k))), stroke_fill=stroke_fill)
        self.dr.text((px, py), s, font=f, fill=fill, anchor=anchor, **kw)

    def result(self):
        return self.img.reduce(self.ss) if self.ss > 1 else self.img


# ------------------------------------------------------------------- bebek --

@dataclass
class Bebek:
    x: float = 540.0           # baş merkezinin dünya konumu
    y: float = 720.0
    s: float = 1.25            # ölçek (baş yarıçapı ≈ 110·s)
    dy: float = 0.0            # sandalyeden bağımsız dikey kayma (taşınma, zıplama)
    look: tuple = (0.0, 0.0)   # göz bebeği yönü (-1..1)
    blink: float = 0.0
    lid: float = 0.0           # üst göz kapağı (0 açık, 1 kapalı)
    happy: float = 0.0         # ^^ gülen gözler
    brow: float = 0.0          # kaş yüksekliği
    brow_tilt: float = 0.0     # + kararlı/kızgın, - endişeli
    brow_skew: float = 0.0     # tek kaş kalkık (şüpheci)
    mouth: str = "smile"
    mopen: float = 0.4
    turn: float = 0.0          # baş dönüşü (-1 sola, +1 sağa)
    tilt: float = 0.0          # baş eğimi (radyan)
    hand_l: tuple = (-100.0, 262.0)
    hand_r: tuple = (100.0, 262.0)
    helmet: float = 0.0
    squash: float = 0.0


def _xf_bebek(b):
    xf = T(b.x, b.y + b.dy) @ S(b.s)
    if b.squash:
        xf = xf @ about(S(1 + 0.08 * b.squash, 1 - 0.08 * b.squash), 0, 320)
    return xf


def bebek_govde(cv, b):
    """Gövde ve önlük (mama sandalyesinin tepsisinin arkasında kalır)."""
    with cv.push(_xf_bebek(b)):
        cv.ellipse(0, 220, 100, 132, fill=ONESIE, line=OUT, lw=6)
        cv.ellipse(0, 170, 74, 64, fill=BIB, line=BIB_TRIM, lw=9)
        roket_ikon(cv, 0, 178, 0.42, ang=0.5, flame=0.0)


def _goz(cv, ex, ey, rx, ry, look, lid, happy):
    if rx < 3:
        return
    if happy > 0.5:
        cv.stroke(ellipse_pts(ex, ey + 8, rx * 0.95, ry * 0.6, a0=math.pi + 0.25, a1=TAU - 0.25, n=24), OUT, 7)
        return
    if lid >= 0.9:
        cv.stroke(ellipse_pts(ex, ey + 2, rx * 0.95, ry * 0.4, a0=0.2, a1=math.pi - 0.2, n=24), OUT, 7)
        return
    cv.ellipse(ex, ey, rx, ry, fill=WHITE, line=OUT, lw=5)
    k = rx / 25.0
    ix = ex + look[0] * rx * 0.24
    iy = ey + look[1] * ry * 0.2
    cv.ellipse(ix, iy, 19 * k, 20, fill=IRIS)
    cv.ellipse(ix + 6.5 * k, iy - 7, 6.5 * k, 6.5, fill=WHITE)
    cv.ellipse(ix - 5.5 * k, iy + 7, 3 * k, 3, fill=WHITE)
    if lid > 0.02:
        s0 = clamp(-1 + 2 * lid, -1, 1)
        a0 = math.pi - math.asin(s0)
        a1 = TAU + math.asin(s0)
        pts = ellipse_pts(ex, ey, rx, ry, a0=a0, a1=a1, n=40)
        cv.poly(pts, fill=SKIN)
        cv.stroke(ellipse_pts(ex, ey, rx, ry, n=48), OUT, 5, closed=True)
        cv.stroke([pts[0], pts[-1]], OUT, 6)


def _agiz(cv, mx, my, kind, op, wk):
    if kind == "smile":
        cv.stroke(ellipse_pts(mx, my - 8, 19 * wk, 10 + op * 7, a0=0.35, a1=math.pi - 0.35, n=20), OUT, 6)
    elif kind in ("open", "grin"):
        ry = 8 + op * 22
        pts = ellipse_pts(mx, my - 10, 23 * wk, ry, a0=0, a1=math.pi, n=24)
        cv.poly(pts, fill=MOUTH, line=OUT, lw=5)
        cv.ellipse(mx, my - 10 + ry * 0.62, 13 * wk, ry * 0.3, fill=TONGUE)
        if kind == "grin" or op > 0.35:
            cv.rrect(mx - 9 * wk, my - 10, mx - 2 * wk, my - 2, 2, fill=WHITE)
            cv.rrect(mx + 2 * wk, my - 10, mx + 9 * wk, my - 2, 2, fill=WHITE)
        cv.stroke([pts[0], pts[-1]], OUT, 5)
    elif kind == "o":
        cv.ellipse(mx, my - 2, (7 + op * 7) * wk, 8 + op * 10, fill=MOUTH, line=OUT, lw=5)
    elif kind == "flat":
        cv.stroke([(mx - 13 * wk, my - 2), (mx + 13 * wk, my - 2)], OUT, 6)
    elif kind == "frown":
        cv.stroke(ellipse_pts(mx, my + 6, 14 * wk, 8, a0=math.pi + 0.5, a1=TAU - 0.5, n=16), OUT, 6)
    elif kind == "smirk":
        cv.stroke(catmull([(mx - 14 * wk, my), (mx, my + 2), (mx + 13 * wk, my - 7)], k=6, closed=False), OUT, 6)
    elif kind == "pursed":
        cv.ellipse(mx + 9 * wk, my, 5 * wk, 4.5, fill=MOUTH, line=OUT, lw=4)


def bebek_bas(cv, b):
    """Kulaklar, baş, saç, yüz. Baş dönüşü yüz öğelerini küre üzerinde kaydırır."""
    phi = b.turn * 0.85
    lid = max(b.lid, b.blink)
    with cv.push(_xf_bebek(b) @ about(R(b.tilt), 0, 95)):
        ears = []
        for side in (-1, 1):
            a = side * 1.72 + phi
            ears.append((112 * math.sin(a), math.cos(a) > 0.05))

        def ear(ex):
            cv.ellipse(ex, 10, 23, 25, fill=SKIN, line=OUT, lw=5)
            cv.ellipse(ex, 12, 10, 12, fill=SKIN_SH)

        for ex, front in ears:
            if not front:
                ear(ex)
        cv.ellipse(0, 0, 112, 104, fill=SKIN, line=OUT, lw=6)
        for ex, front in ears:
            if front:
                ear(ex)

        # saç: tepede kıvrık bir perçem
        hx = 96 * math.sin(phi * 0.9)
        a = np.linspace(0.0, 1.0, 30)
        ang = math.pi / 2 + a * 1.6 * TAU
        rad = 4 + 20 * a
        spiral = np.column_stack((hx + 6 + rad * np.cos(ang) * -1, -112 - 22 + rad * np.sin(ang) * -1))
        cv.stroke(spiral[::-1], HAIR, 8)
        cv.stroke([(hx - 18, -100), (hx - 26, -118)], HAIR, 7)
        cv.stroke([(hx + 18, -101), (hx + 24, -116)], HAIR, 7)

        def proj(alpha, r=104.0):
            ang2 = alpha + phi
            return r * math.sin(ang2), math.cos(ang2)

        # yanaklar
        for side in (-1, 1):
            x, fo = proj(side * 0.78)
            if fo > 0.1:
                cv.ellipse(x, 44, 21 * fo, 13, fill=rgba(CHEEK, 0.42))
        # gözler ve kaşlar
        nose_up = -6 * max(0.0, -b.tilt) * 4
        for side in (-1, 1):
            x, fo = proj(side * 0.42)
            if fo <= 0.12:
                continue
            fk = fo ** 0.7
            _goz(cv, x, 6 + nose_up, 25 * fk, 29, b.look, lid, b.happy)
            by = -36 - b.brow * 11 - (b.brow_skew * 13 if side < 0 else 0) + nose_up
            u = np.linspace(-1, 1, 9)
            bx = x + u * 15 * fk
            byy = by - 4 * (1 - u ** 2) + b.brow_tilt * 8 * u * (-side)
            cv.stroke(np.column_stack((bx, byy)), OUT, 6)
        # burun ve ağız
        x, fo = proj(0.0)
        cv.ellipse(x, 36 + nose_up * 0.6, 9 * (0.6 + 0.4 * fo), 6.5, fill=SKIN_SH)
        mx, _ = proj(0.0, 96.0)
        _agiz(cv, mx, 64 + nose_up * 0.4, b.mouth, b.mopen, 0.55 + 0.45 * math.cos(phi))


def bebek_kollar(cv, b):
    with cv.push(_xf_bebek(b)):
        for side, hand in ((-1, b.hand_l), (1, b.hand_r)):
            hx, hy = hand
            cv.capsule(side * 64, 150, hx, hy, 21, fill=ONESIE, line=OUT, lw=6)
            cv.ellipse(hx, hy, 20, 19, fill=SKIN, line=OUT, lw=5)


def kask_yaka(cv, b):
    if b.helmet <= 0.01:
        return
    a = clamp(b.helmet)
    with cv.push(_xf_bebek(b)):
        cv.ellipse(0, 126, 112 * (0.6 + 0.4 * a), 24, fill=rgba(METAL, a), line=rgba(OUT, a), lw=5)
        for i in range(5):
            x = -70 + i * 35
            cv.circle(x, 126, 5, fill=rgba(NEON, a))


def kask_fanus(cv, b, t=0.0):
    if b.helmet <= 0.01:
        return
    a = clamp(b.helmet)
    sc = 1 + 0.25 * (1 - back_out(a))
    with cv.push(_xf_bebek(b) @ about(S(sc), 0, 0)):
        cv.ellipse(0, -4, 152, 150, fill=rgba((170, 230, 255), 0.13 * a))
        cv.stroke(ellipse_pts(0, -4, 152, 150, n=90), rgba(WHITE, 0.8 * a), 6, closed=True)
        cv.stroke(ellipse_pts(0, -4, 128, 126, a0=3.55, a1=4.35, n=20), rgba(WHITE, 0.75 * a), 13)
        cv.circle(-60, -100, 7, fill=rgba(WHITE, 0.8 * a))
        sweep = (t * 0.6) % 1.0
        cv.stroke(ellipse_pts(0, -4, 140, 138, a0=-0.9 + sweep * 0.3, a1=-0.5 + sweep * 0.3, n=10),
                  rgba(WHITE, 0.35 * a), 6)


# ----------------------------------------------------------- mama sandalyesi --

def sandalye_arka(cv, b, morph, thrust=0.0, t=0.0):
    """Sandalye arkalığı, bacaklar; uzay biçiminde kanatlar ve iticiler."""
    m = clamp(morph)
    frame = mixc(CHAIR, HULL, m)
    cush = mixc(CUSHION, HULL_DK, m)
    leg = mixc(WOOD, METAL, m)
    leg_dk = mixc(WOOD_DK, (110, 118, 160), m)
    with cv.push(T(b.x, b.y) @ S(b.s)):
        # arka bacaklar
        for side in (-1, 1):
            cv.capsule(side * 72, 330, side * 122, 835, 13, fill=leg_dk, line=OUT, lw=5)
        # ayaklık
        cv.rrect(-185, 618, 185, 646, 12, fill=leg, line=OUT, lw=5)
        # ön bacaklar
        for side in (-1, 1):
            cv.capsule(side * 122, 330, side * 205, 858, 15, fill=leg, line=OUT, lw=5)
        # iticiler ve alev
        if m > 0.02:
            for side in (-1, 1):
                for lx, ly, sc in ((side * 205, 858, 1.0), (side * 122, 835, 0.75)):
                    with cv.push(T(lx, ly) @ S(m * sc)):
                        if thrust > 0.01:
                            fl = 1 + 0.18 * math.sin(t * 47 + side * 2 + lx) + 0.1 * math.sin(t * 83 + lx)
                            L = thrust * 210 * fl
                            cv.glow(0, 60 + L * 0.3, 70 + L * 0.5, (255, 170, 60), 0.75 * thrust)
                            cv.poly(catmull([(-30, 30), (0, 40 + L), (30, 30)], k=8), fill=(255, 128, 48))
                            cv.poly(catmull([(-19, 30), (0, 30 + L * 0.72), (19, 30)], k=8), fill=(255, 212, 80))
                            cv.poly(catmull([(-9, 30), (0, 26 + L * 0.42), (9, 30)], k=8), fill=(255, 250, 220))
                        cv.poly([(-24, -10), (24, -10), (34, 34), (-34, 34)], fill=(70, 76, 120), line=OUT, lw=5)
                        cv.rrect(-30, 22, 30, 36, 5, fill=(50, 54, 92))
        # yan kanatlar (uzay)
        if m > 0.02:
            for side in (-1, 1):
                with cv.push(about(S(m, 1), side * 140, 120)):
                    pts = [(side * 140, -10), (side * 214, -70), (side * 226, 170), (side * 140, 230)]
                    cv.poly(pts, fill=frame, line=OUT, lw=6)
                    cv.stroke([(side * 168, 20), (side * 200, 0), (side * 206, 150)], rgba(NEON, m), 6)
            # antenler
            for side in (-1, 1):
                ax, ay = side * 118, -80
                tip = (side * (138 + 10 * m), -80 - 60 * m)
                cv.stroke([(ax, ay), tip], rgba(METAL, m), 6)
                on = 0.5 + 0.5 * math.sin(t * 6 + side)
                cv.glow(tip[0], tip[1], 26, (255, 80, 90), m * on)
                cv.circle(tip[0], tip[1], 9, fill=rgba((255, 90, 100), m), line=rgba(OUT, m), lw=4)
        # arkalık
        cv.rrect(-152, -84, 152, 336, 72, fill=frame, line=OUT, lw=6)
        cv.rrect(-122, -56, 122, 306, 54, fill=cush)
        if m < 0.98:
            dot = rgba(WHITE, 0.55 * (1 - m))
            for i, (x, y) in enumerate([(-80, -10), (-20, -30), (50, -12), (90, 30), (-95, 60),
                                        (0, 20), (70, 95), (-60, 120), (100, 160), (-100, 200)]):
                cv.circle(x, y, 9, fill=dot)
        if m > 0.02:
            cv.stroke(rrect_pts(-122, -56, 122, 306, 54), rgba(NEON, 0.9 * m), 5, closed=True)


def sandalye_tepsi(cv, b, morph, t=0.0, bowl=1.0, spoon=1.0, stick=0.0, lean=0.0):
    """Tepsi; uzay biçiminde kontrol paneli. Kaşık, kumanda koluna dönüşür."""
    m = clamp(morph)
    top = mixc(CHAIR, (44, 48, 86), m)
    front = mixc(TRAY_FRONT, HULL, m)
    with cv.push(T(b.x, b.y) @ S(b.s)):
        cv.rrect(-240, 226, 240, 270, 22, fill=top, line=OUT, lw=6)
        cv.rrect(-232, 256, 232, 322, 26, fill=front, line=OUT, lw=6)
        if m > 0.02:
            cols = [(255, 92, 110), (255, 206, 84), (110, 230, 140), (96, 232, 236)]
            for i, x in enumerate((-196, -160, -124)):
                on = 0.55 + 0.45 * math.sin(t * (5 + i * 1.7) + i * 2)
                c = cols[i % 4]
                cv.glow(x, 289, 30, c, 0.6 * m * on)
                cv.circle(x, 289, 11, fill=rgba(mixc(OUT, c, 0.4 + 0.6 * on), m), line=rgba(OUT, m), lw=4)
            cv.rrect(-92, 282, 6, 296, 7, fill=rgba(HULL_DK, m))
            kx = -80 + 70 * (0.5 + 0.5 * math.sin(t * 1.3))
            cv.rrect(kx - 8, 276, kx + 8, 302, 5, fill=rgba(NEON, m), line=rgba(OUT, m), lw=3)
            # radar
            cv.circle(176, 289, 27, fill=rgba((20, 60, 54), m), line=rgba(OUT, m), lw=4)
            a = t * 3.0
            cv.stroke([(176, 289), (176 + 24 * math.cos(a), 289 + 24 * math.sin(a))], rgba((120, 255, 170), m), 4)
            cv.circle(188, 280, 4, fill=rgba((120, 255, 170), m * (0.5 + 0.5 * math.sin(t * 4))))
            for i in range(4):
                x = 40 + i * 24
                on = (int(t * 4 + i * 1.3) % 3) == 0
                cv.rrect(x, 284, x + 14, 294, 3, fill=rgba((255, 206, 84) if on else (90, 96, 150), m))
        # mama kâsesi
        if bowl * (1 - m) > 0.02:
            a = bowl * (1 - m)
            cv.poly(ellipse_pts(-150, 224, 52, 34, a0=0, a1=math.pi, n=24), fill=rgba((255, 178, 112), a),
                    line=rgba(OUT, a), lw=5)
            cv.ellipse(-150, 224, 52, 11, fill=rgba((255, 150, 64), a), line=rgba(OUT, a), lw=5)
            cv.ellipse(-156, 222, 30, 5, fill=rgba((255, 196, 120), a))
        # kaşık -> kumanda kolu
        if spoon > 0.02 or stick > 0.02:
            u = smooth(stick)
            base = (150.0, 238.0)
            p0 = (lerp(70, base[0], u), lerp(244, base[1], u))
            tip = (lerp(196, base[0] + lean, u), lerp(236, 136, u))
            if u > 0.02:
                cv.ellipse(base[0], 240, 30 * u, 10 * u, fill=(40, 44, 80), line=OUT, lw=5)
            col = mixc(SPOON, (70, 76, 110), u)
            cv.capsule(p0[0], p0[1], tip[0], tip[1], lerp(6, 8, u), fill=col, line=OUT, lw=4)
            hx, hy = tip
            rx, ry = lerp(20, 22, u), lerp(12, 22, u)
            cv.ellipse(hx, hy, rx, ry, fill=mixc(SPOON, (255, 76, 96), u), line=OUT, lw=5)
            cv.ellipse(hx - 6 * u - 4, hy - 6 * u, 6, 4 + 2 * u, fill=rgba(WHITE, 0.8))


# ---------------------------------------------------------------- anne kolu --

def anne_kol(cv, sx, sy, hx, hy, s=1.0, spoon=None, t=0.0, elbow=None):
    """Ekran dışından gelen kol. spoon: (uç_x, uç_y) verilirse brokolili kaşık tutar.
    elbow verilirse kol dirsekten bükülür."""
    if elbow is not None:
        cv.capsule(sx, sy, elbow[0], elbow[1], 44 * s, fill=SLEEVE, line=OUT, lw=6 * s)
        sx, sy = elbow
    dx, dy = hx - sx, hy - sy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    wx, wy = hx - ux * 36 * s, hy - uy * 36 * s
    if spoon is not None:
        tx, ty = spoon
        cv.capsule(hx, hy, tx + (hx - tx) * 0.18, ty + (hy - ty) * 0.18, 7 * s, fill=SPOON, line=OUT, lw=4 * s)
        ang = math.atan2(ty - hy, tx - hx)
        cv.ellipse(tx, ty, 26 * s, 15 * s, fill=SPOON, line=OUT, lw=4 * s, rot=ang)
        brokoli(cv, tx, ty - 6 * s, 0.62 * s, rot=-0.15, t=t)
    cv.capsule(sx, sy, wx, wy, 42 * s, fill=SLEEVE, line=OUT, lw=6 * s)
    cv.capsule(wx + ux * 4 * s, wy + uy * 4 * s, wx - ux * 18 * s, wy - uy * 18 * s, 44 * s,
               fill=SLEEVE_CUFF, line=OUT, lw=5 * s)
    ang = math.atan2(uy, ux)
    cv.ellipse(hx, hy, 38 * s, 30 * s, fill=MOM_SKIN, line=OUT, lw=5 * s, rot=ang)
    nx, ny = -uy, ux
    cv.ellipse(hx + nx * 26 * s + ux * 6 * s, hy + ny * 26 * s + uy * 6 * s, 15 * s, 11 * s,
               fill=MOM_SKIN, line=OUT, lw=4 * s, rot=ang + 0.6)


def anne_kol_pov(cv, sh, el, hand, side, s=1.0):
    """Kameranın bulunduğu yerden uzanan kol: perspektifle incelir, dirsekten bükülür."""
    P = [np.array(sh, float), np.array(el, float), np.array(hand, float)]
    u1 = (P[1] - P[0]) / (np.linalg.norm(P[1] - P[0]) or 1)
    u2 = (P[2] - P[1]) / (np.linalg.norm(P[2] - P[1]) or 1)
    n1, n2 = np.array([-u1[1], u1[0]]), np.array([-u2[1], u2[0]])
    ne = n1 + n2
    ne /= np.linalg.norm(ne) or 1
    wr = P[2] - u2 * 44 * s
    w_sh, w_el, w_wr = 118 * s, 78 * s, 50 * s
    left = [P[0] + n1 * w_sh, P[1] + ne * w_el, wr + n2 * w_wr]
    right = [wr - n2 * w_wr, P[1] - ne * w_el, P[0] - n1 * w_sh]
    pts = catmull(left + right, k=6)
    cv.poly(pts, fill=SLEEVE, line=OUT, lw=6 * s)
    for k in (-0.35, 0.15):
        a = P[1] + ne * w_el * k - u1 * 30 * s
        b = P[1] + ne * w_el * (k + 0.45) + u2 * 24 * s
        cv.stroke([tuple(a), tuple(b)], rgba((214, 96, 92), 0.9), 5 * s)
    c0, c1 = wr - u2 * 16 * s, wr + u2 * 14 * s
    cuff = [c0 + n2 * (w_wr + 8 * s), c1 + n2 * (w_wr + 6 * s), c1 - n2 * (w_wr + 6 * s), c0 - n2 * (w_wr + 8 * s)]
    cv.poly(catmull(cuff, k=4), fill=SLEEVE_CUFF, line=OUT, lw=5 * s)
    ang = math.atan2(u2[1], u2[0])
    hx, hy = P[2]
    cv.ellipse(hx, hy, 44 * s, 36 * s, fill=MOM_SKIN, line=OUT, lw=5 * s, rot=ang)
    for i in range(3):
        fx = hx + u2[0] * 30 * s - n2[0] * side * (i - 1) * 20 * s
        fy = hy + u2[1] * 30 * s - n2[1] * side * (i - 1) * 20 * s
        cv.ellipse(fx, fy, 15 * s, 12 * s, fill=MOM_SKIN, line=OUT, lw=4 * s, rot=ang)
    tx, ty = hx - n2[0] * side * 34 * s + u2[0] * 4 * s, hy - n2[1] * side * 34 * s + u2[1] * 4 * s
    cv.ellipse(tx, ty, 18 * s, 13 * s, fill=MOM_SKIN, line=OUT, lw=4 * s, rot=ang - side * 0.5)


# ---------------------------------------------------------------- brokoli --

_FLORETS = [(0, -64, 40), (-38, -50, 32), (38, -50, 32), (-22, -88, 30), (22, -88, 30), (0, -104, 26),
            (-58, -30, 24), (58, -30, 24), (-48, -76, 22), (48, -76, 22), (0, -38, 30)]


def brokoli(cv, x, y, s, rot=0.0, t=0.0, wobble=0.0, glow=0.0):
    """Brokoli: sap + taç. (x, y) tacın alt orta noktası."""
    with cv.push(T(x, y) @ R(rot) @ S(s)):
        if glow > 0:
            cv.glow(0, -50, 170, (150, 255, 140), glow)
        stem = [(-22, -20), (22, -20), (16, 46), (8, 60), (-8, 60), (-16, 46)]
        cv.poly(catmull(stem, k=5), fill=BROC_STEM, line=OUT, lw=6)
        cv.stroke([(0, -10), (0, 40)], rgba((210, 236, 160), 0.8), 5)
        fl = []
        for i, (fx, fy, fr) in enumerate(_FLORETS):
            if wobble:
                fx += wobble * 3 * math.sin(t * 2.1 + i * 1.7)
                fy += wobble * 3 * math.cos(t * 1.7 + i * 2.3)
                fr *= 1 + wobble * 0.04 * math.sin(t * 2.6 + i)
            fl.append((fx, fy, fr))
        for fx, fy, fr in fl:
            cv.circle(fx, fy, fr + 4, fill=OUT)
        for fx, fy, fr in fl:
            cv.circle(fx, fy, fr - 1, fill=BROC)
        for i, (fx, fy, fr) in enumerate(fl):
            cv.circle(fx + fr * 0.25, fy + fr * 0.35, fr * 0.45, fill=BROC_DK)
            cv.circle(fx - fr * 0.3, fy - fr * 0.35, fr * 0.28, fill=BROC_LT)


def brokoli_gezegen(cv, x, y, r, t=0.0, rot=0.0, alpha=1.0):
    """Uzayda dev, gizemli brokoli gezegeni: halka, atmosfer, yüzen sporlar."""
    s = r / 110.0
    with cv.push(T(x, y) @ R(rot) @ S(s)):
        cv.glow(0, -50, 260, (120, 255, 150), 0.55 * alpha)
        cv.glow(0, -50, 170, (190, 255, 170), 0.35 * alpha)
        ring = (190, 240, 160)
        # halkanın arka yarısı
        cv.stroke(ellipse_pts(0, -40, 185, 44, rot=-0.25, a0=math.pi, a1=TAU, n=60), rgba(ring, 0.55), 14)
    brokoli(cv, x, y + 30 * s, s, rot=rot, t=t, wobble=1.0)
    with cv.push(T(x, y) @ R(rot) @ S(s)):
        cv.stroke(ellipse_pts(0, -40, 185, 44, rot=-0.25, a0=0, a1=math.pi, n=60), rgba(ring, 0.8), 14)
        cv.stroke(ellipse_pts(0, -40, 165, 36, rot=-0.25, a0=0.1, a1=math.pi - 0.1, n=60),
                  rgba((240, 255, 220), 0.45), 5)
        # sporlar
        for i in range(14):
            ph = i * 2.399
            rr = 120 + 50 * ((i * 37) % 11) / 11
            a = ph + t * (0.25 + 0.05 * (i % 3))
            px, py = rr * math.cos(a), -50 + rr * 0.7 * math.sin(a)
            tw = 0.5 + 0.5 * math.sin(t * 3 + i)
            cv.circle(px, py, 3 + 2 * tw, fill=rgba((210, 255, 190), 0.7 * tw))


# ------------------------------------------------------------------ ikonlar --

def roket_ikon(cv, x, y, s, ang=0.0, flame=1.0, t=0.0, body=WHITE, accent=(255, 92, 110)):
    with cv.push(T(x, y) @ R(ang) @ S(s)):
        if flame > 0:
            fl = 1 + 0.15 * math.sin(t * 40)
            cv.glow(0, 78, 60, (255, 170, 60), 0.6 * flame)
            cv.poly(catmull([(-18, 52), (0, 52 + 70 * fl * flame), (18, 52)], k=6), fill=(255, 140, 50))
            cv.poly(catmull([(-10, 52), (0, 52 + 42 * fl * flame), (10, 52)], k=6), fill=(255, 226, 120))
        for side in (-1, 1):
            cv.poly([(side * 22, 10), (side * 46, 44), (side * 40, 62), (side * 18, 50)], fill=accent, line=OUT, lw=6)
        body_pts = catmull([(0, -78), (24, -40), (28, 10), (20, 54), (-20, 54), (-28, 10), (-24, -40)], k=6)
        cv.poly(body_pts, fill=body, line=OUT, lw=6)
        cv.poly(catmull([(0, -78), (18, -50), (-18, -50)], k=4), fill=accent)
        cv.stroke(body_pts, OUT, 6, closed=True)
        cv.circle(0, -8, 13, fill=(110, 200, 240), line=OUT, lw=5)
        cv.circle(-4, -12, 4, fill=WHITE)


def parilti(cv, x, y, r, color=WHITE, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or r <= 0.5:
        return
    cv.poly(star_pts(x, y, r, r * 0.28, 4, rot), fill=rgba(color, alpha))


def brokoli_ikon(cv, x, y, s):
    brokoli(cv, x, y + 22 * s, 0.42 * s)


# --------------------------------------------------------------- arka planlar --

def mutfak(cv, t=0.0):
    """Sıcak, gün ışıklı mutfak. Dünya koordinatlarında çizilir."""
    top, bot = (255, 241, 222), (255, 226, 196)
    y0, y1 = -400, 1180
    n = 28
    for i in range(n):
        a = i / n
        cv.rrect(-400, y0 + (y1 - y0) * a, 1480, y0 + (y1 - y0) * (a + 1.0 / n) + 2, 0, fill=mixc(top, bot, a))
    # pencere
    cv.glow(255, 430, 420, (255, 236, 190), 0.6)
    cv.rrect(64, 196, 446, 716, 34, fill=(255, 255, 255), line=OUT, lw=7)
    cv.rrect(90, 222, 420, 690, 22, fill=(170, 222, 250))
    cv.glow(330, 330, 150, (255, 255, 220), 0.9)
    cv.circle(330, 330, 46, fill=(255, 238, 150))
    for cx, cy, s in ((170, 420, 1.0), (330, 520, 0.8)):
        for dx, dy, r in ((0, 0, 30), (32, -10, 36), (66, 2, 28), (34, 12, 30)):
            cv.circle(cx + dx * s + 12 * math.sin(t * 0.3), cy + dy * s, r * s, fill=(255, 255, 255))
    cv.rrect(90, 600, 420, 690, 0, fill=(150, 210, 130))
    cv.ellipse(170, 612, 120, 34, fill=(126, 196, 112))
    cv.ellipse(360, 618, 110, 30, fill=(110, 186, 100))
    cv.rrect(248, 222, 262, 690, 0, fill=(255, 255, 255))
    cv.rrect(90, 448, 420, 462, 0, fill=(255, 255, 255))
    # perdeler
    for side in (-1, 1):
        x = 255 + side * 205
        pts = catmull([(x - 46, 176), (x + 46, 176), (x + 30 + side * 8, 420), (x + 40, 640),
                       (x - 40, 640), (x - 36 - side * 6, 420)], k=8)
        cv.poly(pts, fill=(255, 180, 186), line=OUT, lw=5)
        for k in (-18, 12):
            cv.stroke([(x + k, 190), (x + k * 1.2, 620)], rgba((236, 140, 150), 0.6), 6)
    cv.rrect(20, 160, 490, 186, 12, fill=(214, 170, 116), line=OUT, lw=5)
    # sarkan saksı
    cv.stroke([(500, -40), (520, 232)], rgba(OUT, 0.8), 4)
    cv.poly([(486, 232), (554, 232), (546, 286), (494, 286)], fill=(232, 136, 96), line=OUT, lw=5)
    for i, a in enumerate((-0.7, -0.2, 0.3, 0.8)):
        sw = 0.08 * math.sin(t * 1.1 + i)
        cv.ellipse(520 + 46 * math.sin(a + sw), 240 + 50 * math.cos(a + sw) + 20, 14, 26,
                   fill=(108, 186, 100), line=OUT, lw=4, rot=a + sw)
    # buzdolabı
    cv.rrect(860, 300, 1220, 1260, 40, fill=(222, 244, 238), line=OUT, lw=7)
    cv.stroke([(860, 640), (1220, 640)], OUT, 6)
    cv.rrect(892, 420, 912, 560, 8, fill=(190, 214, 210), line=OUT, lw=4)
    cv.rrect(892, 700, 912, 900, 8, fill=(190, 214, 210), line=OUT, lw=4)
    # buzdolabındaki çocuk resmi: roket!
    with cv.push(about(R(0.08), 1000, 860)):
        cv.rrect(930, 760, 1070, 950, 6, fill=(255, 255, 255), line=OUT, lw=4)
        cv.stroke(catmull([(950, 920), (980, 880), (1010, 900), (1050, 850)], k=6, closed=False),
                  (255, 196, 84), 5)
        roket_ikon(cv, 1004, 840, 0.5, ang=0.6, flame=0.6, body=(255, 255, 255))
        cv.circle(1000, 762, 9, fill=(255, 92, 110), line=OUT, lw=3)
    cv.circle(960, 360, 18, fill=(255, 206, 84), line=OUT, lw=4)
    cv.circle(1012, 382, 14, fill=(124, 198, 232), line=OUT, lw=4)
    # lambri
    cv.rrect(-400, 1180, 1480, 1600, 0, fill=(206, 232, 214))
    cv.rrect(-400, 1170, 1480, 1196, 0, fill=(255, 255, 255))
    cv.stroke([(-400, 1172), (1480, 1172)], rgba(OUT, 0.6), 4)
    for x in range(-380, 1480, 150):
        cv.rrect(x, 1230, x + 120, 1550, 16, fill=None, line=rgba((180, 210, 192), 1.0), lw=5)
    # zemin
    cv.rrect(-400, 1600, 1480, 2400, 0, fill=(238, 204, 160))
    cv.rrect(-400, 1588, 1480, 1612, 0, fill=(255, 255, 255))
    for i, y in enumerate((1700, 1830, 1990, 2190)):
        cv.stroke([(-400, y), (1480, y)], rgba((214, 176, 128), 1.0), 5)
        off = (i * 170) % 340
        for x in range(-400 + off, 1480, 340):
            cv.stroke([(x, y - (130 if i else 112)), (x, y)], rgba((214, 176, 128), 1.0), 4)
    # yumuşak gölge (sandalyenin altı)
    cv.ellipse(540, 1792, 330, 48, fill=rgba((180, 130, 90), 0.22))
    # güneş ışığı
    for i in range(3):
        x = 140 + i * 120
        cv.poly([(x, 230), (x + 70, 230), (x + 470, 1700), (x + 290, 1700)], fill=rgba((255, 250, 220), 0.12))


class Uzay:
    """Ekran koordinatlarında uzay arka planı: bulutsu dokusu + yıldızlar."""

    def __init__(self, cv_w, cv_h, ss, seed=3):
        rng = np.random.default_rng(seed)
        self.ss = ss
        self.margin = 0.12
        sw, sh = int(cv_w * ss * (1 + 2 * self.margin)), int(cv_h * ss * (1 + 2 * self.margin))
        lw, lh = 180, 320
        small = Image.new("RGB", (lw, lh))
        d = ImageDraw.Draw(small, "RGBA")
        for y in range(lh):
            a = y / lh
            d.line([(0, y), (lw, y)], fill=mixc((10, 10, 40), (40, 20, 84), a))
        for _ in range(26):
            cx, cy = rng.uniform(0, lw), rng.uniform(0, lh)
            r = rng.uniform(18, 60)
            col = [(124, 77, 255), (255, 95, 162), (46, 196, 182), (90, 120, 255)][rng.integers(0, 4)]
            d.ellipse((cx - r, cy - r * 0.7, cx + r, cy + r * 0.7), fill=rgba(col, rng.uniform(0.06, 0.2)))
        small = small.filter(ImageFilter.GaussianBlur(14))
        self.tex = small.resize((sw, sh), Image.BICUBIC)
        n = 240
        self.stars = np.column_stack((rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(0.2, 1.0, n),
                                      rng.uniform(0, TAU, n), rng.uniform(1.5, 4.0, n)))

    def draw(self, cv, t, speed=0.0, drift=(0.0, 0.0), shake=(0.0, 0.0), travel=0.0):
        """speed: yıldız izlerinin uzunluğu; travel: yıldızların aşağı kayma miktarı (tasarım birimi)."""
        mx = int(self.margin * cv.img.width / (1 + 2 * self.margin))
        my = int(self.margin * cv.img.height / (1 + 2 * self.margin))
        ox = int(clamp(mx + (drift[0] + shake[0] * 0.4) * cv.k, 0, 2 * mx))
        oy = int(clamp(my + (drift[1] + shake[1] * 0.4) * cv.k, 0, 2 * my))
        cv.img.paste(self.tex.crop((ox, oy, ox + cv.img.width, oy + cv.img.height)), (0, 0))
        with cv.screen():
            for x, y, z, ph, r in self.stars:
                yy = (y + travel * z) % (H + 200) - 100
                xx = x + shake[0] * z
                yy += shake[1] * z
                tw = 0.6 + 0.4 * math.sin(t * (1.5 + 2 * z) + ph)
                col = rgba((255, 255, 255), clamp(0.35 + 0.65 * z * tw))
                if speed > 0.12:
                    L = speed * 260 * z
                    cv.stroke([(xx, yy - L), (xx, yy)], col, r * 0.7 * (0.6 + 0.4 * z), caps=True)
                elif r > 3.4 and z > 0.7:
                    parilti(cv, xx, yy, r * 3.2 * tw, WHITE, clamp(0.5 + 0.5 * tw))
                else:
                    cv.circle(xx, yy, r * 0.55 * (0.7 + 0.3 * tw), fill=col)


def halkali_gezegen(cv, x, y, r, t=0.0):
    cv.stroke(ellipse_pts(x, y, r * 1.8, r * 0.42, rot=-0.35, a0=math.pi, a1=TAU, n=40), rgba((255, 214, 150), 0.8),
              r * 0.12)
    cv.circle(x, y, r, fill=(255, 160, 96))
    cv.ellipse(x + r * 0.25, y + r * 0.2, r * 0.75, r * 0.7, fill=(240, 130, 80))
    cv.ellipse(x - r * 0.3, y - r * 0.35, r * 0.35, r * 0.22, fill=rgba((255, 220, 170), 0.8))
    cv.stroke(ellipse_pts(x, y, r * 1.8, r * 0.42, rot=-0.35, a0=0, a1=math.pi, n=40), rgba((255, 214, 150), 0.9),
              r * 0.12)


def kokpit(cv, t, slide=1.0, alarm=0.0):
    """Ekranın iki yanında kokpit panelleri (ekran koordinatları)."""
    if slide <= 0.01:
        return
    with cv.screen():
        for side in (-1, 1):
            off = (1 - ease_out(slide)) * 160
            x_edge = 0 if side < 0 else W
            with cv.push(T(-side * off, 0)):
                x0 = x_edge - (0 if side < 0 else 112)
                x1 = x_edge + (112 if side < 0 else 0)
                cv.rrect(x0 - 40, 520, x1 + 40, 1500, 40, fill=HULL, line=OUT, lw=7)
                inner = x1 - 26 if side < 0 else x0 + 26
                cv.stroke([(inner, 560), (inner, 1460)], rgba(NEON, 0.7), 5)
                for i in range(9):
                    y = 600 + i * 96
                    lx = (x0 + x1) / 2 + side * 6
                    ph = t * (3 + (i % 3)) + i * 1.3 + side
                    on = 0.5 + 0.5 * math.sin(ph)
                    col = [(255, 92, 110), (255, 206, 84), (110, 230, 140), (96, 232, 236)][(i + (side > 0)) % 4]
                    if alarm > 0:
                        col = mixc(col, (255, 60, 80), alarm * (0.5 + 0.5 * math.sin(t * 18)))
                    cv.glow(lx, y, 34, col, 0.5 * on)
                    cv.circle(lx, y, 12, fill=mixc(OUT, col, 0.35 + 0.65 * on), line=OUT, lw=4)
