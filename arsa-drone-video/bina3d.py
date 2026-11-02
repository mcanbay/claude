"""
Parsel üzerine yerleştirilen temsili 3B bina kütlesi.

Bina, parselin çekme mesafeleri içinde kalan en büyük dikdörtgene oturan bir
zemin kat (ticari, cam vitrinli) ve onun üzerinde yükselen konut bloğundan
oluşur. Her yüz düzlemsel olduğundan dokular kameraya homografi ile
yansıtılır; böylece yer düzlemiyle aynı perspektif hesabı kullanılır.
"""

import math

import cv2
import numpy as np

PX_PER_M = 10
BORDER = 2  # doku kenarındaki saydam pay (kenar yumuşatma için)

# Güneş: güneybatıdan, 38° yükseklikte (gölgeler kuzeydoğuya düşer)
SUN_AZ, SUN_EL = math.radians(215), math.radians(38)
SUN = np.array([math.sin(SUN_AZ) * math.cos(SUN_EL), math.cos(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_EL)])


# ------------------------------------------------------------- yerleşim ----

def _largest_rectangle(mask):
    """İkili maskedeki en büyük dikdörtgen (r0, c0, r1, c1), histogram yöntemi."""
    h, w = mask.shape
    heights = np.zeros(w, np.int32)
    best = (0, None)
    for r in range(h):
        heights = np.where(mask[r], heights + 1, 0)
        stack = []
        for c in range(w + 1):
            cur = heights[c] if c < w else 0
            start = c
            while stack and stack[-1][1] >= cur:
                s, hh = stack.pop()
                area = hh * (c - s)
                if area > best[0]:
                    best = (area, (r - hh + 1, s, r + 1, c))
                start = s
            stack.append((start, cur))
    return best[1]


def plan_building(ring, floors=9, floor_h=3.1, podium_h=5.0, setback=3.0, slab_depth=15.0, res=0.25):
    """Parsel çokgeninden (dünya metreleri) zemin kat + blok kütlesini çıkarır."""
    ring = np.asarray(ring, np.float64)
    (cx, cy), (rw, rh), ang = cv2.minAreaRect(ring.astype(np.float32))
    a = math.radians(ang)
    u = np.array([math.cos(a), math.sin(a)])
    if rh > rw:
        u = np.array([-u[1], u[0]])
    v = np.array([-u[1], u[0]])
    c = np.array([cx, cy])
    local = np.column_stack([(ring - c) @ u, (ring - c) @ v])
    lo = local.min(0) - 1
    size = np.ceil((local.max(0) + 1 - lo) / res).astype(int)
    mask = np.zeros((size[1], size[0]), np.uint8)
    cv2.fillPoly(mask, [np.round((local - lo) / res).astype(np.int32)], 1)
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5) * res

    for sb in (setback, setback * 0.6, 1.0):
        rect = _largest_rectangle(dist > sb)
        if rect and (rect[2] - rect[0]) * res >= 8 and (rect[3] - rect[1]) * res >= 8:
            break
    r0, c0, r1, c1 = rect
    a0, a1 = lo[0] + c0 * res, lo[0] + c1 * res
    b0, b1 = lo[1] + r0 * res, lo[1] + r1 * res
    if (a1 - a0) < (b1 - b0):  # uzun kenar a ekseni olsun (dönüş yönünü rect_world düzeltir)
        u, v = v, u
        a0, a1, b0, b1 = b0, b1, a0, a1

    def rect_world(aa0, aa1, bb0, bb1):
        pts = [c + u * aa0 + v * bb0, c + u * aa1 + v * bb0, c + u * aa1 + v * bb1, c + u * aa0 + v * bb1]
        pts = np.array(pts)
        x, y = pts[:, 0], pts[:, 1]
        if np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) < 0:
            pts = pts[::-1]
        return pts

    length, depth = a1 - a0, b1 - b0
    t_depth = min(slab_depth, depth - (3.0 if depth > slab_depth + 3 else 0.0))
    t_len = length * (0.78 if length > 30 else 1.0)
    tb0 = b0 + (depth - t_depth) / 2
    boxes = [
        {"kind": "podium", "base": rect_world(a0, a1, b0, b1), "z0": 0.0, "z1": podium_h},
        {"kind": "tower", "base": rect_world(a1 - t_len, a1, tb0, tb0 + t_depth),
         "z0": podium_h, "z1": podium_h + floors * floor_h},
    ]
    top = podium_h + floors * floor_h
    mb = min(6.0, t_len / 5), min(5.0, t_depth / 2.5)
    for frac in (0.25, 0.7):
        am = a1 - t_len + t_len * frac
        bm = tb0 + t_depth / 2
        boxes.append({"kind": "roofbox", "base": rect_world(am - mb[0] / 2, am + mb[0] / 2,
                                                            bm - mb[1] / 2, bm + mb[1] / 2),
                      "z0": top, "z1": top + 2.6})
    return boxes


# ---------------------------------------------------------------- dokular ----

def _rng(seed):
    return np.random.default_rng(seed)


def tower_texture(width_m, height_m, floor_h, seed=0):
    """Krem taş cephe, koyu cam pencereler ve cam korkuluklu balkonlar (RGB)."""
    W, H = max(8, int(width_m * PX_PER_M)), max(8, int(height_m * PX_PER_M))
    img = np.empty((H, W, 3), np.float32)
    img[:] = (238, 229, 212)  # krem taş
    rng = _rng(seed)
    floors = max(1, round(height_m / floor_h))
    fh = H / floors
    bay = 3.6 * PX_PER_M
    nb = max(1, int(round(W / bay)))
    bw = W / nb
    for f in range(floors):
        y0 = f * fh
        cv2.rectangle(img, (0, int(y0)), (W, int(y0 + 0.12 * fh)), (246, 240, 228), -1)  # döşeme bandı
        for b in range(nb):
            x0 = b * bw
            wx0, wx1 = int(x0 + 0.30 * bw), int(x0 + 0.70 * bw)
            wy0, wy1 = int(y0 + 0.28 * fh), int(y0 + 0.94 * fh)
            sky = rng.uniform(0.0, 1.0)
            glass = np.array([104, 120, 134]) * (0.85 + 0.3 * sky)
            for yy in range(wy0, wy1):
                k = (yy - wy0) / max(1, wy1 - wy0)
                img[yy, wx0:wx1] = glass * (1.15 - 0.35 * k)
            cv2.rectangle(img, (wx0, wy0), (wx1, wy1), (60, 62, 64), 1)
            mid = (wx0 + wx1) // 2
            cv2.line(img, (mid, wy0), (mid, wy1), (70, 72, 74), 1)
            if (b + f) % 2 == 0 or nb < 3:  # balkon: açık renk cam korkuluk
                ry0 = int(y0 + 0.62 * fh)
                sub = img[ry0:wy1 + 1, wx0 - 2:wx1 + 2]
                sub[:] = sub * 0.55 + np.array([170, 190, 198]) * 0.45
                cv2.line(img, (wx0 - 2, ry0), (wx1 + 2, ry0), (205, 205, 200), 1)
            cv2.rectangle(img, (int(x0), int(y0)), (int(x0 + 0.05 * bw), int(y0 + fh)), (226, 215, 198), -1)
    img *= np.linspace(1.0, 0.92, H, dtype=np.float32)[:, None, None]
    return np.clip(img, 0, 255).astype(np.uint8)


def podium_texture(width_m, height_m, seed=0):
    """Zemin kat: koyu çerçeveli vitrin camları, üstte koyu saçak bandı."""
    W, H = max(8, int(width_m * PX_PER_M)), max(8, int(height_m * PX_PER_M))
    img = np.empty((H, W, 3), np.float32)
    img[:] = (52, 50, 48)
    fascia = int(H * 0.2)
    rng = _rng(seed + 11)
    mod = 2.6 * PX_PER_M
    n = max(1, int(round(W / mod)))
    mw = W / n
    for i in range(n):
        x0, x1 = int(i * mw + 2), int((i + 1) * mw - 2)
        warm = rng.uniform(0.75, 1.0)
        for yy in range(fascia + 3, H - 3):
            k = (yy - fascia) / (H - fascia)
            img[yy, x0:x1] = np.array([118, 128, 132]) * (1.1 - 0.4 * k) * warm + np.array([40, 30, 10]) * k
    img[:fascia] = (64, 62, 60)
    cv2.line(img, (0, fascia), (W, fascia), (150, 140, 120), 1)
    return np.clip(img, 0, 255).astype(np.uint8)


def plain_texture(width_m, height_m, color, lines=False):
    W, H = max(8, int(width_m * PX_PER_M)), max(8, int(height_m * PX_PER_M))
    img = np.empty((H, W, 3), np.uint8)
    img[:] = color
    if lines:
        for x in range(0, W, 12):
            cv2.line(img, (x, 0), (x, H), tuple(int(c * 0.9) for c in color), 1)
    return img


def roof_texture(width_m, depth_m, color):
    W, H = max(8, int(width_m * PX_PER_M)), max(8, int(depth_m * PX_PER_M))
    img = np.empty((H, W, 3), np.uint8)
    img[:] = color
    noise = _rng(5).normal(0, 4, (H, W, 1))
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    p = max(2, int(0.5 * PX_PER_M))
    cv2.rectangle(img, (0, 0), (W - 1, H - 1), (232, 226, 214), p)  # korkuluk duvarı
    return img


def _with_border(rgb):
    """RGB -> kenarı saydam BGRA (OpenCV için BGR'ye çevrilmiş)."""
    h, w = rgb.shape[:2]
    out = np.zeros((h + 2 * BORDER, w + 2 * BORDER, 4), np.uint8)
    out[BORDER:-BORDER, BORDER:-BORDER, :3] = rgb[:, :, ::-1]
    out[BORDER:-BORDER, BORDER:-BORDER, 3] = 255
    return out


# ------------------------------------------------------------------ bina ----

class Building:
    def __init__(self, ring, floors=9, floor_h=3.1, podium_h=5.0):
        self.boxes = plan_building(ring, floors, floor_h, podium_h)
        self.floor_h = floor_h
        self.top = max(b["z1"] for b in self.boxes)
        self.tower_top = next(b["z1"] for b in self.boxes if b["kind"] == "tower")
        for i, b in enumerate(self.boxes):
            base = b["base"]
            h = b["z1"] - b["z0"]
            b["sides"] = []
            for k in range(4):
                p, q = base[k], base[(k + 1) % 4]
                w = float(np.linalg.norm(q - p))
                if b["kind"] == "tower":
                    tex = tower_texture(w, h, floor_h, seed=i * 7 + k)
                elif b["kind"] == "podium":
                    tex = podium_texture(w, h, seed=i * 7 + k)
                else:
                    tex = plain_texture(w, h, (176, 176, 172), lines=True)
                d = q - p
                n = np.array([d[1], -d[0]]) / max(w, 1e-6)
                b["sides"].append({"p": p, "q": q, "n": n, "tex": _with_border(tex)})
            wa = float(np.linalg.norm(base[1] - base[0]))
            wb = float(np.linalg.norm(base[3] - base[0]))
            roof_color = {"tower": (196, 194, 188), "podium": (150, 150, 146), "roofbox": (168, 168, 164)}[b["kind"]]
            b["roof"] = _with_border(roof_texture(wa, wb, roof_color))
        self.footprint_center = self.boxes[1]["base"].mean(0)

    # -- yardımcılar -------------------------------------------------------
    @staticmethod
    def _shade(n3):
        return 0.72 + 0.34 * max(0.0, float(np.dot(n3, SUN)))

    def _visible_boxes(self, grow):
        level = grow * self.top
        out = []
        for b in self.boxes:
            if level <= b["z0"] + 0.05:
                continue
            out.append((b, min(b["z1"], level)))
        return out

    def draw_shadow(self, frame, Hg, grow, alpha):
        """Bina gölgesini yer düzlemine düşürür (yer homografisi Hg ile)."""
        if alpha <= 0 or grow <= 0:
            return
        offset = -SUN[:2] / SUN[2]
        mask = np.zeros(frame.shape[:2], np.uint8)
        for b, z1 in self._visible_boxes(grow):
            pts = np.vstack([b["base"] + offset * b["z0"], b["base"] + offset * z1])
            hull = cv2.convexHull(pts.astype(np.float32)).reshape(-1, 2)
            scr = _project_h(Hg, hull)
            cv2.fillPoly(mask, [np.round(scr * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
        k = max(3, int(frame.shape[0] / 300)) | 1
        mask = cv2.GaussianBlur(mask, (k, k), 0)
        f = 1 - (mask.astype(np.float32) / 255 * 0.5 * alpha)[:, :, None]
        frame[:] = (frame * f).astype(np.uint8)

    def draw(self, frame, P, cam_pos, grow, alpha):
        """Binayı çizer. P: 3x4 kamera matrisi, cam_pos: dünya koordinatı."""
        if alpha <= 0 or grow <= 0:
            return
        vis = self._visible_boxes(grow)
        vis.sort(key=lambda bz: (bz[0]["z0"], -np.linalg.norm(bz[0]["base"].mean(0) - cam_pos[:2])))
        for b, z1 in vis:
            h_full = b["z1"] - b["z0"]
            h_now = z1 - b["z0"]
            for s in b["sides"]:
                n3 = np.array([s["n"][0], s["n"][1], 0.0])
                mid = np.array([*(s["p"] + s["q"]) / 2, (b["z0"] + z1) / 2])
                if np.dot(n3, cam_pos - mid) <= 0:
                    continue
                tex = s["tex"]
                th = tex.shape[0] - 2 * BORDER
                tw = tex.shape[1] - 2 * BORDER
                # Yükselme animasyonu: dokunun alt kısmı görünür (kat kat yükselir)
                cut = int(round(th * (1 - h_now / h_full)))
                tex = tex[cut:] if cut > 0 else tex
                O = np.array([s["p"][0], s["p"][1], z1])
                U = np.array([*(s["q"] - s["p"]), 0.0]) / tw
                V = np.array([0.0, 0.0, -h_now]) / max(1, th - cut)
                _warp_face(frame, P, tex, O, U, V, self._shade(n3) * (0.97 if b["kind"] == "tower" else 1.0),
                           alpha)
            base = b["base"]
            roof = b["roof"]
            rh, rw = roof.shape[0] - 2 * BORDER, roof.shape[1] - 2 * BORDER
            O = np.array([base[0][0], base[0][1], z1])
            U = np.array([*(base[1] - base[0]), 0.0]) / rw
            V = np.array([*(base[3] - base[0]), 0.0]) / rh
            if cam_pos[2] > z1:
                _warp_face(frame, P, roof, O, U, V, self._shade(np.array([0, 0, 1.0])), alpha)


def _project_h(H, pts):
    p = (H @ np.column_stack([pts, np.ones(len(pts))]).T).T
    return p[:, :2] / p[:, 2:3]


def _warp_face(frame, P, tex, O, U, V, shade, alpha):
    """Doku pikseli (u, v) -> O + (u-B)U + (v-B)V düzlemini ekrana yansıtır."""
    M = np.column_stack([np.append(U, 0), np.append(V, 0), np.append(O, 1)])
    H = P @ M @ np.array([[1, 0, -BORDER], [0, 1, -BORDER], [0, 0, 1.0]])
    h, w = tex.shape[:2]
    corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], float)
    pc = (H @ corners.T).T
    if np.any(pc[:, 2] <= 1e-6):
        return
    pc = pc[:, :2] / pc[:, 2:3]
    Hf, Wf = frame.shape[:2]
    x0, y0 = max(0, int(np.floor(pc[:, 0].min()))), max(0, int(np.floor(pc[:, 1].min())))
    x1, y1 = min(Wf, int(np.ceil(pc[:, 0].max())) + 1), min(Hf, int(np.ceil(pc[:, 1].max())) + 1)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    Ht = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1.0]]) @ H
    # Küçültmede kırpışmayı azaltmak için dokuyu ekrandaki boyutuna yakın ölçekle
    scr_w = max(np.linalg.norm(pc[1] - pc[0]), np.linalg.norm(pc[2] - pc[3]))
    scr_h = max(np.linalg.norm(pc[3] - pc[0]), np.linalg.norm(pc[2] - pc[1]))
    sx, sy = min(1.0, 1.6 * scr_w / w), min(1.0, 1.6 * scr_h / h)
    if sx < 0.9 or sy < 0.9:
        nw, nh = max(4, int(w * sx)), max(4, int(h * sy))
        tex = cv2.resize(tex, (nw, nh), interpolation=cv2.INTER_AREA)
        Ht = Ht @ np.diag([w / nw, h / nh, 1.0])
    warped = cv2.warpPerspective(tex, Ht, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = warped[:, :, 3:4].astype(np.float32) * (alpha / 255.0)
    roi = frame[y0:y1, x0:x1]
    roi[:] = (roi * (1 - a) + warped[:, :, :3].astype(np.float32) * shade * a).clip(0, 255).astype(np.uint8)
