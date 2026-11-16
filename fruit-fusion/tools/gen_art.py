#!/usr/bin/env python3
"""Fruit Fusion - procedural art generator (original artwork, no external sources).

Usage (from fruit-fusion/):
    python3 tools/gen_art.py               # fruits, icon, launch logo, backdrop
    python3 tools/gen_art.py --fetch-font  # additionally (re)download the OFL UI font

Outputs:
    assets/fruits/fruit_01.png .. fruit_11.png  512x512 RGBA, body = circle touching all edges
    assets/icon/icon_1024.png                   1024x1024 RGB (no alpha, square corners)
    assets/icon/launch_logo.png                 600x600 RGBA logo mark
    assets/ui/jar_bg.png                        720x1560 RGB low-contrast backdrop
    assets/fonts/ui_font.ttf + OFL.txt          (only with --fetch-font) Baloo 2, SIL OFL 1.1

Everything is drawn top-down / stylised: stems, leaves and crowns are surface details INSIDE
the circle, because the physics collider is a circle the size of the sprite.
Deterministic: fixed seeds, so re-running reproduces identical files.
Requires: Pillow, numpy.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = 512          # final sprite size
SS = 4             # supersampling factor
S = OUT * SS       # working resolution
H = S / 2.0

_yy, _xx = np.mgrid[0:S, 0:S].astype(np.float32)
X = (_xx + 0.5) / H - 1.0
Y = (_yy + 0.5) / H - 1.0
R = np.hypot(X, Y)
Z = np.sqrt(np.clip(1.0 - R * R, 0.0, 1.0))
THETA = np.arctan2(Y, X)


# ----------------------------------------------------------------------------- helpers
def px(v):
    """normalised [-1,1] -> working pixels"""
    return (v + 1.0) * H


def P(x, y):
    return (px(x), px(y))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def flat(col):
    a = np.empty((S, S, 3), np.float32)
    a[:] = np.array(col, np.float32)
    return a


def mix(a, col, w):
    """blend array a towards colour (or array) by weight map w"""
    w = w[..., None] if getattr(w, "ndim", 0) == 2 else w
    return a * (1 - w) + np.asarray(col, np.float32) * w


def noise(cells, seed, octaves=1):
    """smooth value noise in [0,1] at working resolution"""
    rng = np.random.default_rng(seed)
    acc = np.zeros((S, S), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = cells * (2 ** o)
        small = (rng.random((n, n)) * 255).astype(np.uint8)
        big = Image.fromarray(small, "L").resize((S, S), Image.BICUBIC)
        acc += np.asarray(big, np.float32) / 255.0 * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def grain(seed, blur=1.5):
    """fine speckle in [0,1]"""
    rng = np.random.default_rng(seed)
    g = Image.fromarray((rng.random((S, S)) * 255).astype(np.uint8), "L")
    g = g.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(g, np.float32) / 255.0
    return np.clip((a - 0.5) * (2.5 + blur * 2.0) + 0.5, 0, 1)


class Layer:
    """RGBA PIL layer in normalised coordinates, composited onto an albedo array."""

    def __init__(self):
        self.im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def circle(self, x, y, r, fill, ry=None):
        ry = r if ry is None else ry
        self.d.ellipse([px(x - r), px(y - ry), px(x + r), px(y + ry)], fill=fill)

    def ring(self, x, y, r, col, w):
        self.d.ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], outline=col, width=max(1, int(w * H)))

    def poly(self, pts, fill):
        self.d.polygon([P(*p) for p in pts], fill=fill)

    def line(self, pts, col, w):
        wpx = max(1, int(w * H))
        self.d.line([P(*p) for p in pts], fill=col, width=wpx, joint="curve")
        r = wpx / 2.0
        for p in (pts[0], pts[-1]):
            cx, cy = P(*p)
            self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    def blur(self, r):
        self.im = self.im.filter(ImageFilter.GaussianBlur(r * H))
        self.d = ImageDraw.Draw(self.im)
        return self

    def onto(self, alb, opacity=1.0):
        a = np.asarray(self.im, np.float32)
        w = a[..., 3:4] / 255.0 * opacity
        return alb * (1 - w) + a[..., :3] * w


def star(cx, cy, r_out, r_in, n, rot=0.0):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sphere_points(n, seed, zmin=0.12):
    """random points on the visible hemisphere, projected (denser towards the rim like a real ball)"""
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n * 3, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    v = v[v[:, 2] > zmin][:n]
    return v


def curve(p0, p1, p2, n=40):
    """quadratic bezier"""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]))
    return out


def finish(alb, outline, gloss=0.55, gloss_size=1.0, ambient=0.66, diffuse=0.48, rim_dark=0.55):
    """shade an albedo map as a ball: soft light, darker rim, outline, glossy highlight, circular alpha"""
    lx, ly, lz = -0.42, -0.52, 0.74
    lam = np.clip(X * lx + Y * ly + Z * lz, 0.0, 1.0)
    col = alb * (ambient + diffuse * lam)[..., None]
    # warm bounce light on the lower right
    bounce = smooth(0.55, 0.95, R) * np.clip(X * 0.6 + Y * 0.8, 0, 1) * 0.16
    col = col + (255.0 - col) * bounce[..., None] * 0.5
    # darker rim
    col = mix(col, col * 0.5, smooth(0.70, 0.99, R) * rim_dark)
    # outline
    col = mix(col, outline, smooth(0.925, 0.950, R))
    # glossy highlight (rotated soft ellipse) + small glint
    ang = math.radians(-38)
    gx, gy = X + 0.40, Y + 0.46
    u = gx * math.cos(ang) - gy * math.sin(ang)
    v = gx * math.sin(ang) + gy * math.cos(ang)
    g = np.exp(-((u / (0.30 * gloss_size)) ** 2 + (v / (0.14 * gloss_size)) ** 2) ** 1.4)
    g2 = np.exp(-(((X + 0.10) / 0.06) ** 2 + ((Y + 0.70) / 0.045) ** 2) ** 1.3) * 0.8
    g = np.clip(g + g2, 0, 1) * gloss
    col = col + (255.0 - col) * g[..., None]
    alpha = np.clip((1.0 - R) * H + 0.5, 0.0, 1.0)
    rgba = np.dstack([np.clip(col, 0, 255), alpha * 255.0]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def pores(alb, n, seed, dark, light, rmin=0.010, rmax=0.018, opacity=0.8):
    lay = Layer()
    rng = np.random.default_rng(seed + 1)
    for v in sphere_points(n, seed):
        r = rng.uniform(rmin, rmax)
        ry = r * max(0.35, v[2])  # foreshortening near the rim
        a = math.atan2(v[1], v[0])
        # approximate foreshortened dot by an ellipse squeezed along the radial direction
        cx, cy = float(v[0]), float(v[1])
        pts = []
        for k in range(10):
            t = 2 * math.pi * k / 10
            ex, ey = ry * math.cos(t), r * math.sin(t)
            pts.append((cx + ex * math.cos(a) - ey * math.sin(a), cy + ex * math.sin(a) + ey * math.cos(a)))
        lay.poly([(p[0] + 0.006, p[1] + 0.006) for p in pts], light)
        lay.poly(pts, dark)
    lay.blur(0.003)
    return lay.onto(alb, opacity)


# ----------------------------------------------------------------------------- fruits
def blueberry():
    alb = flat((54, 72, 158))
    alb = mix(alb, (36, 44, 120), noise(5, 11, 2) * 0.55)
    # dusty bloom
    alb = mix(alb, (150, 170, 225), smooth(0.45, 0.8, noise(7, 12, 3)) * 0.38)
    cx, cy = 0.06, 0.02
    lay = Layer()
    lay.circle(cx, cy, 0.50, (30, 36, 100, 150))
    lay.blur(0.05)
    alb = lay.onto(alb)
    lay = Layer()
    lay.poly(star(cx, cy, 0.47, 0.23, 5, -math.pi / 2), (118, 140, 215, 255))   # pale calyx edge
    lay.poly(star(cx, cy, 0.40, 0.19, 5, -math.pi / 2), (22, 26, 78, 255))      # dark crown
    lay.circle(cx, cy, 0.15, (48, 58, 132, 255))
    lay.circle(cx, cy, 0.07, (18, 20, 62, 255))
    lay.blur(0.006)
    alb = lay.onto(alb)
    return finish(alb, (20, 24, 72), gloss=0.50)


def sour_cherry():
    alb = flat((208, 26, 50))
    alb = mix(alb, (150, 8, 40), noise(4, 21, 2) * 0.45)
    alb = mix(alb, (240, 70, 70), smooth(0.55, 0.9, noise(6, 22, 2)) * 0.25)
    dx, dy = 0.02, -0.10
    lay = Layer()
    lay.circle(dx, dy, 0.33, (96, 0, 28, 235), ry=0.27)   # stem dimple
    lay.blur(0.07)
    alb = lay.onto(alb)
    lay = Layer()
    lay.circle(dx - 0.05, dy - 0.04, 0.20, (255, 120, 120, 120), ry=0.05)  # lip highlight of dimple
    lay.blur(0.03)
    alb = lay.onto(alb)
    stem = curve((dx, dy), (0.20, -0.52), (0.60, -0.50))
    lay = Layer()
    lay.line([(p[0] + 0.035, p[1] + 0.05) for p in stem], (90, 0, 26, 170), 0.10)  # stem shadow
    lay.blur(0.02)
    alb = lay.onto(alb)
    lay = Layer()
    lay.line(stem, (70, 82, 24, 255), 0.105)
    lay.line(stem, (150, 172, 62, 255), 0.07)
    lay.line([(p[0] - 0.008, p[1] - 0.012) for p in stem], (206, 222, 120, 255), 0.022)
    ex, ey = stem[-1]
    lay.circle(ex, ey, 0.075, (92, 64, 30, 255))          # woody stem end
    lay.circle(ex, ey, 0.045, (170, 130, 78, 255))
    lay.circle(dx, dy, 0.058, (58, 66, 20, 255))
    lay.blur(0.004)
    alb = lay.onto(alb)
    return finish(alb, (88, 0, 26), gloss=0.72, gloss_size=1.05)


def apricot():
    alb = flat((255, 178, 78))
    alb = mix(alb, (255, 205, 110), noise(4, 31, 2) * 0.5)
    blush = np.exp(-(((X - 0.42) / 0.55) ** 2 + ((Y - 0.30) / 0.60) ** 2)) * (0.55 + 0.45 * noise(5, 32, 2))
    alb = mix(alb, (236, 96, 58), np.clip(blush, 0, 1) * 0.72)
    seam = curve((-0.16, -1.0), (0.34, -0.05), (-0.10, 1.0), 60)
    lay = Layer()
    lay.line(seam, (176, 92, 22, 255), 0.085)
    lay.blur(0.035)
    alb = lay.onto(alb, 0.85)
    lay = Layer()
    lay.line([(p[0] - 0.06, p[1]) for p in seam], (255, 232, 160, 200), 0.04)
    lay.blur(0.03)
    alb = lay.onto(alb, 0.7)
    lay = Layer()
    lay.line(seam, (150, 72, 16, 255), 0.022)
    lay.blur(0.006)
    alb = lay.onto(alb, 0.9)
    # stem dimple on the seam
    sx, sy = 0.035, -0.50
    lay = Layer()
    lay.circle(sx, sy, 0.17, (150, 70, 14, 230), ry=0.13)
    lay.blur(0.04)
    alb = lay.onto(alb)
    lay = Layer()
    lay.circle(sx, sy, 0.06, (88, 52, 20, 255))
    lay.circle(sx - 0.01, sy - 0.01, 0.028, (150, 104, 56, 255))
    lay.blur(0.004)
    alb = lay.onto(alb)
    # freckles
    rng = np.random.default_rng(33)
    lay = Layer()
    for v in sphere_points(46, 34, 0.25):
        lay.circle(float(v[0]), float(v[1]), rng.uniform(0.008, 0.016), (170, 70, 30, 190))
    lay.blur(0.004)
    alb = lay.onto(alb, 0.8)
    return finish(alb, (150, 74, 16), gloss=0.34, gloss_size=1.15)


def lemon():
    alb = flat((252, 226, 58))
    alb = mix(alb, (255, 240, 120), noise(4, 41, 2) * 0.45)
    cx, cy = 0.05, 0.06
    d = np.hypot(X - cx, Y - cy)
    alb = mix(alb, (196, 208, 62), np.exp(-(d / 0.42) ** 2) * 0.55)      # greenish pole
    alb = pores(alb, 300, 42, (206, 172, 20, 255), (255, 248, 170, 255))
    # radial wrinkles around the pointed tip
    rng = np.random.default_rng(43)
    lay = Layer()
    for i in range(16):
        a = 2 * math.pi * i / 16 + rng.uniform(-0.1, 0.1)
        r1 = rng.uniform(0.40, 0.58)
        lay.line([(cx + 0.17 * math.cos(a), cy + 0.17 * math.sin(a)),
                  (cx + r1 * math.cos(a + 0.08), cy + r1 * math.sin(a + 0.08))], (168, 150, 18, 255), 0.026)
    lay.blur(0.012)
    alb = lay.onto(alb, 0.75)
    # the tip (nipple) seen from above
    lay = Layer()
    lay.circle(cx + 0.03, cy + 0.04, 0.24, (150, 132, 12, 200))
    lay.blur(0.035)
    alb = lay.onto(alb, 0.8)
    lay = Layer()
    lay.circle(cx, cy, 0.19, (150, 150, 26, 255))
    lay.circle(cx, cy, 0.165, (236, 226, 84, 255))
    lay.circle(cx - 0.03, cy - 0.035, 0.085, (255, 252, 190, 255))
    lay.circle(cx + 0.035, cy + 0.04, 0.05, (160, 150, 34, 255))
    lay.blur(0.012)
    alb = lay.onto(alb)
    return finish(alb, (150, 118, 0), gloss=0.50, ambient=0.72, diffuse=0.42, rim_dark=0.45)


def mandarin():
    alb = flat((255, 136, 22))
    alb = mix(alb, (255, 166, 50), noise(4, 51, 2) * 0.5)
    cx, cy = -0.04, -0.06
    # segment creases
    lay = Layer()
    for i in range(10):
        a = 2 * math.pi * i / 10 + 0.2
        pts = [(cx + r * math.cos(a + 0.10 * r), cy + r * math.sin(a + 0.10 * r)) for r in np.linspace(0.16, 1.15, 14)]
        lay.line(pts, (196, 78, 0, 255), 0.05)
    lay.blur(0.024)
    alb = lay.onto(alb, 0.62)
    alb = pores(alb, 300, 52, (214, 92, 0, 255), (255, 196, 96, 255))
    lay = Layer()
    lay.circle(cx, cy, 0.30, (180, 70, 0, 220))
    lay.blur(0.05)
    alb = lay.onto(alb, 0.8)
    lay = Layer()
    lay.poly(star(cx, cy, 0.290, 0.130, 5, 0.3), (30, 76, 22, 255))
    lay.poly(star(cx, cy, 0.245, 0.115, 5, 0.3), (88, 158, 58, 255))
    lay.circle(cx, cy, 0.085, (40, 92, 30, 255))
    lay.circle(cx, cy, 0.050, (168, 196, 110, 255))
    lay.blur(0.005)
    alb = lay.onto(alb)
    return finish(alb, (150, 56, 0), gloss=0.52)


def pomegranate():
    alb = flat((158, 24, 54))
    alb = mix(alb, (112, 10, 44), noise(5, 61, 2) * 0.6)
    alb = mix(alb, (205, 70, 70), smooth(0.6, 0.95, noise(7, 62, 2)) * 0.35)
    cx, cy = 0.0, 0.03
    # faint hexagonal ridges
    ridge = (np.cos(6 * (np.arctan2(Y - cy, X - cx)) + 0.5) * 0.5 + 0.5) ** 3
    alb = mix(alb, (214, 84, 84), ridge * smooth(0.35, 0.8, R) * 0.30)
    lay = Layer()
    lay.circle(cx + 0.04, cy + 0.06, 0.60, (70, 0, 26, 190))
    lay.blur(0.06)
    alb = lay.onto(alb)
    lay = Layer()
    lay.poly(star(cx, cy, 0.60, 0.30, 6, 0.26), (255, 196, 150, 255))   # light crown edge
    lay.poly(star(cx, cy, 0.535, 0.275, 6, 0.26), (92, 6, 34, 255))     # sepals
    lay.circle(cx, cy, 0.245, (242, 200, 112, 255))                     # open calyx
    lay.circle(cx, cy, 0.185, (178, 120, 52, 255))
    rng = np.random.default_rng(63)
    for i in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.uniform(0, 1)) * 0.20
        lay.circle(cx + r * math.cos(a), cy + r * math.sin(a), 0.020, (255, 236, 170, 255))
    lay.blur(0.005)
    alb = lay.onto(alb)
    return finish(alb, (64, 0, 24), gloss=0.42, ambient=0.64)


def peach():
    alb = flat((255, 206, 150))
    blush = smooth(0.30, 0.72, noise(3, 71, 2) * 0.6 + 0.4 * np.clip(0.5 + 0.55 * X + 0.35 * Y, 0, 1))
    alb = mix(alb, (240, 104, 112), blush * 0.85)
    alb = mix(alb, (255, 232, 200), (grain(72, 2.0) - 0.5) * 0.30 + 0.10)   # velvety fuzz
    cleft = curve((0.10, -1.02), (-0.42, -0.10), (0.16, 1.02), 60)
    lay = Layer()
    lay.line(cleft, (190, 58, 78, 255), 0.15)
    lay.blur(0.06)
    alb = lay.onto(alb, 0.75)
    lay = Layer()
    lay.line([(p[0] + 0.10, p[1]) for p in cleft], (255, 226, 200, 220), 0.06)
    lay.blur(0.05)
    alb = lay.onto(alb, 0.65)
    lay = Layer()
    lay.line(cleft, (164, 40, 66, 255), 0.03)
    lay.blur(0.012)
    alb = lay.onto(alb, 0.8)
    # leaf lying on the fruit (inside the circle)
    bx, by = -0.10, -0.46
    tx, ty = 0.58, -0.30
    ang = math.atan2(ty - by, tx - bx)
    ln = math.hypot(tx - bx, ty - by)
    leaf = []
    for i in range(25):
        t = i / 24
        w = 0.21 * math.sin(math.pi * t) ** 0.8
        leaf.append((t * ln, -w))
    for i in range(25):
        t = 1 - i / 24
        w = 0.17 * math.sin(math.pi * t) ** 0.8
        leaf.append((t * ln, w))
    rot = lambda p: (bx + p[0] * math.cos(ang) - p[1] * math.sin(ang), by + p[0] * math.sin(ang) + p[1] * math.cos(ang))
    leaf = [rot(p) for p in leaf]
    lay = Layer()
    lay.poly([(p[0] + 0.04, p[1] + 0.06) for p in leaf], (150, 40, 60, 170))
    lay.blur(0.03)
    alb = lay.onto(alb)
    lay = Layer()
    lay.poly(leaf, (34, 96, 44, 255))
    inner = [(bx + (p[0] - bx) * 0.86 + 0.045 * math.cos(ang), by + (p[1] - by) * 0.86 + 0.045 * math.sin(ang)) for p in leaf]
    lay.poly(inner, (96, 176, 78, 255))
    lay.line([rot((0.02, 0)), rot((ln * 0.93, 0))], (38, 104, 48, 255), 0.022)
    for t in (0.25, 0.42, 0.59, 0.75):
        for sgn in (-1, 1):
            lay.line([rot((t * ln, 0)), rot((t * ln + 0.09, sgn * 0.105 * math.sin(math.pi * t)))], (52, 124, 58, 255), 0.012)
    lay.circle(bx, by, 0.065, (96, 62, 30, 255))
    lay.circle(bx, by, 0.035, (160, 116, 66, 255))
    lay.blur(0.004)
    alb = lay.onto(alb)
    return finish(alb, (150, 44, 62), gloss=0.26, gloss_size=1.2, ambient=0.70, diffuse=0.44)


def quince():
    alb = flat((206, 192, 62))
    alb = mix(alb, (172, 180, 70), noise(4, 81, 2) * 0.6)
    cx, cy = 0.02, 0.10
    th = np.arctan2(Y - cy, X - cx)
    d = np.hypot(X - cx, Y - cy)
    # five lumpy lobes: dark furrows between them, lighter crests
    lob = np.cos(5 * th + 0.6 + 0.25 * np.sin(d * 4))
    furrow = smooth(0.55, 1.0, -lob) * smooth(0.08, 0.35, d) * (1 - 0.35 * smooth(0.6, 1.1, d))
    alb = mix(alb, (116, 118, 22), furrow * 0.72)
    alb = mix(alb, (236, 226, 110), smooth(0.4, 1.0, lob) * smooth(0.15, 0.5, d) * 0.40)
    # downy grey fuzz patches
    fuzz = smooth(0.56, 0.74, noise(9, 82, 3)) * (0.55 + 0.45 * grain(83, 1.2))
    alb = mix(alb, (232, 228, 196), fuzz * 0.50)
    lay = Layer()
    lay.circle(cx, cy, 0.27, (92, 84, 14, 235))
    lay.blur(0.05)
    alb = lay.onto(alb)
    lay = Layer()
    lay.poly(star(cx, cy, 0.25, 0.10, 5, 0.6 + math.pi / 5), (62, 40, 16, 255))   # dried calyx
    lay.poly(star(cx, cy, 0.17, 0.08, 5, 0.6 + math.pi / 5), (124, 86, 40, 255))
    lay.circle(cx, cy, 0.06, (40, 26, 10, 255))
    lay.blur(0.006)
    alb = lay.onto(alb)
    return finish(alb, (86, 82, 8), gloss=0.34, ambient=0.66)


def coconut():
    alb = flat((124, 80, 46))
    alb = mix(alb, (92, 56, 30), noise(5, 91, 2) * 0.7)
    cx, cy = -0.06, -0.04
    rng = np.random.default_rng(92)
    cols = [(176, 128, 80, 255), (74, 44, 24, 255), (150, 104, 62, 255), (56, 34, 18, 255), (198, 154, 104, 255)]
    lay = Layer()
    for i in range(520):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(0.10, 1.0)
        ln = rng.uniform(0.10, 0.34)
        sw = rng.uniform(-0.22, 0.22)
        pts = []
        for k in range(6):
            r = r0 + ln * k / 5
            aa = a + sw * (k / 5) + 0.35 * (r - r0)
            pts.append((cx + r * math.cos(aa), cy + r * math.sin(aa)))
        lay.line(pts, cols[int(rng.integers(0, len(cols)))], rng.uniform(0.008, 0.02))
    lay.blur(0.0035)
    alb = lay.onto(alb, 0.85)
    # pale fibrous tuft at the pole
    lay = Layer()
    lay.circle(cx, cy, 0.26, (60, 36, 18, 200))
    lay.blur(0.05)
    alb = lay.onto(alb)
    lay = Layer()
    for i in range(70):
        a = rng.uniform(0, 2 * math.pi)
        r1 = rng.uniform(0.12, 0.30)
        c = (226, 196, 150, 255) if i % 3 else (168, 128, 84, 255)
        lay.line([(cx, cy), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], c, 0.016)
    lay.circle(cx, cy, 0.075, (238, 214, 172, 255))
    lay.blur(0.005)
    alb = lay.onto(alb)
    return finish(alb, (46, 26, 12), gloss=0.20, gloss_size=1.1, ambient=0.66)


def _voronoi_edges(n_pts, seed, res=640):
    """distance-to-cell-border field (second nearest - nearest site) on ball-warped coordinates"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32)
    x = (xx + 0.5) / (res / 2) - 1
    y = (yy + 0.5) / (res / 2) - 1
    r = np.hypot(x, y)
    k = np.arcsin(np.clip(r, 0, 0.999)) / np.maximum(r, 1e-4)   # unwrap the sphere: cells shrink at the rim
    u, v = (x * k).ravel(), (y * k).ravel()
    pts = rng.uniform(-1.65, 1.65, size=(n_pts, 2)).astype(np.float32)
    d1 = np.full(u.shape, 1e9, np.float32)
    d2 = np.full(u.shape, 1e9, np.float32)
    for p in pts:
        d = np.hypot(u - p[0], v - p[1])
        lo = np.minimum(d1, d)
        d2 = np.minimum(d2, np.maximum(d1, d))
        d1 = lo
    e = (d2 - d1).reshape(res, res)
    return np.asarray(Image.fromarray(e, "F").resize((S, S), Image.BICUBIC), np.float32)


def melon():
    alb = flat((164, 172, 104))                       # grey-green rind
    alb = mix(alb, (196, 186, 120), noise(4, 101, 2) * 0.6)
    e = _voronoi_edges(210, 102) + (noise(24, 103, 2) - 0.5) * 0.05
    net_shadow = smooth(0.105, 0.03, e)
    net = smooth(0.060, 0.022, e)
    alb = mix(alb, (104, 116, 60), net_shadow * 0.60)
    alb = mix(alb, (246, 238, 208), net)              # cream netting
    cx, cy = 0.04, -0.02
    lay = Layer()
    lay.circle(cx, cy, 0.25, (86, 94, 44, 230))
    lay.blur(0.04)
    alb = lay.onto(alb)
    lay = Layer()
    lay.circle(cx, cy, 0.175, (240, 230, 196, 255))   # stem scar ring
    lay.circle(cx, cy, 0.125, (122, 118, 66, 255))
    lay.circle(cx, cy, 0.060, (196, 184, 134, 255))
    lay.blur(0.006)
    alb = lay.onto(alb)
    return finish(alb, (74, 82, 34), gloss=0.26, gloss_size=1.1, ambient=0.72, diffuse=0.40, rim_dark=0.5)


def dragon_fruit():
    alb = flat((226, 38, 120))
    alb = mix(alb, (180, 16, 96), noise(5, 111, 2) * 0.6)
    cx, cy = 0.0, 0.0
    rings = [(0.80, 13, 0.40, 0.25, 0.10), (0.52, 10, 0.40, 0.25, 0.42), (0.25, 7, 0.36, 0.22, 0.2), (0.0, 4, 0.30, 0.19, 0.5)]
    for r0, cnt, ln, wd, off in rings:
        shadow, scales, tips = Layer(), Layer(), Layer()
        for i in range(cnt):
            a = 2 * math.pi * (i + off) / cnt
            ca, sa = math.cos(a), math.sin(a)
            tilt = 0.20

            def pt(u, v, grow=0.0):
                # u along the scale (0 base -> 1 tip), v across; slight sideways sweep
                uu = r0 + (u * ln) + grow * (u - 0.3)
                vv = v * (wd + grow) + tilt * u * u * ln
                return (cx + uu * ca - vv * sa, cy + uu * sa + vv * ca)

            def shape(grow=0.0, u0=0.0):
                left = [pt(u, -math.sin(math.pi * min(1.0, 0.5 + 0.5 * u)) ** 0.9, grow) for u in np.linspace(u0, 1, 14)]
                right = [pt(u, math.sin(math.pi * min(1.0, 0.5 + 0.5 * u)) ** 0.9, grow) for u in np.linspace(1, u0, 14)]
                return left + right

            shadow.poly([(p[0] + 0.02, p[1] + 0.035) for p in shape(0.03)], (112, 0, 62, 220))
            scales.poly(shape(0.022), (128, 6, 72, 255))
            scales.poly(shape(), (246, 96, 158, 255))
            tips.poly(shape(0.0, 0.55), (120, 196, 76, 255))
            tips.poly(shape(-0.035, 0.74), (190, 232, 120, 255))
        shadow.blur(0.02)
        alb = shadow.onto(alb)
        scales.blur(0.004)
        alb = scales.onto(alb)
        tips.blur(0.02)
        alb = tips.onto(alb, 0.95)
    return finish(alb, (108, 0, 60), gloss=0.40)


FRUITS = [blueberry, sour_cherry, apricot, lemon, mandarin, pomegranate, peach, quince, coconut, melon, dragon_fruit]
_cache = {}


def fruit_hi(tier):
    """tier 1..11 -> supersampled RGBA image (S x S)"""
    if tier not in _cache:
        _cache[tier] = FRUITS[tier - 1]()
    return _cache[tier]


def fruit_sprite(tier, size=OUT, rot=0.0):
    im = fruit_hi(tier)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC)
    return im.resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------------------- icon / logo
def spark(size, col_core=(255, 255, 255), col_glow=(255, 236, 130)):
    """four-point starburst with a soft glow, RGBA size x size"""
    s2 = size * 2
    c = s2 / 2
    im = Image.new("RGBA", (s2, s2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def burst(r_out, r_in, rot, col):
        pts = []
        for i in range(8):
            r = r_out if i % 2 == 0 else r_in
            a = rot + math.pi * i / 4
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=col)

    burst(c * 0.98, c * 0.20, 0.0, col_glow + (255,))
    burst(c * 0.62, c * 0.17, math.pi / 4, col_glow + (255,))
    glow = im.filter(ImageFilter.GaussianBlur(s2 * 0.035))
    im2 = Image.new("RGBA", (s2, s2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im2)
    burst(c * 0.86, c * 0.13, 0.0, col_core + (255,))
    burst(c * 0.50, c * 0.11, math.pi / 4, col_core + (255,))
    d.ellipse([c - c * 0.17, c - c * 0.17, c + c * 0.17, c + c * 0.17], fill=col_core + (255,))
    im2 = im2.filter(ImageFilter.GaussianBlur(s2 * 0.004))
    out = Image.alpha_composite(glow, im2)
    return out.resize((size, size), Image.LANCZOS)


def shadow_of(sprite, blur, col, opacity):
    a = sprite.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opacity))
    sh = Image.new("RGBA", sprite.size, col + (0,))
    sh.putalpha(a)
    return sh


def paste_c(dst, src, cx, cy):
    dst.alpha_composite(src, (int(round(cx - src.width / 2)), int(round(cy - src.height / 2))))


def compose_mark(size, tier=1, shadow_col=(150, 60, 10), shadow_op=0.38, halo=True):
    """logo mark: two identical fruits touching, fusion spark between them. RGBA size x size."""
    W = size * 2
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    k = W / 1024.0
    fs = int(480 * k)
    a = fruit_sprite(tier, fs, rot=24)
    b = fruit_sprite(tier, fs, rot=-52)
    pa = (512 - 196, 512 + 118)
    pb = (512 + 196, 512 - 118)
    for spr, (x, y) in ((a, pa), (b, pb)):
        pad = Image.new("RGBA", (fs + int(160 * k), fs + int(160 * k)), (0, 0, 0, 0))
        paste_c(pad, spr, pad.width / 2, pad.height / 2)
        paste_c(im, shadow_of(pad, 22 * k, shadow_col, shadow_op), x * k + 10 * k, y * k + 30 * k)
    paste_c(im, a, pa[0] * k, pa[1] * k)
    paste_c(im, b, pb[0] * k, pb[1] * k)
    if halo:
        hs = int(620 * k)
        yy, xx = np.mgrid[0:hs, 0:hs].astype(np.float32)
        r = np.hypot(xx - hs / 2, yy - hs / 2) / (hs / 2)
        al = np.clip(1 - r, 0, 1) ** 2.2 * 215
        h = np.dstack([np.full_like(r, 255), np.full_like(r, 244), np.full_like(r, 176), al]).astype(np.uint8)
        paste_c(im, Image.fromarray(h, "RGBA"), 512 * k, 512 * k)
    paste_c(im, spark(int(470 * k)).rotate(12, resample=Image.BICUBIC), 512 * k, 512 * k)
    for (x, y, s, rot) in ((236, 250, 120, 0), (806, 800, 104, 20), (850, 196, 68, 10), (176, 836, 60, 30)):
        paste_c(im, spark(int(s * k)).rotate(rot, resample=Image.BICUBIC), x * k, y * k)
    return im.resize((size, size), Image.LANCZOS)


def make_icon():
    n = 1024
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    t = np.clip((xx * 0.35 + yy * 0.85) / (n * 1.2), 0, 1)[..., None]
    top = np.array((255, 214, 92), np.float32)
    bot = np.array((255, 122, 72), np.float32)
    bg = top * (1 - t) + bot * t
    cx = cy = n / 2
    r = np.hypot(xx - cx, yy - cy) / (n / 2)
    bg = bg + (np.array((255, 246, 196), np.float32) - bg) * (np.clip(1 - r / 1.05, 0, 1) ** 1.6 * 0.70)[..., None]
    # soft sun rays
    th = np.arctan2(yy - cy, xx - cx)
    rays = smooth(0.25, 0.75, np.cos(th * 12 + 0.4) * 0.5 + 0.5) * smooth(0.25, 0.7, r)
    bg = bg + (255 - bg) * (rays * 0.10)[..., None]
    # gentle vignette
    bg = bg * (1 - 0.16 * smooth(0.75, 1.45, r))[..., None]
    im = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    im.alpha_composite(compose_mark(n))
    return im.convert("RGB")


def make_logo():
    n = 600
    mark = compose_mark(1024, shadow_col=(160, 96, 40), shadow_op=0.26, halo=True)
    bbox = mark.getchannel("A").point(lambda v: 255 if v > 6 else 0).getbbox()
    mark = mark.crop(bbox)
    sc = (n - 24) / max(mark.size)
    mark = mark.resize((int(mark.width * sc), int(mark.height * sc)), Image.LANCZOS)
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    paste_c(out, mark, n / 2, n / 2)
    return out


def make_backdrop():
    w, h = 720, 1560
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (yy / h)[..., None]
    top = np.array((254, 244, 226), np.float32)
    bot = np.array((250, 226, 196), np.float32)
    bg = top * (1 - t) + bot * t
    # kitchen-tile feel: very faint diagonal check + small dots at tile corners
    cell = 120.0
    u = (xx + yy) / cell
    v = (xx - yy) / cell
    check = ((np.floor(u) + np.floor(v)) % 2)
    bg = bg + (check * 2 - 1)[..., None] * 1.6
    fu, fv = np.abs(u - np.round(u)), np.abs(v - np.round(v))
    grout = np.maximum(smooth(0.030, 0.012, fu), smooth(0.030, 0.012, fv))
    bg = mix(bg, (255, 250, 240), grout * 0.55)
    dots = smooth(0.10, 0.06, np.hypot(fu, fv))
    bg = mix(bg, (242, 200, 160), dots * 0.50)
    # soft light from the top, slightly darker floor
    r = np.hypot((xx - w / 2) / w, (yy - h * 0.30) / h)
    bg = bg + (255 - bg) * (np.clip(1 - r / 0.7, 0, 1) ** 2 * 0.35)[..., None]
    bg = bg * (1 - 0.05 * smooth(0.80, 1.0, yy / h))[..., None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")


# ----------------------------------------------------------------------------- font
FONT_BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/baloo2/"
TURKISH = "şğıİöüçŞĞÖÜÇ"


def fetch_font():
    """Download Baloo 2 (SIL OFL 1.1, unmodified variable TTF, default weight 400) and its licence."""
    import urllib.request
    dst = os.path.join(ROOT, "assets", "fonts")
    os.makedirs(dst, exist_ok=True)
    for name, out in (("Baloo2%5Bwght%5D.ttf", "ui_font.ttf"), ("OFL.txt", "OFL.txt")):
        data = urllib.request.urlopen(FONT_BASE + name, timeout=60).read()
        with open(os.path.join(dst, out), "wb") as f:
            f.write(data)
        print("fetched", out, len(data), "bytes")
    try:
        from fontTools.ttLib import TTFont
        cmap = TTFont(os.path.join(dst, "ui_font.ttf")).getBestCmap()
        missing = [c for c in TURKISH if ord(c) not in cmap]
        print("Turkish glyphs missing:", missing or "none")
        if missing:
            sys.exit("font does not cover Turkish")
    except ImportError:
        print("fontTools not installed - glyph coverage not checked")


# ----------------------------------------------------------------------------- main
def save(im, *rel):
    path = os.path.join(ROOT, *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)
    print("wrote", os.path.relpath(path, ROOT), im.size, im.mode)


def main():
    for tier in range(1, 12):
        save(fruit_sprite(tier), "assets", "fruits", "fruit_%02d.png" % tier)
    save(make_icon(), "assets", "icon", "icon_1024.png")
    save(make_logo(), "assets", "icon", "launch_logo.png")
    save(make_backdrop(), "assets", "ui", "jar_bg.png")
    if "--fetch-font" in sys.argv:
        fetch_font()


if __name__ == "__main__":
    main()
