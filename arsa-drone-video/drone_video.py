#!/usr/bin/env python3
"""
Arsa tanıtım videosu üretici: uydu görüntüsünden dron tarzı uçuş videosu.

TKGM Parsel Sorgu servisinden ada/parsel sınırını alır, Esri World Imagery
uydu karolarını indirir ve parselin etrafında dönen, alçalan, tepeden bakan
bir "dron uçuşu" videosu (MP4) üretir. Parsel sınırı, yüzölçümü, kenar
uzunlukları ve bilgi kartı videonun üzerine çizilir.

Örnek:
    python drone_video.py --il Bursa --ilce Nilüfer --mahalle Odunluk \
        --ada 4632 --parsel 9 --contact "0 5xx xxx xx xx"

Parsel sınırı TKGM'den alınamazsa parselsorgu.tkgm.gov.tr'den indirilen
GeoJSON/KML dosyası (--geojson / --kml) ya da köşe koordinatları (--coords)
verilebilir.
"""

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import threading
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

TKGM_BASES = [
    "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api",
    "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api",
]
TILE_URL_DEFAULT = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
IMAGERY_CREDIT = "Uydu görüntüsü: Esri, Maxar, Earthstar Geographics"
WAYBACK_CONFIG = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
EARTH_CIRCUMFERENCE = 40075016.686

# Renkler BGR sırasındadır (OpenCV).
GOLD = (40, 196, 255)
WHITE = (255, 255, 255)
HAZE = (226, 214, 200)

# ---------------------------------------------------------------- metin ----

_TR_ASCII = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def tr_lower(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_title(s):
    return " ".join(tr_upper(w[:1]) + tr_lower(w[1:]) for w in s.split())


def norm_name(s):
    s = tr_lower(str(s)).translate(_TR_ASCII)
    s = re.sub(r"\b(mahallesi|mah\.?|koyu|mh\.?)\s*$", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def fmt_tr(x, decimals=2):
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------- parsel verisi ----

def _tkgm_get(path):
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://parselsorgu.tkgm.gov.tr/",
        "Origin": "https://parselsorgu.tkgm.gov.tr",
        "Accept": "application/json",
    }
    last = None
    for base in TKGM_BASES:
        try:
            r = requests.get(f"{base}/{path}", headers=headers, timeout=30)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except (requests.RequestException, ValueError) as e:
            last = str(e)
    raise RuntimeError(f"TKGM isteği başarısız ({path}): {last}")


def _find_id(collection, name, what):
    feats = collection.get("features", []) if isinstance(collection, dict) else collection
    items = []
    for f in feats:
        p = f.get("properties", f)
        label = p.get("text") or p.get("ad") or p.get("name") or ""
        items.append((label, p.get("id")))
    target = norm_name(name)
    exact = [i for i in items if norm_name(i[0]) == target]
    if not exact:
        exact = [i for i in items if norm_name(i[0]).startswith(target)]
    if len(exact) == 1 or (exact and norm_name(exact[0][0]) == target):
        return exact[0][1]
    options = ", ".join(sorted(i[0] for i in items))
    raise RuntimeError(f"{what} bulunamadı: '{name}'. Mevcut seçenekler: {options}")


def fetch_parcel_tkgm(il, ilce, mahalle, ada, parsel):
    print(f"TKGM: {il} / {ilce} / {mahalle} — {ada} ada {parsel} parsel sorgulanıyor...")
    il_id = _find_id(_tkgm_get("idariYapi/ilListe"), il, "İl")
    ilce_id = _find_id(_tkgm_get(f"idariYapi/ilceListe/{il_id}"), ilce, "İlçe")
    mah_id = _find_id(_tkgm_get(f"idariYapi/mahalleListe/{ilce_id}"), mahalle, "Mahalle")
    feature = _tkgm_get(f"parsel/{mah_id}/{ada}/{parsel}")
    if not isinstance(feature, dict) or not feature.get("geometry"):
        raise RuntimeError("TKGM parsel geometrisi döndürmedi (ada/parsel numarasını kontrol edin).")
    return feature


def _largest_ring(geometry):
    t = geometry.get("type")
    coords = geometry.get("coordinates")
    if t == "Polygon":
        polys = [coords]
    elif t == "MultiPolygon":
        polys = coords
    else:
        raise RuntimeError(f"Desteklenmeyen geometri tipi: {t}")
    rings = [p[0] for p in polys if p]
    ring = max(rings, key=lambda r: abs(_shoelace([(c[0], c[1]) for c in r])))
    return [(float(c[0]), float(c[1])) for c in ring]


def load_geojson(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("type") == "FeatureCollection":
        data = data["features"][0]
    if data.get("type") == "Feature":
        return _largest_ring(data["geometry"]), data.get("properties") or {}
    return _largest_ring(data), {}


def load_kml(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    blocks = re.findall(r"<coordinates>(.*?)</coordinates>", text, flags=re.S)
    if not blocks:
        raise RuntimeError("KML içinde <coordinates> bulunamadı.")
    rings = []
    for b in blocks:
        pts = []
        for tok in b.split():
            parts = tok.split(",")
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
        if len(pts) >= 3:
            rings.append(pts)
    props = {}
    for name, value in re.findall(
            r'<Data\s+name="([^"]+)"\s*>\s*(?:<value>(.*?)</value>|<value\s*/>)', text, flags=re.S):
        props[name.strip()] = value.strip()
    return max(rings, key=lambda r: abs(_shoelace(r))), props


def parse_coords(text):
    pts = []
    for chunk in re.split(r"[;\n]+", text.strip()):
        if chunk.strip():
            lat, lon = (float(v) for v in chunk.replace(" ", "").split(",")[:2])
            pts.append((lon, lat))
    if len(pts) < 3:
        raise RuntimeError("--coords en az 3 köşe içermelidir: 'enlem,boylam; enlem,boylam; ...'")
    return pts, {}


def _shoelace(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return a / 2.0


def simplify_ring(ring, min_turn_deg=5.0, min_edge=0.6):
    """Aynı doğru üzerindeki ara köşeleri ve çok kısa kenarları atar (kenar ölçüleri için)."""
    pts = [np.asarray(p, float) for p in ring]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            u, v = b - a, c - b
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            turn = 0.0 if min(nu, nv) < 1e-9 else math.degrees(
                math.acos(float(np.clip(np.dot(u, v) / (nu * nv), -1, 1))))
            if nu < min_edge or turn < min_turn_deg:
                del pts[i]
                changed = True
                break
    return np.array(pts)


def parcel_props(raw):
    """TKGM özelliklerini ekranda gösterilecek alanlara çevirir."""
    def pick(*keys):
        for k in keys:
            v = raw.get(k)
            if v not in (None, "", "-"):
                return str(v).strip()
        return None

    return {
        "alan": pick("alan", "Alan", "yuzolcum", "yuzOlcum"),
        "nitelik": pick("nitelik", "Nitelik"),
        "mevkii": pick("mevkii", "mevki", "Mevkii"),
        "pafta": pick("pafta", "Pafta"),
    }


# -------------------------------------------------------------- projeksiyon ----

def merc(lon, lat):
    """Web Mercator, [0,1] aralığında normalize."""
    x = (lon + 180.0) / 360.0
    s = math.sin(math.radians(lat))
    y = 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)
    return x, y


class Proj:
    """Parsel merkezli yerel düzlem: X doğu, Y kuzey (metre)."""

    def __init__(self, lon0, lat0):
        self.lon0, self.lat0 = lon0, lat0
        self.mx0, self.my0 = merc(lon0, lat0)
        self.m_per_unit = EARTH_CIRCUMFERENCE * math.cos(math.radians(lat0))

    def to_world(self, lon, lat):
        mx, my = merc(lon, lat)
        return (mx - self.mx0) * self.m_per_unit, -(my - self.my0) * self.m_per_unit

    def mpp(self, z):
        return self.m_per_unit / (256 * 2 ** z)


# ---------------------------------------------------------- uydu karoları ----

_thread_local = threading.local()


def _session():
    if not hasattr(_thread_local, "s"):
        s = requests.Session()
        s.headers["User-Agent"] = USER_AGENT
        _thread_local.s = s
    return _thread_local.s


def _get_tile(url, path):
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    for attempt in range(4):
        try:
            r = _session().get(url, timeout=20)
            if r.status_code == 200 and r.content:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(r.content)
                return r.content
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None


def tile_cache_key(tile_url):
    host = re.sub(r"[^A-Za-z0-9]+", "_", urlparse(tile_url).netloc or "local")[:40]
    return f"{host}_{hashlib.md5(tile_url.encode()).hexdigest()[:8]}"


# ------------------------------------------------- Esri Wayback (tarihli arşiv) ----

def _parse_date(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)) and v > 1e11:  # epoch milisaniye
        return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date()
    m = re.match(r"(\d{4})-?(\d{2})-?(\d{2})", str(int(v)) if isinstance(v, (int, float)) else str(v))
    return date(int(m[1]), int(m[2]), int(m[3])) if m else None


def wayback_releases():
    """Esri Wayback yayınları, en yeniden eskiye."""
    r = requests.get(WAYBACK_CONFIG, timeout=30, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    out = []
    for num, item in r.json().items():
        m = re.search(r"(\d{4}-\d{2}-\d{2})", item.get("itemTitle", ""))
        if not m:
            continue
        out.append({
            "num": num,
            "release": m[1],
            "tile_url": item["itemURL"].replace("{level}", "{z}").replace("{row}", "{y}").replace("{col}", "{x}"),
            "metadata": item.get("metadataLayerUrl"),
        })
    return sorted(out, key=lambda x: x["release"], reverse=True)


def wayback_capture(metadata_url, lon, lat, zoom):
    """Bir yayında, verilen noktadaki görüntünün çekim tarihi ve kaynağı."""
    sess = _session()
    info = sess.get(metadata_url, params={"f": "json"}, timeout=30).json()
    scale = 591657527.591555 / 2 ** zoom
    layers = info.get("layers") or []
    fits = [L["id"] for L in layers
            if (not L.get("minScale") or scale <= L["minScale"]) and (not L.get("maxScale") or scale >= L["maxScale"])]
    for layer_id in fits + [L["id"] for L in layers if L["id"] not in fits]:
        q = sess.get(f"{metadata_url}/{layer_id}/query", timeout=30, params={
            "f": "json", "geometry": json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint", "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*", "returnGeometry": "false"}).json()
        feats = q.get("features") or []
        if feats:
            a = {k.upper(): v for k, v in feats[0]["attributes"].items()}
            d = _parse_date(a.get("SRC_DATE2")) or _parse_date(a.get("SRC_DATE"))
            if d:
                return {"date": d, "source": a.get("NICE_DESC") or a.get("SRC_DESC") or "",
                        "resolution": a.get("SRC_RES")}
    return None


def choose_wayback(lon, lat, zoom, scan=15, release=None):
    """En güncel çekim tarihli Wayback yayınını seçer (ya da istenen yayını)."""
    releases = wayback_releases()
    if release:
        chosen = [r for r in releases if r["release"] == release]
        if not chosen:
            sys.exit(f"HATA: {release} tarihli Wayback yayını yok. Mevcut son yayınlar: "
                     + ", ".join(r["release"] for r in releases[:10]))
        releases = chosen
    best = None
    for rel in releases[:scan]:
        try:
            cap = wayback_capture(rel["metadata"], lon, lat, zoom)
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"  {rel['release']}: çekim tarihi sorgulanamadı ({e.__class__.__name__})")
            continue
        if cap:
            print(f"  Wayback {rel['release']}: çekim {cap['date'].isoformat()} {cap['source']}")
            if best is None or cap["date"] > best["capture"]["date"]:
                best = dict(rel, capture=cap)
    if best is None:
        print("  ! Çekim tarihi öğrenilemedi; en son Wayback yayını kullanılıyor.")
        best = dict(releases[0], capture=None)
    return best


def fetch_mosaic(tile_url, z, proj, radius_m, cache_dir, workers=8):
    """Parsel merkezli, (2*radius_m) genişliğinde kare mozaik indirir (BGR)."""
    scale = 256 * 2 ** z
    cx, cy = proj.mx0 * scale, proj.my0 * scale
    r = radius_m / proj.mpp(z)
    tx0, tx1 = int((cx - r) // 256), int((cx + r) // 256)
    ty0, ty1 = int((cy - r) // 256), int((cy + r) // 256)
    canvas = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), np.uint8)
    root = Path(cache_dir) / tile_cache_key(tile_url)
    jobs = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    stats = {"total": len(jobs), "missing": 0, "placeholder": 0}

    def work(job):
        tx, ty = job
        url = tile_url.format(z=z, x=tx, y=ty)
        data = _get_tile(url, root / str(z) / str(tx) / f"{ty}.jpg")
        img = None
        if data:
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        return tx, ty, img

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for tx, ty, img in ex.map(work, jobs):
            if img is None:
                stats["missing"] += 1
                continue
            if img.shape[:2] != (256, 256):
                img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_AREA)
            # Esri, görüntü olmayan yerlerde düz gri "Map data not yet available" karosu döner.
            if img.std() < 6 and img.mean() > 150:
                stats["placeholder"] += 1
            oy, ox = (ty - ty0) * 256, (tx - tx0) * 256
            canvas[oy:oy + 256, ox:ox + 256] = img

    x0 = int(round(cx - r)) - tx0 * 256
    y0 = int(round(cy - r)) - ty0 * 256
    size = int(round(2 * r))
    crop = canvas[y0:y0 + size, x0:x0 + size].copy()
    origin = (tx0 * 256 + x0, ty0 * 256 + y0)  # global piksel koordinatı
    return crop, origin, stats


def grade(img):
    """Uydu görüntüsünü canlandırır: hafif keskinleştirme, kontrast ve doygunluk."""
    f = img.astype(np.float32)
    blur = cv2.GaussianBlur(f, (0, 0), 1.2)
    f = f + 0.45 * (f - blur)
    mean = f.mean()
    f = (f - mean) * 1.08 + mean + 4
    gray = f.mean(axis=2, keepdims=True)
    f = gray + (f - gray) * 1.18
    return np.clip(f, 0, 255).astype(np.uint8)


class Layer:
    """Tek zoom seviyesindeki mozaik + mipmap piramidi + kenarlarda yumuşak alfa."""

    def __init__(self, img, z, origin, proj):
        self.z = z
        self.mpp = proj.mpp(z)
        scale = 256 * 2 ** z
        # Mozaik pikseli (u, v) -> dünya (X, Y): X = (ox + u - cx) * mpp, Y = -(oy + v - cy) * mpp
        self.ox = origin[0] - proj.mx0 * scale
        self.oy = origin[1] - proj.my0 * scale
        h, w = img.shape[:2]
        feather = max(8, int(min(h, w) * 0.07))
        rx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / feather, 0, 1)
        ry = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / feather, 0, 1)
        a = np.outer(ry, rx)
        a = a * a * (3 - 2 * a)
        rgba = np.dstack([grade(img), (a * 255).astype(np.uint8)])
        self.levels = [rgba]
        while min(self.levels[-1].shape[:2]) > 96:
            self.levels.append(cv2.pyrDown(self.levels[-1]))
        self.size = (w, h)
        self.feather = feather

    def A(self, level=0):
        s = 2 ** level
        m = self.mpp
        return np.array([[m * s, 0, self.ox * m], [0, -m * s, -self.oy * m], [0, 0, 1]])

    def covers(self, world_pts):
        inv = np.linalg.inv(self.A(0))
        w, h = self.size
        f = self.feather
        for X, Y in world_pts:
            u, v, q = inv @ np.array([X, Y, 1.0])
            u, v = u / q, v / q
            if not (f <= u <= w - f and f <= v <= h - f):
                return False
        return True


# ------------------------------------------------------------------ kamera ----

def pchip(xs, ys):
    """Monoton kübik interpolasyon (Fritsch–Carlson): kamera yolunda taşma olmaz."""
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    h = np.diff(xs)
    d = np.diff(ys) / h
    n = len(xs)
    m = np.zeros(n)
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, n - 1):
        if d[k - 1] * d[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])

    def f(x):
        x = min(max(x, xs[0]), xs[-1])
        k = min(int(np.searchsorted(xs, x, side="right")) - 1, n - 2)
        t = (x - xs[k]) / h[k]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[k] + (t3 - 2 * t2 + t) * h[k] * m[k]
                + (-2 * t3 + 3 * t2) * ys[k + 1] + (t3 - t2) * h[k] * m[k + 1])

    return f


class Camera:
    def __init__(self, width, height, vfov_deg):
        self.W, self.H = width, height
        self.vfov = math.radians(vfov_deg)
        self.f = (height / 2) / math.tan(self.vfov / 2)
        self.hfov = 2 * math.atan((width / 2) / self.f)
        self.K = np.array([[self.f, 0, width / 2], [0, self.f, height / 2], [0, 0, 1]])

    def ground_homography(self, target, dist, heading_deg, pitch_deg):
        """Yer düzlemi (X, Y, 1) -> ekran pikseli homografisi."""
        th, ps = math.radians(pitch_deg), math.radians(heading_deg)
        fwd = np.array([math.cos(th) * math.sin(ps), math.cos(th) * math.cos(ps), -math.sin(th)])
        right = np.array([math.cos(ps), -math.sin(ps), 0.0])
        up = np.cross(right, fwd)
        R = np.stack([right, -up, fwd])
        C = np.array([target[0], target[1], 0.0]) - dist * fwd
        P = self.K @ np.column_stack([R[:, 0], R[:, 1], -R @ C])
        return P

    def visible_size(self, dist):
        return 2 * dist * math.tan(self.hfov / 2), 2 * dist * math.tan(self.vfov / 2)


def project(H, pts):
    pts = np.asarray(pts, float)
    p = (H @ np.column_stack([pts, np.ones(len(pts))]).T).T
    return p[:, :2] / p[:, 2:3]


# ------------------------------------------------------------------ çizim ----

FONT_CANDIDATES = {
    True: [
        "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    False: [
        "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ],
}


class Fonts:
    def __init__(self, regular=None, bold=None):
        self.paths = {
            False: regular or next((p for p in FONT_CANDIDATES[False] if Path(p).exists()), None),
            True: bold or next((p for p in FONT_CANDIDATES[True] if Path(p).exists()), None),
        }
        self._cache = {}

    def get(self, size, bold=False):
        key = (int(size), bold)
        if key not in self._cache:
            path = self.paths[bold]
            self._cache[key] = (ImageFont.truetype(path, key[0]) if path
                                else ImageFont.load_default(key[0]))
        return self._cache[key]


def pil_to_bgra(img):
    a = np.asarray(img.convert("RGBA"))
    return a[:, :, [2, 1, 0, 3]].copy()


def text_sprite(fonts, text, size, bold=False, color=(255, 255, 255), tracking=0,
                max_width=None, shadow=True):
    """Gölgeli metin görüntüsü (BGRA). max_width verilirse sığana kadar küçültür."""
    while True:
        font = fonts.get(size, bold)
        widths = [font.getlength(ch) + tracking for ch in text]
        tw = int(sum(widths) - tracking) if text else 1
        if max_width is None or tw <= max_width or size <= 10:
            break
        size = int(size * 0.93)
    asc, desc = font.getmetrics()
    pad = max(4, size // 6)
    img = Image.new("RGBA", (tw + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        _draw_tracked(ImageDraw.Draw(sh), pad + 1, pad + 2, text, font, widths, (0, 0, 0, 170))
        sh_np = np.asarray(sh).copy()
        sh_np[:, :, 3] = cv2.GaussianBlur(sh_np[:, :, 3], (0, 0), max(1.5, size / 22))
        img = Image.alpha_composite(img, Image.fromarray(sh_np))
    _draw_tracked(ImageDraw.Draw(img), pad, pad, text, font, widths, tuple(color) + (255,))
    return pil_to_bgra(img)


def _draw_tracked(draw, x, y, text, font, widths, fill):
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w


def blit(frame, sprite, x, y, alpha=1.0, anchor="lt"):
    """BGRA sprite'ı BGR kareye alfa ile yerleştirir. anchor: [lcr][tmb]."""
    if alpha <= 0.002 or sprite is None:
        return
    h, w = sprite.shape[:2]
    x -= {"l": 0, "c": w / 2, "r": w}[anchor[0]]
    y -= {"t": 0, "m": h / 2, "b": h}[anchor[1]]
    x, y = int(round(x)), int(round(y))
    H, W = frame.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    s = sprite[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[:, :, 3:4].astype(np.float32) * (alpha / 255.0)
    roi = frame[y0:y1, x0:x1]
    roi[:] = (roi * (1 - a) + s[:, :, :3] * a).astype(np.uint8)


def rounded_panel(w, h, radius, fill=(12, 16, 22, 190), outline=None):
    img = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        [0, 0, int(w) - 1, int(h) - 1], radius=int(radius), fill=fill,
        outline=outline, width=2 if outline else 0)
    return pil_to_bgra(img)


def spacer(h):
    return np.zeros((max(1, int(h)), 1, 4), np.uint8)


def stack_sprites(items, gap, align="l"):
    """Dikey sprite listesi -> tek BGRA."""
    w = max(s.shape[1] for s in items)
    h = sum(s.shape[0] for s in items) + gap * (len(items) - 1)
    out = np.zeros((h, w, 4), np.uint8)
    y = 0
    for s in items:
        x = {"l": 0, "c": (w - s.shape[1]) // 2, "r": w - s.shape[1]}[align]
        out[y:y + s.shape[0], x:x + s.shape[1]] = s
        y += s.shape[0] + gap
    return out


def over(dst, src, x, y):
    """BGRA üzerine BGRA (premultiply'sız 'over')."""
    h, w = src.shape[:2]
    roi = dst[y:y + h, x:x + w].astype(np.float32)
    sa = src[:, :, 3:4].astype(np.float32) / 255
    da = roi[:, :, 3:4] / 255
    oa = sa + da * (1 - sa)
    rgb = (src[:, :, :3] * sa + roi[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
    dst[y:y + h, x:x + w] = np.dstack([rgb, oa * 255]).astype(np.uint8)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def window(t, a, b, fin=0.7, fout=0.7):
    """[a, b] aralığında yumuşak giriş/çıkışlı görünürlük (0..1)."""
    if t < a or t > b:
        return 0.0
    return ease((t - a) / fin) * ease((b - t) / fout)


def nice_length(target):
    for v in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000):
        if v >= target * 0.7:
            return v
    return 5000


# ------------------------------------------------------------------ müzik ----

def make_music(path, duration, sr=44100):
    """Telifsiz, sentezlenmiş sakin bir ambiyans altlığı üretir (WAV)."""
    n = int(duration * sr)
    t = np.arange(n) / sr
    out = np.zeros((n, 2), np.float32)
    # Cmaj9 - Am7 - Fmaj7 - Gsus/Cmaj9 (Hz)
    chords = [
        [130.81, 196.00, 246.94, 293.66, 329.63],
        [110.00, 164.81, 196.00, 261.63, 329.63],
        [87.31, 174.61, 220.00, 261.63, 329.63],
        [98.00, 146.83, 196.00, 261.63, 293.66],
    ]
    seg = 6.5
    k = 0
    start = 0.0
    while start < duration:
        notes = chords[k % len(chords)]
        a, b = int(start * sr), min(n, int((start + seg + 3.0) * sr))
        tt = t[a:b] - start
        env = np.minimum(1, tt / 2.2) * np.clip((seg + 3.0 - tt) / 3.0, 0, 1)
        env = env * env * (3 - 2 * env)
        for i, f in enumerate(notes):
            for ch, det in ((0, 0.9985), (1, 1.0015)):
                ph = 2 * np.pi * f * det * tt + i
                v = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
                out[a:b, ch] += (v * env * (0.9 if i == 0 else 0.55)).astype(np.float32)
        start += seg
        k += 1
    shimmer = np.sin(2 * np.pi * 659.25 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t)) * 0.08
    out[:, 0] += shimmer
    out[:, 1] += np.roll(shimmer, int(0.013 * sr))
    # Basit yankı: üstel sönümlü gürültü ile FFT konvolüsyonu.
    rng = np.random.default_rng(7)
    ir_len = int(2.8 * sr)
    tail = np.exp(-np.arange(ir_len) / (0.9 * sr))
    size = 1 << int(np.ceil(np.log2(n + ir_len)))
    for ch in range(2):
        ir = rng.standard_normal(ir_len) * tail
        ir[0] = 6.0
        wet = np.fft.irfft(np.fft.rfft(out[:, ch], size) * np.fft.rfft(ir, size), size)[:n]
        out[:, ch] = 0.55 * out[:, ch] + 0.45 * wet / np.abs(ir).sum() * 12
    fade = np.minimum(1, t / 1.5) * np.clip((duration - t) / 3.0, 0, 1)
    out *= fade[:, None]
    out *= 0.35 / max(1e-6, np.abs(out).max())
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ----------------------------------------------------------------- video ----

class Video:
    DURATION = 52.0

    def __init__(self, args, ring_ll, props):
        self.args = args
        self.W, self.H = args.width, args.height
        self.portrait = self.H > self.W
        self.S = min(self.W, self.H) / 1080.0
        self.fonts = Fonts(args.font, args.font_bold)

        lon0 = sum(p[0] for p in ring_ll) / len(ring_ll)
        lat0 = sum(p[1] for p in ring_ll) / len(ring_ll)
        self.proj = Proj(lon0, lat0)
        ring = [self.proj.to_world(lon, lat) for lon, lat in ring_ll]
        if len(ring) > 1 and np.allclose(ring[0], ring[-1]):
            ring = ring[:-1]
        self.ring = np.array(ring)
        # Ağırlık merkezi (çokgen centroid'i)
        a = _shoelace([tuple(p) for p in self.ring])
        cx = cy = 0.0
        for (x1, y1), (x2, y2) in zip(self.ring, np.roll(self.ring, -1, axis=0)):
            c = x1 * y2 - x2 * y1
            cx += (x1 + x2) * c
            cy += (y1 + y2) * c
        self.center = np.array([cx / (6 * a), cy / (6 * a)]) if abs(a) > 1e-6 else self.ring.mean(0)
        self.area = abs(a)
        self.ring_simple = simplify_ring(self.ring)
        self.radius = float(np.max(np.linalg.norm(self.ring - self.center, axis=1)))
        self.props = parcel_props(props)

        self.cam = Camera(self.W, self.H, 62 if self.portrait else 44)
        self._plan_camera()

    # -- kamera planı ----------------------------------------------------
    def _plan_camera(self):
        cam = self.cam
        min_fov = min(cam.hfov, cam.vfov)
        self.d_orbit = float(np.clip(2 * self.radius / (0.30 * 2 * math.tan(min_fov / 2)), 180, 1100))
        ext = self.ring.max(0) - self.ring.min(0)
        fw, fh = (0.80, 0.36) if self.portrait else (0.44, 0.62)
        self.d_top = max(ext[0] / (fw * 2 * math.tan(cam.hfov / 2)),
                         ext[1] / (fh * 2 * math.tan(cam.vfov / 2)), 110.0)
        vis_w, vis_h = cam.visible_size(self.d_top)
        if self.portrait:
            off_top = (0.0, -0.20 * vis_h)
        else:
            off_top = (0.20 * vis_w, 0.0)
        # Parselin top-view'daki ekran konumu ile merkez arasındaki fark (bilgi kartı için yer açar)
        self.top_offset = off_top

        t = [0, 5, 10.5, 17, 34, 41.5, 52]
        d0 = 9000.0
        self.f_logd = pchip(t, np.log([d0, 7200, 1700, self.d_orbit, self.d_orbit * 1.05,
                                       self.d_top, self.d_top * 1.12]))
        self.f_pitch = pchip(t, [90, 90, 70, 48, 44, 90, 90])
        self.f_heading = pchip(t, [-20, -12, 25, 85, 320, 360, 364])
        self.f_offx = pchip(t, [0, 0, 0, 0, 0, off_top[0], off_top[0]])
        self.f_offy = pchip(t, [0, 0, 0, 0, 0, off_top[1], off_top[1]])
        self.min_pitch = math.degrees(cam.vfov) / 2 + 9

    def camera_at(self, t):
        dist = math.exp(self.f_logd(t))
        pitch = max(self.f_pitch(t), self.min_pitch)
        heading = self.f_heading(t)
        # El kamerası değil ama dron gibi hafif salınım
        heading += 0.35 * math.sin(2 * math.pi * 0.07 * t) + 0.15 * math.sin(2 * math.pi * 0.19 * t + 1)
        wob = 0.004 * dist
        tx = self.center[0] + self.f_offx(t) + wob * math.sin(2 * math.pi * 0.05 * t)
        ty = self.center[1] + self.f_offy(t) + wob * math.cos(2 * math.pi * 0.043 * t + 2)
        return (tx, ty), dist, heading, pitch

    # -- görüntü katmanları ---------------------------------------------
    def load_imagery(self):
        a = self.args
        zd = a.detail_zoom
        self.imagery_date = None
        if a.tile_url:
            tile_url, self.credit = a.tile_url, IMAGERY_CREDIT
        else:
            print("Esri Wayback arşivinde en güncel çekim aranıyor...")
            try:
                wb = choose_wayback(self.proj.lon0, self.proj.lat0, zd, release=a.wayback_release)
            except (requests.RequestException, ValueError) as e:
                print(f"  ! Wayback arşivine ulaşılamadı ({e.__class__.__name__}); güncel World Imagery kullanılıyor.")
                wb = {"release": "güncel", "tile_url": TILE_URL_DEFAULT, "capture": None}
            tile_url = wb["tile_url"]
            cap = wb["capture"]
            self.credit = "Uydu görüntüsü: Esri World Imagery"
            if cap:
                self.imagery_date = cap["date"]
                src = f" · {cap['source']}" if cap["source"] else ""
                self.credit += f"{src} · Çekim: {cap['date'].strftime('%d.%m.%Y')}"
                print(f"Seçilen: Wayback {wb['release']} yayını, çekim tarihi {cap['date'].isoformat()}")
            else:
                self.credit += f" (Wayback {wb['release']})"
        r_detail = float(np.clip(self.d_orbit * 1.5 + self.radius, 420, 1400))
        plan = [(zd - 6, 20000), (zd - 4, 6500), (zd - 2, max(1900, r_detail * 3)), (zd, r_detail)]
        self.layers = []
        for z, radius in plan:
            img, origin, st = fetch_mosaic(tile_url, z, self.proj, radius, a.cache_dir, a.workers)
            print(f"  zoom {z}: {img.shape[1]}x{img.shape[0]} px, {st['total']} karo, "
                  f"eksik {st['missing']}, boş {st['placeholder']}")
            bad = (st["missing"] + st["placeholder"]) / max(1, st["total"])
            if bad > 0.25:
                if z == zd:
                    print(f"  ! zoom {z} görüntüsü bu bölgede eksik; daha düşük çözünürlükle devam.")
                    continue
                raise RuntimeError(f"zoom {z} karolarının %{bad * 100:.0f}'i indirilemedi.")
            self.layers.append(Layer(img, z, origin, self.proj))

    # -- tek kare --------------------------------------------------------
    def render_ground(self, P, dist, pitch):
        W, H = self.W, self.H
        corners = [(0, 0), (W, 0), (0, H), (W, H), (W / 2, 0)]
        Pinv = np.linalg.inv(P)
        world = []
        for x, y in corners:
            v = Pinv @ np.array([x, y, 1.0])
            world.append((v[0] / v[2], v[1] / v[2]))
        start = 0
        for i in range(len(self.layers) - 1, -1, -1):
            if self.layers[i].covers(world):
                start = i
                break
        out = np.empty((H, W, 3), np.float32)
        out[:] = HAZE
        footprint = dist / (self.cam.f * math.sqrt(math.sin(math.radians(pitch))))
        for layer in self.layers[start:]:
            lam = math.log2(max(footprint / layer.mpp, 1e-6)) + self.args.mip_bias
            lam = min(max(lam, 0.0), len(layer.levels) - 1.0)
            l0 = int(lam)
            frac = lam - l0
            warped = self._warp(layer, l0, P)
            if frac > 0.04 and l0 + 1 < len(layer.levels):
                w2 = self._warp(layer, l0 + 1, P)
                warped = cv2.addWeighted(warped, 1 - frac, w2, frac, 0)
            alpha = warped[:, :, 3:4].astype(np.float32) * (1 / 255.0)
            out += (warped[:, :, :3].astype(np.float32) - out) * alpha
        # Uzak kısımlarda atmosferik pus (eğik çekimlerde)
        haze = max(0.0, min(1.0, (75 - pitch) / 30)) * 0.42
        if haze > 0:
            yy = np.linspace(1, 0, H, dtype=np.float32)
            g = (np.clip((yy - 0.45) / 0.55, 0, 1) ** 1.6 * haze)[:, None, None]
            out += (np.array(HAZE, np.float32) - out) * g
        return out

    def _warp(self, layer, level, P):
        Hm = P @ layer.A(level)
        return cv2.warpPerspective(layer.levels[level], Hm, (self.W, self.H),
                                   flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=(0, 0, 0, 0))

    def _vignette(self):
        if not hasattr(self, "_vig"):
            yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
            r = np.sqrt(((xx - self.W / 2) / (self.W / 2)) ** 2 + ((yy - self.H / 2) / (self.H / 2)) ** 2)
            self._vig = (1 - 0.28 * np.clip((r - 0.55) / 0.9, 0, 1) ** 1.5)[:, :, None]
        return self._vig

    # -- üst katman öğeleri ---------------------------------------------
    def prepare_overlays(self):
        a, S, F = self.args, self.S, self.fonts
        loc = f"{tr_title(a.mahalle)} Mahallesi · {tr_title(a.ilce)} / {tr_title(a.il)}"
        parcel_txt = f"{a.ada} Ada · {a.parsel} Parsel"
        if self.props["alan"]:
            area = self.props["alan"]
            area_txt = area if "m" in area else f"{area} m²"
        else:
            area_txt = f"≈ {fmt_tr(self.area, 0)} m²"
        self.area_txt = area_txt
        maxw = int(self.W * 0.86)

        title = stack_sprites([
            text_sprite(F, tr_upper(a.title), int(30 * S), True, (255, 205, 60), tracking=int(7 * S), max_width=maxw),
            text_sprite(F, parcel_txt, int(88 * S), True, max_width=maxw),
            text_sprite(F, loc, int(34 * S), False, (235, 235, 235), max_width=maxw),
        ], gap=int(6 * S), align="c")
        self.spr_title = title

        pill_txt = text_sprite(F, parcel_txt, int(30 * S), True, shadow=False)
        pw, ph = pill_txt.shape[1] + int(54 * S), pill_txt.shape[0] + int(14 * S)
        pill = rounded_panel(pw, ph, ph // 2, fill=(14, 18, 24, 215), outline=(255, 196, 40, 255))
        r = int(7 * S)
        dot = Image.new("RGBA", (2 * r + 1, 2 * r + 1), (0, 0, 0, 0))
        ImageDraw.Draw(dot).ellipse([0, 0, 2 * r, 2 * r], fill=(255, 196, 40, 255))
        over(pill, pil_to_bgra(dot), int(18 * S), (ph - 2 * r) // 2)
        over(pill, pill_txt, int(36 * S), (ph - pill_txt.shape[0]) // 2)
        self.spr_pill = pill

        lt_items = [text_sprite(F, "YÜZÖLÇÜMÜ", int(22 * S), True, (255, 205, 60), tracking=int(4 * S)),
                    text_sprite(F, area_txt, int(54 * S), True)]
        sub = " · ".join(v for v in (self.props["nitelik"] and tr_title(self.props["nitelik"]),
                                     self.props["mevkii"] and f"Mevkii: {tr_title(self.props['mevkii'])}") if v)
        if sub:
            lt_items.append(text_sprite(F, sub, int(26 * S), False, (230, 230, 230)))
        lt = stack_sprites(lt_items, gap=int(2 * S))
        pad = int(26 * S)
        panel = rounded_panel(lt.shape[1] + 2 * pad + int(8 * S), lt.shape[0] + 2 * pad, int(18 * S))
        cv2.rectangle(panel, (0, int(14 * S)), (int(6 * S), panel.shape[0] - int(14 * S)),
                      (40, 196, 255, 255), -1)
        over(panel, lt, pad + int(8 * S), pad)
        self.spr_lower = panel

        self.spr_card = self._info_card(parcel_txt)
        self.spr_compass = self._compass()

        end = [text_sprite(F, tr_upper(a.title), int(30 * S), True, (255, 205, 60), tracking=int(7 * S), max_width=maxw),
               text_sprite(F, parcel_txt, int(84 * S), True, max_width=maxw),
               text_sprite(F, loc, int(34 * S), False, (235, 235, 235), max_width=maxw),
               text_sprite(F, f"Yüzölçümü: {area_txt}", int(34 * S), False, (235, 235, 235), max_width=maxw)]
        if a.contact:
            end.append(spacer(18 * S))
            end.append(text_sprite(F, a.contact, int(44 * S), True, (255, 205, 60), max_width=maxw))
        self.spr_end = stack_sprites(end, gap=int(8 * S), align="c")
        small = int(19 * S)
        self.spr_credit = text_sprite(F, self.credit, small, False, (235, 235, 235))
        self.spr_end_credit = stack_sprites([
            text_sprite(F, f"{self.credit} · Parsel sınırı: TKGM", small, False, (200, 200, 200), max_width=maxw),
            text_sprite(F, "Görüntüler uydu verisinden oluşturulmuştur, temsilidir; "
                           "resmi bilgi için tapu kayıtlarını esas alınız.", small, False, (170, 170, 170),
                        max_width=maxw),
        ], gap=int(2 * S), align="c")

    def _info_card(self, parcel_txt):
        a, S, F = self.args, self.S, self.fonts
        rows = [("Konum", f"{tr_title(a.mahalle)} Mah., {tr_title(a.ilce)} / {tr_title(a.il)}"),
                ("Ada / Parsel", f"{a.ada} / {a.parsel}"),
                ("Yüzölçümü", self.area_txt)]
        for key, label in (("nitelik", "Nitelik"), ("mevkii", "Mevkii"), ("pafta", "Pafta")):
            if self.props[key]:
                rows.append((label, tr_title(self.props[key]) if key != "pafta" else self.props[key]))
        if self.imagery_date:
            rows.append(("Görüntü tarihi", self.imagery_date.strftime("%d.%m.%Y")))
        card_w = int((self.W * 0.40) if not self.portrait else (self.W * 0.88))
        pad = int(34 * S)
        inner = card_w - 2 * pad
        items = [text_sprite(F, tr_upper(a.title), int(22 * S), True, (255, 205, 60), tracking=int(5 * S),
                             shadow=False, max_width=inner),
                 text_sprite(F, parcel_txt, int(46 * S), True, shadow=False, max_width=inner),
                 spacer(14 * S)]
        for label, value in rows:
            items.append(text_sprite(F, tr_upper(label), int(18 * S), True, (175, 175, 175),
                                     tracking=int(3 * S), shadow=False, max_width=inner))
            items.append(spacer(2 * S))
            items.append(text_sprite(F, value, int(30 * S), False, shadow=False, max_width=inner))
            items.append(spacer(14 * S))
        if a.contact:
            items.append(spacer(6 * S))
            items.append(text_sprite(F, a.contact, int(32 * S), True, (255, 205, 60), shadow=False,
                                     max_width=inner))
        body = stack_sprites(items, gap=0)
        card = rounded_panel(card_w, body.shape[0] + 2 * pad, int(22 * S), fill=(12, 16, 22, 238))
        over(card, body, pad, pad)
        return card

    def _compass(self):
        S = self.S
        size = int(92 * S)
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, size - 3, size - 3], fill=(12, 16, 22, 170), outline=(255, 255, 255, 200), width=2)
        c = size / 2
        d.polygon([(c, size * 0.17), (c - size * 0.11, c), (c + size * 0.11, c)], fill=(60, 80, 255, 255))
        d.polygon([(c, size * 0.83), (c - size * 0.11, c), (c + size * 0.11, c)], fill=(235, 235, 235, 255))
        f = self.fonts.get(int(15 * S), True)
        d.text((c, size * 0.06), "K", font=f, fill=(255, 255, 255, 255), anchor="mt")
        return pil_to_bgra(img)

    def draw_parcel(self, frame, H, progress, alpha, fill):
        if alpha <= 0:
            return
        S = self.S
        pts = project(H, self.ring_simple)
        closed = np.vstack([pts, pts[:1]])
        if progress < 1:
            seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
            cum = np.concatenate([[0], np.cumsum(seg)])
            L = progress * cum[-1]
            k = int(np.searchsorted(cum, L, side="right")) - 1
            k = min(k, len(seg) - 1)
            r = (L - cum[k]) / max(seg[k], 1e-6)
            path = np.vstack([closed[:k + 1], closed[k] + (closed[k + 1] - closed[k]) * r])
        else:
            path = closed
        ip = np.round(path * 16).astype(np.int32)
        overlay = np.zeros_like(frame)
        if fill > 0:
            cv2.fillPoly(overlay, [np.round(pts * 16).astype(np.int32)], GOLD, cv2.LINE_AA, shift=4)
            cv2.addWeighted(frame, 1.0, overlay, 0.22 * fill * alpha, 0, dst=frame)
            overlay[:] = 0
        cv2.polylines(overlay, [ip], False, GOLD, max(2, int(14 * S)), cv2.LINE_AA, shift=4)
        overlay = cv2.GaussianBlur(overlay, (0, 0), 9 * S)
        cv2.add(frame, (overlay * (0.9 * alpha)).astype(np.uint8), dst=frame)
        line = frame.copy()
        cv2.polylines(line, [ip], False, GOLD, max(2, int(4.5 * S)), cv2.LINE_AA, shift=4)
        cv2.polylines(line, [ip], False, WHITE, max(1, int(1.4 * S)), cv2.LINE_AA, shift=4)
        n_vis = len(path) - (1 if progress >= 1 else 0)
        for p in path[:n_vis]:
            cv2.circle(line, (int(p[0] * 16), int(p[1] * 16)), int(5 * S) * 16, WHITE, -1, cv2.LINE_AA, shift=4)
        cv2.addWeighted(line, alpha, frame, 1 - alpha, 0, dst=frame)

    def draw_edge_lengths(self, frame, H, alpha):
        if alpha <= 0:
            return
        ring = self.ring_simple
        pts = project(H, ring)
        nxt = np.roll(ring, -1, axis=0)
        lens = np.linalg.norm(nxt - ring, axis=1)
        perim = lens.sum()
        c = project(H, [self.center])[0]
        shown = sorted(range(len(lens)), key=lambda i: -lens[i])[:12]
        placed = []
        for i in shown:
            if lens[i] < max(4.0, perim * 0.05):
                continue
            a, b = pts[i], pts[(i + 1) % len(pts)]
            mid = (a + b) / 2
            d = b - a
            nrm = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-6)
            if np.dot(nrm, mid - c) < 0:
                nrm = -nrm
            key = ("edge", i)
            if key not in self._edge_cache:
                txt = text_sprite(self.fonts, f"{fmt_tr(lens[i], 1)} m", int(22 * self.S), True, shadow=False)
                pad = int(8 * self.S)
                spr = rounded_panel(txt.shape[1] + 2 * pad, txt.shape[0] + pad // 2, int(10 * self.S),
                                    fill=(12, 16, 22, 200))
                over(spr, txt, pad, pad // 4)
                self._edge_cache[key] = spr
            p = mid + nrm * 30 * self.S
            spr = self._edge_cache[key]
            m = 6 * self.S
            box = (p[0] - spr.shape[1] / 2 - m, p[1] - spr.shape[0] / 2 - m,
                   p[0] + spr.shape[1] / 2 + m, p[1] + spr.shape[0] / 2 + m)
            if any(box[0] < q[2] and q[0] < box[2] and box[1] < q[3] and q[1] < box[3] for q in placed):
                continue
            placed.append(box)
            blit(frame, spr, p[0], p[1], alpha, "cm")

    def draw_scale_bar(self, frame, dist, alpha):
        if alpha <= 0:
            return
        S = self.S
        mpp = dist / self.cam.f
        meters = nice_length(170 * S * mpp)
        px = meters / mpp
        x0 = int(48 * S)
        y0 = int(self.H - 70 * S) if not self.portrait else int(100 * S)
        key = ("scale", meters)
        if key not in self._edge_cache:
            self._edge_cache[key] = text_sprite(self.fonts, f"{meters} m", int(22 * S), True)
        layer = frame.copy()
        cv2.rectangle(layer, (x0, y0), (int(x0 + px), y0 + int(7 * S)), WHITE, -1, cv2.LINE_AA)
        cv2.rectangle(layer, (x0, y0), (int(x0 + px / 2), y0 + int(7 * S)), (30, 30, 30), -1, cv2.LINE_AA)
        cv2.addWeighted(layer, alpha, frame, 1 - alpha, 0, dst=frame)
        blit(frame, self._edge_cache[key], x0, y0 - int(4 * S), alpha, "lb")

    def render_frame(self, t):
        target, dist, heading, pitch = self.camera_at(t)
        P = self.cam.ground_homography(target, dist, heading, pitch)
        img = self.render_ground(P, dist, pitch)
        img *= self._vignette()
        frame = np.clip(img, 0, 255).astype(np.uint8)
        S, W, H = self.S, self.W, self.H

        # Parsel sınırı: alçalırken çizilir, sonra parlar.
        prog = ease((t - 9.0) / 4.0)
        self.draw_parcel(frame, P, prog, window(t, 8.6, 50.0, 0.5, 2.0), ease((t - 13.0) / 1.5))

        # Açılış başlığı
        a = window(t, 0.6, 6.2, 1.0, 1.0)
        if a > 0:
            dark = frame.astype(np.float32)
            yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            g = np.exp(-((yy - 0.5) / 0.28) ** 2) * 0.5 * a
            frame[:] = (dark * (1 - g)).astype(np.uint8)
            blit(frame, self.spr_title, W / 2, H / 2 + (1 - ease((t - 0.6) / 1.6)) * 30 * S, a, "cm")

        # Parsel etiketi (pin)
        a = window(t, 15.0, 35.0, 1.2, 1.2)
        if a > 0:
            c = project(P, [self.center])[0]
            top = c[1] - 120 * S
            line = frame.copy()
            cv2.line(line, (int(c[0]), int(c[1])), (int(c[0]), int(top)), WHITE, max(1, int(2 * S)), cv2.LINE_AA)
            cv2.circle(line, (int(c[0]), int(c[1])), int(6 * S), WHITE, -1, cv2.LINE_AA)
            cv2.addWeighted(line, a, frame, 1 - a, 0, dst=frame)
            blit(frame, self.spr_pill, c[0], top, a, "cb")

        # Alt bilgi bandı (yüzölçümü)
        a = window(t, 19.0, 33.5, 0.9, 0.9)
        if a > 0:
            slide = (1 - ease((t - 19.0) / 0.9)) * 40 * S
            blit(frame, self.spr_lower, 48 * S - slide, H - 56 * S, a, "lb")

        # Tepeden görünüm: kenar uzunlukları, ölçek, bilgi kartı
        a = window(t, 40.0, 47.5, 1.0, 0.8)
        self.draw_edge_lengths(frame, P, a)
        self.draw_scale_bar(frame, dist, a)
        a = window(t, 40.3, 47.6, 1.0, 0.8)
        if a > 0:
            slide = (1 - ease((t - 40.3) / 1.0)) * 60 * S
            if self.portrait:
                blit(frame, self.spr_card, W / 2, H - 70 * S + slide, a, "cb")
            else:
                blit(frame, self.spr_card, W - 60 * S + slide, H / 2, a, "rm")

        # Pusula
        a = window(t, 7.0, 47.5, 1.0, 0.8)
        if a > 0:
            M = cv2.getRotationMatrix2D((self.spr_compass.shape[1] / 2, self.spr_compass.shape[0] / 2), heading, 1)
            rot = cv2.warpAffine(self.spr_compass, M, self.spr_compass.shape[1::-1], flags=cv2.INTER_LINEAR)
            blit(frame, rot, W - 40 * S, 40 * S, a, "rt")

        # Görüntü kaynağı (lisans gereği)
        blit(frame, self.spr_credit, W - 24 * S, H - 14 * S, 0.85 * (1 - ease((t - 47.0) / 1.0)), "rb")

        # Kapanış kartı
        e = ease((t - 47.3) / 1.6)
        if e > 0:
            small = cv2.resize(frame, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
            small = cv2.GaussianBlur(small, (0, 0), 1 + 3 * e)
            blurred = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
            mix = cv2.addWeighted(frame, 1 - e, blurred, e, 0)
            frame[:] = (mix.astype(np.float32) * (1 - 0.55 * e)).astype(np.uint8)
            a = ease((t - 48.0) / 1.0)
            blit(frame, self.spr_end, W / 2, H * 0.46 + (1 - a) * 24 * S, a, "cm")
            blit(frame, self.spr_end_credit, W / 2, H - 40 * S, a, "cb")
        fade = ease((self.DURATION - t) / 0.8)
        if fade < 1:
            frame[:] = (frame * fade).astype(np.uint8)
        return frame

    # -- çıktı -----------------------------------------------------------
    def render(self, out_path):
        self._edge_cache = {}
        self.prepare_overlays()
        fps = self.args.fps
        n = int(self.DURATION * fps)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        audio = None
        if self.args.music:
            audio = Path(self.args.music)
        elif not self.args.no_music:
            audio = out_path.with_suffix(".muzik.wav")
            make_music(audio, self.DURATION)

        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
               "-s", f"{self.W}x{self.H}", "-r", str(fps), "-i", "-"]
        if audio:
            cmd += ["-i", str(audio)]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(self.args.crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        if audio:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={self.DURATION - 2.5}:d=2.5",
                    "-shortest"]
        cmd.append(str(out_path))
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        poster_t = 44.0
        t0 = time.time()
        try:
            for i in range(n):
                t = i / fps
                frame = self.render_frame(t)
                if abs(t - poster_t) < 0.5 / fps:
                    cv2.imwrite(str(out_path.with_suffix(".kapak.jpg")), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
                proc.stdin.write(frame.tobytes())
                if i % fps == 0 or i == n - 1:
                    el = time.time() - t0
                    eta = el / (i + 1) * (n - i - 1)
                    print(f"\r  kare {i + 1}/{n}  ({(i + 1) / n * 100:4.1f}%)  kalan ~{eta:4.0f} sn",
                          end="", flush=True)
        finally:
            proc.stdin.close()
            proc.wait()
        print()
        if audio and not self.args.music:
            audio.unlink(missing_ok=True)
        if proc.returncode != 0:
            raise RuntimeError("ffmpeg video kodlamasında hata verdi.")


# ------------------------------------------------------------------- main ----

def main(argv=None):
    p = argparse.ArgumentParser(description="Uydu görüntüsünden dron tarzı arsa tanıtım videosu üretir.")
    g = p.add_argument_group("Parsel")
    g.add_argument("--il", default="Bursa")
    g.add_argument("--ilce", default="Nilüfer")
    g.add_argument("--mahalle", default="Odunluk")
    g.add_argument("--ada", default="4632")
    g.add_argument("--parsel", default="9")
    g.add_argument("--geojson", help="TKGM'den indirilmiş parsel GeoJSON dosyası")
    g.add_argument("--kml", help="Parsel KML dosyası")
    g.add_argument("--coords", help="Köşe koordinatları: 'enlem,boylam; enlem,boylam; ...'")
    v = p.add_argument_group("Video")
    v.add_argument("--out", help="Çıktı MP4 yolu (varsayılan: cikti/arsa_<ada>_<parsel>.mp4)")
    v.add_argument("--title", default="Arsa Tanıtımı", help="Üst başlık, ör. 'Satılık Arsa'")
    v.add_argument("--contact", default="", help="Kapanışta gösterilecek iletişim bilgisi")
    v.add_argument("--width", type=int, default=1920)
    v.add_argument("--height", type=int, default=1080)
    v.add_argument("--vertical", action="store_true", help="Dikey 1080x1920 (Reels/Shorts/Story)")
    v.add_argument("--fps", type=int, default=30)
    v.add_argument("--crf", type=int, default=18, help="x264 kalite (düşük = daha iyi)")
    v.add_argument("--preview", action="store_true", help="Hızlı önizleme: yarı çözünürlük, 24 fps")
    v.add_argument("--music", help="Kendi müzik dosyanız (mp3/wav)")
    v.add_argument("--no-music", action="store_true")
    v.add_argument("--font", help="Normal yazı tipi dosyası (.ttf/.otf)")
    v.add_argument("--font-bold", help="Kalın yazı tipi dosyası (.ttf/.otf)")
    m = p.add_argument_group("Görüntü kaynağı")
    m.add_argument("--tile-url", help="Kendi XYZ karo adresiniz ({z}/{x}/{y}); verilmezse Esri Wayback "
                                      "arşivindeki en güncel çekim kullanılır")
    m.add_argument("--wayback-release", help="Belirli bir Wayback yayın tarihi (YYYY-AA-GG)")
    m.add_argument("--detail-zoom", type=int, default=19, help="En yakın zoom seviyesi (18-19)")
    m.add_argument("--cache-dir", default=str(Path(__file__).with_name(".karo_onbellek")))
    m.add_argument("--workers", type=int, default=8)
    m.add_argument("--mip-bias", type=float, default=-0.25, help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    if args.vertical:
        args.width, args.height = 1080, 1920
    if args.preview:
        args.width, args.height, args.fps = args.width // 2, args.height // 2, 24
    args.width -= args.width % 2
    args.height -= args.height % 2

    if args.geojson:
        ring, props = load_geojson(args.geojson)
    elif args.kml:
        ring, props = load_kml(args.kml)
        for arg, key in (("il", "İl"), ("ilce", "İlçe"), ("mahalle", "Mahalle"), ("ada", "Ada"),
                         ("parsel", "ParselNo")):
            if props.get(key):
                setattr(args, arg, props[key])
    elif args.coords:
        ring, props = parse_coords(args.coords)
    else:
        try:
            feature = fetch_parcel_tkgm(args.il, args.ilce, args.mahalle, args.ada, args.parsel)
        except RuntimeError as e:
            sys.exit(f"HATA: {e}\n\nParsel sınırı alınamadı. parselsorgu.tkgm.gov.tr üzerinden parseli "
                     f"bulup GeoJSON/KML olarak indirin ve --geojson / --kml ile verin.")
        ring = _largest_ring(feature["geometry"])
        props = feature.get("properties") or {}
        out_dir = Path(args.out).parent if args.out else Path("cikti")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"parsel_{args.ada}_{args.parsel}.geojson").write_text(
            json.dumps(feature, ensure_ascii=False, indent=2), encoding="utf-8")

    out = args.out or f"cikti/arsa_{args.ada}_{args.parsel}{'_dikey' if args.vertical else ''}.mp4"
    video = Video(args, ring, props)
    print(f"Parsel: {len(video.ring)} köşe, ≈{fmt_tr(video.area, 0)} m², merkez "
          f"{video.proj.lat0:.6f}, {video.proj.lon0:.6f}")
    print("Uydu görüntüsü indiriliyor...")
    video.load_imagery()
    print(f"Video oluşturuluyor: {video.W}x{video.H} @ {args.fps} fps, {video.DURATION:.0f} sn")
    video.render(out)
    print(f"Tamamlandı: {out}")
    print(f"Kapak görseli: {Path(out).with_suffix('.kapak.jpg')}")


if __name__ == "__main__":
    main()
