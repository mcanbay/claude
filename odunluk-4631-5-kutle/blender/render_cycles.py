"""Odunluk 4631/5 — fotogerçekçi cephe render'ı (Blender Cycles).

Kullanım (Blender'ın Python modülüyle: pip install bpy==5.2.3):
    python blender/render_cycles.py --glb blender/model_tasarim.glb --cikti renders/tasarim \
        [--gorunus kuzeydogu,kose,...] [--ornek 256] [--en 1920] [--boy 1200]

Geometri, kutle.js'in "tasarim" modundan dışa aktarılan GLB'dir (blender/disa_aktar.mjs).
Malzemeler burada malzeme adına göre prosedürel PBR olarak yeniden kurulur.
"""
import argparse
import math
import os
import sys

import bpy
import mathutils

# ---------------------------------------------------------------------------
# Kameralar (three.js dünya koordinatı: X doğu, Y yukarı, Z güney) ve güneş
# gunes: (azimut kuzeyden saat yönünde, yükseklik) derece
# ---------------------------------------------------------------------------
GORUNUSLER = {
    'kuzeydogu': dict(poz=(33, 17, -36), hedef=(-3, 5, 0), fov=37, gunes=(72, 27)),
    'kose':      dict(poz=(21, 1.65, -19), hedef=(-6, 6.2, -3), fov=54, gunes=(72, 27)),
    'sokak':     dict(poz=(-0.6, 5.2, -41), hedef=(-0.6, 5.6, 0), fov=44, gunes=(68, 24)),
    'batikose':  dict(poz=(-27, 1.65, -21), hedef=(-9, 6.5, -4), fov=52, gunes=(285, 24)),
    'guneybati': dict(poz=(-40, 28, 40), hedef=(-3, 3.5, 0.5), fov=34, gunes=(228, 38)),
    'test':      dict(poz=(-6, 2.5, -13), hedef=(-7, 0, -9), fov=40, gunes=(72, 27)),
    'giris':     dict(poz=(-4.2, 1.6, -14.5), hedef=(-8.6, 4.6, -6.0), fov=50, gunes=(72, 27)),
}


def srgb(h):
    """'#RRGGBB' -> doğrusal RGBA."""
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, 1.0)


# ---------------------------------------------------------------------------
# Malzeme kurucuları
# ---------------------------------------------------------------------------
class Dugum:
    def __init__(self, ad):
        self.mat = bpy.data.materials.new(ad)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.out = self.n('ShaderNodeOutputMaterial')
        self.bsdf = self.n('ShaderNodeBsdfPrincipled')
        self.l(self.bsdf.outputs[0], self.out.inputs['Surface'])

    def n(self, tip, **kw):
        d = self.nt.nodes.new(tip)
        for k, v in kw.items():
            setattr(d, k, v)
        return d

    def l(self, a, b):
        self.nt.links.new(a, b)

    def girdi(self, ad, deger):
        self.bsdf.inputs[ad].default_value = deger

    def gurultu(self, vektor, olcek, detay=4.0, puruz=0.55, bozulma=0.0):
        t = self.n('ShaderNodeTexNoise')
        t.inputs['Scale'].default_value = olcek
        t.inputs['Detail'].default_value = detay
        t.inputs['Roughness'].default_value = puruz
        t.inputs['Distortion'].default_value = bozulma
        if vektor is not None:
            self.l(vektor, t.inputs['Vector'])
        return t

    def aralik(self, cikis, a, b, c=0.0, d=1.0):
        m = self.n('ShaderNodeMapRange')
        m.inputs['From Min'].default_value = c
        m.inputs['From Max'].default_value = d
        m.inputs['To Min'].default_value = a
        m.inputs['To Max'].default_value = b
        self.l(cikis, m.inputs['Value'])
        return m.outputs['Result']

    def renk_carp(self, renk, carpan):
        mx = self.n('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
        mx.inputs['Factor'].default_value = 1.0
        if isinstance(renk, bpy.types.NodeSocket):
            self.l(renk, mx.inputs[6])
        else:
            mx.inputs[6].default_value = renk
        if isinstance(carpan, bpy.types.NodeSocket):
            self.l(carpan, mx.inputs[7])
        else:
            mx.inputs[7].default_value = (carpan, carpan, carpan, 1.0)
        return mx.outputs[2]

    def kabartma(self, yukseklik, guc, mesafe=0.002, ters=False):
        b = self.n('ShaderNodeBump')
        b.inputs['Strength'].default_value = guc
        b.inputs['Distance'].default_value = mesafe
        b.invert = ters
        self.l(yukseklik, b.inputs['Height'])
        self.l(b.outputs['Normal'], self.bsdf.inputs['Normal'])
        return b


def m_siva():
    d = Dugum('siva')
    pos = d.n('ShaderNodeNewGeometry').outputs['Position']
    ince = d.gurultu(pos, 380, 6, 0.62)
    kaba = d.gurultu(pos, 0.7, 2, 0.5)
    d.l(d.renk_carp(srgb('#E7E2D8'), d.aralik(kaba.outputs['Fac'], 0.955, 1.03, 0.3, 0.7)), d.bsdf.inputs['Base Color'])
    d.girdi('Roughness', 0.9)
    d.kabartma(ince.outputs['Fac'], 0.09, 0.0015)
    return d.mat


def m_kompozit(ad, renk, metal=0.55, puruz=0.34):
    d = Dugum(ad)
    rnd = d.n('ShaderNodeObjectInfo').outputs['Random']
    d.l(d.renk_carp(srgb(renk), d.aralik(rnd, 0.965, 1.035)), d.bsdf.inputs['Base Color'])
    pos = d.n('ShaderNodeNewGeometry').outputs['Position']
    g = d.gurultu(pos, 2.5, 3, 0.5)
    d.l(d.aralik(g.outputs['Fac'], puruz - 0.04, puruz + 0.05, 0.3, 0.7), d.bsdf.inputs['Roughness'])
    d.girdi('Metallic', metal)
    d.girdi('Coat Weight', 0.12)
    d.girdi('Coat Roughness', 0.2)
    return d.mat


def m_ahsap():
    d = Dugum('ahsap')
    tc = d.n('ShaderNodeTexCoord')
    rnd = d.n('ShaderNodeObjectInfo').outputs['Random']
    # her lambriye farklı desen: nesne koordinatını rastgele kaydır
    kay = d.n('ShaderNodeVectorMath', operation='ADD')
    d.l(tc.outputs['Object'], kay.inputs[0])
    cmb = d.n('ShaderNodeCombineXYZ')
    for i in range(3):
        d.l(d.aralik(rnd, 0, 17.0 + i * 5), cmb.inputs[i])
    d.l(cmb.outputs[0], kay.inputs[1])
    mp = d.n('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (34.0, 34.0, 0.75)   # damar lambri boyunca (yerel Z)
    d.l(kay.outputs[0], mp.inputs['Vector'])
    damar = d.gurultu(mp.outputs[0], 2.2, 10, 0.62, 0.35)
    ramp = d.n('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.32, srgb('#6A4226')
    el[1].position, el[1].color = 0.72, srgb('#B07A4B')
    orta = el.new(0.52)
    orta.color = srgb('#93613A')
    d.l(damar.outputs['Fac'], ramp.inputs['Fac'])
    d.l(d.renk_carp(ramp.outputs['Color'], d.aralik(rnd, 0.86, 1.1)), d.bsdf.inputs['Base Color'])
    d.girdi('Roughness', 0.52)
    d.girdi('Coat Weight', 0.1)
    d.kabartma(damar.outputs['Fac'], 0.04, 0.001)
    return d.mat


def m_duz(ad, renk, puruz=0.8, metal=0.0, gur=0.0):
    d = Dugum(ad)
    if gur > 0:
        pos = d.n('ShaderNodeNewGeometry').outputs['Position']
        g = d.gurultu(pos, 1.5, 3, 0.5)
        d.l(d.renk_carp(srgb(renk), d.aralik(g.outputs['Fac'], 1 - gur, 1 + gur, 0.3, 0.7)), d.bsdf.inputs['Base Color'])
    else:
        d.girdi('Base Color', srgb(renk))
    d.girdi('Roughness', puruz)
    d.girdi('Metallic', metal)
    return d.mat


def m_cam(ad, renk, puruz=0.0):
    d = Dugum(ad)
    d.girdi('Base Color', srgb(renk))
    d.girdi('Roughness', puruz)
    d.girdi('IOR', 1.52)
    d.girdi('Transmission Weight', 1.0)
    return d.mat


def m_asfalt():
    d = Dugum('asfalt')
    pos = d.n('ShaderNodeNewGeometry').outputs['Position']
    leke = d.gurultu(pos, 0.12, 4, 0.6)
    tane = d.n('ShaderNodeTexVoronoi')
    tane.inputs['Scale'].default_value = 260
    d.l(pos, tane.inputs['Vector'])
    d.l(d.renk_carp(srgb('#45484B'), d.aralik(leke.outputs['Fac'], 0.82, 1.12, 0.3, 0.7)), d.bsdf.inputs['Base Color'])
    d.girdi('Roughness', 0.9)
    d.kabartma(tane.outputs['Distance'], 0.25, 0.002)
    return d.mat


def m_parke():
    """Kilitli parke taşı (20x10 cm) — parsel zemini."""
    d = Dugum('zemin')
    pos = d.n('ShaderNodeNewGeometry').outputs['Position']
    br = d.n('ShaderNodeTexBrick')
    br.offset = 0.5
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.0045
    br.inputs['Mortar Smooth'].default_value = 0.3
    br.inputs['Brick Width'].default_value = 0.2
    br.inputs['Row Height'].default_value = 0.1
    br.inputs['Color1'].default_value = srgb('#B9B4A9')
    br.inputs['Color2'].default_value = srgb('#A49F95')
    br.inputs['Mortar'].default_value = srgb('#6F6B64')
    d.l(pos, br.inputs['Vector'])
    leke = d.gurultu(pos, 0.5, 3, 0.55)
    d.l(d.renk_carp(br.outputs['Color'], d.aralik(leke.outputs['Fac'], 0.9, 1.06, 0.3, 0.7)), d.bsdf.inputs['Base Color'])
    d.girdi('Roughness', 0.86)
    d.kabartma(br.outputs['Fac'], 0.35, 0.004, ters=True)
    return d.mat


def m_cevre():
    d = Dugum('cevre')
    pos = d.n('ShaderNodeNewGeometry').outputs['Position']
    leke = d.gurultu(pos, 0.08, 5, 0.6)
    tane = d.n('ShaderNodeTexVoronoi')
    tane.inputs['Scale'].default_value = 90
    d.l(pos, tane.inputs['Vector'])
    d.l(d.renk_carp(srgb('#A8A398'), d.aralik(leke.outputs['Fac'], 0.85, 1.1, 0.3, 0.7)), d.bsdf.inputs['Base Color'])
    d.girdi('Roughness', 0.96)
    d.kabartma(tane.outputs['Distance'], 0.3, 0.004)
    return d.mat


PUS_GOK = []   # uzak zemin pusunda kullanılan gök dokuları (güneşle birlikte güncellenir)


def pus_ekle(mat, bas=70.0, son=900.0):
    """Hava perspektifi: uzaklaştıkça yüzey, o yöndeki ufuk gök rengine karışır."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    yuzey = out.inputs['Surface'].links[0].from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    ters = nt.nodes.new('ShaderNodeVectorMath'); ters.operation = 'SCALE'
    ters.inputs['Scale'].default_value = -1.0
    nt.links.new(geo.outputs['Incoming'], ters.inputs[0])
    ayir = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(ters.outputs[0], ayir.inputs[0])
    bir = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(ayir.outputs[0], bir.inputs[0]); nt.links.new(ayir.outputs[1], bir.inputs[1])
    bir.inputs[2].default_value = 0.03                      # ufkun hemen üstü
    nrm = nt.nodes.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'
    nt.links.new(bir.outputs[0], nrm.inputs[0])
    gok = nt.nodes.new('ShaderNodeTexSky'); gok.sky_type = 'MULTIPLE_SCATTERING'; gok.sun_disc = False
    nt.links.new(nrm.outputs[0], gok.inputs['Vector'])
    PUS_GOK.append(gok)
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(gok.outputs[0], em.inputs['Color'])
    cam = nt.nodes.new('ShaderNodeCameraData')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = bas; mr.inputs['From Max'].default_value = son
    nt.links.new(cam.outputs['View Distance'], mr.inputs['Value'])
    us = nt.nodes.new('ShaderNodeMath'); us.operation = 'POWER'; us.inputs[1].default_value = 0.65
    nt.links.new(mr.outputs['Result'], us.inputs[0])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(us.outputs[0], mix.inputs['Fac'])
    nt.links.new(yuzey, mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return mat


def malzemeleri_kur():
    return {
        'siva': m_siva(),
        'koyugri': m_kompozit('koyugri', '#565C60'),
        'antrasit': m_kompozit('antrasit', '#33383C', metal=0.6, puruz=0.36),
        'ahsap': m_ahsap(),
        'alu': m_duz('metal_antrasit', '#2A2E32', 0.3, 0.85),
        'derz': m_duz('derz', '#121416', 0.8),
        'cam': m_cam('cam', '#EEF6F4'),
        'korkulukCam': m_cam('korkuluk_cam', '#E3F0F0'),
        'kapiCam': m_duz('kapi_cam', '#0E1214', 0.03, 0.0),
        'icDuvar': m_duz('ic_duvar', '#D8D1C5', 0.95),
        'mermer': m_duz('mermer', '#ECE9E2', 0.24, gur=0.02),
        'cati': m_duz('cati', '#8E8B85', 0.92, gur=0.05),
        'zemin': m_parke(),
        'asfalt': pus_ekle(m_asfalt()),
        'maket': pus_ekle(m_cevre()),
        'sinir': m_duz('bordur', '#ABA79F', 0.9, gur=0.05),
        'cizgi': m_duz('cizgi', '#F0F0EA', 0.6),
    }


# ---------------------------------------------------------------------------
# Sahne
# ---------------------------------------------------------------------------
def sahne_kur(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    mats = malzemeleri_kur()
    eksik = set()
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue
        for slot in ob.material_slots:
            ad = slot.material.name.split('.')[0] if slot.material else ''
            if ad in mats:
                slot.material = mats[ad]
            else:
                eksik.add(ad)
                slot.material = mats['siva']
    if eksik:
        print('Eşlenmeyen malzemeler (sıva verildi):', sorted(eksik))
    # çevre zemini (maket tablasının dışı)
    bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, -0.03))
    bpy.context.active_object.data.materials.append(mats['maket'])
    return mats


def gok_kur(az, el):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('gok')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(el)
    sky.sun_rotation = math.radians(az)     # kuzeyden saat yönünde (Blender +Y kuzey)
    sky.sun_disc = True
    sky.sun_size = math.radians(0.545)
    sky.altitude = 150
    sky.air_density = 1.0
    sky.aerosol_density = 1.6
    for g in PUS_GOK:
        for ad in ('sun_elevation', 'sun_rotation', 'altitude', 'air_density', 'aerosol_density'):
            setattr(g, ad, getattr(sky, ad))
    bg = nt.nodes['Background']
    bg.inputs['Strength'].default_value = 1.0
    nt.links.new(sky.outputs[0], bg.inputs[0])


def kamera_kur(v, en, boy):
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new('kamera')
    cam = bpy.data.objects.new('kamera', cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    t2b = lambda p: mathutils.Vector((p[0], -p[2], p[1]))
    poz, hedef = t2b(v['poz']), t2b(v['hedef'])
    cam.location = poz
    cam.rotation_euler = (hedef - poz).to_track_quat('-Z', 'Y').to_euler()
    cam_data.sensor_fit = 'VERTICAL'
    cam_data.sensor_height = 24.0
    cam_data.lens = 12.0 / math.tan(math.radians(v['fov']) / 2)
    cam_data.clip_start = 0.1
    cam_data.clip_end = 3000
    # mimari fotoğraf: düşey çizgiler paralel kalsın (kaydırmalı objektif)
    if v.get('dusey', True) and v['poz'][1] < 8:
        yon = hedef - poz
        egim = math.atan2(yon.z, math.hypot(yon.x, yon.y))
        cam.rotation_euler = mathutils.Vector((yon.x, yon.y, 0)).to_track_quat('-Z', 'Y').to_euler()
        # kaydırma, karenin büyük kenarı cinsindendir
        cam_data.shift_y = math.tan(egim) * cam_data.lens / cam_data.sensor_height * min(1.0, boy / en)
    sc.render.resolution_x, sc.render.resolution_y = en, boy


def render_ayar(ornek):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = ornek
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.015
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy.max_bounces = 8
    cy.diffuse_bounces = 4
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.transparent_max_bounces = 8
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.sample_clamp_indirect = 10.0
    cy.blur_glossy = 0.5
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    vs = sc.view_settings
    vs.view_transform = 'AgX'
    try:
        vs.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    vs.exposure = -3.4
    vs.gamma = 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--glb', required=True)
    ap.add_argument('--cikti', required=True)
    ap.add_argument('--gorunus', default=','.join(GORUNUSLER))
    ap.add_argument('--ornek', type=int, default=256)
    ap.add_argument('--en', type=int, default=1920)
    ap.add_argument('--boy', type=int, default=1200)
    ap.add_argument('--pozlama', type=float, default=None)
    a = ap.parse_args(sys.argv[1:])
    os.makedirs(a.cikti, exist_ok=True)
    sahne_kur(a.glb)
    render_ayar(a.ornek)
    if a.pozlama is not None:
        bpy.context.scene.view_settings.exposure = a.pozlama
    for ad in a.gorunus.split(','):
        v = GORUNUSLER[ad]
        gok_kur(*v['gunes'])
        for ob in [o for o in bpy.context.scene.objects if o.type == 'CAMERA']:
            bpy.data.objects.remove(ob)
        kamera_kur(v, a.en, a.boy)
        bpy.context.scene.render.filepath = os.path.join(a.cikti, ad + '.png')
        bpy.ops.render.render(write_still=True)
        print('yazildi', bpy.context.scene.render.filepath, flush=True)


if __name__ == '__main__':
    main()
