"""Basit kütle modeli oluşturucu: adlandırılmış nesneler + malzemeler -> OBJ/MTL ve GLB.
Model koordinatları: x,y plan (m), z yukarı. Dışa aktarımda Y-yukarı (x, z, -y) kullanılır."""
import math, os
import numpy as np

MATERIALS = {  # ad: (r, g, b, opaklık, metalik, pürüzlülük)
    "cephe_beyaz": (0.92, 0.91, 0.88, 1, 0, 0.8),
    "doseme_bandi": (0.55, 0.56, 0.58, 1, 0, 0.7),
    "zemin_kat": (0.30, 0.31, 0.33, 1, 0, 0.6),
    "tabela_bandi": (0.12, 0.13, 0.14, 1, 0, 0.5),
    "cam": (0.45, 0.62, 0.72, 0.45, 0.1, 0.05),
    "cam_vitrin": (0.55, 0.70, 0.78, 0.40, 0.1, 0.05),
    "sagir_duvar": (0.78, 0.55, 0.42, 1, 0, 0.8),
    "balkon_doseme": (0.85, 0.84, 0.80, 1, 0, 0.7),
    "cekirdek": (0.80, 0.80, 0.80, 1, 0, 0.8),
    "arsa_zemin": (0.86, 0.83, 0.77, 1, 0, 0.9),
    "yesil": (0.47, 0.64, 0.36, 1, 0, 0.95),
    "asfalt": (0.36, 0.36, 0.37, 1, 0, 0.9),
    "kaldirim": (0.75, 0.74, 0.71, 1, 0, 0.9),
    "rampa": (0.55, 0.58, 0.63, 1, 0, 0.9),
    "agac_govde": (0.40, 0.30, 0.22, 1, 0, 0.9),
    "agac_tac": (0.36, 0.55, 0.30, 1, 0, 0.95),
}

class Model:
    def __init__(self):
        self.objs = {}   # ad -> (malzeme, [verts], [faces])
    def _add(self, name, mat, V, F):
        o = self.objs.setdefault(name, (mat, [], []))
        base = len(o[1]); o[1].extend(V); o[2].extend([tuple(i + base for i in f) for f in F])
    def prism(self, name, mat, poly, z0, z1):
        """Dışbükey çokgeni z0..z1 arasında yükselt (saat yönü tersine sıralanır)."""
        P = list(poly)
        a = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
        if a < 0: P = P[::-1]
        n = len(P)
        V = [(x, y, z0) for x, y in P] + [(x, y, z1) for x, y in P]
        F = [(0, i + 1, i) for i in range(1, n - 1)] + [(n, n + i, n + i + 1) for i in range(1, n - 1)]
        for i in range(n):
            j = (i + 1) % n
            F += [(i, j, n + j), (i, n + j, n + i)]
        self._add(name, mat, V, F)
    def box(self, name, mat, x0, y0, z0, x1, y1, z1):
        self.prism(name, mat, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)
    def panel(self, name, mat, a, b, z0, z1, t=0.04):
        """a-b doğrusu boyunca ince dikey panel (cam/korkuluk/duvar)."""
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        nx, ny = -dy / L * t / 2, dx / L * t / 2
        self.prism(name, mat, [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                               (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], z0, z1)
    def tree(self, name, x, y, h=6.0, r=2.0, n=8):
        ring = lambda rr: [(x + rr * math.cos(2 * math.pi * k / n), y + rr * math.sin(2 * math.pi * k / n)) for k in range(n)]
        self.prism(name + "_govde", "agac_govde", ring(0.18), 0, h * 0.45)
        zc = h * 0.45 + r * 0.9
        rings = [(zc - r * 0.9, 0.35), (zc - r * 0.4, 0.95), (zc + r * 0.3, 0.85), (zc + r * 0.9, 0.0)]
        V, F = [], []
        for z, k in rings:
            V += [(px, py, z) for px, py in ring(max(r * k, 0.001))]
        for ri in range(len(rings) - 1):
            for k in range(n):
                a, b = ri * n + k, ri * n + (k + 1) % n
                F += [(a, b, b + n), (a, b + n, a + n)]
        F += [(0, (k + 1) % n, k) for k in range(1, n - 1)]
        self._add(name + "_tac", "agac_tac", V, F)

    # ---------------- dışa aktarım ----------------
    def export_obj(self, path):
        mtl = os.path.splitext(os.path.basename(path))[0] + ".mtl"
        with open(os.path.join(os.path.dirname(path), mtl), "w") as f:
            for m, (r, g, b, a, _, _) in MATERIALS.items():
                f.write(f"newmtl {m}\nKd {r:.3f} {g:.3f} {b:.3f}\nKa 0 0 0\nKs 0.05 0.05 0.05\nd {a}\nillum 2\n\n")
        with open(path, "w") as f:
            f.write(f"# 4622/3 kütle modeli · birim: metre · Y-yukarı\nmtllib {mtl}\n")
            off = 1
            for name, (mat, V, F) in self.objs.items():
                f.write(f"o {name}\nusemtl {mat}\n")
                for x, y, z in V: f.write(f"v {x:.3f} {z:.3f} {-y:.3f}\n")
                for a, b, c in F: f.write(f"f {a + off} {b + off} {c + off}\n")
                off += len(V)
    def export_glb(self, path):
        import trimesh
        from trimesh.visual.material import PBRMaterial
        sc = trimesh.Scene()
        for name, (mat, V, F) in self.objs.items():
            v = np.array(V, float); v = np.c_[v[:, 0], v[:, 2], -v[:, 1]]
            r, g, b, a, met, rough = MATERIALS[mat]
            pm = PBRMaterial(name=mat, baseColorFactor=[r, g, b, a], metallicFactor=met, roughnessFactor=rough,
                             alphaMode="BLEND" if a < 1 else "OPAQUE", doubleSided=True)
            m = trimesh.Trimesh(v, np.array(F), process=False)
            m.visual = trimesh.visual.TextureVisuals(material=pm)
            sc.add_geometry(m, node_name=name, geom_name=name)
        sc.export(path)
    def stats(self):
        return len(self.objs), sum(len(o[2]) for o in self.objs.values())
