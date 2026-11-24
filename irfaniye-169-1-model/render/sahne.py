"""İrfaniye 169 Ada 1 Parsel - Blender (Cycles) render sahnesi.

Kullanım:
    python sahne.py --kaydet sahne.blend                 # sahneyi kur, .blend kaydet
    python sahne.py --render kus_bakisi,avlu --cozunurluk 1920x1080 --ornek 160 --cikti ../gorseller/render

Gerekenler: `pip install bpy` (Blender 5.x Python modülü) ve `python indir.py` ile indirilen
Poly Haven (CC0) dokuları, modelleri ve HDRI'si (assets/ klasörü).
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'assets')
UNITS = json.load(open(os.path.join(HERE, '..', 'kaynak', 'units.json'), encoding='utf-8'))
RING = json.load(open(os.path.join(HERE, '..', 'kaynak', 'ring.json'), encoding='utf-8'))   # ring road + pool (kaynak/ring.py)

rng = random.Random(169)

# ---------------------------------------------------------------- plan data
FH, SL, BASE = 3.0, 0.18, 0.30
WH = FH - SL
S = 8.065
CX, CZ = 604 / S, 374 / S


def wx(x):
    return x / S - CX


def wy(y):  # plan y (down = south) -> Blender Y (north positive)
    return -(y / S - CZ)


def P(p):
    return (wx(p[0]), wy(p[1]))


BLOCKS = [
    dict(id='D', type='u31', x=212.3, y=189.3, park=False),
    dict(id='C', type='u31', x=384.8, y=189.3, park=False),
    dict(id='B', type='u31', x=700.1, y=189.3, park=True),
    dict(id='A', type='u31', x=872.6, y=189.3, park=True),
    dict(id='E', type='u21', x=156.7, y=445.4, park=False),
    dict(id='F', type='u21', x=291.0, y=445.4, park=True),
    dict(id='G', type='u21', x=425.3, y=445.4, park=True),
    dict(id='H', type='u21', x=604.1, y=445.4, park=True),
    dict(id='I', type='u21', x=738.4, y=445.4, park=True),
    dict(id='J', type='u21', x=872.6, y=445.4, park=True),
]
TYPE = {
    'u31': dict(balcony=(11.532, 13.532), core=(9.39, 11.984)),
    'u21': dict(balcony=(-1.994, 0.0), core=(7.091, 9.686)),
}
PARCEL = [(196.0, 143.7), (1072.0, 143.6), (1105.9, 183.4), (1044.4, 573.2), (1007.2, 604.2), (401.3, 587.4), (102.5, 587.5)]
FENCE = [tuple(RING['gate']['fence_south_end']), (1042.9, 572.2), (1006.6, 602.5), (401.3, 585.7), (104.4, 585.8), (197.3, 145.3), (1071.2, 145.2), (1104.2, 183.9), tuple(RING['gate']['fence_north_end'])]
GREEN = [
    [(197.3, 145.3), (620.6, 145.3), (620.6, 306.7), (612.6, 314.7), (161.6, 314.7)],
    [(636.8, 173.1), (1037, 173.1), (1061.4, 197.4), (1061.4, 290.5), (1037.3, 314.7), (644.9, 314.7), (636.8, 306.7)],
    [(158.2, 330.8), (210.4, 330.8), (210.4, 396.9), (144.2, 396.9)],
    [(238.6, 330.8), (300, 330.8), (307.2, 335.1), (333.6, 385.2), (326.5, 396.9), (238.6, 396.9)],
    [(331, 330.8), (462.7, 330.8), (470.6, 337.4), (480.5, 387.3), (472.6, 396.9), (357, 396.9), (349.9, 392.6), (323.8, 342.7)],
    [(491.9, 330.8), (598.9, 330.8), (606.4, 342), (586.2, 391.9), (578.8, 396.9), (501.2, 396.9), (493.3, 390.3), (484, 340.4)],
    [(632.5, 330.8), (777.4, 330.8), (785.4, 337.5), (794.2, 387.4), (786.2, 396.9), (612.2, 396.9), (604.8, 385.9), (625, 335.8)],
    [(806.4, 330.8), (939.2, 330.8), (947.2, 340.2), (939.2, 390.2), (931.3, 396.9), (814.9, 396.9), (806.9, 390.2), (798.5, 340.3)],
    [(968.3, 330.8), (1025.4, 330.8), (1033.2, 341.1), (1019, 391), (1011.2, 396.9), (960, 396.9), (952.1, 387.6), (960.4, 337.6)],
    [(140.9, 413.1), (1000.1, 413.1), (1024.3, 437.2), (1024.3, 537.3), (1000.1, 561.4), (342, 561.4), (318.6, 545.4), (318.6, 585.7), (104.4, 585.8)],
]


def prect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


PATHS = [
    prect(284, 282, 313, 314.7), prect(456.6, 282, 485.6, 314.7), prect(771.8, 282, 800.9, 314.7), prect(944.5, 282, 973.6, 314.7),
    prect(720.6, 173.1, 759.7, 190), prect(840.8, 173.1, 880, 190), prect(986, 173.1, 1030, 190),
    prect(210.4, 413.1, 238.6, 446), prect(344.6, 413.1, 372.8, 446), prect(478.9, 413.1, 507.1, 446),
    prect(657.7, 413.1, 685.9, 446), prect(792, 413.1, 820.2, 446), prect(926.3, 413.1, 954.5, 446),
    prect(574.3, 413.1, 590.5, 561.4),
    prect(418.4, 544, 463.6, 561.4), prect(731.5, 544, 776.6, 561.4), prect(865.8, 544, 910.9, 561.4),
]
TREES = [
    (579, 167, 1.1), (605, 167, 1.0),
    (173, 347, 1.0), (200, 353, 0.9), (196, 376, 1.0),
    (523, 363, 1.0), (546, 344, 1.15), (569, 376, 1.0),
    (723, 376, 1.0), (753, 350, 1.15), (779, 380, 1.0),
    (134, 540, 1.0), (128, 569, 0.9), (157, 566, 1.0),
]


def edge_x(y):  # east parcel edge (plan points)
    return 1105.9 - (y - 183.4) * 0.15779


# ---------------------------------------------------------------- materials
IMG = {}


def img(path, noncolor=False):
    key = (path, noncolor)
    if key not in IMG:
        im = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            im.colorspace_settings.name = 'Non-Color'
        IMG[key] = im
    return IMG[key]


def sock(coll, name, typ):
    for s_ in coll:
        if s_.name == name and s_.type == typ and getattr(s_, 'enabled', True):
            return s_
    raise KeyError(name)


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    return m, nt, bsdf


def pmat(name, color, rough=0.5, metal=0.0, **kw):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    for k, v in kw.items():
        b.inputs[k].default_value = v
    if kw.get('Alpha', 1) < 1:
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    return m


def tmat(name, tex, size, tint=(1, 1, 1), bump=0.6, rough_mul=1.0, uv=False, hue_var=0.0, color_override=None):
    """Image-textured PBR material. Object-space box projection (meters) unless uv=True."""
    m, nt, b = new_mat(name)
    N, L = nt.nodes, nt.links
    d = os.path.join(ASSETS, 'tex', tex)
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size, 1 / size, 1 / size)
    L.new(tc.outputs['UV' if uv else 'Object'], mp.inputs['Vector'])

    def tx(fn, nc):
        t = N.new('ShaderNodeTexImage')
        t.image = img(os.path.join(d, fn), nc)
        if not uv:
            t.projection = 'BOX'
            t.projection_blend = 0.3
        L.new(mp.outputs['Vector'], t.inputs['Vector'])
        return t
    diff = tx('Diffuse.jpg', False)
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    L.new(diff.outputs['Color'], sock(mix.inputs, 'A', 'RGBA'))
    sock(mix.inputs, 'B', 'RGBA').default_value = (*tint, 1)
    mix_out = sock(mix.outputs, 'Result', 'RGBA')
    if hue_var:
        oi = N.new('ShaderNodeObjectInfo')
        hsv = N.new('ShaderNodeHueSaturation')
        mr = N.new('ShaderNodeMapRange')
        sock(mr.inputs, 'To Min', 'VALUE').default_value = 1 - hue_var
        sock(mr.inputs, 'To Max', 'VALUE').default_value = 1 + hue_var
        L.new(oi.outputs['Random'], sock(mr.inputs, 'Value', 'VALUE'))
        L.new(sock(mr.outputs, 'Result', 'VALUE'), hsv.inputs['Value'])
        L.new(mix_out, hsv.inputs['Color'])
        L.new(hsv.outputs['Color'], b.inputs['Base Color'])
    else:
        L.new(mix_out, b.inputs['Base Color'])
    if os.path.exists(os.path.join(d, 'Rough.jpg')):
        r = tx('Rough.jpg', True)
        mm = N.new('ShaderNodeMath')
        mm.operation = 'MULTIPLY'
        mm.inputs[1].default_value = rough_mul
        L.new(r.outputs['Color'], mm.inputs[0])
        L.new(mm.outputs[0], b.inputs['Roughness'])
    if os.path.exists(os.path.join(d, 'nor_gl.jpg')) and bump > 0:
        n = tx('nor_gl.jpg', True)
        nm = N.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = bump
        L.new(n.outputs['Color'], nm.inputs['Color'])
        L.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m


def glass_mat(name, tint=(0.82, 0.9, 0.9), rough=0.0):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*tint, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.5
    return m


def emit_mat(name, color, strength):
    m, nt, b = new_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Emission Color'].default_value = (*color, 1)
    b.inputs['Emission Strength'].default_value = strength
    return m


def car_paint():
    m, nt, b = new_mat('arac_boya')
    N, L = nt.nodes, nt.links
    oi = N.new('ShaderNodeObjectInfo')
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    cols = [(0.82, 0.82, 0.8), (0.02, 0.022, 0.025), (0.35, 0.37, 0.39), (0.62, 0.63, 0.64), (0.25, 0.02, 0.02),
            (0.03, 0.08, 0.2), (0.9, 0.9, 0.88), (0.12, 0.13, 0.14), (0.45, 0.32, 0.2), (0.85, 0.85, 0.84)]
    els = ramp.color_ramp.elements
    els[0].color = (*cols[0], 1)
    els[1].position = 0.999
    els[1].color = (*cols[-1], 1)
    for i, c in enumerate(cols[1:-1], 1):
        e = els.new(i / len(cols))
        e.color = (*c, 1)
    L.new(oi.outputs['Random'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.55
    b.inputs['Roughness'].default_value = 0.28
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Coat Roughness'].default_value = 0.03
    return m


def curtain_mat():
    m, nt, b = new_mat('perde')
    b.inputs['Base Color'].default_value = (0.92, 0.9, 0.85, 1)
    b.inputs['Roughness'].default_value = 0.9
    b.inputs['Transmission Weight'].default_value = 0.35
    b.inputs['Subsurface Weight'].default_value = 0.0
    return m


def build_materials():
    M = {}
    M['siva'] = tmat('siva_beyaz', 'plastered_wall_02', 2.5, tint=(1.0, 0.985, 0.95), bump=0.35)
    M['seramik'] = tmat('kompozit_kaplama', 'exterior_wall_cladding_03', 2.0, tint=(0.95, 0.86, 0.74), bump=0.9)
    M['tas'] = tmat('tas_subasman', 'granite_tile_04', 1.6, tint=(0.55, 0.55, 0.56), bump=0.6)
    M['silme'] = pmat('silme', (0.86, 0.85, 0.82), 0.6)
    M['ic_duvar'] = pmat('ic_duvar', (0.88, 0.87, 0.84), 0.9)
    M['doseme'] = pmat('doseme_beton', (0.83, 0.82, 0.8), 0.85)
    M['parke'] = pmat('ic_parke', (0.42, 0.28, 0.17), 0.45)
    M['dograma'] = pmat('dograma_antrasit', (0.035, 0.038, 0.042), 0.35, 0.6)
    M['cam'] = glass_mat('cam')
    M['korkuluk_cam'] = glass_mat('korkuluk_cam', (0.78, 0.88, 0.86), 0.02)
    M['celik'] = pmat('paslanmaz', (0.78, 0.78, 0.77), 0.22, 1.0)
    M['denizlik'] = pmat('denizlik_mermer', (0.9, 0.89, 0.86), 0.25)
    M['balkon_zemin'] = tmat('balkon_zemin', 'granite_tile_04', 1.2, tint=(0.95, 0.93, 0.9), bump=0.3)
    M['kapi'] = pmat('kapi_ceviz', (0.2, 0.11, 0.06), 0.4)
    M['merdiven'] = pmat('merdiven_mermer', (0.8, 0.79, 0.76), 0.3)
    M['kiremit'] = tmat('kiremit', 'clay_roof_tiles_02', 2.0, tint=(1.0, 0.9, 0.85), bump=1.0, uv=True, hue_var=0.08)
    M['mahya'] = pmat('mahya', (0.36, 0.12, 0.06), 0.7)
    M['sacak'] = pmat('sacak_alti', (0.92, 0.91, 0.88), 0.8)
    M['oluk'] = pmat('oluk', (0.09, 0.09, 0.1), 0.4, 0.7)
    M['beton'] = pmat('beton', (0.6, 0.59, 0.57), 0.85)
    M['otopark_zemin'] = tmat('otopark_zemin', 'concrete_tile_facade', 3.0, tint=(1.6, 1.6, 1.6), bump=0.2)
    M['cizgi'] = pmat('yol_cizgi', (0.85, 0.85, 0.82), 0.6)
    M['led'] = emit_mat('led', (1.0, 0.95, 0.85), 6.0)
    M['parke_tasi'] = tmat('parke_tasi', 'concrete_pavers_02', 2.4, tint=(1.05, 1.0, 0.95), bump=0.8)
    M['kaldirim'] = tmat('kaldirim', 'rectangular_paving', 2.0, tint=(1.0, 0.98, 0.95), bump=0.8)
    M['bordur'] = tmat('bordur', 'granite_tile_04', 1.0, tint=(0.85, 0.85, 0.85), bump=0.3)
    M['asfalt'] = tmat('asfalt', 'asphalt_02', 5.0, tint=(0.75, 0.75, 0.75), bump=0.5)
    M['cim'] = tmat('cim_zemin', 'leafy_grass', 2.5, tint=(0.55, 0.8, 0.4), bump=0.6)
    M['arazi'] = tmat('arazi', 'leafy_grass', 4.0, tint=(0.42, 0.55, 0.3), bump=0.4)
    M['duvar_tas'] = tmat('cevre_duvar', 'granite_tile_04', 1.4, tint=(0.85, 0.83, 0.8), bump=0.4)
    M['beyaz'] = pmat('beyaz_boya', (0.92, 0.92, 0.9), 0.4)
    M['kirmizi'] = pmat('kirmizi_boya', (0.6, 0.03, 0.03), 0.4)
    M['klima'] = pmat('klima', (0.9, 0.9, 0.88), 0.35)
    M['koyu'] = pmat('koyu_plastik', (0.03, 0.03, 0.03), 0.6)
    M['ahsap'] = pmat('ahsap', (0.38, 0.24, 0.13), 0.55)
    M['saksi'] = pmat('saksi', (0.45, 0.2, 0.12), 0.7)
    M['perde'] = curtain_mat()
    M['gunes_panel'] = pmat('gunes_paneli', (0.02, 0.03, 0.06), 0.15, 0.3)
    M['lastik'] = pmat('lastik', (0.02, 0.02, 0.02), 0.85)
    M['jant'] = pmat('jant', (0.7, 0.7, 0.72), 0.25, 1.0)
    M['arac_cam'] = pmat('arac_cam', (0.01, 0.012, 0.015), 0.04)
    M['far'] = emit_mat('far', (1.0, 0.98, 0.92), 1.5)
    M['stop'] = emit_mat('stop', (0.8, 0.02, 0.01), 1.0)
    M['cim_yaprak'] = grass_blade_mat()
    M['lamba'] = emit_mat('lamba', (1.0, 0.92, 0.78), 3.0)
    for i, col in enumerate(((0.6, 0.57, 0.52), (0.66, 0.6, 0.5), (0.55, 0.55, 0.54))):
        M[f'kont_cephe{i}'] = context_facade(f'cevre_bina{i}', col)
    M['tabela'] = pmat('tabela', (0.75, 0.74, 0.72), 0.3, 1.0)
    M['su'] = water_mat()
    M['havuz_fayans'] = pool_tile_mat()
    M['havuz_lamba'] = emit_mat('havuz_lamba', (0.75, 0.9, 1.0), 4.0)
    return M


def water_mat():
    m, nt, b = new_mat('su')
    N, L = nt.nodes, nt.links
    b.inputs['Base Color'].default_value = (0.62, 0.88, 0.92, 1)
    b.inputs['Roughness'].default_value = 0.0
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.333
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.6
    nz.inputs['Detail'].default_value = 3.0
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.08
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    L.new(nz.outputs['Fac'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def pool_tile_mat():
    """Blue glass mosaic: (x, y) mapping on the floor, (x + y, z) on the walls."""
    m, nt, b = new_mat('havuz_mozaik')
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    add = N.new('ShaderNodeMath')
    add.operation = 'ADD'
    L.new(sep.outputs['X'], add.inputs[0])
    L.new(sep.outputs['Y'], add.inputs[1])
    zoff = N.new('ShaderNodeMath')
    zoff.operation = 'ADD'
    zoff.inputs[1].default_value = 0.013
    L.new(sep.outputs['Z'], zoff.inputs[0])
    wall_v = N.new('ShaderNodeCombineXYZ')
    L.new(add.outputs[0], wall_v.inputs['X'])
    L.new(zoff.outputs[0], wall_v.inputs['Y'])
    floor_v = N.new('ShaderNodeCombineXYZ')
    L.new(sep.outputs['X'], floor_v.inputs['X'])
    L.new(sep.outputs['Y'], floor_v.inputs['Y'])

    def brick(vec):
        br = N.new('ShaderNodeTexBrick')
        br.offset = 0.0
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 0.05
        br.inputs['Row Height'].default_value = 0.05
        br.inputs['Mortar Size'].default_value = 0.004
        br.inputs['Color1'].default_value = (0.08, 0.42, 0.68, 1)
        br.inputs['Color2'].default_value = (0.14, 0.52, 0.76, 1)
        br.inputs['Mortar'].default_value = (0.7, 0.8, 0.84, 1)
        L.new(vec.outputs[0], br.inputs['Vector'])
        return br
    bw, bf = brick(wall_v), brick(floor_v)
    geo = N.new('ShaderNodeNewGeometry')
    sn = N.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Normal'], sn.inputs[0])
    ab = N.new('ShaderNodeMath')
    ab.operation = 'ABSOLUTE'
    L.new(sn.outputs['Z'], ab.inputs[0])
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    L.new(ab.outputs[0], sock(mix.inputs, 'Factor', 'VALUE'))
    L.new(bw.outputs['Color'], sock(mix.inputs, 'A', 'RGBA'))
    L.new(bf.outputs['Color'], sock(mix.inputs, 'B', 'RGBA'))
    L.new(sock(mix.outputs, 'Result', 'RGBA'), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.12
    return m


def context_facade(name, wall):
    """Distant neighbour buildings: plaster with a brick-pattern window grid."""
    m, nt, b = new_mat(name)
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    br = N.new('ShaderNodeTexBrick')
    br.offset = 0.0
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.9
    br.inputs['Brick Width'].default_value = 2.2
    br.inputs['Row Height'].default_value = 3.0
    br.inputs['Color1'].default_value = (0.08, 0.1, 0.12, 1)
    br.inputs['Color2'].default_value = (0.1, 0.12, 0.14, 1)
    br.inputs['Mortar'].default_value = (*wall, 1)
    sep = N.new('ShaderNodeSeparateXYZ')
    comb = N.new('ShaderNodeCombineXYZ')
    add = N.new('ShaderNodeMath')
    add.operation = 'ADD'
    L.new(tc.outputs['Object'], sep.inputs[0])
    L.new(sep.outputs['X'], add.inputs[0])
    L.new(sep.outputs['Y'], add.inputs[1])
    L.new(add.outputs[0], comb.inputs['X'])
    L.new(sep.outputs['Z'], comb.inputs['Y'])
    L.new(comb.outputs[0], br.inputs['Vector'])
    L.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    return m


# ---------------------------------------------------------------- mesh builder
class MB:
    def __init__(self):
        self.v, self.f, self.uv = [], [], []

    def face(self, pts, uvs=None):
        i = len(self.v)
        self.v.extend(pts)
        self.f.append(list(range(i, i + len(pts))))
        self.uv.append(uvs)

    def box(self, x0, y0, z0, x1, y1, z1):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return
        i = len(self.v)
        self.v.extend([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.f.append([i + k for k in f])
            self.uv.append(None)

    def obox(self, ax, ay, bx, by, t, z0, z1):
        """Box along segment a->b (XY), thickness t, z range."""
        dx, dy = bx - ax, by - ay
        ln = math.hypot(dx, dy)
        if ln < 1e-4:
            return
        nx, ny = -dy / ln * t / 2, dx / ln * t / 2
        q = [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]
        self.prism(q, z0, z1)

    def poly(self, pj, z0, z1, top=True, sides=True):
        """Extruded plan polygon with holes ({'ext': [...], 'holes': [[...]]} in plan points)."""
        from mathutils.geometry import tessellate_polygon
        loops = [[P(p) for p in pj['ext']]] + [[P(p) for p in h] for h in pj['holes']]
        if top:
            tris = tessellate_polygon([[Vector((x, y, 0)) for x, y in lp] for lp in loops])
            flat = [pt for lp in loops for pt in lp]
            i = len(self.v)
            self.v.extend([(x, y, z1) for x, y in flat])
            for t in tris:
                a, b, c = (flat[k] for k in t)
                cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                self.f.append([i + t[0], i + t[1], i + t[2]] if cr > 0 else [i + t[0], i + t[2], i + t[1]])
                self.uv.append(None)
        if sides:
            for lp in loops:
                n = len(lp)
                i = len(self.v)
                self.v.extend([(x, y, z0) for x, y in lp] + [(x, y, z1) for x, y in lp])
                for k in range(n):
                    k2 = (k + 1) % n
                    self.f.append([i + k, i + k2, i + n + k2, i + n + k])
                    self.uv.append(None)

    def prism(self, pts, z0, z1, top=True, sides=True, bottom=False):
        a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        if a < 0:
            pts = pts[::-1]
        n = len(pts)
        i = len(self.v)
        self.v.extend([(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts])
        if top:
            self.f.append([i + n + k for k in range(n)])
            self.uv.append(None)
        if bottom:
            self.f.append([i + k for k in range(n)][::-1])
            self.uv.append(None)
        if sides:
            for k in range(n):
                k2 = (k + 1) % n
                self.f.append([i + k, i + k2, i + n + k2, i + n + k])
                self.uv.append(None)

    def cyl(self, a, b, r, seg=10):
        a, b = Vector(a), Vector(b)
        ax = (b - a).normalized()
        up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
        u = ax.cross(up).normalized()
        w = ax.cross(u).normalized()
        i = len(self.v)
        for p in (a, b):
            for k in range(seg):
                t = 2 * math.pi * k / seg
                self.v.append(tuple(p + (u * math.cos(t) + w * math.sin(t)) * r))
        for k in range(seg):
            k2 = (k + 1) % seg
            self.f.append([i + k, i + k2, i + seg + k2, i + seg + k])
            self.uv.append(None)
        self.f.append([i + k for k in range(seg)][::-1])
        self.uv.append(None)
        self.f.append([i + seg + k for k in range(seg)])
        self.uv.append(None)

    def to_object(self, name, mat, coll, smooth=False):
        if not self.f:
            return None
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        if any(u is not None for u in self.uv):
            lay = me.uv_layers.new(name='UVMap')
            li = 0
            for poly, uvs in zip(me.polygons, self.uv):
                for k in range(poly.loop_total):
                    lay.data[poly.loop_start + k].uv = uvs[k] if uvs else (0, 0)
        me.validate()
        if smooth:
            me.shade_smooth()
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


BUILD = {}


def mb(key):
    if key not in BUILD:
        BUILD[key] = MB()
    return BUILD[key]


# ---------------------------------------------------------------- building helpers
class Block:
    def __init__(self, b):
        self.b = b
        self.T = UNITS[b['type']]
        self.TT = TYPE[b['type']]
        self.ox, self.oz = b['x'] / S - CX, b['y'] / S - CZ
        self.W = self.T['R']['bbox'][2]
        self.D = self.T['L']['bbox'][3]

    def X(self, lx):
        return self.ox + lx

    def Y(self, lz):
        return -(self.oz + lz)

    def box(self, mat, x0, z0, x1, z1, y0, y1):
        """box in block-local plan coords (x, z south) and absolute height."""
        mb(mat).box(self.X(x0), self.Y(z0), y0, self.X(x1), self.Y(z1), y1)


UNIT_BOXES = []


def unit_boxes():
    for b in BLOCKS:
        T = UNITS[b['type']]
        for side in 'LR':
            x0, z0, x1, z1 = T[side]['bbox']
            ox, oz = b['x'] / S - CX, b['y'] / S - CZ
            UNIT_BOXES.append(dict(b=b['id'], side=side, x0=ox + x0, z0=oz + z0, x1=ox + x1, z1=oz + z1))


def touching(me, edge):
    for o in UNIT_BOXES:
        if o is me:
            continue
        if min(o['z1'], me['z1']) - max(o['z0'], me['z0']) <= 1:
            continue
        if edge == 'W' and abs(o['x1'] - me['x0']) < 0.35:
            return True
        if edge == 'E' and abs(o['x0'] - me['x1']) < 0.35:
            return True
    return False


class Edge:
    """Exterior wall edge of a unit: converts (along, depth-inward) to block plan coords."""

    def __init__(self, side, bbox):
        self.side = side
        self.ux0, self.uz0, self.ux1, self.uz1 = bbox

    def rect(self, a0, a1, d0, d1):
        s = self.side
        if s == 'N':
            return a0, self.uz0 + d0, a1, self.uz0 + d1
        if s == 'S':
            return a0, self.uz1 - d1, a1, self.uz1 - d0
        if s == 'W':
            return self.ux0 + d0, a0, self.ux0 + d1, a1
        return self.ux1 - d1, a0, self.ux1 - d0, a1


def window_assembly(B, E, a, b, y0, sill, head, kind, curtain):
    """Frame, sashes, glass, sill and curtains in an opening from along a..b."""
    def bx(mat, a0, a1, d0, d1, h0, h1):
        x0, z0, x1, z1 = E.rect(a0, a1, d0, d1)
        B.box(mat, x0, z0, x1, z1, y0 + h0, y0 + h1)
    f = 0.055
    fd0, fd1 = 0.045, 0.115
    # outer frame
    bx('dograma', a, b, fd0, fd1, sill, sill + f)
    bx('dograma', a, b, fd0, fd1, head - f, head)
    bx('dograma', a, a + f, fd0, fd1, sill, head)
    bx('dograma', b - f, b, fd0, fd1, sill, head)
    w = b - a
    if kind == 'door':
        # two sliding panels: each with its own frame, glass between
        mid = a + w / 2
        for (p0, p1, d0, d1) in ((a + f, mid + 0.03, 0.05, 0.08), (mid - 0.03, b - f, 0.08, 0.11)):
            bx('dograma', p0, p1, d0, d1, sill + f, sill + f + 0.07)
            bx('dograma', p0, p1, d0, d1, head - f - 0.05, head - f)
            bx('dograma', p0, p0 + 0.05, d0, d1, sill + f, head - f)
            bx('dograma', p1 - 0.05, p1, d0, d1, sill + f, head - f)
            bx('cam', p0 + 0.05, p1 - 0.05, d0 + 0.012, d0 + 0.02, sill + f + 0.07, head - f - 0.05)
    else:
        n = max(1, round(w / 0.75))
        n = min(n, 3)
        edges = [a + f + (w - 2 * f) * i / n for i in range(n + 1)]
        for i in range(1, n):
            bx('dograma', edges[i] - 0.03, edges[i] + 0.03, fd0, fd1, sill, head)
        tall = head - sill > 1.7
        if tall:  # fixed lower light + opening upper sash split
            bx('dograma', a, b, fd0, fd1, sill + 0.55, sill + 0.6)
        for i in range(n):
            bx('cam', edges[i] + 0.03, edges[i + 1] - 0.03, 0.075, 0.085, sill + f, head - f)
        # exterior marble sill and inner sill board
        bx('denizlik', a - 0.04, b + 0.04, -0.05, 0.06, sill - 0.04, sill)
        bx('denizlik', a, b, 0.115, 0.2, sill - 0.03, sill)
    if curtain:
        mode = curtain
        h0 = 0.04 if kind == 'door' else max(0.04, sill - 0.25)
        if mode == 'sheer':
            bx('perde', a + 0.02, b - 0.02, 0.26, 0.275, h0, head + 0.12)
        else:
            cw = min(0.55, w * 0.3)
            bx('perde', a - 0.1, a - 0.1 + cw, 0.24, 0.27, h0, head + 0.12)
            bx('perde', b + 0.1 - cw, b + 0.1, 0.24, 0.27, h0, head + 0.12)


def railing(mat_g, pts_open, z):
    """Glass balustrade with steel posts and handrail along open edges (Blender XY coords)."""
    for (ax, ay), (bx_, by) in pts_open:
        ln = math.hypot(bx_ - ax, by - ay)
        n = max(1, math.ceil(ln / 1.3))
        for i in range(n + 1):
            t = i / n
            px, py = ax + (bx_ - ax) * t, ay + (by - ay) * t
            mb('celik').box(px - 0.022, py - 0.022, z, px + 0.022, py + 0.022, z + 1.04)
        for i in range(n):
            t0, t1 = (i + 0.02) / n, (i + 0.98) / n
            mb('korkuluk_cam').obox(ax + (bx_ - ax) * t0, ay + (by - ay) * t0, ax + (bx_ - ax) * t1, ay + (by - ay) * t1, 0.012, z + 0.1, z + 0.98)
        mb('celik').obox(ax, ay, bx_, by, 0.055, z + 0.99, z + 1.05)


def hip_roof(x0, y0, x1, y1, z0, pitch):
    """Hip roof over Blender-XY rect; returns ridge/hip lines and height function."""
    m = mb('kiremit')
    Lx, Ly = x1 - x0, y1 - y0
    k = math.sqrt(1 + pitch * pitch)
    if Lx >= Ly:
        h = Ly / 2 * pitch
        ym = (y0 + y1) / 2
        r0, r1 = (x0 + Ly / 2, ym, z0 + h), (x1 - Ly / 2, ym, z0 + h)
        A, B_, C, D = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
        faces = [([A, B_, r1, r0], 'S'), ([C, D, r0, r1], 'N'), ([B_, C, r1], 'E'), ([D, A, r0], 'W')]
    else:
        h = Lx / 2 * pitch
        xm = (x0 + x1) / 2
        r0, r1 = (xm, y0 + Lx / 2, z0 + h), (xm, y1 - Lx / 2, z0 + h)
        A, B_, C, D = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
        faces = [([A, B_, r0], 'S'), ([B_, C, r1, r0], 'E'), ([C, D, r1], 'N'), ([D, A, r0, r1], 'W')]
    for pts, side in faces:
        uvs = []
        for (px, py, pz) in pts:
            if side == 'S':
                uvs.append((px, (py - y0) * k))
            elif side == 'N':
                uvs.append((-px, (y1 - py) * k))
            elif side == 'E':
                uvs.append((py, (x1 - px) * k))
            else:
                uvs.append((-py, (px - x0) * k))
        m.face(pts, uvs)
    hips = [(A, r0), (D, r0), (B_, r1), (C, r1)] if Lx >= Ly else [(A, r0), (B_, r0), (C, r1), (D, r1)]
    return (r0, r1), hips, h


# ---------------------------------------------------------------- props (collections)
def hidden_collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    lc = bpy.context.view_layer.layer_collection.children[name]
    lc.exclude = True
    return c


def instance(coll, loc, rot=0.0, scale=1.0, parent_coll=None, name=None):
    e = bpy.data.objects.new(name or coll.name, None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = coll
    e.location = loc
    e.rotation_euler = (0, 0, rot)
    e.scale = (scale, scale, scale)
    (parent_coll or bpy.context.scene.collection).objects.link(e)
    return e


def import_gltf(name, target):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, 'models', name, name + '.gltf'))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        target.objects.link(o)
    return new


def split_variants(name, objs):
    """Poly Haven variant packs: one object per variant laid out in a row. Return a collection per variant."""
    cols = []
    for i, o in enumerate(o for o in objs if o.type == 'MESH'):
        c = hidden_collection(f'{name}_{i}')
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        c.objects.link(o)
        bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
        cx = sum(p.x for p in bb) / 8
        cy = sum(p.y for p in bb) / 8
        zmin = min(p.z for p in bb)
        o.location -= Vector((cx, cy, zmin))
        cols.append(c)
    return cols


CAR_COLORS = {
    'beyaz': (0.8, 0.8, 0.78), 'siyah': (0.015, 0.016, 0.018), 'gumus': (0.55, 0.56, 0.57), 'fume': (0.16, 0.17, 0.18),
    'lacivert': (0.02, 0.05, 0.14), 'bordo': (0.22, 0.015, 0.02), 'krem': (0.62, 0.55, 0.45),
}


def paint_mat(name, color):
    m, nt, b = new_mat('boya_' + name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = 0.5 if name not in ('beyaz',) else 0.1
    b.inputs['Roughness'].default_value = 0.3
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Coat Roughness'].default_value = 0.03
    return m


def make_car(variant, M, paint, tag):
    """Procedural car: bevelled body, tapered greenhouse, wheels, lights. Front towards +X."""
    c = hidden_collection(f'arac_{variant}_{tag}')
    if variant == 'sedan':
        body = [(-2.32, 0.3), (2.3, 0.3), (2.36, 0.6), (2.24, 0.8), (1.2, 0.9), (-1.55, 0.95), (-2.24, 0.97), (-2.36, 0.64)]
        green = [(1.15, 0.89), (0.4, 1.38), (-0.85, 1.4), (-1.6, 0.94)]
        L_, Wd = 4.65, 1.8
    elif variant == 'hatch':
        body = [(-1.98, 0.3), (2.0, 0.3), (2.05, 0.6), (1.92, 0.8), (1.0, 0.9), (-1.88, 0.97), (-2.03, 0.64)]
        green = [(0.98, 0.89), (0.3, 1.4), (-1.6, 1.43), (-1.93, 0.96)]
        L_, Wd = 4.0, 1.76
    else:
        body = [(-2.3, 0.4), (2.28, 0.4), (2.33, 0.74), (2.2, 0.98), (1.25, 1.08), (-2.2, 1.12), (-2.34, 0.78)]
        green = [(1.22, 1.07), (0.55, 1.66), (-1.95, 1.7), (-2.22, 1.1)]
        L_, Wd = 4.6, 1.86

    def loft(profile, w_of_z, mat, name, bevel, seg=4):
        m = MB()
        n = len(profile)
        for sgn in (-1, 1):
            for (x, z) in profile:
                m.v.append((x, sgn * w_of_z(z) / 2, z))
        m.f.append(list(range(n)))
        m.uv.append(None)
        m.f.append([n + k for k in range(n)][::-1])
        m.uv.append(None)
        for k in range(n):
            k2 = (k + 1) % n
            m.f.append([k2, k, n + k, n + k2])
            m.uv.append(None)
        ob = m.to_object(name, mat, c)
        bev = ob.modifiers.new('bevel', 'BEVEL')
        bev.width = bevel
        bev.segments = seg
        bev.limit_method = 'ANGLE'
        ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
        ob.data.shade_smooth()
        return ob
    zb = min(z for _, z in green)
    zt = max(z for _, z in green)
    loft(body, lambda z: Wd, paint, 'govde', 0.1)
    loft(green, lambda z: (Wd - 0.12) - (z - zb) / (zt - zb) * 0.42, M['arac_cam'], 'kabin', 0.07, 3)
    # roof skin and pillars (paint) over the glass
    top = sorted(green, key=lambda p: -p[1])[:2]
    xs = sorted(p[0] for p in top)
    m = MB()
    m.box(xs[0] - 0.06, -(Wd - 0.56) / 2, zt - 0.02, xs[1] + 0.06, (Wd - 0.56) / 2, zt + 0.025)
    ob = m.to_object('tavan', paint, c)
    ob.modifiers.new('bevel', 'BEVEL').width = 0.02
    # black trim along the beltline and bumpers
    m = MB()
    fx = max(p[0] for p in body)
    bx_ = min(p[0] for p in body)
    zb0 = body[0][1]
    m.box(bx_ - 0.02, -Wd / 2 - 0.005, zb0, fx + 0.02, Wd / 2 + 0.005, zb0 + 0.1)
    m.to_object('tampon', M['koyu'], c)
    wz = 0.34 if variant != 'suv' else 0.38
    wr = 0.33 if variant != 'suv' else 0.37
    for sx in (L_ / 2 - 0.82, -L_ / 2 + 0.85):
        for sy in (-1, 1):
            t = MB()
            t.cyl((sx, sy * (Wd / 2 - 0.2), wz), (sx, sy * (Wd / 2 + 0.005), wz), wr, 28)
            t.to_object('lastik', M['lastik'], c, smooth=True)
            r = MB()
            r.cyl((sx, sy * (Wd / 2 - 0.01), wz), (sx, sy * (Wd / 2 + 0.012), wz), wr * 0.6, 20)
            r.to_object('jant', M['jant'], c, smooth=True)
            # dark wheel well
            ww = MB()
            ww.cyl((sx, sy * (Wd / 2 - 0.25), wz), (sx, sy * (Wd / 2 + 0.002), wz), wr + 0.04, 20)
            ww.to_object('camurluk', M['koyu'], c)
    zl = body[2][1] + 0.06
    for sy in (-1, 1):
        mb_ = MB()
        mb_.box(fx - 0.04, sy * (Wd / 2 - 0.2) - 0.18, zl - 0.03, fx + 0.012, sy * (Wd / 2 - 0.2) + 0.18, zl + 0.05)
        mb_.to_object('far', M['far'], c)
        mb_ = MB()
        mb_.box(bx_ - 0.012, sy * (Wd / 2 - 0.15) - 0.22, zl + 0.06, bx_ + 0.04, sy * (Wd / 2 - 0.15) + 0.22, zl + 0.12)
        mb_.to_object('stop', M['stop'], c)
    return c


def make_grass_tufts(M, n_var=5):
    cols = []
    r = random.Random(7)
    for v in range(n_var):
        c = hidden_collection(f'cim_tutam_{v}')
        m = MB()
        for k in range(16):
            bx, by = r.uniform(-0.07, 0.07), r.uniform(-0.07, 0.07)
            ang = r.uniform(0, math.pi)
            w = r.uniform(0.006, 0.011)
            h = r.uniform(0.1, 0.2)
            lean = r.uniform(0.02, 0.07)
            la = r.uniform(0, 2 * math.pi)
            px, py = math.cos(ang) * w, math.sin(ang) * w
            mx, my = bx + math.cos(la) * lean * 0.4, by + math.sin(la) * lean * 0.4
            tx, ty = bx + math.cos(la) * lean, by + math.sin(la) * lean
            m.face([(bx - px, by - py, 0), (bx + px, by + py, 0), (mx + px * 0.6, my + py * 0.6, h * 0.55), (mx - px * 0.6, my - py * 0.6, h * 0.55)])
            m.face([(mx - px * 0.6, my - py * 0.6, h * 0.55), (mx + px * 0.6, my + py * 0.6, h * 0.55), (tx, ty, h)])
        m.to_object('tutam', M['cim_yaprak'], c)
        cols.append(c)
    return cols


def grass_blade_mat():
    m, nt, b = new_mat('cim_yaprak')
    N, L = nt.nodes, nt.links
    oi = N.new('ShaderNodeObjectInfo')
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.05, 0.12, 0.02, 1)
    ramp.color_ramp.elements[1].color = (0.2, 0.3, 0.06, 1)
    e = ramp.color_ramp.elements.new(0.5)
    e.color = (0.09, 0.2, 0.03, 1)
    L.new(oi.outputs['Random'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Subsurface Weight'].default_value = 0.0
    b.inputs['Transmission Weight'].default_value = 0.15
    return m


def context_building(x0, y0, x1, y1, floors, var=0):
    """Neighbouring apartment block (Blender XY rect) with window grid facade and hip roof."""
    h = floors * 3.0 + 0.4
    mb(f'kont_cephe{var}').box(x0, y0, 0, x1, y1, h)
    mb('tas').box(x0 - 0.05, y0 - 0.05, 0, x1 + 0.05, y1 + 0.05, 0.8)
    for k in range(1, floors):
        mb('silme').box(x0 - 0.06, y0 - 0.06, k * 3.0 + 0.2, x1 + 0.06, y1 + 0.06, k * 3.0 + 0.45)
    oh = 0.5
    if (int(abs(x0 * 7 + y1 * 3)) % 3) == 0:   # flat roof with parapet
        mb('silme').box(x0 - 0.1, y0 - 0.1, h, x1 + 0.1, y1 + 0.1, h + 0.9)
    else:
        mb('sacak').box(x0 - oh, y0 - oh, h - 0.15, x1 + oh, y1 + oh, h)
        hip_roof(x0 - oh, y0 - oh, x1 + oh, y1 + oh, h, 0.33)


def make_ac(M):
    c = hidden_collection('klima')
    m = MB()
    m.box(-0.4, -0.14, 0, 0.4, 0.14, 0.55)
    m.to_object('klima_govde', M['klima'], c)
    m = MB()
    m.cyl((0.12, -0.141, 0.28), (0.12, -0.15, 0.28), 0.19, 20)
    m.to_object('klima_fan', M['koyu'], c)
    m = MB()
    for (x0, x1) in ((-0.36, -0.3), (0.3, 0.36)):
        m.box(x0, -0.14, -0.05, x1, 0.14, 0.0)
    m.to_object('klima_ayak', M['koyu'], c)
    return c


def make_table_set(M):
    c = hidden_collection('balkon_takim')
    m = MB()
    m.cyl((0, 0, 0.0), (0, 0, 0.72), 0.025, 8)
    m.cyl((0, 0, 0.72), (0, 0, 0.74), 0.35, 24)
    m.to_object('masa', M['beyaz'], c)
    m = MB()
    for sx in (-0.6, 0.6):
        m.box(sx - 0.22, -0.22, 0.42, sx + 0.22, 0.22, 0.46)
        bxk = sx + (0.2 if sx > 0 else -0.2)
        m.box(bxk - 0.02, -0.22, 0.46, bxk + 0.02, 0.22, 0.9)
        for dx in (-0.19, 0.19):
            for dy in (-0.19, 0.19):
                m.box(sx + dx - 0.015, dy - 0.015, 0, sx + dx + 0.015, dy + 0.015, 0.42)
    m.to_object('sandalye', M['ahsap'], c)
    return c


def make_lamp(M):
    c = hidden_collection('aydinlatma')
    m = MB()
    m.cyl((0, 0, 0), (0, 0, 4.2), 0.06, 12)
    m.box(-0.12, -0.12, 0, 0.12, 0.12, 0.35)
    m.to_object('direk', M['dograma'], c, smooth=True)
    m = MB()
    m.cyl((0, 0, 4.2), (0, 0, 4.3), 0.3, 24)
    m.to_object('armatur', M['dograma'], c, smooth=True)
    m = MB()
    m.cyl((0, 0, 4.18), (0, 0, 4.2), 0.26, 24)
    m.to_object('led', M['lamba'], c)
    return c


def make_bollard(M):
    c = hidden_collection('bolar')
    m = MB()
    m.cyl((0, 0, 0), (0, 0, 0.8), 0.08, 16)
    m.to_object('bolar', M['dograma'], c, smooth=True)
    m = MB()
    m.cyl((0, 0, 0.62), (0, 0, 0.7), 0.081, 16)
    m.to_object('bolar_isik', M['lamba'], c)
    return c


def make_bench(M):
    c = hidden_collection('bank')
    m = MB()
    for sx in (-0.7, 0.7):
        m.box(sx - 0.12, -0.25, 0, sx + 0.12, 0.25, 0.4)
    m.to_object('bank_ayak', M['beton'], c)
    m = MB()
    for i in range(5):
        y = -0.24 + i * 0.1
        m.box(-0.95, y, 0.4, 0.95, y + 0.08, 0.45)
    for i in range(3):
        z = 0.55 + i * 0.13
        m.box(-0.95, 0.22, z, 0.95, 0.27, z + 0.09)
    m.to_object('bank_ahsap', M['ahsap'], c)
    return c


def make_lounger(M):
    c = hidden_collection('sezlong')
    m = MB()
    for sx in (-0.3, 0.3):
        m.box(-0.95, sx - 0.02, 0.0, 0.95, sx + 0.02, 0.32)
    m.to_object('sezlong_kasa', M['beyaz'], c)
    m = MB()
    m.box(-0.95, -0.31, 0.3, 0.35, 0.31, 0.38)
    m.face([(0.35, -0.31, 0.38), (0.35, 0.31, 0.38), (0.95, 0.31, 0.85), (0.95, -0.31, 0.85)])
    m.face([(0.35, 0.31, 0.3), (0.35, -0.31, 0.3), (0.95, -0.31, 0.77), (0.95, 0.31, 0.77)])
    m.to_object('sezlong_minder', M['klima'], c)
    return c


def make_umbrella(M):
    c = hidden_collection('semsiye')
    m = MB()
    m.cyl((0, 0, 0), (0, 0, 2.45), 0.03, 10)
    m.cyl((0, 0, 0), (0, 0, 0.08), 0.28, 16)
    m.to_object('semsiye_direk', M['dograma'], c, smooth=True)
    m = MB()
    n, r, z0, z1 = 16, 1.5, 2.05, 2.5
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        m.face([(r * math.cos(a0), r * math.sin(a0), z0), (r * math.cos(a1), r * math.sin(a1), z0), (0, 0, z1)])
    m.to_object('semsiye_kumas', M['perde'], c)
    return c


def make_pot(M, plant_cols):
    c = hidden_collection('saksi')
    m = MB()
    m.cyl((0, 0, 0), (0, 0, 0.42), 0.2, 16)
    m.to_object('saksi', M['saksi'], c, smooth=True)
    e = instance(plant_cols[0], (0, 0, 0.38), 0, 1.3, c)
    return c


# ---------------------------------------------------------------- build
def build_block(B, M, props):
    b = B.b
    T, TT = B.T, B.TT
    D, W = B.D, B.W
    bz0, bz1 = TT['balcony']
    cx0, cx1 = TT['core']
    bal_side = 'S' if b['type'] == 'u31' else 'N'
    for lvl in range(3):
        e = BASE + lvl * FH
        parking = b['park'] and lvl == 0
        for side in 'LR':
            U = T[side]
            ux0, uz0, ux1, uz1 = U['bbox']
            me = next(u for u in UNIT_BOXES if u['b'] == b['id'] and u['side'] == side)
            end_side = 'W' if side == 'L' else 'E'
            core_side = 'E' if side == 'L' else 'W'
            end_free = not touching(me, end_side)
            if parking:
                B.box('otopark_zemin', ux0, uz0, ux1, uz1, 0.0, 0.12)
                # street side closed (cars reach the parking from the ring only): low wall + steel louvres
                sz, sd = (uz0, 0.2) if b['type'] == 'u31' else (uz1, -0.2)
                B.box('seramik', ux0, sz, ux1, sz + sd, 0.0, 1.0)
                B.box('dograma', ux0, sz + sd / 2 - 0.03, ux1, sz + sd / 2 + 0.03, 1.0, 1.06)
                nl = int((ux1 - ux0) / 0.16)
                for k in range(nl):
                    lx = ux0 + 0.08 + k * (ux1 - ux0 - 0.16) / max(nl - 1, 1)
                    B.box('dograma', lx - 0.025, sz + sd / 2 - 0.06, lx + 0.025, sz + sd / 2 + 0.06, 1.06, e + WH - 0.05)
                xs = [ux0 + 0.2, (ux0 + ux1) / 2, ux1 - 0.2]
                zs = [uz0 + 0.25, (uz0 + uz1) / 2, uz1 - 0.25]
                for cx in xs:
                    for cz in zs:
                        B.box('beton', cx - 0.18, cz - 0.25, cx + 0.18, cz + 0.25, 0.12, e + WH)
                # painted bays
                nb = int((ux1 - ux0 - 0.4) // 2.6)
                for i in range(nb + 1):
                    lx = ux0 + 0.2 + i * 2.6 + ((ux1 - ux0 - 0.4) - nb * 2.6) / 2
                    for (za, zb) in ((uz0 + 0.3, uz0 + 5.2), (uz1 - 5.2, uz1 - 0.3)):
                        B.box('cizgi', lx - 0.05, za, lx + 0.05, zb, e, e + 0.005)
                # LED strips on the ceiling
                for lz in (uz0 + 3.0, uz1 - 3.0):
                    for i in range(3):
                        lx = ux0 + (i + 0.5) * (ux1 - ux0) / 3
                        B.box('led', lx - 0.6, lz - 0.05, lx + 0.6, lz + 0.05, e + WH - 0.03, e + WH)
                if end_free:  # closed end wall with ceramic cladding
                    if side == 'L':
                        B.box('seramik', ux0, uz0, ux0 + 0.2, uz1, 0, e + WH)
                    else:
                        B.box('seramik', ux1 - 0.2, uz0, ux1, uz1, 0, e + WH)
                # cars
                rows = [uz0 + 2.75, uz1 - 2.75]
                for ri, rz in enumerate(rows):
                    for i in range(nb):
                        if rng.random() < 0.22:
                            continue
                        lx = ux0 + 0.2 + (i + 0.5) * 2.6 + ((ux1 - ux0 - 0.4) - nb * 2.6) / 2
                        rot = math.pi / 2 if b['type'] == 'u31' else -math.pi / 2   # nose-in from the ring
                        props['cars'].append((B.X(lx), B.Y(rz), 0.12, rot + rng.uniform(-0.03, 0.03)))
                continue
            # slab + floor finish
            if lvl == 0:
                B.box('tas', ux0 - 0.04, uz0 - 0.04, ux1 + 0.04, uz1 + 0.04, 0.0, e)
            else:
                B.box('doseme', ux0, uz0, ux1, uz1, e - SL, e)
            B.box('parke', ux0 + 0.15, uz0 + 0.15, ux1 - 0.15, uz1 - 0.15, e, e + 0.012)
            # floor band (silme) on exterior faces
            if lvl > 0:
                for s_ in 'NSEW':
                    if s_ == bal_side:
                        continue
                    if s_ == end_side and not end_free:
                        continue
                    Ed = Edge(s_, U['bbox'])
                    a0, a1 = (ux0, ux1) if s_ in 'NS' else (uz0, uz1)
                    x0, z0_, x1, z1_ = Ed.rect(a0 - (0.05 if s_ in 'NS' else 0), a1 + (0.05 if s_ in 'NS' else 0), -0.05, 0.0)
                    B.box('silme', x0, z0_, x1, z1_, e - 0.26, e + 0.02)
            # walls
            for (a, c_, d_, f_) in U['walls']:
                ext_end = (side == 'L' and a <= ux0 + 0.02) or (side == 'R' and d_ >= ux1 - 0.02)
                exterior = a <= ux0 + 0.02 or d_ >= ux1 - 0.02 or c_ <= uz0 + 0.02 or f_ >= uz1 - 0.02
                mat = 'seramik' if (ext_end and end_free) else ('siva' if exterior else 'ic_duvar')
                B.box(mat, a, c_, d_, f_, e, e + WH)
            # openings
            for g in U['gaps']:
                s_ = g['side']
                horiz = s_ in 'NS'
                a = g['a'][0] if horiz else g['a'][1]
                bb = g['b'][0] if horiz else g['b'][1]
                Ed = Edge(s_, U['bbox'])
                wall_mat = 'seramik' if (s_ == end_side and end_free) else 'siva'
                if (s_ in 'WE') and s_ != core_side and touching(me, s_):
                    kind = 'solid'
                elif s_ == bal_side:
                    kind = 'door'
                elif s_ == core_side:
                    kind = 'entry'
                else:
                    kind = 'win'

                def piece(h0, h1, mat=wall_mat):
                    x0, z0_, x1, z1_ = Ed.rect(a, bb, 0, 0.15)
                    B.box(mat, x0, z0_, x1, z1_, e + h0, e + h1)
                if kind == 'solid':
                    piece(0, WH)
                elif kind == 'entry':
                    piece(2.15, WH, 'siva')
                    x0, z0_, x1, z1_ = Ed.rect(a + 0.04, bb - 0.04, 0.05, 0.1)
                    B.box('kapi', x0, z0_, x1, z1_, e, e + 2.15)
                else:
                    sill = 0.0 if kind == 'door' else (1.5 if bb - a < 0.9 else 0.9)
                    head = 2.35 if kind == 'door' else 2.3
                    if sill > 0:
                        piece(0, sill)
                    piece(head, WH)
                    r = rng.random()
                    curtain = 'sheer' if r < 0.35 else ('side' if r < 0.75 else None)
                    window_assembly(B, Ed, a, bb, e, sill, head, kind, curtain)
            # balcony
            bx0, bx1 = ux0 + 0.02, ux1 - 0.02
            if lvl == 0:
                B.box('tas', bx0, bz0, bx1, bz1, 0.0, e)
            else:
                B.box('silme', bx0, bz0, bx1, bz1, e - 0.24, e)
            B.box('balkon_zemin', bx0 + 0.03, bz0 + 0.03, bx1 - 0.03, bz1 - 0.03, e, e + 0.015)
            outer = bz1 if b['type'] == 'u31' else bz0
            inner = bz0 if b['type'] == 'u31' else bz1
            ins = 0.06 if outer > inner else -0.06
            lines = [((B.X(bx0 + 0.06), B.Y(outer - ins)), (B.X(bx1 - 0.06), B.Y(outer - ins))),
                     ((B.X(bx0 + 0.06), B.Y(inner)), (B.X(bx0 + 0.06), B.Y(outer - ins))),
                     ((B.X(bx1 - 0.06), B.Y(inner)), (B.X(bx1 - 0.06), B.Y(outer - ins)))]
            railing('korkuluk_cam', lines, e + 0.015)
            # balcony props
            r = rng.random()
            mid_z = (bz0 + bz1) / 2
            if r < 0.45:
                props['ac'].append((B.X(bx0 + 0.55 if side == 'L' else bx1 - 0.55), B.Y(inner + (0.2 if outer > inner else -0.2)), e + 0.015, 0 if outer > inner else math.pi))
            if rng.random() < 0.45:
                props['table'].append((B.X((bx0 + bx1) / 2 + rng.uniform(-1.5, 1.5)), B.Y(mid_z), e + 0.015, rng.uniform(-0.2, 0.2)))
            if rng.random() < 0.6:
                for _ in range(rng.randint(1, 3)):
                    props['pot'].append((B.X(bx1 - 0.35 if side == 'L' else bx0 + 0.35), B.Y(outer - ins * 3.5 + rng.uniform(-0.3, 0.3)), e + 0.015, rng.uniform(0, 6)))
        # ---- core
        build_core(B, lvl, e)
    build_roof(B, M, props)


def build_core(B, lvl, e):
    b = B.b
    cx0, cx1 = B.TT['core']
    parking = b['park'] and lvl == 0
    ls = 0.0 if lvl == 0 else e - SL
    if b['type'] == 'u31':
        B.box('seramik', cx0, 3.246, cx1, 3.496, e - (SL if lvl else e), e + WH)       # north face
        B.box('ic_duvar', cx0, 3.496, cx1, 5.69, e, e + WH)                            # shaft
        B.box('celik', 10.09, 5.69, 11.29, 5.73, e, e + 2.15)                          # lift door
        B.box('merdiven', cx0, 5.69, cx1, 8.18, ls, e + 0.01)
        if lvl < 2:
            stairs(B, cx0, 10.585, 8.18, 10.88, e, e + FH / 2)
            B.box('merdiven', cx0, 10.88, cx1, 12.08, e + FH / 2 - SL, e + FH / 2)
            stairs(B, 10.79, cx1, 10.88, 8.18, e + FH / 2, e + FH)
        else:
            B.box('merdiven', cx0, 8.18, cx1, 12.08, ls, e)
        for xa, xb in ((cx0 - 0.15, cx0), (cx1, cx1 + 0.15)):
            B.box('seramik', xa, 11.532, xb, 12.23, e - (SL if lvl else e), e + WH)
        front_z = (12.08, 12.23)
        if parking:
            B.box('seramik', cx0 - 0.15, 3.246, cx0, 11.532, 0, e + WH)
            B.box('seramik', cx1, 3.246, cx1 + 0.15, 11.532, 0, e + WH)
        outward = 'S'
    else:
        B.box('seramik', cx0, 8.73, cx1, 8.98, e - (SL if lvl else e), e + WH)
        B.box('ic_duvar', cx0, 6.6, cx1, 8.73, e, e + WH)
        B.box('celik', 7.79, 6.56, 8.99, 6.6, e, e + 2.15)
        B.box('merdiven', cx0, 4.048, cx1, 6.6, ls, e + 0.01)
        if lvl < 2:
            stairs(B, cx0, 8.286, 4.048, 1.347, e, e + FH / 2)
            B.box('merdiven', cx0, 0.15, cx1, 1.347, e + FH / 2 - SL, e + FH / 2)
            stairs(B, 8.49, cx1, 1.347, 4.048, e + FH / 2, e + FH)
        else:
            B.box('merdiven', cx0, 0.15, cx1, 4.048, ls, e)
        front_z = (0.0, 0.15)
        if parking:
            B.box('seramik', cx0 - 0.15, 0, cx0, 8.98, 0, e + WH)
            B.box('seramik', cx1, 0, cx1 + 0.15, 8.98, 0, e + WH)
        outward = 'N'
    # curtain wall front with mullions and spandrel
    Ed = Edge(outward, (cx0, front_z[0], cx1, front_z[1]))
    if lvl == 0:
        B.box('merdiven', cx0, min(front_z), cx1, max(front_z), 0, e)
        # entrance: glass doors, side lights, canopy, sign
        for (a0, a1) in ((cx0, cx0 + 0.35), (cx1 - 0.35, cx1)):
            x0, z0, x1, z1 = Ed.rect(a0, a1, 0, 0.15)
            B.box('seramik', x0, z0, x1, z1, e, e + WH)
        x0, z0, x1, z1 = Ed.rect(cx0 + 0.35, cx1 - 0.35, 0, 0.15)
        B.box('seramik', x0, z0, x1, z1, e + 2.45, e + WH)
        window_assembly(B, Ed, cx0 + 0.35, cx1 - 0.35, e, 0.0, 2.45, 'door', None)
        # canopy
        d = 1.4
        if outward == 'S':
            cz0, cz1 = max(front_z), max(front_z) + d
        else:
            cz0, cz1 = min(front_z) - d, min(front_z)
        B.box('dograma', cx0 - 0.5, cz0, cx1 + 0.5, cz1, e + 2.62, e + 2.8)
        B.box('silme', cx0 - 0.45, cz0 + 0.05 if outward == 'S' else cz0 + 0.05, cx1 + 0.45, cz1 - 0.05, e + 2.6, e + 2.62)
        # step / ramp in front of the door
        B.box('tas', cx0 - 0.6, cz0, cx1 + 0.6, cz1, 0.0, e - 0.02)
        props_sign.append((B, outward, cz1 if outward == 'S' else cz0, e + 2.71))
    else:
        x0, z0, x1, z1 = Ed.rect(cx0, cx1, 0, 0.15)
        B.box('seramik', x0, z0, x1, z1, e - 0.3, e + 0.4)
        n = 3
        for i in range(n + 1):
            a = cx0 + (cx1 - cx0) * i / n
            x0, z0, x1, z1 = Ed.rect(a - 0.04, a + 0.04, 0.0, 0.14)
            B.box('dograma', x0, z0, x1, z1, e + 0.4, e + WH - 0.3)
        x0, z0, x1, z1 = Ed.rect(cx0, cx1, 0.0, 0.14)
        B.box('dograma', x0, z0, x1, z1, e + 1.5, e + 1.56)
        x0, z0, x1, z1 = Ed.rect(cx0, cx1, 0.06, 0.075)
        B.box('cam', x0, z0, x1, z1, e + 0.4, e + WH - 0.3)
        x0, z0, x1, z1 = Ed.rect(cx0, cx1, 0, 0.15)
        B.box('seramik', x0, z0, x1, z1, e + WH - 0.3, e + WH)


props_sign = []


def stairs(B, x0, x1, zf, zt, yf, yt, steps=10):
    dz = (zt - zf) / steps
    dy = (yt - yf) / steps
    for i in range(steps):
        za, zb = zf + dz * i, zf + dz * (i + 1)
        B.box('merdiven', x0, min(za, zb), x1, max(za, zb), yf + dy * i - 0.15, yf + dy * (i + 1))


def build_roof(B, M, props):
    b = B.b
    D, W = B.D, B.W
    e = BASE + 3 * FH
    B.box('doseme', 0, 0, W, D, e - SL, e)
    B.box('silme', -0.04, -0.04, W + 0.04, D + 0.04, e - 0.26, e + 0.3)       # cornice band
    oh, pitch = 0.65, 0.33
    z0 = e + 0.3
    x0, x1 = B.X(-oh), B.X(W + oh)
    y0, y1 = B.Y(D + oh), B.Y(-oh)
    (r0, r1), hips, h = hip_roof(x0, y0, x1, y1, z0, pitch)
    # roof thickness edge (fascia) and soffit
    for (ax, ay, bx_, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        mb('sacak').obox(ax, ay, bx_, by, 0.04, z0 - 0.22, z0 + 0.02)
    mb('sacak').box(x0, y0, z0 - 0.23, x1, y1, z0 - 0.2)
    # ridge and hip caps
    mb('mahya').cyl((r0[0], r0[1], r0[2] + 0.04), (r1[0], r1[1], r1[2] + 0.04), 0.11, 10)
    for a, c in hips:
        mb('mahya').cyl((a[0], a[1], a[2] + 0.04), (c[0], c[1], c[2] + 0.04), 0.09, 8)
    # gutters + downspouts
    for (ax, ay, bx_, by) in ((x0, y0 - 0.08, x1, y0 - 0.08), (x0, y1 + 0.08, x1, y1 + 0.08)):
        mb('oluk').cyl((ax, ay, z0 - 0.05), (bx_, by, z0 - 0.05), 0.075, 10)
    for (px, py) in ((B.X(-0.1), B.Y(D + 0.1)), (B.X(W + 0.1), B.Y(D + 0.1)), (B.X(-0.1), B.Y(-0.1)), (B.X(W + 0.1), B.Y(-0.1))):
        ox_ = px + (-0.55 if px < B.X(W / 2) else 0.55)
        oy_ = py + (-0.55 if py < B.Y(D / 2) else 0.55)
        mb('oluk').cyl((ox_, oy_, z0 - 0.05), (px, py, z0 - 0.45), 0.045, 8)
        mb('oluk').cyl((px, py, z0 - 0.45), (px, py, 0.1), 0.05, 8)

    def roof_h(px, py):
        d = min(px - x0, x1 - px, py - y0, y1 - py)
        return z0 + max(0, d) * pitch
    # chimneys and solar water heaters
    ym = (y0 + y1) / 2
    for fx in (0.3, 0.7):
        px = x0 + (x1 - x0) * fx
        py = ym + rng.choice((-1, 1)) * 1.2
        zt = z0 + h + 0.7
        mb('siva').box(px - 0.32, py - 0.32, roof_h(px, py) - 0.4, px + 0.32, py + 0.32, zt)
        mb('dograma').box(px - 0.4, py - 0.4, zt, px + 0.4, py + 0.4, zt + 0.06)
        mb('dograma').cyl((px, py, zt + 0.06), (px, py, zt + 0.35), 0.08, 10)
    south_y = y0 + (y1 - y0) * 0.22
    for fx in (0.38, 0.62):
        px = x0 + (x1 - x0) * fx
        zr = roof_h(px, south_y)
        # tilted collector following the slope + tank
        pz = zr + 0.15
        mb('gunes_panel').face([(px - 1.0, south_y - 0.9, pz), (px + 1.0, south_y - 0.9, pz), (px + 1.0, south_y + 0.9, pz + 0.9 * 2 * 0.62), (px - 1.0, south_y + 0.9, pz + 0.9 * 2 * 0.62)])
        mb('dograma').obox(px - 1.02, south_y - 0.92, px + 1.02, south_y - 0.92, 0.04, pz - 0.02, pz + 0.04)
        mb('klima').cyl((px - 1.05, south_y + 1.15, pz + 1.35), (px + 1.05, south_y + 1.15, pz + 1.35), 0.27, 16)


def build_pool(S_):
    """Pool basin with mosaic tiles, water volume, stone coping, ladder and glass safety fence."""
    x0, y0, x1, y1 = RING['pool']
    (ax_, ay1), (bx_, ay0) = P((x0, y0)), P((x1, y1))     # Blender XY: ay0 < ay1
    top, depth, t = 0.1, 1.45, 0.25
    S_('havuz_fayans').box(ax_ - t, ay0 - t, top - depth - 0.2, bx_ + t, ay0, top)
    S_('havuz_fayans').box(ax_ - t, ay1, top - depth - 0.2, bx_ + t, ay1 + t, top)
    S_('havuz_fayans').box(ax_ - t, ay0, top - depth - 0.2, ax_, ay1, top)
    S_('havuz_fayans').box(bx_, ay0, top - depth - 0.2, bx_ + t, ay1, top)
    S_('havuz_fayans').box(ax_, ay0, top - depth - 0.2, bx_, ay1, top - depth)
    S_('su').box(ax_ + 0.002, ay0 + 0.002, top - depth, bx_ - 0.002, ay1 - 0.002, top - 0.1)
    for (a0, b0, a1, b1) in ((ax_ - 0.4, ay0 - 0.4, bx_ + 0.4, ay0), (ax_ - 0.4, ay1, bx_ + 0.4, ay1 + 0.4),
                             (ax_ - 0.4, ay0, ax_, ay1), (bx_, ay0, bx_ + 0.4, ay1)):
        S_('denizlik').box(a0, b0, top + 0.08, a1, b1, top + 0.15)
    # steps into the shallow end (south) and a steel ladder at the deep end
    for k in range(3):
        S_('havuz_fayans').box(ax_, ay0, top - 0.3 * (k + 1), bx_, ay0 + 0.35 * (3 - k), top - 0.3 * k - 0.05)
    lx = (ax_ + bx_) / 2
    for dx in (-0.25, 0.25):
        S_('celik').cyl((lx + dx, ay1 - 0.05, top - 1.0), (lx + dx, ay1 - 0.05, top + 0.2), 0.022, 10)
        S_('celik').cyl((lx + dx, ay1 - 0.05, top + 0.2), (lx + dx, ay1 + 0.3, top + 0.75), 0.022, 10)
        S_('celik').cyl((lx + dx, ay1 + 0.3, top + 0.75), (lx + dx, ay1 + 0.45, top + 0.15), 0.022, 10)
    # underwater lights
    for fy in (0.3, 0.7):
        y = ay0 + (ay1 - ay0) * fy
        for xx in (ax_ + 0.003, bx_ - 0.003):
            S_('havuz_lamba').cyl((xx, y, top - 0.6), (xx + (0.01 if xx < lx else -0.01), y, top - 0.6), 0.1, 16)
    # frameless glass safety fence with steel top rail
    for line in RING['pool_fence']:
        pts = [P(p) for p in line]
        for (pa, pb) in zip(pts, pts[1:]):
            S_('korkuluk_cam').obox(pa[0], pa[1], pb[0], pb[1], 0.012, 0.22, 1.3)
            S_('celik').obox(pa[0], pa[1], pb[0], pb[1], 0.03, 1.3, 1.33)


def build_signs(M, coll):
    for B, outward, zf, h in props_sign:
        cx0, cx1 = B.TT['core']
        cu = bpy.data.curves.new(f"tabela_{B.b['id']}", 'FONT')
        cu.body = f"{B.b['id']} BLOK"
        cu.size = 0.26
        cu.extrude = 0.01
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        ob = bpy.data.objects.new(cu.name, cu)
        ob.data.materials.append(M['tabela'])
        coll.objects.link(ob)
        x = B.X((cx0 + cx1) / 2)
        if outward == 'S':
            ob.location = (x, B.Y(zf) - 0.02, h)
            ob.rotation_euler = (math.pi / 2, 0, 0)
        else:
            ob.location = (x, B.Y(zf) + 0.02, h)
            ob.rotation_euler = (math.pi / 2, 0, math.pi)


def build_site(M):
    S_ = mb
    # ground
    # terrain slab with an opening for the pool basin
    px0, py0, px1, py1 = RING['pool']
    (hx0, hy1), (hx1, hy0) = P((px0, py0)), P((px1, py1))
    hx0, hy0, hx1, hy1 = hx0 - 0.3, hy0 - 0.3, hx1 + 0.3, hy1 + 0.3
    for (a0, b0, a1, b1) in ((-600, -600, hx0, 600), (hx1, -600, 600, 600), (hx0, -600, hx1, hy0), (hx0, hy1, hx1, 600)):
        S_('arazi').box(a0, b0, -0.5, a1, b1, -0.02)
    ex = edge_x
    roads = [
        [(-2600, 52), (3200, 52), (3200, 128), (-2600, 128)],
        [(-2600, 603.5), (401.3, 603.4), (1007.2, 620.2), (3200, 620.2), (3200, 677.6), (-2600, 677.6)],
        [(ex(-2600) + 18, -2600), (ex(-2600) + 114, -2600), (ex(3200) + 114, 3200), (ex(3200) + 18, 3200)],
    ]
    for r in roads:
        S_('asfalt').prism([P(p) for p in r], -0.05, 0.02)
    sidewalks = [
        [(-2600, 128), (ex(128) + 18, 128), (ex(143.5) + 18, 143.5), (-2600, 143.5)],
        [(-2600, 587.6), (401.3, 587.5), (1007.2, 604.3), (ex(604.3) + 18, 604.3), (ex(620.2) + 18, 620.2), (1007.2, 620.2), (401.3, 603.4), (-2600, 603.5)],
        [(-2600, 677.6), (ex(677.6) + 18, 677.6), (ex(693.6) + 18, 693.6), (-2600, 693.6)],
        [(ex(143.5), 143.5), (ex(143.5) + 18, 143.5), (ex(318) + 18, 318), (ex(318), 318)],
        [(ex(402), 402), (ex(402) + 18, 402), (ex(604.3) + 18, 604.3), (ex(604.3), 604.3)],
        [(ex(128) + 114, 128), (ex(128) + 130, 128), (ex(604.3) + 130, 604.3), (ex(604.3) + 114, 604.3)],
        [(-2600, 36), (3200, 36), (3200, 52), (-2600, 52)],
    ]
    for s in sidewalks:
        S_('kaldirim').prism([P(p) for p in s], -0.05, 0.15, sides=False)
        S_('bordur').prism([P(p) for p in s], -0.05, 0.15, top=False)
    # park
    S_('cim').prism([P(p) for p in [(-2600, 693.6), (ex(693.6) - 2, 693.6), (ex(1400), 1400), (-2600, 1400)]], -0.05, 0.12)
    # lane markings
    for (y, x0, x1) in ((90, -1400, 1700), (640.5, -1400, 1700)):
        x = x0
        while x < x1:
            yy = y if y == 90 else (640.5 if x < 401 else 640.5 + min(1, (x - 401) / 606) * 8.4)
            S_('cizgi').box(wx(x), wy(yy) - 0.075, 0.02, wx(x + 24), wy(yy) + 0.075, 0.025)
            x += 48
    y = -600
    while y < 1500:
        a, c = P((ex(y) + 66, y)), P((ex(y + 24) + 66, y + 24))
        S_('cizgi').obox(a[0], a[1], c[0], c[1], 0.15, 0.02, 0.025)
        y += 48
    # crosswalk at the site entrance
    for i in range(7):
        y0 = 425 + i * 6.2
        a, c = P((ex(y0) + 20, y0)), P((ex(y0) + 112, y0))
        S_('cizgi').obox(a[0], a[1], c[0], c[1], 0.45, 0.02, 0.026)
    # parcel paving (cut around the ring), ring road with curbs, lawns, median path, pool deck
    for pj in RING['paving']:
        S_('parke_tasi').poly(pj, -0.05, 0.1, sides=False)
        S_('bordur').poly(pj, -0.05, 0.13, top=False)
    for pj in RING['road']:
        S_('asfalt').poly(pj, -0.05, 0.03, sides=False)
    for pj in RING['greens'] + RING['median_green']:
        S_('cim').poly(pj, 0.05, 0.2, sides=False)
        S_('bordur').poly(pj, 0.0, 0.2, top=False)
    for pj in RING['median_path']:
        S_('kaldirim').poly(pj, 0.1, 0.21, sides=False)
    for pj in RING['deck']:
        S_('balkon_zemin').poly(pj, 0.1, 0.22, sides=False)
    build_pool(S_)
    # zebra crossings and one-way arrows on the ring
    for c in RING['crossings']:
        (ax_, ay_), (bx_, by_) = P(c['a']), P(c['b'])
        ln = math.hypot(bx_ - ax_, by_ - ay_)
        ux, uy = (bx_ - ax_) / ln, (by_ - ay_) / ln
        w = c['w'] / S
        t = 0.3
        while t < ln - 0.3:
            cx, cy = ax_ + ux * t, ay_ + uy * t
            S_('cizgi').obox(cx - uy * w / 2, cy + ux * w / 2, cx + uy * w / 2, cy - ux * w / 2, 0.5, 0.03, 0.036)
            t += 1.0
    for (x, y, ang) in RING['arrows']:
        cx, cy = P((x, y))
        dx, dy = math.cos(ang), -math.sin(ang)          # plan y points south
        nx, ny = -dy, dx
        tail = (cx - dx * 1.7, cy - dy * 1.7)
        neck = (cx + dx * 0.5, cy + dy * 0.5)
        S_('cizgi').obox(tail[0], tail[1], neck[0], neck[1], 0.3, 0.03, 0.036)
        tip = (cx + dx * 1.7, cy + dy * 1.7)
        S_('cizgi').face([(neck[0] + nx * 0.6, neck[1] + ny * 0.6, 0.036), (tip[0], tip[1], 0.036), (neck[0] - nx * 0.6, neck[1] - ny * 0.6, 0.036)])
        S_('cizgi').face([(neck[0] - nx * 0.6, neck[1] - ny * 0.6, 0.036), (tip[0], tip[1], 0.036), (neck[0] + nx * 0.6, neck[1] + ny * 0.6, 0.036)])
    # perimeter wall with steel railing
    for i in range(len(FENCE) - 1):
        a, c = P(FENCE[i]), P(FENCE[i + 1])
        S_('duvar_tas').obox(a[0], a[1], c[0], c[1], 0.25, 0, 0.65)
        S_('silme').obox(a[0], a[1], c[0], c[1], 0.32, 0.65, 0.72)
        ln = math.hypot(c[0] - a[0], c[1] - a[1])
        n = int(ln / 0.13)
        ux, uy = (c[0] - a[0]) / ln, (c[1] - a[1]) / ln
        for k in range(n + 1):
            px, py = a[0] + ux * k * 0.13, a[1] + uy * k * 0.13
            S_('dograma').box(px - 0.01, py - 0.01, 0.72, px + 0.01, py + 0.01, 1.75)
        S_('dograma').obox(a[0], a[1], c[0], c[1], 0.05, 1.72, 1.78)
        S_('dograma').obox(a[0], a[1], c[0], c[1], 0.04, 0.8, 0.84)
        m = int(ln / 2.6)
        for k in range(m + 1):
            px, py = a[0] + ux * k * ln / max(m, 1), a[1] + uy * k * ln / max(m, 1)
            S_('dograma').box(px - 0.04, py - 0.04, 0.72, px + 0.04, py + 0.04, 1.82)
    # gate island with guard booth and barriers
    for pj in RING['gate']['island']:
        S_('kaldirim').poly(pj, 0.0, 0.18, sides=False)
        S_('bordur').poly(pj, 0.0, 0.18, top=False)
    x0, y0, x1, y1 = RING['gate']['booth']
    (bx0, by1), (bx1, by0) = P((x0, y0)), P((x1, y1))
    S_('siva').box(bx0, by0, 0.18, bx1, by1, 1.0)
    S_('cam').box(bx0 + 0.02, by0 + 0.02, 1.0, bx1 - 0.02, by1 - 0.02, 2.3)
    S_('dograma').box(bx0, by0, 1.0, bx0 + 0.08, by1, 2.3)
    S_('dograma').box(bx1 - 0.08, by0, 1.0, bx1, by1, 2.3)
    S_('siva').box(bx0, by0, 2.3, bx1, by1, 2.75)
    S_('silme').box(bx0 - 0.5, by0 - 0.5, 2.75, bx1 + 0.5, by1 + 0.5, 2.95)
    for (pa, pc) in RING['gate']['barriers']:
        (ax_, ay_), (cx_, cy_) = P(pa), P(pc)
        n = 6
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            S_('kirmizi' if k % 2 else 'beyaz').obox(ax_ + (cx_ - ax_) * t0, ay_ + (cy_ - ay_) * t0, ax_ + (cx_ - ax_) * t1, ay_ + (cy_ - ay_) * t1, 0.1, 0.95, 1.06)
        S_('dograma').box(ax_ - 0.18, ay_ - 0.18, 0.18, ax_ + 0.18, ay_ + 0.18, 1.15)
    # neighbouring buildings (context), generated on a jittered grid around the parcel
    r = random.Random(42)
    spots = []
    for gx in range(-420, 1500, 230):
        for gy in (-45, -300):
            spots.append((gx + r.uniform(-25, 25), gy + r.uniform(-20, 20)))
    for gy in range(120, 1000, 150):
        for k in range(2):
            spots.append((ex(gy) + 220 + k * 170 + r.uniform(-20, 20), gy + r.uniform(-20, 20)))
    spots = [p for p in spots if not (p[0] > 1050 and p[1] > 480)]
    for (cx_, cy_) in spots:
        w_, d_ = r.uniform(95, 150), r.uniform(70, 95)
        if r.random() < 0.5:
            w_, d_ = d_, w_
        x0, x1 = wx(cx_ - w_ / 2), wx(cx_ + w_ / 2)
        y0, y1 = wy(cy_ + d_ / 2), wy(cy_ - d_ / 2)
        context_building(x0, y0, x1, y1, r.choice((3, 4, 4, 5)), r.randint(0, 2))
    CONTEXT_SPOTS.extend(spots)


CONTEXT_SPOTS = []


def scatter_points_in(poly_pts, density, exclude, seed):
    """Random XY points inside a Blender-XY polygon, rejecting exclusion rectangles."""
    r = random.Random(seed)
    xs = [p[0] for p in poly_pts]
    ys = [p[1] for p in poly_pts]
    area = abs(sum(poly_pts[i][0] * poly_pts[(i + 1) % len(poly_pts)][1] - poly_pts[(i + 1) % len(poly_pts)][0] * poly_pts[i][1] for i in range(len(poly_pts)))) / 2
    n = int(area * density)
    out = []

    def inside(x, y):
        c = False
        j = len(poly_pts) - 1
        for i in range(len(poly_pts)):
            xi, yi = poly_pts[i]
            xj, yj = poly_pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
                c = not c
            j = i
        return c
    tries = 0
    while len(out) < n and tries < n * 4:
        tries += 1
        x, y = r.uniform(min(xs), max(xs)), r.uniform(min(ys), max(ys))
        if not inside(x, y):
            continue
        if any(a <= x <= c and b <= y <= d for (a, b, c, d) in exclude):
            continue
        out.append((x, y))
    return out


def grass_system(points, z, cols, name):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x, y in points], [], [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    gcol = bpy.data.collections.new(name + '_kaynak')
    for c in cols:
        for o in c.objects:
            gcol.objects.link(o)
    ng = bpy.data.node_groups.new(name + '_gn', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = gcol
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    iop = N.new('GeometryNodeInstanceOnPoints')
    iop.inputs['Pick Instance'].default_value = True
    ri = N.new('FunctionNodeRandomValue')
    ri.data_type = 'INT'
    ri.inputs['Min'].default_value = 0
    ri.inputs['Max'].default_value = len(gcol.objects) - 1
    rr = N.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT_VECTOR'
    rr.inputs['Min'].default_value = (0, 0, 0)
    rr.inputs['Max'].default_value = (0, 0, 6.283)
    rs = N.new('FunctionNodeRandomValue')
    rs.data_type = 'FLOAT_VECTOR'
    rs.inputs['Min'].default_value = (0.8, 0.8, 0.7)
    rs.inputs['Max'].default_value = (1.4, 1.4, 1.3)
    L.new(gi.outputs[0], iop.inputs['Points'])
    L.new(ci.outputs[0], iop.inputs['Instance'])
    L.new(ri.outputs[0], iop.inputs['Instance Index'])
    L.new(rr.outputs[0], iop.inputs['Rotation'])
    L.new(rs.outputs[0], iop.inputs['Scale'])
    L.new(iop.outputs[0], go.inputs[0])
    mod = ob.modifiers.new('cim', 'NODES')
    mod.node_group = ng
    return ob


def setup_world(sun_az_deg=-120):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('gokyuzu')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    # sun in HDRI sits at azimuth -34.2 deg (atan2(y, x)); rotate to requested azimuth
    # (the mapping rotates the lookup vector, so the sky turns the opposite way)
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(-34.2 - sun_az_deg))
    env = N.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(os.path.join(ASSETS, 'hdri', 'kloofendal_48d_partly_cloudy_puresky.hdr'))
    bg = N.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 1.0
    out = N.new('ShaderNodeOutputWorld')
    L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    L.new(mp.outputs['Vector'], env.inputs['Vector'])
    L.new(env.outputs['Color'], bg.inputs['Color'])
    L.new(bg.outputs[0], out.inputs[0])


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    M = build_materials()
    unit_boxes()
    props = dict(cars=[], ac=[], table=[], pot=[])
    blocks = [Block(b) for b in BLOCKS]
    for B in blocks:
        build_block(B, M, props)
    build_site(M)
    arch = bpy.data.collections.new('Mimari')
    sc.collection.children.link(arch)
    for k, m in BUILD.items():
        m.to_object(k, M[k], arch, smooth=(k in ('oluk', 'mahya')))
    build_signs(M, arch)
    w = bpy.data.objects.get('su')
    if w:  # no caustics on CPU: let light reach the pool floor through the water
        w.visible_shadow = False

    # ---- assets
    veg = bpy.data.collections.new('Bitki_ve_donati')
    sc.collection.children.link(veg)
    tmp = hidden_collection('_import')
    trees = {}
    for name in ('jacaranda_tree', 'island_tree_01', 'island_tree_02'):
        c = hidden_collection(name)
        for o in import_gltf(name, c):
            if o.type == 'MESH':
                bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
                o.location -= Vector((sum(p.x for p in bb) / 8, sum(p.y for p in bb) / 8, 0))
        trees[name] = c
    shrubs = split_variants('shrub_02', import_gltf('shrub_02', tmp))
    bushes = split_variants('searsia_lucida', import_gltf('searsia_lucida', tmp))
    small = split_variants('shrub_03', import_gltf('shrub_03', tmp))
    grass = make_grass_tufts(M)

    car_cols = []
    for v in ('sedan', 'hatch', 'suv'):
        for cname, col in CAR_COLORS.items():
            if v == 'suv' and cname in ('krem',):
                continue
            car_cols.append((v, make_car(v, M, paint_mat(f'{v}_{cname}', col), cname)))
    def car():
        weights = [3 if v == 'sedan' else 2 for v, _ in car_cols]
        return rng.choices([c for _, c in car_cols], weights)[0]
    ac, table, lamp, bollard, bench = make_ac(M), make_table_set(M), make_lamp(M), make_bollard(M), make_bench(M)
    pot = make_pot(M, small)
    lounger, umbrella = make_lounger(M), make_umbrella(M)

    for (x, y, z, r) in props['cars']:
        instance(car(), (x, y, z), r, 1.0, veg)
    for (x, y, z, r) in props['ac']:
        instance(ac, (x, y, z), r, 1.0, veg)
    for (x, y, z, r) in props['table']:
        instance(table, (x, y, z), r, 1.0, veg)
    for (x, y, z, r) in props['pot']:
        instance(pot, (x, y, z), r, rng.uniform(0.8, 1.2), veg)

    # street-parked cars (plan points; 1 m = 8.065 pt)
    x = -150.0
    while x < 1150:
        if rng.random() < 0.6:
            yy = 610 + (min(max(x - 401, 0), 606) / 606) * 8.4
            instance(car(), (wx(x), wy(yy + 4), 0.02), rng.choice((0, math.pi)) + rng.uniform(-0.02, 0.02), 1.0, veg)
        x += rng.uniform(5.6, 6.6) * S
    x = -150.0
    while x < 1100:
        if rng.random() < 0.5:
            instance(car(), (wx(x), wy(121), 0.02), rng.choice((0, math.pi)) + rng.uniform(-0.02, 0.02), 1.0, veg)
        x += rng.uniform(5.6, 6.6) * S
    for (x, y, r_) in ((300, 98, 0), (820, 82, math.pi), (150, 660, math.pi), (700, 666, 0), (edge_x(260) + 50, 260, -math.pi / 2 - 0.157)):
        instance(car(), (wx(x), wy(y), 0.02), r_, 1.0, veg)

    # trees
    for i, (x, y, s) in enumerate(TREES):
        kind = 'jacaranda_tree' if i % 3 != 1 else 'island_tree_01'
        sc_ = (0.36 if kind == 'jacaranda_tree' else 1.6) * s * rng.uniform(0.9, 1.1)
        instance(trees[kind], (wx(x), wy(y), 0.18), rng.uniform(0, 6.28), sc_, veg)
    r3 = random.Random(11)
    for i in range(260):  # distant tree belt to break the horizon
        ang, dist = r3.uniform(0, 6.283), r3.uniform(190, 520)
        k = r3.choice(('island_tree_01', 'island_tree_02', 'jacaranda_tree'))
        sc_ = {'island_tree_01': 1.7, 'island_tree_02': 2.1, 'jacaranda_tree': 0.36}[k] * r3.uniform(0.8, 1.2)
        instance(trees[k], (math.cos(ang) * dist, math.sin(ang) * dist, 0.0), r3.uniform(0, 6.28), sc_, veg)
    for x in range(-60, 1150, 72):  # street trees on the far sidewalks
        instance(trees['jacaranda_tree'], (wx(x), wy(686), 0.15), rng.uniform(0, 6.28), rng.uniform(0.28, 0.34), veg)
    for x in range(120, 1100, 90):
        instance(trees['jacaranda_tree'], (wx(x), wy(44), 0.15), rng.uniform(0, 6.28), rng.uniform(0.28, 0.34), veg)
    for y in range(160, 600, 80):
        instance(trees['jacaranda_tree'], (wx(edge_x(y) + 122), wy(y), 0.15), rng.uniform(0, 6.28), rng.uniform(0.28, 0.34), veg)
    r2 = random.Random(5)
    for (cx_, cy_) in CONTEXT_SPOTS:  # trees between neighbouring buildings
        for k in range(2):
            k = r2.choice(('island_tree_01', 'island_tree_02', 'jacaranda_tree'))
            sc_ = {'island_tree_01': 1.5, 'island_tree_02': 1.9, 'jacaranda_tree': 0.3}[k] * r2.uniform(0.85, 1.1)
            instance(trees[k], (wx(cx_ + r2.uniform(-90, 90)), wy(cy_ + r2.choice((-60, 60))), 0.0), r2.uniform(0, 6.28), sc_, veg)
    for i in range(55):  # park
        x, y = rng.uniform(-80, 1000), rng.uniform(712, 900)
        k = rng.choice(('jacaranda_tree', 'island_tree_01', 'island_tree_02'))
        s = {'jacaranda_tree': 0.32, 'island_tree_01': 1.6, 'island_tree_02': 2.0}[k] * rng.uniform(0.8, 1.2)
        instance(trees[k], (wx(x), wy(y), 0.12), rng.uniform(0, 6.28), s, veg)
    # small ornamental trees in the south lawn and along the east zone
    for (x, y) in ((205, 576), (262, 572), (300, 577)):
        instance(trees['island_tree_02'], (wx(x), wy(y), 0.2), rng.uniform(0, 6.28), rng.uniform(1.2, 1.5), veg)
    # hedge rows (privacy in front of ground floor terraces) and shrub groups
    def hedge(x0, x1, y, step=9.0):
        x = x0
        while x < x1:
            if not any(p[0][0] - 3 <= x <= p[1][0] + 3 and p[0][1] - 3 <= y <= p[2][1] + 3 for p in PATHS):
                instance(rng.choice(bushes), (wx(x), wy(y + rng.uniform(-1.5, 1.5)), 0.2), rng.uniform(0, 6.28), rng.uniform(0.38, 0.5), veg)
            x += step * rng.uniform(0.8, 1.2)
    hedge(150, 240, 423)
    for (x0, x1, y) in ((212, 540, 160), (190, 312, 568)):
        x = x0
        while x < x1:
            instance(rng.choice(shrubs), (wx(x), wy(y + rng.uniform(-4, 4)), 0.2), rng.uniform(0, 6.28), rng.uniform(0.7, 0.95), veg)
            x += 14
    SEC = RING['section']
    cross_x = [c['a'][0] for c in RING['crossings']]

    def free(x, margin=26):
        return not (540 < x < 720) and all(abs(x - cx) > margin for cx in cross_x)
    k = 0
    x = SEC['X_W'] + 16
    while x < SEC['X_E']:  # median trees in the lawn strips either side of the path
        if free(x):
            yy = SEC['YC'] + (-15 if k % 2 else 15)
            instance(trees['island_tree_02'], (wx(x), wy(yy), 0.2), rng.uniform(0, 6.28), rng.uniform(1.15, 1.35), veg)
            for j in range(2):
                instance(rng.choice(small), (wx(x + rng.uniform(-12, 12)), wy(yy + rng.uniform(-4, 4)), 0.2), rng.uniform(0, 6.28), rng.uniform(1.6, 2.2), veg)
        k += 1
        x += 58
    for (x, y) in ((690, 180), (800, 180), (930, 180), (1040, 230), (870, 160), (990, 165)):
        instance(rng.choice(shrubs), (wx(x), wy(y), 0.2), rng.uniform(0, 6.28), 0.7, veg)

    # lamps, benches, pool furniture
    x = SEC['X_W'] + 10
    k = 0
    while x < SEC['X_E']:
        if free(x, 14):
            instance(lamp, (wx(x), wy(SEC['Y_I0'] + 5 if k % 2 else SEC['Y_I1'] - 5), 0.2), 0, 1.0, veg)
        k += 1
        x += 40
    for x in range(-100, 1150, 110):
        instance(lamp, (wx(x), wy(593), 0.15), 0, 1.25, veg)
    x = SEC['X_W'] + 40
    while x < SEC['X_E'] - 20:
        if free(x, 20):
            instance(bench, (wx(x), wy(SEC['YC'] - 10), 0.2), 0, 1.0, veg)
            instance(bench, (wx(x + 30), wy(SEC['YC'] + 10), 0.2), math.pi, 1.0, veg)
        x += 105
    px0, py0, px1, py1 = RING['pool']
    for side in (-1, 1):
        for j in range(4):
            xx = px0 - 9.5 if side < 0 else px1 + 9.5
            instance(lounger, (wx(xx), wy(py0 + 16 + j * 22), 0.22), math.pi / 2, 1.0, veg)
    for xx in (px0 - 4, px1 + 4):
        instance(umbrella, (wx(xx), wy(py0 - 12), 0.22), 0, 1.0, veg)
    for (xx, yy) in ((px0 - 9, py1 + 10), (px1 + 9, py1 + 10)):
        instance(rng.choice(small), (wx(xx), wy(yy), 0.22), 0, 2.4, veg)
    # cars driving on the ring (one-way)
    LANE_PT = 3.5 * S
    for (x, y, r_) in ((450, SEC['Y_N0'] + LANE_PT / 2, math.pi), (840, SEC['Y_I1'] + LANE_PT / 2, 0.0),
                       (SEC['BX'] + SEC['BHW'] + LANE_PT / 2, 268, math.pi / 2)):
        instance(car(), (wx(x), wy(y), 0.03), r_, 1.0, veg)

    # grass scatter on lawns, excluding buildings and paths
    excl = []
    for B in blocks:
        bz0, bz1 = B.TT['balcony']
        zs = [0, B.D, bz0, bz1, 12.23 if B.b['type'] == 'u31' else 0]
        excl.append((B.X(-0.5), B.Y(max(zs) + 0.5), B.X(B.W + 0.5), B.Y(min(zs) - 0.5)))
    pts = []
    for i, g in enumerate(RING['greens'] + RING['median_green']):
        pts += scatter_points_in([P(p) for p in g['ext']], 45.0, excl, 100 + i)
    grass_system(pts, 0.2, grass, 'cim_sacilim')
    print('grass instances', len(pts))
    return M


# ---------------------------------------------------------------- cameras & render
VIEWS = {
    # name: (location, target, lens)
    'kus_bakisi': ((70, -100, 78), (-3, 4, 0), 30),
    'kus_bakisi_alcak': ((96, -72, 40), (-6, 6, 0), 28),
    'kus_bakisi_kuzeybati': ((-88, 70, 46), (2, -2, 2), 30),
    'avlu': ((wx(1030), wy(305), 1.7), (wx(700), wy(366), 3.5), 22),
    'havuz': ((wx(628.75), wy(378), 3.2), (wx(628.75), wy(240), 0.8), 22),
    'havuz_ust': ((wx(560), wy(420), 16), (wx(628.75), wy(268), 0.0), 26),
    'plan': ((0.0, 2.0, 220.0), (0.0, 2.001, 0.0), ('ORTHO', 132.0)),
    'sokak': ((wx(985), wy(690), 1.7), (wx(760), wy(520), 6.0), 24),
    'giris': ((wx(edge_x(362) + 126), wy(362), 1.7), (wx(990), wy(340), 4.5), 24),
    'cephe': ((wx(868), wy(324), 1.7), (wx(784), wy(292), 4.8), 22),
}


def setup_render(res, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.max_bounces = 8
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 3
    cy.transmission_bounces = 8
    cy.transparent_max_bounces = 24
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            pass
    sc.view_settings.exposure = 0.15
    sc.render.threads_mode = 'AUTO'


def set_camera(name):
    sc = bpy.context.scene
    loc, tgt, lens = VIEWS[name]
    cam = bpy.data.objects.get('Kamera')
    if cam is None:
        cd = bpy.data.cameras.new('Kamera')
        cam = bpy.data.objects.new('Kamera', cd)
        sc.collection.objects.link(cam)
    cam.location = loc
    d = Vector(tgt) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if isinstance(lens, tuple):
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = lens[1]
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = lens
    cam.data.clip_start = 0.1
    cam.data.clip_end = 2000
    cam.data.sensor_width = 36
    sc.camera = cam


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kaydet')
    ap.add_argument('--ac')
    ap.add_argument('--render', default='')
    ap.add_argument('--cozunurluk', default='1920x1080')
    ap.add_argument('--ornek', type=int, default=128)
    ap.add_argument('--cikti', default=os.path.join(HERE, 'cikti'))
    ap.add_argument('--gunes', type=float, default=-120)
    a = ap.parse_args()
    if a.ac:
        bpy.ops.wm.open_mainfile(filepath=a.ac)
    else:
        build_scene()
        setup_world(a.gunes)
    if a.kaydet:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.kaydet))
    res = tuple(int(v) for v in a.cozunurluk.split('x'))
    setup_render(res, a.ornek)
    os.makedirs(a.cikti, exist_ok=True)
    for v in [v for v in a.render.split(',') if v]:
        set_camera(v)
        bpy.context.scene.render.filepath = os.path.join(a.cikti, v + '.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', v, flush=True)


if __name__ == '__main__':
    main()
