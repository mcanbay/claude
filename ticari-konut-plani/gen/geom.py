"""Arsa geometrisi, çekme mesafeleri, bina modülleri ve basit SVG yardımcıları.

Koordinat sistemi (metre): x = parselin uzun ekseni (arkadan yola doğru, +x yol tarafı),
y = parsel genişliği (+y kuzey kenarı / 100 m'lik kenar). Ölçüler uydu görüntüsündeki
kenar uzunluklarından türetilmiştir (100 / 94.1 / 31.2 / 32.3 m); yaklaşıktır.
"""
import math

# ---------------- ARSA ----------------
N_LEN, S_LEN, BACK_LEN, FRONT_LEN = 100.0, 94.1, 31.2, 32.3
_diff = N_LEN - S_LEN                                   # 5.9
D0 = ((FRONT_LEN**2 - BACK_LEN**2) / _diff - _diff) / 2  # arka kenar kayması
D1 = D0 + _diff                                          # ön kenar kayması
H = math.sqrt(BACK_LEN**2 - D0**2)                       # parsel genişliği (dik)

SW, SE = (0.0, 0.0), (S_LEN, 0.0)
NW, NE = (D0, H), (D0 + N_LEN, H)
PLOT = [SW, SE, NE, NW]
PLOT_AREA = (N_LEN + S_LEN) / 2 * H

FRONT_SB, SIDE_SB, REAR_SB = 10.0, 3.0, 3.0   # arka çekme: varsayım (3 m)

def x_front(y, d=FRONT_SB):
    dx, dy = NE[0] - SE[0], NE[1] - SE[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L          # içe doğru (−x yönlü) normal
    px, py = SE[0] + nx * d, SE[1] + ny * d
    return px + (y - py) * dx / dy

def x_rear(y, d=REAR_SB):
    dx, dy = NW[0] - SW[0], NW[1] - SW[1]
    L = math.hypot(dx, dy)
    nx, ny = dy / L, -dx / L          # içe doğru (+x yönlü) normal
    px, py = SW[0] + nx * d, SW[1] + ny * d
    return px + (y - py) * dx / dy

Y_S_ENV, Y_N_ENV = SIDE_SB, H - SIDE_SB
ENVELOPE = [(x_rear(Y_S_ENV), Y_S_ENV), (x_front(Y_S_ENV), Y_S_ENV),
            (x_front(Y_N_ENV), Y_N_ENV), (x_rear(Y_N_ENV), Y_N_ENV)]

def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2

# ---------------- BİNA ----------------
Y_N = Y_N_ENV                 # bina kuzey cephesi = kuzey yan çekme hattı
GF_DEPTH = 11.5               # zemin kat derinliği
Y_GF_S = Y_N - GF_DEPTH       # zemin kat güney cephesi
FLAT_D, CORR_D = 8.0, 2.0     # daire derinliği, kat koridoru
Y_UP_S = Y_N - FLAT_D - CORR_D  # normal kat güney cephesi
Y_CORR = Y_N - CORR_D         # koridor güney duvarı
BALC_D = Y_UP_S - Y_GF_S      # balkon derinliği (zemin kat cephesine hizalı)
FLAT_W, CORE_W = 10.0, 5.4
X0 = 6.0

# normal kat modülleri (arkadan yola doğru)
UP_MODULES = []
_x = X0
for name in ["D1", "CB", "D2", "D3", "D4", "D5", "D6", "CA", "D7"]:
    w = CORE_W if name.startswith("C") else FLAT_W
    UP_MODULES.append((name, _x, _x + w)); _x += w
X1 = _x

# zemin kat modülleri
def _gf():
    m = {n: (a, b) for n, a, b in UP_MODULES}
    tech_w = 3.0
    out = [("TEKNIK", X0, X0 + tech_w), ("DK7", X0 + tech_w, m["D1"][1]),
           ("LOBI_B", *m["CB"])]
    for i, n in enumerate(["D2", "D3", "D4", "D5", "D6"]):
        out.append((f"DK{6 - i}", *m[n]))
    out += [("LOBI_A", *m["CA"]), ("DK1", *m["D7"])]
    return out
GF_MODULES = _gf()

# daire iç bölümleri (yerel: x batıdan doğuya 0..10, y güney cepheden koridora 0..8)
FLAT_ROOMS = [
    ("Yatak 2", 0.0, 0.0, 2.8, 4.2),
    ("Yatak 1", 2.8, 0.0, 5.8, 4.2),
    ("Salon", 5.8, 0.0, 10.0, 6.0),
    ("Açık Mutfak", 5.8, 6.0, 10.0, 8.0),
    ("Banyo", 0.0, 4.2, 2.4, 6.6),
    ("Kiler", 0.0, 6.6, 2.4, 8.0),
    ("Hol", 2.4, 4.2, 5.8, 6.0),
    ("WC", 2.4, 6.0, 3.8, 8.0),
    ("Antre", 3.8, 6.0, 5.8, 8.0),
]
BALCONY = (5.8, -BALC_D, 10.0, 0.0)
WALL_LOSS = 0.10   # duvar payı (net/brüt)

# ---------------- SVG ----------------
class Svg:
    def __init__(self, x0, y0, x1, y1, scale, pad=40, pad_top=None):
        self.x0, self.y0, self.x1, self.y1, self.s = x0, y0, x1, y1, scale
        self.pad = pad; self.pt = pad if pad_top is None else pad_top
        self.w = (x1 - x0) * scale + 2 * pad
        self.h = (y1 - y0) * scale + pad + self.pt
        self.el = []
    def X(self, x): return self.pad + (x - self.x0) * self.s
    def Y(self, y): return self.pt + (self.y1 - y) * self.s
    def _a(self, kw):
        return " ".join(f'{k.rstrip("_").replace("_", "-")}="{v}"' for k, v in kw.items())
    def rect(self, x0, y0, x1, y1, **kw):
        self.el.append(f'<rect x="{self.X(x0):.1f}" y="{self.Y(y1):.1f}" width="{(x1-x0)*self.s:.1f}" '
                       f'height="{(y1-y0)*self.s:.1f}" {self._a(kw)}/>')
    def poly(self, pts, **kw):
        p = " ".join(f"{self.X(x):.1f},{self.Y(y):.1f}" for x, y in pts)
        self.el.append(f'<polygon points="{p}" {self._a(kw)}/>')
    def line(self, a, b, **kw):
        self.el.append(f'<line x1="{self.X(a[0]):.1f}" y1="{self.Y(a[1]):.1f}" x2="{self.X(b[0]):.1f}" '
                       f'y2="{self.Y(b[1]):.1f}" {self._a(kw)}/>')
    def text(self, x, y, t, size=11, anchor="middle", rot=0, **kw):
        tr = f' transform="rotate({rot} {self.X(x):.1f} {self.Y(y):.1f})"' if rot else ""
        self.el.append(f'<text x="{self.X(x):.1f}" y="{self.Y(y):.1f}" font-size="{size}" '
                       f'text-anchor="{anchor}" dominant-baseline="middle"{tr} {self._a(kw)}>{t}</text>')
    def raw(self, s): self.el.append(s)
    def dim(self, a, b, off, label=None, size=10):
        """a-b arasında, sola doğru 'off' metre kaydırılmış ölçü çizgisi."""
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        nx, ny = -dy / L * off, dx / L * off
        A, B = (a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)
        self.line(a, A, class_="dimx"); self.line(b, B, class_="dimx")
        self.line(A, B, class_="dim")
        for P in (A, B):
            self.el.append(f'<circle cx="{self.X(P[0]):.1f}" cy="{self.Y(P[1]):.1f}" r="1.8" class="dimdot"/>')
        ang = -math.degrees(math.atan2(dy, dx))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        m = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
        lbl = label if label is not None else f"{L:.2f}".rstrip("0").rstrip(".")
        self.text(m[0], m[1], lbl, size=size, rot=ang, class_="dimt")
    def svg(self, title=""):
        return (f'<svg viewBox="0 0 {self.w:.0f} {self.h:.0f}" xmlns="http://www.w3.org/2000/svg" '
                f'role="img" aria-label="{title}">' + "".join(self.el) + "</svg>")

if __name__ == "__main__":
    print(f"D0={D0:.2f} D1={D1:.2f} H={H:.2f} arsa={PLOT_AREA:.0f} m2")
    print("zarf:", [(round(x, 2), round(y, 2)) for x, y in ENVELOPE], f"{poly_area(ENVELOPE):.0f} m2")
    print("X1 =", X1, " ön hat @ y_gf_s:", round(x_front(Y_GF_S), 2), " arka @ Y_N:", round(x_rear(Y_N), 2))
    print("GF:", [(n, a, b) for n, a, b in GF_MODULES])
    shops = sum((b - a) * GF_DEPTH for n, a, b in GF_MODULES if n.startswith("DK"))
    print(f"ticari = {shops:.1f} m2, balkon d = {BALC_D:.2f}")
