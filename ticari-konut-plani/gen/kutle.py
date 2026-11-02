"""Kütle modeli: zemin kat 7 dükkan (770,5 m²) + 7 normal kat × 5 daire = 35 daire.
python3 kutle.py  ->  ../kutle/ altına OBJ+MTL ve GLB (düz ve testere dişi balkonlu iki sürüm)."""
import os, math
from geom import (PLOT, SE, NE, H, X0, X1, Y_N, Y_GF_S, Y_UP_S, Y_CORR, GF_DEPTH, FLAT_W, CORE_W,
                  BALC_D, SAW_DEPTH, PLOT_AREA, x_front, x_rear)
from mesh import Model

GF_H, FL_H, N_FL = 4.5, 3.0, 7
ROOF = GF_H + N_FL * FL_H
# normal kat: 5 daire + 2 çekirdek, yol tarafına yaslı
UP = []
_x = X1 - (5 * FLAT_W + 2 * CORE_W)
for n in ["D1", "CB", "D2", "D3", "D4", "CA", "D5"]:
    w = CORE_W if n[0] == "C" else FLAT_W
    UP.append((n, _x, _x + w)); _x += w
UX0 = UP[0][1]
CB = [m for m in UP if m[0] == "CB"][0]
# zemin kat: lobi B çekirdek B'nin altına alındı; dükkan alanları aynı
GF = [("TEKNIK", 6.0, 9.0), ("DK7", 9.0, 16.0), ("DK6", 16.0, 26.0), ("DK5", 26.0, CB[1]),
      ("LOBI_B", CB[1], CB[2]), ("DK4", CB[2], CB[2] + 10), ("DK3", CB[2] + 10, CB[2] + 20),
      ("DK2", CB[2] + 20, CB[2] + 30), ("LOBI_A", CB[2] + 30, CB[2] + 30 + CORE_W), ("DK1", X1 - 10, X1)]

def build(saw):
    m = Model()
    # ---- çevre ----
    m.prism("arsa", "arsa_zemin", PLOT, -0.05, 0.0)
    m.prism("yesil_kuzey", "yesil", [(x_rear(Y_N, 0), Y_N), (x_front(Y_N, 0), Y_N), NE, (PLOT[3])], 0, 0.03)
    m.prism("yesil_arka", "yesil", [PLOT[0], (x_rear(Y_N, 0), Y_N), (X0, Y_N), (X0, 0)], 0, 0.03)
    m.prism("arac_yolu", "asfalt", [(X0, 6), (x_front(6, 0), 6), (x_front(12, 0), 12), (X0, 12)], 0, 0.01)
    m.prism("otopark", "asfalt", [(8, 0.8), (x_front(0.8, 0), 0.8), (x_front(6, 0), 6), (8, 6)], 0, 0.01)
    m.prism("rampa", "rampa", [(59.5, 0.8), (83.5, 0.8), (83.5, 6), (59.5, 6)], 0, 0.02)
    dx, dy = NE[0] - SE[0], NE[1] - SE[1]; L = math.hypot(dx, dy); nx, ny = dy / L, -dx / L
    on = lambda y, o: (SE[0] + (y - SE[1]) * dx / dy + nx * o, y + ny * o)
    m.prism("kaldirim", "kaldirim", [on(-12, 0), on(-12, 3.5), on(44, 3.5), on(44, 0)], -0.05, 0.12)
    m.prism("cadde", "asfalt", [on(-12, 3.5), on(-12, 17), on(44, 17), on(44, 3.5)], -0.1, -0.02)
    for i, y in enumerate(range(-8, 44, 7)):
        m.tree(f"agac_cadde_{i}", *on(y, 1.75), h=6.5, r=1.8)
    for i, x in enumerate([14, 30, 46, 62, 78]):
        m.tree(f"agac_kuzey_{i}", x, 29.6, h=5.5, r=1.4)
    for i, (x, y) in enumerate([(91.0, 21.0), (93.5, 26.0), (89.0, 14.0)]):
        m.tree(f"agac_meydan_{i}", x, y, h=6, r=1.7)
    # ---- zemin kat ----
    m.box("zemin_kat", "zemin_kat", X0, Y_GF_S + 0.55, 0, X1 - 0.1, Y_N, GF_H - 0.6)
    m.box("tabela_bandi", "tabela_bandi", X0, Y_GF_S, GF_H - 0.6, X1, Y_N, GF_H)
    for n, a, b in GF:
        mat = "cam_vitrin" if n.startswith(("DK", "LOBI")) else "zemin_kat"
        m.panel(f"vitrin_{n}", mat, (a + 0.15, Y_GF_S + 0.4), (b - 0.15, Y_GF_S + 0.4), 0, GF_H - 0.6, t=0.06)
        m.box(f"kolon_{n}", "doseme_bandi", a - 0.15, Y_GF_S, 0, a + 0.15, Y_GF_S + 0.4, GF_H - 0.6)
    m.box("kolon_son", "doseme_bandi", X1 - 0.3, Y_GF_S, 0, X1, Y_GF_S + 0.4, GF_H - 0.6)
    m.panel("vitrin_DK1_yol", "cam_vitrin", (X1, Y_GF_S + 0.6), (X1, Y_N - 0.3), 0, GF_H - 0.6, t=0.06)
    # zemin kat çatısı: arka bölüm ortak teras (korkuluk)
    if UX0 > X0 + 1:
        for a, b in [((X0, Y_GF_S), (UX0, Y_GF_S)), ((X0, Y_GF_S), (X0, Y_N)), ((X0, Y_N), (UX0, Y_N))]:
            m.panel("teras_korkuluk", "cam", a, b, GF_H, GF_H + 1.1, t=0.03)
    # ---- normal katlar ----
    for k in range(N_FL):
        z0 = GF_H + k * FL_H
        m.box(f"kat_{k+1}", "cephe_beyaz", UX0, Y_UP_S, z0 + 0.3, X1, Y_N, z0 + FL_H)
        m.box(f"kat_{k+1}_doseme", "doseme_bandi", UX0 - 0.05, Y_UP_S - 0.05, z0, X1 + 0.05, Y_N + 0.05, z0 + 0.3)
        for n, a, b in UP:
            if n[0] == "C":
                m.panel(f"kat_{k+1}_cekirdek_cam", "cam", (a + 0.6, Y_UP_S - 0.03), (b - 0.6, Y_UP_S - 0.03), z0 + 0.6, z0 + 2.7)
                continue
            ys = Y_UP_S - 0.03
            for wa, wb, wz in [(0.5, 2.3, 0.9), (3.3, 5.3, 0.9), (6.3, 9.5, 0.3)]:
                m.panel(f"kat_{k+1}_pencere", "cam", (a + wa, ys), (a + wb, ys), z0 + wz, z0 + 2.7)
            if n == "D5":
                m.panel(f"kat_{k+1}_pencere_yol", "cam", (X1 + 0.03, Y_UP_S + 1.0), (X1 + 0.03, Y_UP_S + 5.0), z0 + 0.9, z0 + 2.7)
            if saw:
                tri = [(a + 5.8, Y_UP_S), (a + 5.8, Y_UP_S - SAW_DEPTH), (a + 10.0, Y_UP_S)]
                m.prism(f"kat_{k+1}_balkon", "balkon_doseme", tri, z0, z0 + 0.25)
                m.box(f"kat_{k+1}_sagir_duvar", "sagir_duvar", a + 5.8, Y_UP_S - SAW_DEPTH, z0, a + 6.0, Y_UP_S, z0 + FL_H)
                m.panel(f"kat_{k+1}_korkuluk", "cam", (a + 6.0, Y_UP_S - SAW_DEPTH + 0.14), (a + 10.0, Y_UP_S), z0 + 0.25, z0 + 1.35, t=0.03)
            else:
                m.box(f"kat_{k+1}_balkon", "balkon_doseme", a + 5.8, Y_UP_S - BALC_D, z0, a + 10.0, Y_UP_S, z0 + 0.25)
                for p, q in [((a + 5.8, Y_UP_S - BALC_D), (a + 10, Y_UP_S - BALC_D)), ((a + 5.8, Y_UP_S - BALC_D), (a + 5.8, Y_UP_S)),
                             ((a + 10, Y_UP_S - BALC_D), (a + 10, Y_UP_S))]:
                    m.panel(f"kat_{k+1}_korkuluk", "cam", p, q, z0 + 0.25, z0 + 1.35, t=0.03)
        for x in range(int(UX0) + 3, int(X1) - 1, 6):
            m.panel(f"kat_{k+1}_koridor_pencere", "cam", (x, Y_N + 0.03), (x + 1.6, Y_N + 0.03), z0 + 1.0, z0 + 2.4)
    # ---- çatı ----
    m.box("cati_doseme", "doseme_bandi", UX0 - 0.05, Y_UP_S - 0.05, ROOF, X1 + 0.05, Y_N + 0.05, ROOF + 0.3)
    for p, q in [((UX0, Y_UP_S), (X1, Y_UP_S)), ((X1, Y_UP_S), (X1, Y_N)), ((X1, Y_N), (UX0, Y_N)), ((UX0, Y_N), (UX0, Y_UP_S))]:
        m.panel("cati_parapet", "cephe_beyaz", p, q, ROOF + 0.3, ROOF + 1.2, t=0.2)
    for n, a, b in UP:
        if n[0] == "C":
            m.box(f"cati_cikisi_{n}", "cekirdek", a + 0.3, Y_UP_S + 0.3, ROOF + 0.3, b - 0.3, Y_CORR - 0.1, ROOF + 3.0)
    return m

def areas():
    gf = (X1 - X0) * GF_DEPTH
    shops = sum((b - a) * GF_DEPTH for n, a, b in GF if n.startswith("DK"))
    lobby = sum((b - a) * GF_DEPTH for n, a, b in GF if n.startswith("LOBI"))
    up = (X1 - UX0) * (Y_N - Y_UP_S)
    common = (up - 5 * FLAT_W * 8.0) * N_FL + lobby
    return dict(gf=gf, shops=shops, up=up, total=gf + N_FL * up, emsal=(gf + N_FL * up) / PLOT_AREA,
                share=common / 35, height=ROOF, ux0=UX0)

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kutle")
    os.makedirs(out, exist_ok=True)
    for saw, tag in [(True, "testere"), (False, "duz")]:
        m = build(saw)
        m.export_obj(os.path.join(out, f"kutle_{tag}.obj"))
        m.export_glb(os.path.join(out, f"kutle_{tag}.glb"))
        print(tag, "nesne/üçgen:", m.stats())
    print({k: round(v, 2) for k, v in areas().items()})
    print("GF:", GF); print("UP:", UP)
