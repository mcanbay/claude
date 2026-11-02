"""
Firma açılış/kapanış animasyonu (sade, siyah zeminli "logo reveal").

Akış: monogram çerçevesi çizilir, harfler sırayla netleşerek yükselir,
alt satırın harf aralığı daralarak yerine oturur, metnin üzerinden ışık
geçer, sonra sahne yavaşça büyüyerek kararır.
"""

import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

GOLD_RGB = (255, 205, 60)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def _tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def _monogram(name):
    words = [w for w in name.split() if w]
    return "".join(w[0] for w in words[:2]).upper() if words else "•"


def _glyph(font, ch, color_top, color_bottom):
    """Tek harf: dikey metalik geçişli RGBA (float32, premultiplied değil)."""
    l, t, r, b = font.getbbox(ch)
    asc, desc = font.getmetrics()
    w = max(1, int(math.ceil(font.getlength(ch))) + 4)
    h = asc + desc + 4
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((2, 2), ch, font=font, fill=255)
    a = np.asarray(m, np.float32) / 255
    k = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    rgb = np.array(color_top, np.float32) * (1 - k) + np.array(color_bottom, np.float32) * k
    return np.dstack([np.broadcast_to(rgb, (h, w, 3)), a[:, :, None]])


class BrandAnim:
    def __init__(self, fonts, name, width, height, sub=None, tagline=None):
        words = name.split()
        if sub is None and len(words) >= 3:
            name, sub = " ".join(words[:-1]), words[-1]
        self.W, self.H = width, height
        S = min(width, height) / 1080.0
        self.S = S
        maxw = width * 0.84

        size = int(118 * S)
        while True:
            font = fonts.get(size, True)
            tw = sum(font.getlength(c) for c in name)
            if tw <= maxw or size < 20:
                break
            size = int(size * 0.94)
        self.main = []
        x = -tw / 2
        for ch in name:
            g = _glyph(font, ch, (246, 246, 248), (176, 178, 184))
            self.main.append((x, g))
            x += font.getlength(ch)
        self.main_h = self.main[0][1].shape[0] if self.main else 0

        self.sub = []
        if sub:
            sfont = fonts.get(int(34 * S), True)
            letters = list(_tr_upper(sub))
            track = 16 * S
            sw = sum(sfont.getlength(c) for c in letters) + track * (len(letters) - 1)
            x = -sw / 2
            for ch in letters:
                g = _glyph(sfont, ch, GOLD_RGB, (214, 160, 40))
                self.sub.append((x + sfont.getlength(ch) / 2, g))
                x += sfont.getlength(ch) + track
        self.tagline = None
        if tagline:
            tf = fonts.get(int(26 * S), False)
            tw2 = sum(tf.getlength(c) for c in tagline)
            if tw2 > maxw:
                tf = fonts.get(int(26 * S * maxw / tw2), False)
            self.tagline = _glyph(tf, tagline, (190, 190, 196), (150, 150, 156))

        mfont = fonts.get(int(64 * S), True)
        self.mono_box = int(150 * S)
        self.mono = _glyph(mfont, _monogram(name), (250, 250, 252), (190, 192, 198))

        # Dikey yerleşim (merkez 0'a göre)
        gap = 34 * S
        self.y_mono = -(self.mono_box + gap + self.main_h) / 2 - 20 * S
        self.y_main = self.y_mono + self.mono_box + gap
        self.y_sub = self.y_main + self.main_h + 10 * S
        self.y_tag = self.y_sub + 70 * S

        yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
        r = np.sqrt(((xx - width / 2) / width) ** 2 + ((yy - height / 2) / height) ** 2)
        self.bg = (np.clip(1 - r * 1.6, 0, 1)[:, :, None] * np.array([22, 20, 18], np.float32) + 4)

    # ------------------------------------------------------------------
    def frame(self, t, duration, outro=False):
        """t: animasyon içindeki zaman (sn). BGR uint8 kare döndürür."""
        W, H, S = self.W, self.H, self.S
        layer = np.zeros((H, W, 4), np.float32)  # premultiplied RGBA
        cx, cy = W / 2, H / 2

        # 1) Monogram çerçevesi çizilir, içindeki harfler belirir
        draw = ease_out((t - 0.25) / 1.1)
        box = self.mono_box
        x0, y0 = cx - box / 2, cy + self.y_mono
        rr = 26 * S
        pts = _rounded_rect_path(x0, y0, box, box, rr)
        n = max(2, int(len(pts) * draw))
        if draw > 0:
            stroke = np.zeros((H, W), np.uint8)
            cv2.polylines(stroke, [np.round(pts[:n] * 16).astype(np.int32)], False, 255,
                          max(2, int(3 * S)), cv2.LINE_AA, shift=4)
            glow = cv2.GaussianBlur(stroke, (0, 0), 6 * S).astype(np.float32) / 255 * 0.6
            sa = stroke.astype(np.float32) / 255
            gold = np.array(GOLD_RGB[::-1], np.float32)
            layer[:, :, :3] += (sa + glow)[:, :, None] * gold
            layer[:, :, 3] = np.maximum(layer[:, :, 3], np.minimum(1, sa + glow))
        a = ease((t - 0.9) / 0.7)
        if a > 0:
            g = self.mono
            _paste(layer, g, cx - g.shape[1] / 2, y0 + (box - g.shape[0]) / 2 + (1 - a) * 8 * S, a)

        # 2) Ana metin: harfler sırayla yükselir
        for i, (x, g) in enumerate(self.main):
            a = ease((t - 1.15 - i * 0.045) / 0.55)
            if a > 0:
                _paste(layer, g, cx + x, cy + self.y_main + (1 - ease_out(a)) * 26 * S, a)

        # 3) Alt satır: harf aralığı daralarak yerine oturur
        a = ease((t - 1.9) / 0.9)
        if a > 0:
            spread = 1 + 0.9 * (1 - ease_out((t - 1.9) / 1.3))
            for x, g in self.sub:
                _paste(layer, g, cx + x * spread - g.shape[1] / 2, cy + self.y_sub, a)
        if self.tagline is not None:
            a = ease((t - 2.6) / 0.8)
            if a > 0:
                g = self.tagline
                _paste(layer, g, cx - g.shape[1] / 2, cy + self.y_tag, a * 0.9)

        # Odak netleşmesi: başta hafif bulanık
        blur = (1 - ease((t - 0.9) / 1.4)) * 5 * S
        if blur > 0.4:
            layer = cv2.GaussianBlur(layer, (0, 0), blur)

        # 4) Işık geçişi
        sweep = (t - 2.5) / 1.0
        if 0 < sweep < 1.3:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            pos = -0.3 * W + sweep * 1.6 * W
            band = np.exp(-(((xx + 0.45 * (yy - cy)) - pos) / (55 * S)) ** 2) * 0.85
            layer[:, :, :3] += band[:, :, None] * layer[:, :, 3:4] * 255 * 0.6

        # 5) Çıkış: yavaş büyüme + kararma (açılışta), kapanışta sadece kararma
        k = 1.0 + 0.035 * ease((t - 2.0) / max(0.1, duration - 2.0))
        out = self.bg * ease(t / 0.5)
        if k != 1.0:
            M = cv2.getRotationMatrix2D((cx, cy), 0, k)
            layer = cv2.warpAffine(layer, M, (W, H), flags=cv2.INTER_LINEAR)
        out = out * (1 - layer[:, :, 3:4]) + layer[:, :, :3]
        fade = ease((duration - t) / (0.9 if not outro else 1.2))
        return np.clip(out * fade, 0, 255).astype(np.uint8)


def _rounded_rect_path(x, y, w, h, r, steps=10):
    """Sol üstten saat yönünde yuvarlatılmış kare yolu (çizim animasyonu için)."""
    pts = []
    corners = [(x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)]
    pts.append((x + r, y))
    for cxx, cyy, start in corners:
        for k in range(steps + 1):
            ang = math.radians(start + 90 * k / steps)
            pts.append((cxx + r * math.cos(ang), cyy + r * math.sin(ang)))
    pts.append((x + r, y))
    # Kenarları eşit aralıklı noktalara böl (çizgi hızı sabit olsun)
    pts = np.array(pts, np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, cum[-1], 240)
    return np.column_stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])])


def _paste(layer, g, x, y, alpha):
    """Harf görüntüsünü (RGB + alfa, RGB sırası) premultiplied katmana ekler."""
    h, w = g.shape[:2]
    xi, yi = int(round(x)), int(round(y))
    H, W = layer.shape[:2]
    x0, y0, x1, y1 = max(xi, 0), max(yi, 0), min(xi + w, W), min(yi + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    s = g[y0 - yi:y1 - yi, x0 - xi:x1 - xi]
    a = s[:, :, 3:4] * alpha
    roi = layer[y0:y1, x0:x1]
    roi[:, :, :3] = roi[:, :, :3] * (1 - a) + s[:, :, 2::-1] * a
    roi[:, :, 3:4] = roi[:, :, 3:4] * (1 - a) + a
