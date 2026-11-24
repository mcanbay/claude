"""Site içi ring yolu ve merkezi havuz geometrisi.

Tüm koordinatlar vaziyet planı noktası (pt) cinsindedir; 1 m = 8.065 pt, y aşağı = güney.
Çıktı: ring.json (web modeli ve Blender sahnesi okur) ve ../gorseller/ring_plani.png

Kullanım: python ring.py
"""
import json
import math
import os

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
S = 8.065
m = lambda v: v * S          # meters -> pt

UNITS = json.load(open(os.path.join(HERE, 'units.json'), encoding='utf-8'))
BLOCKS = [
    ('D', 'u31', 212.3, 189.3, False), ('C', 'u31', 384.8, 189.3, False),
    ('B', 'u31', 700.1, 189.3, True), ('A', 'u31', 872.6, 189.3, True),
    ('E', 'u21', 156.7, 445.4, False), ('F', 'u21', 291.0, 445.4, True),
    ('G', 'u21', 425.3, 445.4, True), ('H', 'u21', 604.1, 445.4, True),
    ('I', 'u21', 738.4, 445.4, True), ('J', 'u21', 872.6, 445.4, True),
]
CORE = {'u31': (9.39, 11.984, 3.246, 12.23), 'u21': (7.091, 9.686, 0.0, 8.98)}
BAL = {'u31': (11.532, 13.532), 'u21': (-1.994, 0.0)}


def edge_x(y):  # east parcel edge
    return 1105.9 - (y - 183.4) * 0.15779


def fence_x_north(y):  # fence segment (1104.2,183.9)-(1080.4,335.4) extended
    return 1104.2 - (y - 183.9) * (23.8 / 151.5)


def fence_x_south(y):  # fence segment (1071.4,392.1)-(1042.9,572.2)
    return 1071.4 - (y - 392.1) * (28.5 / 180.1)


# ------------------------------------------------------------ building footprints
foot, terr, canopy, parking_faces = [], [], [], []
for bid, t, bx, by, park in BLOCKS:
    U = UNITS[t]
    W = U['R']['bbox'][2]
    D = U['L']['bbox'][3]
    for s in 'LR':
        x0, z0, x1, z1 = U[s]['bbox']
        foot.append((bid, box(bx + m(x0), by + m(z0), bx + m(x1), by + m(z1))))
        b0, b1 = BAL[t]
        bal = box(bx + m(x0), by + m(b0), bx + m(x1), by + m(b1))
        (foot if not park else terr).append((bid + '-teras' if not park else bid + '-ust_balkon', bal))
    cx0, cx1, cz0, cz1 = CORE[t]
    foot.append((bid + '-cekirdek', box(bx + m(cx0), by + m(cz0), bx + m(cx1), by + m(cz1))))
    if t == 'u31':
        canopy.append((bid, box(bx + m(cx0 - 0.5), by + m(cz1), bx + m(cx1 + 0.5), by + m(cz1 + 1.4))))
    else:
        canopy.append((bid, box(bx + m(cx0 - 0.5), by + m(-1.4), bx + m(cx1 + 0.5), by)))
    if park:
        parking_faces.append((bid, t, bx, bx + m(W), by, by + m(D)))
hard = unary_union([g for _, g in foot] + [g for _, g in canopy])

# ------------------------------------------------------------ cross-section (north -> south)
LANE = m(3.5)
Y_BAL_N = 298.4            # north row balcony / terrace line
Y_BAL_S = 429.2            # south row balcony / terrace line
Y_N0 = Y_BAL_N + m(1.75)   # north lane outer edge (1.75 m sidewalk)
Y_I0 = Y_N0 + LANE         # island top
Y_S1 = Y_BAL_S - m(1.6)    # south lane outer edge (1.6 m sidewalk)
Y_I1 = Y_S1 - LANE         # island bottom
YC = (Y_I0 + Y_I1) / 2
HW = (Y_I1 - Y_I0) / 2     # median half width

X_W, X_E = 300.0, 990.0     # median nose centres
median = LineString([(X_W, YC), (X_E, YC)]).buffer(HW, cap_style='round', quad_segs=24)

# pool bulge in the C-B gap
GAP_X0, GAP_X1 = 557.4, 700.1
BX = (GAP_X0 + GAP_X1) / 2
BHW = (GAP_X1 - GAP_X0) / 2 - LANE - m(1.0)    # 1 m to the end walls
BTOP = 145.3 + m(3.4) + LANE + BHW              # keep a 3.4 m garden at the north fence
bulge = unary_union([box(BX - BHW, BTOP, BX + BHW, YC), Point(BX, BTOP).buffer(BHW, quad_segs=24)])
FILLET = m(3.7)
island = unary_union([median, bulge]).buffer(FILLET, quad_segs=16).buffer(-FILLET, quad_segs=16)

band = island.buffer(LANE, quad_segs=24).difference(island)

# gate plaza and gate lanes to the public road
GATE_Y0, GATE_Y1 = 318.0, 402.0
plaza = box(X_E - 5, Y_N0, 1045.0, Y_S1)
gate_lanes = Polygon([(1035, GATE_Y0), (edge_x(GATE_Y0) + 19, GATE_Y0), (edge_x(GATE_Y1) + 19, GATE_Y1), (1035, GATE_Y1)])
gate_island = Polygon([(1050, GATE_Y0 + LANE), (fence_x_north(GATE_Y0 + LANE) + 4, GATE_Y0 + LANE),
                       (fence_x_south(GATE_Y1 - LANE) + 4, GATE_Y1 - LANE), (1050, GATE_Y1 - LANE)])
gate_island = gate_island.union(Point(1050, (GATE_Y0 + GATE_Y1) / 2).buffer((GATE_Y1 - GATE_Y0) / 2 - LANE, quad_segs=12))
road = unary_union([band, plaza, gate_lanes]).difference(island).difference(gate_island)

# ------------------------------------------------------------ checks
clash = road.intersection(hard)
print('road x building/canopy overlap area (pt2):', round(clash.area, 2))
for name, g in foot + canopy:
    d = road.distance(g)
    if d < m(0.6):
        print(f'  close: {name:16s} {d / S:.2f} m')
for name, g in terr:
    if road.intersects(g):
        print(f'  under first-floor balcony of parking block {name}: {road.intersection(g).area / S / S:.1f} m2 (clear height ~3.0 m)')

# ------------------------------------------------------------ pool and island layout
POOL_W, POOL_L = m(5.0), m(12.5)
pool_y0 = BTOP - m(1.2)
pool = box(BX - POOL_W / 2, pool_y0, BX + POOL_W / 2, pool_y0 + POOL_L)
deck_zone = island.intersection(box(GAP_X0 - 20, 0, GAP_X1 + 20, Y_I0 + m(1.2)))
deck = deck_zone.difference(pool)
path = LineString([(X_W - HW + m(1.0), YC), (X_E + HW - m(1.0), YC)]).buffer(m(0.75), cap_style='flat')
path = path.intersection(island).difference(deck_zone)
median_green = island.difference(deck_zone).difference(path)

# sidewalk band (for removing old lawns) and parking aprons
walk_zone = road.buffer(m(1.75))
aprons = []
for bid, t, x0, x1, y0, y1 in parking_faces:
    if t == 'u31':
        aprons.append(box(x0, y1, x1, Y_N0 + 1))
    else:
        aprons.append(box(x0, Y_S1 - 1, x1, y0))
OLD_GREEN = [
    [(197.3, 145.3), (620.6, 145.3), (620.6, 306.7), (612.6, 314.7), (161.6, 314.7)],
    [(636.8, 173.1), (1037, 173.1), (1061.4, 197.4), (1061.4, 290.5), (1037.3, 314.7), (644.9, 314.7), (636.8, 306.7)],
    [(158.2, 330.8), (210.4, 330.8), (210.4, 396.9), (144.2, 396.9)],
    [(140.9, 413.1), (1000.1, 413.1), (1024.3, 437.2), (1024.3, 537.3), (1000.1, 561.4), (342, 561.4), (318.6, 545.4), (318.6, 585.7), (104.4, 585.8)],
]
# north lawn east of the pool reaches the north fence now (old parking driveways closed)
OLD_GREEN[1] = [(636.8, 152.0), (1066.0, 152.0), (1075.0, 160.0), (1061.4, 197.4), (1061.4, 290.5), (1037.3, 314.7), (644.9, 314.7), (636.8, 306.7)]
cut = unary_union([walk_zone, island, unary_union(aprons), gate_lanes.buffer(m(1.2)), box(620.6, 140, 636.8, 320)])
greens = [Polygon(g).difference(cut) for g in OLD_GREEN]
greens = [g for g in greens if not g.is_empty]

# pedestrian crossings (zebra), defined by a centre line across the lane
def crossing_across(p0, p1, width=m(3.0)):
    return {'a': list(p0), 'b': list(p1), 'w': width}


crossings = [
    crossing_across((BX - BHW - LANE - 2, 288.0), (BX - BHW + 2, 288.0)),     # west leg of the bulge
    crossing_across((BX + BHW - 2, 288.0), (BX + BHW + LANE + 2, 288.0)),     # east leg
    crossing_across((BX, BTOP - BHW - LANE - 2), (BX, BTOP - BHW + 2)),       # top, towards the north garden
    crossing_across((582.4, Y_I1 - 2), (582.4, Y_S1 + 2)),                     # south lane, from the G-H walkway
    crossing_across((470.0, Y_N0 - 2), (470.0, Y_I0 + 2)),
    crossing_across((880.0, Y_N0 - 2), (880.0, Y_I0 + 2)),
    crossing_across((360.0, Y_I1 - 2), (360.0, Y_S1 + 2)),
    crossing_across((815.0, Y_I1 - 2), (815.0, Y_S1 + 2)),
]

# direction arrows along the lane centreline (one-way, counter-clockwise on the map)
centre = island.buffer(LANE / 2, quad_segs=24).exterior
coords = list(centre.coords)
# orient so that the north lane runs westwards
probe = centre.project(Point(800, Y_N0 + LANE / 2))
p_a, p_b = centre.interpolate(probe), centre.interpolate(probe + 5)
if p_b.x > p_a.x:
    centre = LineString(coords[::-1])
L = centre.length
arrows = []
k = 0.0
while k < L:
    p = centre.interpolate(k)
    q = centre.interpolate(min(k + 4, L))
    ang = math.atan2(q.y - p.y, q.x - p.x)
    near_cross = any(LineString([c['a'], c['b']]).distance(p) < m(4) for c in crossings)
    if not near_cross and p.x < 1000:
        arrows.append([round(p.x, 2), round(p.y, 2), round(ang, 4)])
    k += m(12)

# gate details
booth = box(1056, (GATE_Y0 + GATE_Y1) / 2 - m(1.1), 1070, (GATE_Y0 + GATE_Y1) / 2 + m(1.1))
barriers = [[[1062, GATE_Y0 + LANE], [1062, GATE_Y0 + 2]], [[1062, GATE_Y1 - LANE], [1062, GATE_Y1 - 2]]]

# glass pool fence along the bulge edge, with gaps at the three crossings
fence_line = island.buffer(-m(0.35)).exterior.intersection(box(GAP_X0 - 30, 100, GAP_X1 + 30, Y_I0 + m(1.0)))
gaps = unary_union([LineString([c['a'], c['b']]).buffer(m(1.0)) for c in crossings[:3]])
fence_parts = fence_line.difference(gaps)
fence_lines = []
for g in getattr(fence_parts, 'geoms', [fence_parts]):
    if g.length > m(0.5):
        fence_lines.append([[round(x, 2), round(y, 2)] for x, y in g.coords])


def poly_json(g):
    out = []
    for p in getattr(g, 'geoms', [g]):
        if p.is_empty or p.area < 1:
            continue
        p = p.simplify(0.15)
        out.append({'ext': [[round(x, 2), round(y, 2)] for x, y in p.exterior.coords[:-1]],
                    'holes': [[[round(x, 2), round(y, 2)] for x, y in h.coords[:-1]] for h in p.interiors]})
    return out


PARCEL_PTS = [(196.0, 143.7), (1072.0, 143.6), (1105.9, 183.4), (1044.4, 573.2), (1007.2, 604.2), (401.3, 587.4), (102.5, 587.5)]
paving = Polygon(PARCEL_PTS).difference(road).difference(pool.buffer(m(0.35), join_style='mitre'))

R = {
    'scale_pt_per_m': S,
    'paving': poly_json(paving),
    'road': poly_json(road),
    'island': poly_json(island),
    'median_green': poly_json(median_green),
    'median_path': poly_json(path),
    'deck': poly_json(deck),
    'pool': list(pool.bounds),
    'greens': [pj for g in greens for pj in poly_json(g)],
    'aprons': [list(a.bounds) for a in aprons],
    'crossings': crossings,
    'arrows': arrows,
    'gate': {'island': poly_json(gate_island), 'booth': list(booth.bounds), 'barriers': barriers,
             'fence_north_end': [round(fence_x_north(GATE_Y0), 2), GATE_Y0], 'fence_south_end': [round(fence_x_south(GATE_Y1), 2), GATE_Y1],
             'lanes_y': [GATE_Y0, GATE_Y1]},
    'pool_fence': fence_lines,
    'section': {'Y_N0': Y_N0, 'Y_I0': Y_I0, 'Y_I1': Y_I1, 'Y_S1': Y_S1, 'YC': YC, 'X_W': X_W, 'X_E': X_E, 'BX': BX, 'BHW': BHW, 'BTOP': BTOP},
    'stats': {
        'lane_m': 3.5, 'north_sidewalk_m': round((Y_N0 - Y_BAL_N) / S, 2), 'south_sidewalk_m': round((Y_BAL_S - Y_S1) / S, 2),
        'median_m': round((Y_I1 - Y_I0) / S, 2), 'ring_centreline_m': round(L / S, 1),
        'pool_m': [5.0, 12.5], 'pool_island_width_m': round(2 * BHW / S, 2),
        'turn_radius_centre_m': round((HW + LANE / 2) / S, 2), 'road_area_m2': round(road.area / S / S, 0),
        'pool_area_m2': 62.5, 'gate_lane_m': round(LANE / S, 2),
    },
}
json.dump(R, open(os.path.join(HERE, 'ring.json'), 'w'), separators=(',', ':'))
print(json.dumps(R['stats'], indent=1))
print('arrows', len(arrows), 'greens', len(R['greens']), 'fence parts', len(fence_lines))

# ------------------------------------------------------------ dimensioned plan
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, FancyArrow

PARCEL = [(196.0, 143.7), (1072.0, 143.6), (1105.9, 183.4), (1044.4, 573.2), (1007.2, 604.2), (401.3, 587.4), (102.5, 587.5)]
fig, ax = plt.subplots(figsize=(16.5, 9.2), dpi=150)
ax.set_aspect('equal')
ax.invert_yaxis()
ax.axis('off')


def draw(g, **kw):
    hole = kw.pop('hole', '#f4f1ea')
    for p in getattr(g, 'geoms', [g]):
        if p.is_empty:
            continue
        if p.geom_type == 'Polygon':
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, **kw))
            for h in p.interiors:
                ax.add_patch(MPoly(list(h.coords), closed=True, facecolor=hole, edgecolor='none'))


draw(Polygon(PARCEL), facecolor='#e9e4d8', edgecolor='#555', lw=1.2)
for g in greens:
    draw(g, facecolor='#b9d39a', edgecolor='#7fa05c', lw=0.5, hole='#e9e4d8')
draw(median_green, facecolor='#b9d39a', edgecolor='#7fa05c', lw=0.5)
draw(path, facecolor='#f2ecdf', edgecolor='#b8ad97', lw=0.4)
draw(road, facecolor='#5b5f64', edgecolor='#2c2f33', lw=0.8, hole='#b9d39a')
draw(deck, facecolor='#d9c7a6', edgecolor='#9c8a66', lw=0.5)
draw(pool, facecolor='#5fb3d9', edgecolor='#1f6f96', lw=1.0)
draw(gate_island, facecolor='#cfc8b8', edgecolor='#555', lw=0.6)
draw(booth, facecolor='#ffffff', edgecolor='#333', lw=0.8)
for a in aprons:
    draw(a, facecolor='#d6d0c3', edgecolor='#a59d8c', lw=0.4, hatch='///')
for name, g in foot:
    is_bal = 'teras' in name
    draw(g, facecolor='#ffffff' if is_bal else '#8d939a', edgecolor='#333', lw=0.6)
for name, g in terr:
    draw(g, facecolor='none', edgecolor='#666', lw=0.5, linestyle='--')
for c in crossings:
    ln = LineString([c['a'], c['b']])
    draw(ln.buffer(c['w'] / 2, cap_style='flat'), facecolor='#ffffff', edgecolor='#ffffff', lw=0.2, hatch='|||')
for x, y, a in arrows:
    ax.add_patch(FancyArrow(x - math.cos(a) * 8, y - math.sin(a) * 8, math.cos(a) * 16, math.sin(a) * 16, width=3.2, head_width=9, head_length=7,
                            color='white', length_includes_head=True, zorder=5))
for gl in fence_lines:
    xs, ys = zip(*gl)
    ax.plot(xs, ys, color='#2b7bb9', lw=1.0)
for bid, t, bx, by, park in BLOCKS:
    W = UNITS[t]['R']['bbox'][2]
    D = UNITS[t]['L']['bbox'][3]
    ax.text(bx + m(W) / 2, by + m(D) / 2, f'{bid} BLOK\n' + ('zemin: otopark' if park else 'zemin: konut'), ha='center', va='center',
            fontsize=7.5, color='white', fontweight='bold')
# gate & entries
ax.annotate('SİTE GİRİŞİ\n(giriş / çıkış)', xy=(1085, 360), xytext=(1125, 300), fontsize=8, ha='left', arrowprops=dict(arrowstyle='->', lw=0.8))
for bid, t, x0, x1, y0, y1 in parking_faces:
    yy = y1 + 4 if t == 'u31' else y0 - 4
    ax.text((x0 + x1) / 2, yy + (6 if t == 'u31' else -6), 'otopark girişi', ha='center', va='center', fontsize=6, color='#333')


def dim(p0, p1, text, off=(0, 0), rot=0):
    ax.annotate('', xy=p1, xytext=p0, arrowprops=dict(arrowstyle='<->', lw=0.7, color='#c0392b'))
    ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], text, fontsize=7, color='#c0392b', ha='center', va='center', rotation=rot,
            bbox=dict(facecolor='white', edgecolor='none', pad=0.6, alpha=0.85))


xd = 455
dim((xd, Y_BAL_N), (xd, Y_N0), f'kaldırım {R["stats"]["north_sidewalk_m"]:.2f} m', off=(34, 0))
dim((xd, Y_N0), (xd, Y_I0), 'şerit 3,50 m', off=(28, 0))
dim((xd, Y_I0), (xd, Y_I1), f'orta ada {R["stats"]["median_m"]:.2f} m', off=(32, 0))
dim((xd, Y_I1), (xd, Y_S1), 'şerit 3,50 m', off=(28, 0))
dim((xd, Y_S1), (xd, Y_BAL_S), f'kaldırım {R["stats"]["south_sidewalk_m"]:.2f} m', off=(34, 0))
pb = pool.bounds
dim((pb[0], pb[1] - 6), (pb[2], pb[1] - 6), '5,00 m', off=(0, -6))
dim((pb[2] + 6, pb[1]), (pb[2] + 6, pb[3]), '12,50 m', off=(14, 0), rot=90)
ax.text(BX, (pb[1] + pb[3]) / 2, 'HAVUZ', ha='center', va='center', fontsize=8, color='white', fontweight='bold', rotation=90)
ax.text(1150, 470, 'Ring yolu: tek yönlü, saat yönünün tersine\n'
        f'Şerit 3,50 m · Orta eksen uzunluğu ≈ {R["stats"]["ring_centreline_m"]:.0f} m\n'
        f'U dönüşlerinde eksen yarıçapı ≈ {R["stats"]["turn_radius_centre_m"]:.1f} m\n'
        'Otoparklara giriş yalnızca ringden (avlu tarafı)\n'
        'Cadde tarafı otopark girişleri kapatıldı\n'
        f'Havuz 5,00 × 12,50 m ({R["stats"]["pool_area_m2"]:.1f} m²), cam güvenlik korkuluğu\n'
        'Beyaz çizgili alanlar: yaya geçitleri', fontsize=8, va='top', ha='left',
        bbox=dict(facecolor='white', edgecolor='#999', pad=6))
ax.set_xlim(90, 1330)
ax.set_ylim(615, 130)
ax.set_title('İrfaniye 169 Ada 1 Parsel · Site içi ring yolu ve merkezi havuz (öneri)', fontsize=12, loc='left')
os.makedirs(os.path.join(HERE, '..', 'gorseller'), exist_ok=True)
fig.savefig(os.path.join(HERE, '..', 'gorseller', 'ring_plani.png'), bbox_inches='tight', facecolor='white')
print('plan written')
