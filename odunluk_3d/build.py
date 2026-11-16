# -*- coding: utf-8 -*-
"""
4622/3 Odunluk Caddesi projesi - 3D model + render (Blender / Cycles)

Kullanim:
    python3 build.py --assets <assets_dir> --view hero --res 2400 1600 --samples 300 --out hero.png
    python3 build.py --assets <assets_dir> --save model.blend --no-render

Olculer PDF kat planlarindan vektorel olarak okunmustur (bkz. README.md).
Koordinat sistemi: orijin = ana blok guneybati kosesi, +X dogu (Odunluk Cad.), +Y kuzey, +Z yukari. Birim metre.
"""
import bpy, math, random, sys, os, argparse
from mathutils import Vector
from collections import defaultdict

# ----------------------------------------------------------------------------- arguments
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument('--assets', required=True)
ap.add_argument('--view', default='hero')
ap.add_argument('--res', nargs=2, type=int, default=[1200, 800])
ap.add_argument('--samples', type=int, default=96)
ap.add_argument('--out', default='render.png')
ap.add_argument('--save', default='')
ap.add_argument('--no-render', action='store_true')
ap.add_argument('--no-trees', action='store_true')
ap.add_argument('--no-context', action='store_true')
ap.add_argument('--gf', type=float, default=2.95, help='zemin kat (dukkan) kat yuksekligi')
args = ap.parse_args(argv)
A = os.path.abspath(args.assets)
random.seed(11)

# ----------------------------------------------------------------------------- project dimensions (m)
FH = 2.95                # kat yuksekligi: 18 riht x 16.38 cm (plandaki merdiven notu)
GF = args.gf             # zemin kat yuksekligi
W, D = 27.67, 23.38      # ana blok dis olculeri (D-B x K-G)
YN0, YS1 = 17.01, 6.37   # kuzey kanat guney yuzu / guney kanat kuzey yuzu (avlu)
XC = 12.88               # cekirdek bati duvari
X7 = 14.28               # 7. kat bati siniri (batisi gezilemeyen teras)
NUP = 7                  # zemin ustu kat sayisi (1-6 normal + 7. kat)
def zf(k):               # k. kat doseme kotu
    return GF + (k - 1) * FH if k >= 1 else 0.0
HT = zf(NUP + 1)         # ust cati kotu
H7 = zf(NUP)             # 7. kat doseme / bati teras kotu
PAR = 0.9                # parapet
SILL, HEAD = 0.9, 2.5
SHEAD = GF - 0.55        # vitrin ust kotu (ustu tabela bandi)
LOG = 1.63               # balkon (loggia) derinligi

# ticari blok (tek kat, C plan, avlusu doguya acik)
TX0, TX1 = -27.94, -13.46
TY1 = 23.72
TS = -21.74              # sirt (spine) dogu yuzu
TAN, TAS = 17.52, 6.21   # kuzey kol guney yuzu / guney kol kuzey yuzu
TROOF, TTOP = 3.30, 4.20

# parsel koseleri
P_NW, P_NE, P_SE, P_SW = (-58.39, 28.54), (44.89, 29.77), (37.58, -3.10), (-59.93, -3.10)
B0 = Vector((P_SE[0], P_SE[1], 0))
T = Vector((P_NE[0] - P_SE[0], P_NE[1] - P_SE[1], 0)).normalized()   # cadde dogrultusu
R = Vector((T.y, -T.x, 0))                                           # caddeye dik (doguya)
def st(r, t, z=0.0):
    p = B0 + R * r + T * t
    return Vector((p.x, p.y, z))
ROAD_Z = -0.15
SW_W, ROAD_W = 3.0, 12.0

# ----------------------------------------------------------------------------- mesh builder
class MB:
    def __init__(s):
        s.v = []; s.f = []
    def quad(s, a, b, c, d):
        i = len(s.v); s.v.extend((tuple(a), tuple(b), tuple(c), tuple(d))); s.f.append((i, i + 1, i + 2, i + 3))
    def poly(s, pts):
        i = len(s.v); s.v.extend(tuple(p) for p in pts); s.f.append(tuple(range(i, i + len(pts))))
    def box(s, o, a, b, c):
        o = Vector(o)
        p = [o, o + a, o + a + b, o + b, o + c, o + a + c, o + a + b + c, o + b + c]
        i = len(s.v); s.v.extend(tuple(x) for x in p)
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            s.f.append(tuple(i + k for k in q))
    def strip(s, bottom, top):
        i = len(s.v); n = len(bottom)
        s.v.extend(tuple(p) for p in bottom); s.v.extend(tuple(p) for p in top)
        for k in range(n - 1):
            s.f.append((i + k, i + k + 1, i + n + k + 1, i + n + k))

M = defaultdict(MB)
MAT = {}

def flush(prefix):
    coll = bpy.data.collections.new(prefix); bpy.context.scene.collection.children.link(coll)
    for name, mb in list(M.items()):
        me = bpy.data.meshes.new(prefix + '_' + name); me.from_pydata(mb.v, [], mb.f); me.update()
        ob = bpy.data.objects.new(prefix + '_' + name, me); coll.objects.link(ob)
        me.materials.append(MAT[name])
    M.clear()
    return coll

class Plane:
    """Dusey cephe duzlemi. u: disaridan bakinca soldan saga, v: mutlak z, d: disari (+)"""
    def __init__(s, P0, N):
        s.P0 = Vector((P0[0], P0[1], 0)); s.N = Vector(N).normalized(); s.U = Vector((0, 0, 1)).cross(s.N)
    def p(s, u, v, d=0.0):
        return s.P0 + s.U * u + s.N * d + Vector((0, 0, v))

def fbox(pl, u0, u1, v0, v1, d0, d1, mat):
    M[mat].box(pl.p(u0, v0, d0), pl.U * (u1 - u0), Vector((0, 0, v1 - v0)), pl.N * (d1 - d0))

# panel modulleri: (genislik, yukseklik, derz, kalinlik)
MOD = {
    'cer_ivory': (1.20, 0.60, 0.012, 0.022),
    'cer_dark':  (0.60, 1.20, 0.012, 0.022),
    'cer_wood':  (0.20, 1.30, 0.005, 0.015),
    'comp_dark': (1.60, 1.50, 0.018, 0.030),
    'comp_bronze': (1.60, 1.50, 0.018, 0.030),
}

def subdiv(a, b, m):
    L = b - a
    n = max(1, round(L / m))
    if L / n > m * 1.3:
        n += 1
    return [a + L * i / n for i in range(n + 1)]

def panels(pl, u0, u1, v0, v1, mat):
    if mat not in MOD:
        M[mat].quad(pl.p(u0, v0), pl.p(u1, v0), pl.p(u1, v1), pl.p(u0, v1)); return
    mu, mv, g, t = MOD[mat]
    M['backing'].quad(pl.p(u0, v0, -0.035), pl.p(u1, v0, -0.035), pl.p(u1, v1, -0.035), pl.p(u0, v1, -0.035))
    us, vs = subdiv(u0, u1, mu), subdiv(v0, v1, mv)
    mb = M[mat]
    for a in range(len(us) - 1):
        for b in range(len(vs) - 1):
            x0, x1, y0, y1 = us[a] + g / 2, us[a + 1] - g / 2, vs[b] + g / 2, vs[b + 1] - g / 2
            f = [pl.p(x0, y0), pl.p(x1, y0), pl.p(x1, y1), pl.p(x0, y1)]
            k = [pl.p(x0, y0, -t), pl.p(x1, y0, -t), pl.p(x1, y1, -t), pl.p(x0, y1, -t)]
            i = len(mb.v); mb.v.extend(tuple(x) for x in f + k)
            mb.f.append((i, i + 1, i + 2, i + 3))
            for q in range(4):
                r = (q + 1) % 4
                mb.f.append((i + q, i + 4 + q, i + 4 + r, i + r))

def facade(pl, ua, ub, va, vb, base, regions=(), groups=None, coping=None, floors=()):
    groups = groups or [(va, vb)]
    vbs = {va, vb}
    for r in regions:
        for k in ('v0', 'v1'):
            if va < r[k] < vb: vbs.add(r[k])
    for z in list(floors) + [g for gg in groups for g in gg]:
        if va < z < vb: vbs.add(z)
    vbs = sorted(vbs)
    gb = []
    for g in groups:
        s = {ua, ub}
        for r in regions:
            if r['v1'] > g[0] + 1e-6 and r['v0'] < g[1] - 1e-6:
                for k in ('u0', 'u1'):
                    if ua < r[k] < ub: s.add(r[k])
        gb.append((g, sorted(s)))
    for j in range(len(vbs) - 1):
        v0, v1 = vbs[j], vbs[j + 1]; vm = (v0 + v1) / 2
        ubs = next(u for g, u in gb if g[0] - 1e-6 <= vm <= g[1] + 1e-6)
        for i in range(len(ubs) - 1):
            u0, u1 = ubs[i], ubs[i + 1]; um = (u0 + u1) / 2
            mat = base; hole = False
            for r in regions:
                if r['u0'] < um < r['u1'] and r['v0'] < vm < r['v1']:
                    if r['t'] == 'mat': mat = r['m']
                    else: hole = True
            if not hole:
                panels(pl, u0, u1, v0, v1, mat)
    for r in regions:
        t = r['t']
        if t == 'win': window(pl, r['u0'], r['u1'], r['v0'], r['v1'], r.get('zf', r['v0'] - SILL), r.get('door', False))
        elif t == 'cwin': cwindow(pl, r['u0'], r['u1'], r['v0'], r['v1'])
        elif t == 'loggia': loggia(pl, r['u0'], r['u1'], r['zf'], r['depth'], r['doors'])
        elif t == 'shop': shopfront(pl, r['u0'], r['u1'], r['v0'], r['v1'], r.get('deep', 2.8), r.get('door', True))
    if coping is not None:
        fbox(pl, ua - 0.03, ub + 0.03, vb, vb + 0.05, -0.30, 0.05, 'alu')
        M['roof_par'].quad(pl.p(ua, coping, -0.30), pl.p(ub, coping, -0.30), pl.p(ub, vb, -0.30), pl.p(ua, vb, -0.30))

# ----------------------------------------------------------------------------- facade components
def curtain(pl, ua, ub, z0, z1, d):
    n = max(2, int((ub - ua) / 0.07))
    bot, top = [], []
    for i in range(n + 1):
        u = ua + (ub - ua) * i / n
        dd = d + (0.03 if i % 2 else -0.03) + random.uniform(-0.008, 0.008)
        bot.append(pl.p(u, z0, dd)); top.append(pl.p(u, z1, dd))
    M['curtain'].strip(bot, top)

def window(pl, u0, u1, v0, v1, zfl, door=False, d=0.16):
    Rv = M['reveal']
    Rv.quad(pl.p(u0, v0, 0), pl.p(u0, v0, -d), pl.p(u0, v1, -d), pl.p(u0, v1, 0))
    Rv.quad(pl.p(u1, v0, -d), pl.p(u1, v0, 0), pl.p(u1, v1, 0), pl.p(u1, v1, -d))
    Rv.quad(pl.p(u0, v1, -d), pl.p(u1, v1, -d), pl.p(u1, v1, 0), pl.p(u0, v1, 0))
    if door:
        Rv.quad(pl.p(u0, v0, 0), pl.p(u1, v0, 0), pl.p(u1, v0, -d), pl.p(u0, v0, -d))
    else:
        fbox(pl, u0 - 0.02, u1 + 0.02, v0 - 0.035, v0 + 0.005, -d, 0.05, 'alu')
    fw, fd = 0.055, 0.07
    fbox(pl, u0, u0 + fw, v0, v1, -d - fd, -d, 'alu'); fbox(pl, u1 - fw, u1, v0, v1, -d - fd, -d, 'alu')
    fbox(pl, u0, u1, v1 - fw, v1, -d - fd, -d, 'alu'); fbox(pl, u0, u1, v0, v0 + fw, -d - fd, -d, 'alu')
    n = max(1, round((u1 - u0) / 0.85))
    for i in range(1, n):
        um = u0 + (u1 - u0) * i / n
        fbox(pl, um - 0.04, um + 0.04, v0, v1, -d - fd, -d, 'alu')
    g = -d - 0.035
    M['glass'].quad(pl.p(u0, v0, g), pl.p(u1, v0, g), pl.p(u1, v1, g), pl.p(u0, v1, g))
    # ic mekan
    ru0, ru1, z0, z1, dn, df = u0 - 0.45, u1 + 0.45, zfl + 0.005, zfl + 2.70, -d - 0.08, -3.3
    I = M['int_wall']
    I.quad(pl.p(ru0, z0, df), pl.p(ru1, z0, df), pl.p(ru1, z1, df), pl.p(ru0, z1, df))
    I.quad(pl.p(ru0, z0, dn), pl.p(ru0, z0, df), pl.p(ru0, z1, df), pl.p(ru0, z1, dn))
    I.quad(pl.p(ru1, z0, df), pl.p(ru1, z0, dn), pl.p(ru1, z1, dn), pl.p(ru1, z1, df))
    I.quad(pl.p(ru0, z0, dn), pl.p(ru1, z0, dn), pl.p(ru1, v0, dn), pl.p(ru0, v0, dn))
    M['int_ceil'].quad(pl.p(ru0, z1, dn), pl.p(ru1, z1, dn), pl.p(ru1, z1, df), pl.p(ru0, z1, df))
    M['int_floor'].quad(pl.p(ru0, z0, dn), pl.p(ru1, z0, dn), pl.p(ru1, z0, df), pl.p(ru0, z0, df))
    # perdeler
    rr = random.random(); cd = -d - 0.20; cz0, cz1 = zfl + 0.04, min(v1 + 0.12, z1)
    w = u1 - u0
    if rr < 0.30:
        curtain(pl, u0 - 0.1, u1 + 0.1, cz0, cz1, cd)
    elif rr < 0.85:
        a, b = random.uniform(0.12, 0.45), random.uniform(0.12, 0.45)
        curtain(pl, u0 - 0.1, u0 + w * a, cz0, cz1, cd); curtain(pl, u1 - w * b, u1 + 0.1, cz0, cz1, cd)

def cwindow(pl, u0, u1, v0, v1, d=0.12):
    Rv = M['reveal_ctx']
    Rv.quad(pl.p(u0, v0, 0), pl.p(u0, v0, -d), pl.p(u0, v1, -d), pl.p(u0, v1, 0))
    Rv.quad(pl.p(u1, v0, -d), pl.p(u1, v0, 0), pl.p(u1, v1, 0), pl.p(u1, v1, -d))
    Rv.quad(pl.p(u0, v1, -d), pl.p(u1, v1, -d), pl.p(u1, v1, 0), pl.p(u0, v1, 0))
    Rv.quad(pl.p(u0, v0, 0), pl.p(u1, v0, 0), pl.p(u1, v0, -d), pl.p(u0, v0, -d))
    M['glass_ctx'].quad(pl.p(u0, v0, -d), pl.p(u1, v0, -d), pl.p(u1, v1, -d), pl.p(u0, v1, -d))
    um = (u0 + u1) / 2
    fbox(pl, um - 0.03, um + 0.03, v0, v1, -d, -d + 0.03, 'reveal_ctx')

def loggia(pl, u0, u1, zfl, depth, doors):
    top = zfl + HEAD
    M['tile'].quad(pl.p(u0, zfl + 0.02, 0.0), pl.p(u1, zfl + 0.02, 0.0), pl.p(u1, zfl + 0.02, -depth), pl.p(u0, zfl + 0.02, -depth))
    M['soffit'].quad(pl.p(u0, top, 0.0), pl.p(u1, top, 0.0), pl.p(u1, top, -depth), pl.p(u0, top, -depth))
    M['soffit'].quad(pl.p(u0, zfl, 0.0), pl.p(u1, zfl, 0.0), pl.p(u1, zfl, -depth), pl.p(u0, zfl, -depth))
    bp = Plane(pl.P0 - pl.N * depth, pl.N)
    facade(bp, u0, u1, zfl, top, 'cer_wood',
           [dict(t='win', u0=a, u1=b, v0=zfl + 0.02, v1=zfl + 2.25, zf=zfl, door=True) for a, b in doors])
    facade(Plane(pl.P0 + pl.U * u0, pl.U), 0, depth, zfl, top, 'cer_ivory', floors=[zfl + SILL])
    facade(Plane(pl.P0 + pl.U * u1 - pl.N * depth, -pl.U), 0, depth, zfl, top, 'cer_ivory', floors=[zfl + SILL])
    # cam korkuluk
    g = -0.07
    fbox(pl, u0, u1, zfl + 0.02, zfl + 0.13, g - 0.03, g + 0.03, 'alu')
    M['glass_bal'].quad(pl.p(u0 + 0.01, zfl + 0.13, g), pl.p(u1 - 0.01, zfl + 0.13, g), pl.p(u1 - 0.01, zfl + 1.06, g), pl.p(u0 + 0.01, zfl + 1.06, g))
    fbox(pl, u0, u1, zfl + 1.06, zfl + 1.10, g - 0.03, g + 0.03, 'steel')
    n = max(1, round((u1 - u0) / 1.45))
    for i in range(1, n):
        um = u0 + (u1 - u0) * i / n
        fbox(pl, um - 0.006, um + 0.006, zfl + 0.13, zfl + 1.06, g - 0.012, g + 0.012, 'alu')
    # tavan spotu
    for a, b in doors:
        um = (a + b) / 2
        fbox(pl, um - 0.06, um + 0.06, top - 0.012, top, -depth / 2 - 0.06, -depth / 2 + 0.06, 'spot')

def shopfront(pl, u0, u1, v0, v1, deep=2.8, door=True, d=0.12):
    Rv = M['reveal']
    Rv.quad(pl.p(u0, v0, 0), pl.p(u0, v0, -d), pl.p(u0, v1, -d), pl.p(u0, v1, 0))
    Rv.quad(pl.p(u1, v0, -d), pl.p(u1, v0, 0), pl.p(u1, v1, 0), pl.p(u1, v1, -d))
    Rv.quad(pl.p(u0, v1, -d), pl.p(u1, v1, -d), pl.p(u1, v1, 0), pl.p(u0, v1, 0))
    fd = 0.08
    fbox(pl, u0, u1, v0, v0 + 0.12, -d - fd, -d + 0.02, 'alu')
    fbox(pl, u0, u0 + 0.06, v0, v1, -d - fd, -d, 'alu'); fbox(pl, u1 - 0.06, u1, v0, v1, -d - fd, -d, 'alu')
    fbox(pl, u0, u1, v1 - 0.06, v1, -d - fd, -d, 'alu')
    w = u1 - u0
    n = max(1, round(w / 1.45))
    for i in range(1, n):
        um = u0 + w * i / n
        fbox(pl, um - 0.03, um + 0.03, v0, v1, -d - fd, -d, 'alu')
    if door and n >= 1:
        k = n // 2
        a, b = u0 + w * k / n, u0 + w * (k + 1) / n
        fbox(pl, a, b, v0 + 2.12, v0 + 2.18, -d - fd, -d, 'alu')
        if b - a > 1.3:
            um = (a + b) / 2
            fbox(pl, um - 0.025, um + 0.025, v0, v0 + 2.12, -d - fd, -d, 'alu')
        for um in ((a + b) / 2 - 0.12, (a + b) / 2 + 0.12):
            fbox(pl, um - 0.012, um + 0.012, v0 + 0.85, v0 + 1.35, -d + 0.0, -d + 0.05, 'steel')
    g = -d - 0.04
    M['glass_shop'].quad(pl.p(u0, v0 + 0.12, g), pl.p(u1, v0 + 0.12, g), pl.p(u1, v1, g), pl.p(u0, v1, g))
    ru0, ru1, z0, z1, dn, df = u0 - 0.2, u1 + 0.2, v0 + 0.02, min(v1 + 0.35, GF - 0.12), -d - 0.10, -deep
    I = M['shop_wall']
    I.quad(pl.p(ru0, z0, df), pl.p(ru1, z0, df), pl.p(ru1, z1, df), pl.p(ru0, z1, df))
    I.quad(pl.p(ru0, z0, dn), pl.p(ru0, z0, df), pl.p(ru0, z1, df), pl.p(ru0, z1, dn))
    I.quad(pl.p(ru1, z0, df), pl.p(ru1, z0, dn), pl.p(ru1, z1, dn), pl.p(ru1, z1, df))
    M['int_ceil'].quad(pl.p(ru0, z1, dn), pl.p(ru1, z1, dn), pl.p(ru1, z1, df), pl.p(ru0, z1, df))
    M['shop_floor'].quad(pl.p(ru0, z0, dn), pl.p(ru1, z0, dn), pl.p(ru1, z0, df), pl.p(ru0, z0, df))
    # tavan aydinlatmasi + basit tefris
    for dd in (-0.9, -deep + 0.8):
        if dd > df + 0.3:
            fbox(pl, u0 + 0.3, u1 - 0.3, z1 - 0.02, z1 - 0.005, dd - 0.06, dd + 0.06, 'shop_light')
    if w > 2.5 and deep > 2.2:
        cu = u0 + w * random.uniform(0.15, 0.3)
        fbox(pl, cu, cu + min(1.8, w * 0.35), z0, z0 + 0.95, -deep + 0.5, -deep + 1.05, 'shop_furn')
        fbox(pl, u0 + 0.15, u1 - 0.15, z0 + 0.3, z0 + 2.0, df + 0.02, df + 0.32, 'shop_furn2')

def shop_regs(ua, ub, piers=None, pw=0.5, head=None, top=None, deep=2.8, solid=(), bay=4.6):
    head = SHEAD if head is None else head; top = GF if top is None else top
    regs = [dict(t='mat', u0=ua, u1=ub, v0=0, v1=head, m='cer_dark'),
            dict(t='mat', u0=ua, u1=ub, v0=head, v1=top, m='comp_dark')]
    if piers is None:
        n = max(1, math.ceil((ub - ua - pw) / bay))
        piers = [ua + pw / 2 + (ub - ua - pw) * i / n for i in range(1, n)]
    edges = [ua + pw] + [x for p in piers for x in (p - pw / 2, p + pw / 2)] + [ub - pw]
    for i in range(0, len(edges), 2):
        if i // 2 in solid: continue
        if edges[i + 1] - edges[i] > 0.6:
            regs.append(dict(t='shop', u0=edges[i], u1=edges[i + 1], v0=0.0, v1=head, deep=deep))
    return regs

# ----------------------------------------------------------------------------- main block
def main_block():
    TOP, TOP7 = HT + PAR, H7 + PAR
    FL = [zf(k) for k in range(1, NUP + 2)]
    G2 = lambda top: [(0, GF), (GF, top)]
    def wins(cols, kmax, mat='comp_dark', strip_top=None):
        out = []
        for a, b in cols:
            out.append(dict(t='mat', u0=a, u1=b, v0=GF, v1=strip_top, m=mat))
            for k in range(1, kmax + 1):
                out.append(dict(t='win', u0=a, u1=b, v0=zf(k) + SILL, v1=zf(k) + HEAD, zf=zf(k)))
        return out
    crown = lambda a, b: [dict(t='mat', u0=a, u1=b, v0=H7, v1=TOP, m='comp_dark')]

    # --- DOGU (cadde) cephesi
    pl = Plane((W, 0), (1, 0, 0))
    regs = shop_regs(0, D, piers=[6.37, 12.25, 17.01], deep=5.0)
    regs += [dict(t='mat', u0=6.37, u1=12.27, v0=GF, v1=TOP, m='cer_dark')]
    regs += crown(0, D)
    for k in range(1, NUP + 1):
        z = zf(k)
        for a, b, doors in [(0.30, 6.07, [(1.41, 3.02), (3.94, 5.54)]),
                            (12.45, 16.85, [(13.56, 15.17)]),
                            (17.20, 23.08, [(17.82, 19.41), (20.34, 21.94)])]:
            regs.append(dict(t='loggia', u0=a, u1=b, v0=z, v1=z + HEAD, zf=z, doors=doors, depth=LOG))
        for a, b in [(6.97, 8.58), (9.92, 11.52)]:
            regs.append(dict(t='win', u0=a, u1=b, v0=z + SILL, v1=z + HEAD, zf=z))
    facade(pl, 0, D, 0, TOP, 'cer_ivory', regs, G2(TOP), coping=HT, floors=FL)
    fbox(pl, -0.05, D + 0.05, GF - 0.02, GF + 0.12, 0.0, 1.10, 'comp_dark')          # sacak

    # --- KUZEY cephe (u: dogudan batiya, X = W - u)
    pl = Plane((W, D), (0, 1, 0))
    ub = W - X7
    regs = shop_regs(0, ub) + wins([(7.11, 8.72), (10.79, 12.40)], NUP, strip_top=TOP) + crown(0, ub)
    facade(pl, 0, ub, 0, TOP, 'cer_ivory', regs, G2(TOP), coping=HT, floors=FL)
    regs = shop_regs(ub, W) + wins([(14.25, 15.85), (17.92, 19.52)], NUP - 1, strip_top=TOP7)
    facade(pl, ub, W, 0, TOP7, 'cer_ivory', regs, G2(TOP7), coping=H7, floors=FL)

    # --- GUNEY cephe (u = X)
    pl = Plane((0, 0), (0, -1, 0))
    regs = shop_regs(0, X7) + wins([(8.15, 9.75), (11.82, 13.42)], NUP - 1, strip_top=TOP7)
    facade(pl, 0, X7, 0, TOP7, 'cer_ivory', regs, G2(TOP7), coping=H7, floors=FL)
    regs = shop_regs(X7, W, solid=(0, 1)) + wins([(15.27, 16.88), (18.95, 20.56)], NUP, strip_top=TOP) + crown(X7, W)
    facade(pl, X7, W, 0, TOP, 'cer_ivory', regs, G2(TOP), coping=HT, floors=FL)

    # --- BATI kanat uclari (balkonlu)
    for y_top, doors in ((D, [(1.44, 3.04), (4.24, 5.84)]), (YS1, [(0.55, 2.16), (3.35, 4.96)])):
        pl = Plane((0, y_top), (-1, 0, 0))
        regs = shop_regs(0, 6.37)
        for k in range(1, NUP):
            regs.append(dict(t='loggia', u0=0.30, u1=6.07, v0=zf(k), v1=zf(k) + HEAD, zf=zf(k), doors=doors, depth=LOG))
        facade(pl, 0, 6.37, 0, TOP7, 'cer_ivory', regs, G2(TOP7), coping=H7, floors=FL)

    # --- AVLU cepheleri
    pl = Plane((0, YN0), (0, -1, 0))
    facade(pl, 0, XC, 0, TOP7, 'cer_ivory', shop_regs(0, XC), G2(TOP7), coping=H7, floors=FL)
    pl = Plane((XC, YS1), (0, 1, 0))
    facade(pl, 0, XC, 0, TOP7, 'cer_ivory', shop_regs(0, XC), G2(TOP7), coping=H7, floors=FL)
    pl = Plane((XC, YN0), (-1, 0, 0))                    # cekirdek bati yuzu: bina girisi + merdiven camlari
    wc = YN0 - YS1
    regs = [dict(t='mat', u0=0, u1=wc, v0=0, v1=SHEAD, m='cer_dark'), dict(t='mat', u0=0, u1=wc, v0=SHEAD, v1=GF, m='comp_dark'),
            dict(t='shop', u0=3.7, u1=6.94, v0=0, v1=SHEAD, deep=4.0)]
    regs += wins([(4.52, 6.12)], NUP, strip_top=TOP) + crown(0, wc)
    facade(pl, 0, wc, 0, TOP, 'cer_ivory', regs, G2(TOP), coping=HT, floors=FL)
    fbox(pl, 3.2, 7.44, SHEAD, SHEAD + 0.12, 0.0, 1.6, 'comp_dark')   # giris sacagi

    # --- 7. kat bati duvarlari (terasa bakan)
    for P0, N, wd in (((X7, D), (-1, 0, 0), D - YN0), ((X7, YS1), (-1, 0, 0), YS1),
                      ((X7, YN0), (0, 1, 0), X7 - XC), ((XC, YS1), (0, -1, 0), X7 - XC)):
        facade(Plane(P0, N), 0, wd, H7, TOP, 'comp_dark', coping=HT, floors=FL)

    # --- catilar
    R_ = M['roof']
    R_.quad((0, YN0, H7), (X7, YN0, H7), (X7, D, H7), (0, D, H7))
    R_.quad((0, 0, H7), (X7, 0, H7), (X7, YS1, H7), (0, YS1, H7))
    R_.quad((X7, 0, HT), (W, 0, HT), (W, D, HT), (X7, D, HT))
    R_.quad((XC, YS1, HT), (X7, YS1, HT), (X7, YN0, HT), (XC, YN0, HT))
    # merdiven / asansor kulesi
    x0, x1, y0, y1, z0, z1 = XC + 0.35, 19.0, 7.8, 15.6, HT, HT + 2.7
    for P0, N, wd in (((x1, y0), (1, 0, 0), y1 - y0), ((x1, y1), (0, 1, 0), x1 - x0),
                      ((x0, y1), (-1, 0, 0), y1 - y0), ((x0, y0), (0, -1, 0), x1 - x0)):
        facade(Plane(P0, N), 0, wd, z0, z1, 'comp_dark', coping=z1 - 0.3)
    R_.quad((x0, y0, z1 - 0.3), (x1, y0, z1 - 0.3), (x1, y1, z1 - 0.3), (x0, y1, z1 - 0.3))
    # dis uniteler / cati ekipmani (basit)
    for i in range(4):
        M['equip'].box((21.0 + i * 1.4, 9.0, HT), Vector((1.0, 0, 0)), Vector((0, 0.45, 0)), Vector((0, 0, 0.8)))
    flush('ANA_BLOK')

# ----------------------------------------------------------------------------- commercial block (single storey)
def ticari_block():
    hd = 2.75
    def sr(ua, ub, **kw):
        return shop_regs(ua, ub, head=hd, top=TTOP, **kw)
    G = [(0, hd), (hd, TTOP)]
    faces = [((TX1, TAN), (1, 0, 0), TY1 - TAN), ((TX1, 0), (1, 0, 0), TAS),
             ((TX1, TY1), (0, 1, 0), TX1 - TX0), ((TX0, 0), (0, -1, 0), TX1 - TX0),
             ((TX0, TY1), (-1, 0, 0), TY1),
             ((TS, TAN), (0, -1, 0), TX1 - TS), ((TX1, TAS), (0, 1, 0), TX1 - TS),
             ((TS, TAS), (1, 0, 0), TAN - TAS)]
    for P0, N, wd in faces:
        facade(Plane(P0, N), 0, wd, 0, TTOP, 'cer_dark', sr(0, wd, deep=2.6), G, coping=TROOF)
    R_ = M['roof']
    R_.quad((TX0, TAN, TROOF), (TX1, TAN, TROOF), (TX1, TY1, TROOF), (TX0, TY1, TROOF))
    R_.quad((TX0, 0, TROOF), (TX1, 0, TROOF), (TX1, TAS, TROOF), (TX0, TAS, TROOF))
    R_.quad((TX0, TAS, TROOF), (TS, TAS, TROOF), (TS, TAN, TROOF), (TX0, TAN, TROOF))
    flush('TICARI_BLOK')

# ----------------------------------------------------------------------------- site
def bx(y):  # dogu parsel siniri x(y)
    return P_SE[0] + (P_NE[0] - P_SE[0]) * (y - P_SE[1]) / (P_NE[1] - P_SE[1])

def site():
    F = 900.0
    # cadde
    M['asphalt_road'].quad(st(SW_W, -F, ROAD_Z), st(SW_W + ROAD_W, -F, ROAD_Z), st(SW_W + ROAD_W, F, ROAD_Z), st(SW_W, F, ROAD_Z))
    for r0 in (SW_W - 0.15, SW_W + ROAD_W):
        M['curb'].box(st(r0, -F, ROAD_Z), R * 0.15, T * 2 * F, Vector((0, 0, 0.16)))
    M['sidewalk'].quad(st(0, -F), st(SW_W - 0.15, -F), st(SW_W - 0.15, F), st(0, F))
    M['sidewalk'].quad(st(SW_W + ROAD_W + 0.15, -F), st(SW_W + ROAD_W + 3.2, -F), st(SW_W + ROAD_W + 3.2, F), st(SW_W + ROAD_W + 0.15, F))
    M['ground_far'].quad(st(SW_W + ROAD_W + 3.2, -F, -0.01), st(F, -F, -0.01), st(F, F, -0.01), st(SW_W + ROAD_W + 3.2, F, -0.01))
    zr = ROAD_Z + 0.004
    rc = SW_W + ROAD_W / 2
    for off in (-0.12, 0.12):
        M['paint'].quad(st(rc + off - 0.06, -F, zr), st(rc + off + 0.06, -F, zr), st(rc + off + 0.06, F, zr), st(rc + off - 0.06, F, zr))
    for rl in (SW_W + ROAD_W / 4, SW_W + 3 * ROAD_W / 4):
        t = -400.0
        while t < 400:
            M['paint'].quad(st(rl - 0.06, t, zr), st(rl + 0.06, t, zr), st(rl + 0.06, t + 3, zr), st(rl - 0.06, t + 3, zr)); t += 9
    # yaya gecidi (kuzeyde)
    for i in range(12):
        r0 = SW_W + 0.4 + i * 0.95
        M['paint'].quad(st(r0, 44, zr), st(r0 + 0.5, 44, zr), st(r0 + 0.5, 47.5, zr), st(r0, 47.5, zr))
    # cevre zemin (parsel disi)
    zt = -0.01
    G = M['ground_far']
    G.poly([(P_SE[0], P_SE[1], zt), tuple(st(0, -F, zt)), (-F, -F, zt), (-F, P_SW[1], zt)])
    G.poly([(P_NE[0], P_NE[1], zt), (P_NW[0], P_NW[1], zt), (-F, P_NW[1], zt), (-F, F, zt), tuple(st(0, F, zt))])
    G.poly([(P_SW[0], P_SW[1], zt), (-F, P_SW[1], zt), (-F, P_NW[1], zt), (P_NW[0], P_NW[1], zt)])
    M['grass'].poly([(-104, -3.35, 0.02), (-104, -64, 0.02), (bx(-64) - 0.2, -64, 0.02), (P_SE[0] - 0.2, -3.35, 0.02)])
    # parsel zemini (rampa boslugu ile)
    RX0, RX1, RY0, RY1 = 14.0, 30.5, -2.85, -0.45
    M['pavers'].poly([(P_SW[0], P_SW[1], 0), (RX0, P_SW[1], 0), (RX0, RY1, 0), (RX1, RY1, 0), (RX1, P_SE[1], 0),
                      (P_SE[0], P_SE[1], 0), (P_NE[0], P_NE[1], 0), (P_NW[0], P_NW[1], 0)])
    M['pavers'].quad((RX0, P_SW[1], 0), (RX1, P_SW[1], 0), (RX1, RY0, 0), (RX0, RY0, 0))
    # kapali otopark rampasi
    zb = -2.5
    M['asphalt_lot'].quad((RX1, RY0, 0), (RX1, RY1, 0), (RX0, RY1, zb), (RX0, RY0, zb))
    M['asphalt_lot'].quad((RX0, RY0, zb), (RX0, RY1, zb), (RX0 - 9, RY1, zb), (RX0 - 9, RY0, zb))
    C = M['concrete']
    C.poly([(RX1, RY1, 0), (RX0, RY1, 0), (RX0, RY1, zb)]); C.poly([(RX1, RY0, 0), (RX0, RY0, zb), (RX0, RY0, 0)])
    C.quad((RX0, RY0, zb + 2.25), (RX0, RY1, zb + 2.25), (RX0, RY1, 0), (RX0, RY0, 0))
    Dk = M['dark']
    Dk.quad((RX0, RY0, zb), (RX0 - 9, RY0, zb), (RX0 - 9, RY0, zb + 2.25), (RX0, RY0, zb + 2.25))
    Dk.quad((RX0, RY1, zb), (RX0 - 9, RY1, zb), (RX0 - 9, RY1, zb + 2.25), (RX0, RY1, zb + 2.25))
    Dk.quad((RX0, RY0, zb + 2.25), (RX0 - 9, RY0, zb + 2.25), (RX0 - 9, RY1, zb + 2.25), (RX0, RY1, zb + 2.25))
    Dk.quad((RX0 - 9, RY0, zb), (RX0 - 9, RY1, zb), (RX0 - 9, RY1, zb + 2.25), (RX0 - 9, RY0, zb + 2.25))
    C.box((RX0 - 0.2, RY1, 0), Vector((RX1 - RX0 + 0.2, 0, 0)), Vector((0, 0.15, 0)), Vector((0, 0, 0.95)))
    C.box((RX0 - 0.2, RY0, 0), Vector((0.2, 0, 0)), Vector((0, RY1 - RY0, 0)), Vector((0, 0, 0.95)))
    # asfalt alanlar
    za = 0.008
    L = M['asphalt_lot']
    L.quad((-59.2, -2.7, za), (-29.6, -2.7, za), (-29.6, 28.1, za), (-58.0, 28.1, za))
    L.quad((-29.6, 24.6, za), (bx(24.6) + 0.0, 24.6, za), (bx(28.4), 28.4, za), (-29.6, 28.1, za))
    L.quad(st(-5.7, 3.9, za), st(0, 3.9, za), st(0, 27.9, za), st(-5.7, 27.9, za))
    # otopark cizgileri
    zp = 0.014
    P = M['paint']
    def stalls(x0, x1, y0, n):
        dy = 2.585
        for i in range(n + 1):
            y = y0 + i * dy
            P.quad((x0, y - 0.05, zp), (x1, y - 0.05, zp), (x1, y + 0.05, zp), (x0, y + 0.05, zp))
        return [((x0 + x1) / 2, y0 + (i + 0.5) * dy) for i in range(n)]
    S1 = stalls(-57.63, -52.48, -0.89, 11)
    S2 = stalls(-47.27, -42.11, 1.75, 9)
    S3 = stalls(-36.41, -31.26, 1.75, 9)
    SE_ = []
    for i in range(10):
        t = 4.16 + i * 2.61
        P.quad(st(-5.3, t - 0.05, zp), st(-0.15, t - 0.05, zp), st(-0.15, t + 0.05, zp), st(-5.3, t + 0.05, zp))
        if i < 9: SE_.append(st(-2.7, t + 1.305))
    # yesil alanlar
    beds = [(-27.5, -2.85, 13.0, -0.7), (-11.6, 0.8, -1.8, 5.0), (-11.6, 18.6, -1.8, 22.8), (-29.3, -2.7, -28.3, 28.0),
            ]
    for x0, y0, x1, y1 in beds:
        M['grass'].quad((x0, y0, 0.05), (x1, y0, 0.05), (x1, y1, 0.05), (x0, y1, 0.05))
        for (a, b, c, d_) in ((x0 - 0.12, y0 - 0.12, x1 + 0.12, y0), (x0 - 0.12, y1, x1 + 0.12, y1 + 0.12),
                              (x0 - 0.12, y0, x0, y1), (x1, y0, x1 + 0.12, y1)):
            M['curb'].box((a, b, 0), Vector((c - a, 0, 0)), Vector((0, d_ - b, 0)), Vector((0, 0, 0.10)))
    # parsel duvari (K, B, G)
    def wall(p, q, h=1.1):
        p = Vector((p[0], p[1], 0)); q = Vector((q[0], q[1], 0)); dvec = q - p; n = Vector((-dvec.y, dvec.x, 0)).normalized() * 0.2
        M['plaster_b'].box(p, dvec, n, Vector((0, 0, h)))
        M['curb'].box(p + Vector((0, 0, h)) - n * 0.15, dvec, n * 1.3, Vector((0, 0, 0.05)))
    wall(P_NE, P_NW); wall(P_NW, P_SW); wall(P_SW, (P_SE[0] - 0.3, P_SE[1]))
    # aydinlatma direkleri
    for r, tt, sgn in [(SW_W - 0.6, -34, 1), (SW_W - 0.6, 62, 1), (SW_W + ROAD_W + 0.6, 14, -1), (SW_W + ROAD_W + 0.6, -52, -1), (SW_W + ROAD_W + 0.6, 78, -1)]:
        p = st(r, tt)
        M['pole'].box(p - Vector((0.06, 0.06, 0)), Vector((0.12, 0, 0)), Vector((0, 0.12, 0)), Vector((0, 0, 8.0)))
        M['pole'].box(p + Vector((0, 0, 7.9)) - T * 0.05, R * (2.0 * sgn), T * 0.1, Vector((0, 0, 0.1)))
        M['pole'].box(p + Vector((0, 0, 7.82)) + R * (1.5 * sgn) - T * 0.12, R * (0.6 * sgn), T * 0.24, Vector((0, 0, 0.08)))
    flush('VAZIYET')
    return S1 + S2 + S3, SE_

# ----------------------------------------------------------------------------- context buildings
def block(cx, cy, w, d, ang, floors, mat, fh=3.0, far=False):
    c, s = math.cos(ang), math.sin(ang)
    ex, ey, C = Vector((c, s, 0)), Vector((-s, c, 0)), Vector((cx, cy, 0))
    H = floors * fh
    for P0, N, wd in ((C + ex * w / 2 - ey * d / 2, ex, d), (C + ex * w / 2 + ey * d / 2, ey, w),
                      (C - ex * w / 2 + ey * d / 2, -ex, d), (C - ex * w / 2 - ey * d / 2, -ey, w)):
        pl = Plane(P0, N)
        n = max(1, int((wd - 1.0) / 3.1))
        if far:
            M[mat].quad(pl.p(0, 0), pl.p(wd, 0), pl.p(wd, H + 0.8), pl.p(0, H + 0.8))
            G = M['glass_ctx']
            for i in range(n):
                um = wd * (i + 0.5) / n
                for k in range(0, floors):
                    G.quad(pl.p(um - 0.75, k * fh + 0.9, 0.02), pl.p(um + 0.75, k * fh + 0.9, 0.02),
                           pl.p(um + 0.75, k * fh + 2.35, 0.02), pl.p(um - 0.75, k * fh + 2.35, 0.02))
            continue
        regs = [dict(t='mat', u0=0, u1=wd, v0=0, v1=fh, m='plaster_d')]
        for i in range(n):
            um = wd * (i + 0.5) / n
            regs.append(dict(t='cwin', u0=um - 1.1, u1=um + 1.1, v0=0.3, v1=fh - 0.5))
            for k in range(1, floors):
                regs.append(dict(t='cwin', u0=um - 0.75, u1=um + 0.75, v0=k * fh + 0.9, v1=k * fh + 2.35))
        facade(pl, 0, wd, 0, H + 0.8, mat, regs, coping=H)
    M['roof_ctx'].quad(tuple(C - ex * w / 2 - ey * d / 2 + Vector((0, 0, H))), tuple(C + ex * w / 2 - ey * d / 2 + Vector((0, 0, H))),
                       tuple(C + ex * w / 2 + ey * d / 2 + Vector((0, 0, H))), tuple(C - ex * w / 2 + ey * d / 2 + Vector((0, 0, H))))

CTX_BLOCKS = []

def context():
    rnd = random.Random(5)
    mats = ['plaster_a', 'plaster_b', 'plaster_c', 'plaster_e', 'plaster_a']
    ang = math.atan2(T.y, T.x)
    L = []
    # caddenin batisi: eksenlere paralel doku
    for gx in range(-14, 6):
        for gy in range(-13, 14):
            cx = -32 + gx * 35 + rnd.uniform(-3, 3); cy = 12 + gy * 34 + rnd.uniform(-3, 3)
            w, d = rnd.uniform(18, 26), rnd.uniform(13, 17)
            if rnd.random() < 0.3: w, d = d, w
            if cx + w / 2 > -66 and cx - w / 2 < 49 and cy + d / 2 > -9.5 and cy - d / 2 < 36: continue     # parsel
            if -118 < cx < 50 and -70 < cy < -3: continue                                                   # guneydeki park
            r = (Vector((cx, cy, 0)) - B0).dot(R)
            if r + abs(R.x) * w / 2 + abs(R.y) * d / 2 > -4.0: continue                                    # cadde
            near = abs(cx + 5) < 110 and abs(cy - 12) < 75
            fl = rnd.choice((4, 5, 5, 6)) if (near and cy < 0) else rnd.choice((5, 6, 6, 7, 8))
            L.append((cx, cy, w, d, 0.0, fl, not near))
    # cadde karsisi: caddeye paralel doku
    for it in range(-16, 17):
        for ir in range(0, 12):
            w, d = rnd.uniform(19, 26), rnd.uniform(13, 17)
            r = SW_W + ROAD_W + 3.2 + 4.5 + d / 2 + ir * 34 + (rnd.uniform(-2, 2) if ir else 0)
            p = st(r, it * 33 + rnd.uniform(-3, 3))
            near = ir < 2 and abs(it) < 5
            L.append((p.x, p.y, w, d, ang, rnd.choice((5, 6, 7, 8)), not near))
    for (x, y, w, d, a, fl, far) in L:
        block(x, y, w, d, a, fl, rnd.choice(mats), far=far)
        CTX_BLOCKS.append((x, y, max(w, d) / 2 + 2.5))
    flush('CEVRE')

# ----------------------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    MAT[name] = m
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']

def simple(name, color, rough=0.6, metal=0.0, emit=None, **kw):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    for k, v in kw.items(): b.inputs[k].default_value = v
    return m

def panel_mat(name, color, rough, metal=0.0, var=0.05, mottle=0.06, mscale=2.5, coat=0.0, bump=0.0):
    m, nt, b = new_mat(name); N = nt.nodes; Lk = nt.links.new
    geo = N.new('ShaderNodeNewGeometry')
    mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var
    Lk(geo.outputs['Random Per Island'], mr.inputs['Value'])
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = mscale; nz.inputs['Detail'].default_value = 6
    Lk(tc.outputs['Object'], nz.inputs['Vector'])
    mr2 = N.new('ShaderNodeMapRange'); mr2.inputs['To Min'].default_value = 1 - mottle; mr2.inputs['To Max'].default_value = 1 + mottle
    Lk(nz.outputs['Fac'], mr2.inputs['Value'])
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; Lk(mr.outputs[0], mul.inputs[0]); Lk(mr2.outputs[0], mul.inputs[1])
    hsv = N.new('ShaderNodeHueSaturation'); hsv.inputs['Color'].default_value = (*color, 1)
    Lk(mul.outputs[0], hsv.inputs['Value']); Lk(hsv.outputs[0], b.inputs['Base Color'])
    mr3 = N.new('ShaderNodeMapRange'); mr3.inputs['To Min'].default_value = rough - 0.05; mr3.inputs['To Max'].default_value = rough + 0.07
    Lk(nz.outputs['Fac'], mr3.inputs['Value']); Lk(mr3.outputs[0], b.inputs['Roughness'])
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.15
    if bump:
        nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 60; Lk(tc.outputs['Object'], nz2.inputs['Vector'])
        bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.002
        Lk(nz2.outputs['Fac'], bp.inputs['Height']); Lk(bp.outputs[0], b.inputs['Normal'])
    return m

def wood_mat(name):
    m, nt, b = new_mat(name); N = nt.nodes; Lk = nt.links.new
    geo = N.new('ShaderNodeNewGeometry'); tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (14, 14, 0.6)
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    cmb = N.new('ShaderNodeCombineXYZ'); mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 37.0
    Lk(geo.outputs['Random Per Island'], mm.inputs[0]); Lk(mm.outputs[0], cmb.inputs['Z']); Lk(mm.outputs[0], cmb.inputs['X'])
    Lk(tc.outputs['Object'], add.inputs[0]); Lk(cmb.outputs[0], add.inputs[1]); Lk(add.outputs[0], mp.inputs['Vector'])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 8; nz.inputs['Distortion'].default_value = 1.2
    Lk(mp.outputs[0], nz.inputs['Vector'])
    cr = N.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.25; cr.color_ramp.elements[0].color = (0.16, 0.085, 0.045, 1)
    cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (0.40, 0.24, 0.13, 1)
    Lk(nz.outputs['Fac'], cr.inputs['Fac'])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.82; mr.inputs['To Max'].default_value = 1.15
    Lk(geo.outputs['Random Per Island'], mr.inputs['Value'])
    hsv = N.new('ShaderNodeHueSaturation'); Lk(cr.outputs[0], hsv.inputs['Color']); Lk(mr.outputs[0], hsv.inputs['Value'])
    Lk(hsv.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.42
    return m

def glass_mat(name, tint, ior=2.1, rough=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; MAT[name] = m
    nt = m.node_tree; N = nt.nodes; Lk = nt.links.new
    N.remove(N['Principled BSDF']); out = N['Material Output']
    fr = N.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = ior
    tr = N.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (*tint, 1)
    gl = N.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = rough; gl.inputs['Color'].default_value = (1, 1, 1, 1)
    mx = N.new('ShaderNodeMixShader'); Lk(fr.outputs[0], mx.inputs['Fac']); Lk(tr.outputs[0], mx.inputs[1]); Lk(gl.outputs[0], mx.inputs[2])
    Lk(mx.outputs[0], out.inputs['Surface'])
    return m

def curtain_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; MAT[name] = m
    nt = m.node_tree; N = nt.nodes; Lk = nt.links.new
    N.remove(N['Principled BSDF']); out = N['Material Output']
    df = N.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = (0.86, 0.84, 0.80, 1)
    tl = N.new('ShaderNodeBsdfTranslucent'); tl.inputs['Color'].default_value = (0.86, 0.84, 0.80, 1)
    tr = N.new('ShaderNodeBsdfTransparent')
    m1 = N.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = 0.45; Lk(df.outputs[0], m1.inputs[1]); Lk(tl.outputs[0], m1.inputs[2])
    m2 = N.new('ShaderNodeMixShader'); m2.inputs['Fac'].default_value = 0.22; Lk(m1.outputs[0], m2.inputs[1]); Lk(tr.outputs[0], m2.inputs[2])
    Lk(m2.outputs[0], out.inputs['Surface'])

def tex_mat(name, tex, size, tint=(1, 1, 1), rough_mul=1.0, bump=1.0, vary=0.0, rot=0.0, sat=1.0):
    m, nt, b = new_mat(name); N = nt.nodes; Lk = nt.links.new
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size, 1 / size, 1 / size); mp.inputs['Rotation'].default_value = (0, 0, rot)
    Lk(tc.outputs['Object'], mp.inputs['Vector'])
    def img(suffix, cs):
        n = N.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(A, 'tex', f'{tex}_{suffix}.jpg'), check_existing=True)
        n.image.colorspace_settings.name = cs; Lk(mp.outputs[0], n.inputs['Vector']); return n
    dfn = img('diff', 'sRGB'); rgn = img('rough', 'Non-Color'); nrn = img('nor', 'Non-Color')
    mul = N.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1.0; mul.inputs['Color2'].default_value = (*tint, 1)
    Lk(dfn.outputs['Color'], mul.inputs['Color1'])
    last = mul
    if vary:
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 5
        Lk(tc.outputs['Object'], nz.inputs['Vector'])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - vary; mr.inputs['To Max'].default_value = 1 + vary
        Lk(nz.outputs['Fac'], mr.inputs['Value'])
        hsv = N.new('ShaderNodeHueSaturation'); Lk(mul.outputs[0], hsv.inputs['Color']); Lk(mr.outputs[0], hsv.inputs['Value']); last = hsv
        hsv.inputs['Saturation'].default_value = sat
    Lk(last.outputs[0], b.inputs['Base Color'])
    rm = N.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
    Lk(rgn.outputs['Color'], rm.inputs[0]); Lk(rm.outputs[0], b.inputs['Roughness'])
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
    Lk(nrn.outputs['Color'], nm.inputs['Color']); Lk(nm.outputs[0], b.inputs['Normal'])
    return m

def car_paint_mat():
    m, nt, b = new_mat('car_paint'); N = nt.nodes; Lk = nt.links.new
    oi = N.new('ShaderNodeObjectInfo'); cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.interpolation = 'CONSTANT'
    cols = [(0.85, 0.85, 0.85), (0.55, 0.57, 0.60), (0.03, 0.03, 0.035), (0.20, 0.21, 0.23), (0.80, 0.80, 0.78),
            (0.05, 0.09, 0.20), (0.35, 0.02, 0.02), (0.60, 0.62, 0.64), (0.9, 0.9, 0.9)]
    e = cr.color_ramp.elements
    e[0].position = 0; e[0].color = (*cols[0], 1); e[1].position = 1 / len(cols); e[1].color = (*cols[1], 1)
    for i, c in enumerate(cols[2:], 2):
        x = e.new(i / len(cols)); x.color = (*c, 1)
    Lk(oi.outputs['Random'], cr.inputs['Fac']); Lk(cr.outputs[0], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.55; b.inputs['Roughness'].default_value = 0.32
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.03

def materials():
    panel_mat('cer_ivory', (0.60, 0.55, 0.46), 0.36, var=0.045, mottle=0.04, bump=0.05)
    panel_mat('cer_dark', (0.060, 0.062, 0.066), 0.33, var=0.10, mottle=0.12, bump=0.05)
    panel_mat('comp_dark', (0.045, 0.048, 0.054), 0.30, metal=0.55, var=0.04, mottle=0.02, coat=0.25)
    panel_mat('comp_bronze', (0.33, 0.24, 0.15), 0.30, metal=0.85, var=0.04, mottle=0.02, coat=0.2)
    wood_mat('cer_wood')
    simple('backing', (0.012, 0.012, 0.012), 0.9)
    simple('reveal', (0.04, 0.042, 0.046), 0.35, 0.5)
    simple('reveal_ctx', (0.25, 0.25, 0.26), 0.6)
    simple('alu', (0.035, 0.037, 0.040), 0.38, 0.7)
    simple('steel', (0.62, 0.62, 0.62), 0.25, 1.0)
    simple('pole', (0.18, 0.19, 0.20), 0.45, 0.6)
    glass_mat('glass', (0.80, 0.86, 0.84), 2.1)
    glass_mat('glass_shop', (0.90, 0.94, 0.93), 1.8)
    glass_mat('glass_bal', (0.86, 0.92, 0.90), 1.65)
    simple('glass_ctx', (0.02, 0.025, 0.03), 0.03, 0.0, **{'Specular IOR Level': 1.0, 'IOR': 2.0})
    simple('int_wall', (0.62, 0.60, 0.56), 0.9); simple('int_ceil', (0.80, 0.80, 0.78), 0.9)
    simple('int_floor', (0.30, 0.20, 0.12), 0.5)
    curtain_mat('curtain')
    simple('tile', (0.36, 0.35, 0.33), 0.45); simple('soffit', (0.66, 0.65, 0.62), 0.8)
    simple('spot', (0.9, 0.9, 0.88), 0.4)
    simple('shop_wall', (0.70, 0.69, 0.66), 0.85); simple('shop_floor', (0.55, 0.54, 0.52), 0.25)
    simple('shop_light', (1, 1, 1), 0.5, emit=((1.0, 0.93, 0.82), 22.0))
    simple('shop_furn', (0.20, 0.13, 0.08), 0.5); simple('shop_furn2', (0.45, 0.43, 0.40), 0.6)
    simple('roof', (0.20, 0.20, 0.20), 0.9); simple('roof_par', (0.30, 0.30, 0.30), 0.85)
    simple('equip', (0.75, 0.75, 0.74), 0.5, 0.3)
    simple('plaster_a', (0.46, 0.45, 0.43), 0.85); simple('plaster_b', (0.44, 0.40, 0.34), 0.85); simple('plaster_e', (0.40, 0.31, 0.26), 0.85); simple('roof_ctx', (0.17, 0.165, 0.16), 0.9)
    simple('plaster_c', (0.38, 0.40, 0.42), 0.85); simple('plaster_d', (0.22, 0.21, 0.20), 0.8)
    simple('paint', (0.82, 0.82, 0.80), 0.6); simple('curb', (0.55, 0.55, 0.53), 0.8)
    simple('concrete', (0.50, 0.50, 0.48), 0.8); simple('dark', (0.03, 0.03, 0.03), 0.9)
    tex_mat('asphalt_road', 'asphalt_02', 4.0, tint=(0.75, 0.75, 0.78), vary=0.10)
    tex_mat('asphalt_lot', 'asphalt_04', 4.0, tint=(0.85, 0.85, 0.87), vary=0.10)
    tex_mat('pavers', 'concrete_pavers', 2.0, tint=(0.92, 0.94, 0.96), vary=0.06, sat=0.6)
    tex_mat('sidewalk', 'rectangular_paving', 2.4, tint=(0.80, 0.84, 0.88), vary=0.06, rot=math.atan2(T.y, T.x), sat=0.45)
    tex_mat('ground_far', 'concrete_pavement', 5.0, tint=(0.62, 0.66, 0.70), vary=0.10)
    tex_mat('grass', 'leafy_grass', 2.5, tint=(0.62, 0.80, 0.50), vary=0.22)
    car_paint_mat()
    simple('car_glass', (0.01, 0.012, 0.015), 0.02, 0.0, **{'Specular IOR Level': 1.0, 'IOR': 1.8})
    simple('tire', (0.012, 0.012, 0.012), 0.85); simple('rim', (0.22, 0.22, 0.23), 0.35, 1.0)
    simple('lamp_w', (0.75, 0.75, 0.75), 0.1, 0.0); simple('lamp_r', (0.16, 0.006, 0.006), 0.25)

# ----------------------------------------------------------------------------- cars
def make_car():
    import bmesh
    # anahtar kesitler: x, yari genislik, alt kot, omuz kotu, cati yari genisligi, cati kotu
    keys = [(0.00, 0.55, 0.42, 0.56, 0.45, 0.60), (0.06, 0.76, 0.30, 0.64, 0.66, 0.68), (0.20, 0.86, 0.23, 0.72, 0.76, 0.76),
            (0.50, 0.90, 0.20, 0.80, 0.80, 0.84), (1.15, 0.91, 0.20, 0.92, 0.78, 0.96), (1.85, 0.91, 0.20, 0.95, 0.70, 1.50),
            (2.60, 0.91, 0.20, 0.96, 0.70, 1.53), (3.50, 0.91, 0.20, 0.98, 0.70, 1.50), (4.12, 0.90, 0.20, 1.00, 0.78, 1.06),
            (4.30, 0.86, 0.24, 0.95, 0.76, 0.99), (4.38, 0.74, 0.32, 0.85, 0.64, 0.89), (4.40, 0.55, 0.45, 0.75, 0.45, 0.79)]
    xs = sorted(set([k[0] for k in keys] + [round(0.08 * i, 3) for i in range(1, 55)]))
    def par(x):
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if a[0] <= x <= b[0]:
                f = (x - a[0]) / (b[0] - a[0])
                return [a[j] + (b[j] - a[j]) * f for j in range(1, 6)]
        return list(keys[-1][1:])
    bm = bmesh.new(); loops = []
    for x in xs:
        w, zb, zs, wr, zr = par(x)
        half = [(0.0, zb), (w - 0.14, zb), (w - 0.04, zb + 0.05), (w, zb + 0.20), (w, zs - 0.12), (w - 0.025, zs),
                (wr + 0.03, zs + (zr - zs) * 0.8), (wr - 0.06, zr), (0.0, zr + 0.025)]
        pts = half + [(-y, z) for (y, z) in reversed(half[1:-1])]
        loops.append([bm.verts.new((x - 2.2, y, z)) for (y, z) in pts])
    n = len(loops[0])
    def inr(x, rs): return any(a <= x <= b for a, b in rs)
    for i in range(len(loops) - 1):
        xm = (xs[i] + xs[i + 1]) / 2
        for j in range(n):
            k = (j + 1) % n
            f = bm.faces.new((loops[i][j], loops[i][k], loops[i + 1][k], loops[i + 1][j]))
            seg = j if j < 8 else n - 1 - j
            if seg == 5 and inr(xm, ((1.50, 2.52), (2.64, 3.42), (3.56, 3.96))): f.material_index = 1
            if seg == 7 and inr(xm, ((1.22, 1.80), (3.56, 4.08))): f.material_index = 1
    bm.faces.new(list(reversed(loops[0]))); bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('car_body0'); bm.to_mesh(me); bm.free()
    me.materials.append(MAT['car_paint']); me.materials.append(MAT['car_glass'])
    body0 = bpy.data.objects.new('car_body0', me)
    WX = (-1.36, 1.28)
    # davlumbaz oyma (boolean)
    bm = bmesh.new()
    for x in WX:
        ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.40, radius2=0.40, depth=2.6)
        for v in ret['verts']: v.co = Vector((v.co.x + x, v.co.z, v.co.y + 0.33))
    mc = bpy.data.meshes.new('car_cut'); bm.to_mesh(mc); bm.free()
    cut = bpy.data.objects.new('car_cut', mc)
    sc = bpy.context.scene
    sc.collection.objects.link(body0); sc.collection.objects.link(cut)
    md = body0.modifiers.new('b', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cut
    dg = bpy.context.evaluated_depsgraph_get()
    me_b = bpy.data.meshes.new_from_object(body0.evaluated_get(dg))
    sc.collection.objects.unlink(body0); sc.collection.objects.unlink(cut)
    for p_ in me_b.polygons: p_.use_smooth = True
    body = bpy.data.objects.new('car_body', me_b)
    # tekerlekler, ic hacim, farlar
    bm = bmesh.new()
    def cyl(x, y, z, r, wdt, mi, seg=28):
        ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=wdt)
        vs = set(ret['verts'])
        for v in vs: v.co = Vector((v.co.x + x, v.co.z + y, v.co.y + z))
        for f in bm.faces:
            if all(v in vs for v in f.verts): f.material_index = mi
    def cube(c, sz, mi):
        ret = bmesh.ops.create_cube(bm, size=1.0)
        vs = set(ret['verts'])
        for v in vs: v.co = Vector((c[0] + v.co.x * sz[0], c[1] + v.co.y * sz[1], c[2] + v.co.z * sz[2]))
        for f in bm.faces:
            if all(v in vs for v in f.verts): f.material_index = mi
    for x in WX:
        for sgn in (-1, 1):
            cyl(x, sgn * 0.80, 0.33, 0.33, 0.23, 0)
            cyl(x, sgn * 0.918, 0.33, 0.205, 0.012, 1)
            cyl(x, sgn * 0.922, 0.33, 0.06, 0.012, 0)
    cube((0.0, 0.0, 0.46), (3.7, 1.66, 0.50), 0)                        # ic karanlik hacim
    for sgn in (-1, 1):
        cube((-2.155, sgn * 0.50, 0.665), (0.07, 0.32, 0.085), 2)       # farlar
        cube((2.165, sgn * 0.56, 0.90), (0.07, 0.30, 0.09), 3)          # stoplar
        cube((-0.92, sgn * 0.985, 0.99), (0.10, 0.16, 0.10), 4)         # aynalar
    cube((-2.17, 0.0, 0.43), (0.06, 1.0, 0.16), 0)                      # on izgara
    cube((2.18, 0.0, 0.40), (0.06, 1.2, 0.12), 0)
    me2 = bpy.data.meshes.new('car_parts'); bm.to_mesh(me2); bm.free()
    wheels = bpy.data.objects.new('car_parts', me2)
    for mn in ('tire', 'rim', 'lamp_w', 'lamp_r', 'car_paint'): me2.materials.append(MAT[mn])
    col = bpy.data.collections.new('CAR_SRC'); col.objects.link(body); col.objects.link(wheels)
    return col

def place_cars(car_col, west, east):
    coll = bpy.data.collections.new('ARACLAR'); bpy.context.scene.collection.children.link(coll)
    rnd = random.Random(21)
    def inst(p, ang):
        e = bpy.data.objects.new('car', None); e.instance_type = 'COLLECTION'; e.instance_collection = car_col
        e.location = (p[0], p[1], p[2] if len(p) > 2 else 0.0); e.rotation_euler = (0, 0, ang)
        s = rnd.uniform(0.96, 1.05); e.scale = (s, rnd.uniform(0.97, 1.03), rnd.uniform(0.96, 1.06)); coll.objects.link(e)
    for (x, y) in west:
        if rnd.random() < 0.62:
            inst((x + rnd.uniform(-0.15, 0.15), y, 0.01), rnd.choice((0, math.pi)) + rnd.uniform(-0.03, 0.03))
    a = math.atan2(R.y, R.x)
    for i, p in enumerate(east):
        if i in (0, 3, 4, 7):
            inst((p.x, p.y, 0.01), a + rnd.choice((0, math.pi)) + rnd.uniform(-0.03, 0.03))
    at = math.atan2(T.y, T.x)
    for r, t, d in ((SW_W + 1.6, 49, 1), (SW_W + ROAD_W - 1.7, -58, -1), (SW_W + 4.6, -75, 1)):
        p = st(r, t, ROAD_Z)
        inst((p.x, p.y, ROAD_Z), at + (math.pi if d > 0 else 0))

# ----------------------------------------------------------------------------- vegetation
def load_tree(asset, objname):
    path = os.path.join(A, 'models', asset, asset + '.blend')
    before = set(bpy.data.images)
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [objname]
    for im in set(bpy.data.images) - before:
        if im.filepath.startswith('//'):
            im.filepath = os.path.join(A, 'models', asset, im.filepath[2:])
    ob = dst.objects[0]
    col = bpy.data.collections.new('SRC_' + asset); col.objects.link(ob)
    return col

def trees():
    srcs = [(load_tree('island_tree_02', 'island_tree_02_LOD1'), 3.4),
            (load_tree('tree_small_02', 'tree_small_02_LOD1'), 4.6),
            (load_tree('jacaranda_tree', 'jacaranda_tree_LOD1'), 19.5)]
    coll = bpy.data.collections.new('AGACLAR'); bpy.context.scene.collection.children.link(coll)
    rnd = random.Random(3)
    def put(x, y, h, kind=None, z=0.0):
        k = rnd.randrange(2) if kind is None else kind
        col, h0 = srcs[k]
        e = bpy.data.objects.new('tree', None); e.instance_type = 'COLLECTION'; e.instance_collection = col
        s = h / h0; e.location = (x, y, z); e.rotation_euler = (0, 0, rnd.uniform(0, 6.28)); e.scale = (s, s, s * rnd.uniform(0.92, 1.08))
        coll.objects.link(e)
    # parsel ici
    for x, y in ((-9.5, 2.9), (-4.2, 2.9), (-9.5, 20.7), (-4.2, 20.7)):
        put(x, y, rnd.uniform(5.5, 6.8))
    for x in (-24, -14, -4, 6):
        put(x, -1.8, rnd.uniform(4.2, 5.2), 0)
    for y in (2, 10, 18, 26):
        put(-28.8, y, rnd.uniform(4.5, 5.5), 1)
    # komsu bahceleri
    for x in range(-60, 40, 11):
        put(x + rnd.uniform(-2, 2), 33.5 + rnd.uniform(-1, 2), rnd.uniform(7, 11))
    for y in range(-2, 30, 9):
        put(-64 + rnd.uniform(-1.5, 1.5), y, rnd.uniform(7, 11))
    # cadde agaclari
    for t in (-95, -80, -65, -50, -36, 44, 58, 72, 86, 100):
        p = st(1.3, t); put(p.x, p.y, rnd.uniform(7, 9))
    k = 0
    while k < 34:                                                      # park
        x, y = rnd.uniform(-100, 30), rnd.uniform(-60, -7)
        if x > -70 and y > -34 - (x + 70) * 0.05 and x > -20 and y > -30: continue
        if x > 8 and y > -40: continue
        put(x, y, rnd.uniform(6.5, 11)); k += 1
    for t in range(-110, 120, 14):
        if -34 < t < 6 or 24 < t < 60: continue
        p = st(SW_W + ROAD_W + 1.6, t + rnd.uniform(-1, 1)); put(p.x, p.y, rnd.uniform(7.5, 10))
    # uzak cevre agaclari
    n = 0
    while n < 420:
        x, y = rnd.uniform(-480, 420), rnd.uniform(-430, 450)
        if -70 < x < 52 and -12 < y < 40: continue
        r = (Vector((x, y, 0)) - B0).dot(R)
        if -1.0 < r < SW_W + ROAD_W + 4.5: continue
        if any((x - bx_) ** 2 + (y - by_) ** 2 < rr * rr for bx_, by_, rr in CTX_BLOCKS): continue
        put(x, y, rnd.uniform(7, 12)); n += 1
    for (x, y, h) in ((-45, 62, 15), (-80, -42, 15), (-99, 12, 14)):
        if not any((x - bx_) ** 2 + (y - by_) ** 2 < (rr + 4) ** 2 for bx_, by_, rr in CTX_BLOCKS): put(x, y, h, 2)

# ----------------------------------------------------------------------------- world, cameras, render
SUN_TEX_ANGLE = -34.2   # HDRI'da gunesin konumu (derece, +X'ten saat yonu tersine)

def world(sun_az, strength=1.0):
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; N = nt.nodes; Lk = nt.links.new
    bg = N['Background']; bg.inputs['Strength'].default_value = strength
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping')
    env = N.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(os.path.join(A, 'hdri', 'kloofendal_48d_partly_cloudy_puresky_4k.hdr'))
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(SUN_TEX_ANGLE - (90.0 - sun_az)))
    Lk(tc.outputs['Generated'], mp.inputs['Vector']); Lk(mp.outputs[0], env.inputs['Vector']); Lk(env.outputs[0], bg.inputs['Color'])

VIEWS = {
    # ad: (konum, hedef, lens, shift_y, gunes azimutu [K'den saat yonu], duz_kamera)
    'hero':   (tuple(st(SW_W + ROAD_W + 1.6, -6.0, 1.65)), (14.0, 12.5, 1.65), 21, 0.25, 118, True),
    'north':  (tuple(st(SW_W + ROAD_W + 1.4, 42.0, 1.65)), (14.0, 9.0, 1.65), 24, 0.26, 78, True),
    'aerial': ((-36.0, -74.0, 60.0), (-4.0, 10.0, 3.0), 30, 0.0, 212, False),
    'aerial2': ((62.0, -30.0, 46.0), (4.0, 12.0, 6.0), 28, 0.0, 135, False),
    'west':   ((-57.0, -1.5, 7.5), (-6.0, 13.0, 9.0), 22, 0.0, 232, False),
    'detail': (tuple(st(SW_W + 1.0, -4.0, 1.65)), (W, 13.5, 1.65), 40, 0.33, 118, True),
    'cars':   (tuple(st(SW_W + 2.5, 8.0, 1.5)), tuple(st(-3.0, 14.0, 0.8)), 35, 0.0, 118, False),
    'court':  ((-19.5, 11.8, 1.65), (6.0, 11.7, 1.65), 19, 0.27, 222, True),
}

def camera(view):
    loc, tgt, lens, shift, az, level = VIEWS[view]
    cam = bpy.data.cameras.new('cam'); cam.lens = lens; cam.shift_y = shift; cam.clip_end = 2000; cam.sensor_width = 36
    ob = bpy.data.objects.new('Kamera_' + view, cam); bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(tgt) - Vector(loc)
    if level: d.z = 0
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    return az

def render_settings():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; c = sc.cycles
    c.device = 'CPU'; c.samples = args.samples; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.02
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
    try: c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    except Exception: pass
    c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 4; c.transmission_bounces = 8; c.transparent_max_bounces = 32
    c.caustics_reflective = False; c.caustics_refractive = False; c.filter_width = 1.2
    sc.render.resolution_x, sc.render.resolution_y = args.res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.abspath(args.out)
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as e:
        print('view transform:', e)
    sc.view_settings.exposure = 0.0

# ----------------------------------------------------------------------------- build
def build():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    materials()
    main_block()
    ticari_block()
    west, east = site()
    if not args.no_context:
        context()
    place_cars(make_car(), west, east)
    if not args.no_trees:
        trees()
    az = camera(args.view)
    world(az)
    render_settings()

build()
if args.save:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save))
if not args.no_render:
    bpy.ops.render.render(write_still=True)
    print('RENDERED', args.out)
