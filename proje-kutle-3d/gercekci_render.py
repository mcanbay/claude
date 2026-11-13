"""
Gerçekçi render: plandan çıkarılan duvarlar, pencereler ve odalarla detaylı bina,
Poly Haven HDRI gökyüzü, PBR dokular, ağaç ve sokak mobilyası modelleriyle Cycles render.

    python varliklar_indir.py                 # bir kez (~240 MB)
    python gercekci_render.py --out cikti_gercekci
    python gercekci_render.py --out deneme --scale 0.4 --samples 24 --only cadde

Bina, plan_geometri.json'daki gerçek duvar çizgilerinden kurulur: dış duvarlar,
iç bölmeler, pencere/balkon kapısı boşlukları, balkonlar ve dükkan bölmeleri plandan gelir.
Cephe malzemeleri, doğrama rengi, perdeler, mobilya, araçlar, ağaçlar ve çevre
binaları temsilidir.
"""

import argparse
import json
import math
import os
import random
import sys

import bpy  # noqa: I001  (bmesh, bpy yüklendikten sonra içe aktarılabilir)
import bmesh
from mathutils import Matrix, Vector
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kutle_blender as kb  # noqa: E402
from kutle_blender import (DOSEME, KAT_H, KAT_SAYISI, TOPLAM_H, ZEMIN_H, MeshBuilder, P,  # noqa: E402
                           clean_ring, edge_list, eye_camera_pos, parts, prism_data, street_frame)

VAR = os.path.join(HERE, "varliklar")
DOKU = os.path.join(VAR, "doku")
MODEL = os.path.join(VAR, "model")
HDRI = os.path.join(VAR, "hdri", "kloofendal_48d_partly_cloudy_puresky_4k.hdr")
# HDRI'daki güneşin yatay açısı (atan2(y, x), derece) ve yüksekliği. Blender eşdikdörtgen eşlemesi:
# u = 0.5 - atan2(y, x) / 2π  →  açı = (0.5 - u) · 360
HDRI_SUN = (-34.2, 47.9)
HDRI_AKSAM = os.path.join(VAR, "hdri", "evening_road_01_puresky_4k.hdr")
HDRI_AKSAM_SUN = (-34.8, 10.0)
AKSAM_HEADING = 162.0          # akşam güneşi göz hizası kamerasından bakınca binanın arkasında
SUN_HEADING = -55.3            # istenen güneş yönü: cadde (+x) ve güney (-y) cepheleri aydınlık

PENCERE_ALT, PENCERE_UST, KAPI_UST = 0.90, 2.45, 2.45
VITRIN_UST = 3.45


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(HERE, "plan_geometri.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "cikti_gercekci"))
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--only", default="")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--web-glb", default="", help="Web görüntüleyici için hafif GLB yolu (render yapmaz)")
    return ap.parse_args(argv)


# ===================================================================== malzemeler

def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    return nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]


def plain(name, color, rough=0.6, metal=0.0, **kw):
    m = bpy.data.materials.new(name)
    nt, N, L, b = _nodes(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        b.inputs[k].default_value = v
    m.diffuse_color = (*color, 1)
    return m


def textured(name, folder, size, tint=(1, 1, 1), rough_mul=1.0, bump=0.25, macro=0.0, proj="BOX"):
    """PBR doku: nesne koordinatı + kutu izdüşümü (UV gerektirmez), gerçek ölçekte."""
    m = bpy.data.materials.new(name)
    nt, N, L, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / size, 1 / size, 1 / size)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(fname, noncolor):
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(DOKU, folder, fname), check_existing=True)
        if noncolor:
            t.image.colorspace_settings.name = "Non-Color"
        t.projection = proj
        if proj == "BOX":
            t.projection_blend = 0.3
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    d = img("Diffuse.jpg", False)
    col = d.outputs["Color"]
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    L.new(col, mix.inputs["A"])
    mix.inputs["B"].default_value = (*tint, 1)
    col = mix.outputs["Result"]
    if macro > 0:  # büyük ölçekli renk dalgalanması (tekrar eden desen görünmesin)
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 0.02
        nz.inputs["Detail"].default_value = 3
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = N.new("ShaderNodeMapRange")
        ramp.inputs["To Min"].default_value = 1 - macro
        ramp.inputs["To Max"].default_value = 1 + macro * 0.6
        L.new(nz.outputs["Fac"], ramp.inputs["Value"])
        mix2 = N.new("ShaderNodeMix")
        mix2.data_type = "RGBA"
        mix2.blend_type = "MULTIPLY"
        mix2.inputs["Factor"].default_value = 1.0
        L.new(col, mix2.inputs["A"])
        comb = N.new("ShaderNodeCombineColor")
        for ch in ("Red", "Green", "Blue"):
            L.new(ramp.outputs["Result"], comb.inputs[ch])
        L.new(comb.outputs["Color"], mix2.inputs["B"])
        col = mix2.outputs["Result"]
    L.new(col, b.inputs["Base Color"])
    r = img("Rough.jpg", True)
    if rough_mul != 1.0:
        mm = N.new("ShaderNodeMath")
        mm.operation = "MULTIPLY"
        mm.inputs[1].default_value = rough_mul
        L.new(r.outputs["Color"], mm.inputs[0])
        L.new(mm.outputs["Value"], b.inputs["Roughness"])
    else:
        L.new(r.outputs["Color"], b.inputs["Roughness"])
    if bump > 0:
        h = img("Displacement.jpg", True)
        bp = N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.02 * size
        L.new(h.outputs["Color"], bp.inputs["Height"])
        L.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (*tint, 1)
    return m


def glass(name, tint=(0.92, 0.96, 0.96), rough=0.0, spec=1.0):
    m = plain(name, tint, rough)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.52
    b.inputs["Specular IOR Level"].default_value = spec   # kaplamalı cam: gökyüzü yansıması
    return m


def emission(name, color, strength):
    m = bpy.data.materials.new(name)
    nt, N, L, b = _nodes(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


def curtain_mat():
    m = bpy.data.materials.new("Perde")
    nt, N, L, b = _nodes(m)
    out = N["Material Output"]
    tr = N.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.95, 0.92, 0.86, 1)
    b.inputs["Base Color"].default_value = (0.9, 0.88, 0.83, 1)
    b.inputs["Roughness"].default_value = 0.9
    mx = N.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.45
    L.new(b.outputs["BSDF"], mx.inputs[1])
    L.new(tr.outputs["BSDF"], mx.inputs[2])
    L.new(mx.outputs["Shader"], out.inputs["Surface"])
    return m


def car_paint():
    m = bpy.data.materials.new("Arac_Boya")
    nt, N, L, b = _nodes(m)
    oi = N.new("ShaderNodeObjectInfo")
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    cols = [(0.85, 0.85, 0.85), (0.6, 0.61, 0.63), (0.02, 0.02, 0.025), (0.22, 0.23, 0.25),
            (0.03, 0.07, 0.2), (0.5, 0.03, 0.03), (0.75, 0.73, 0.68), (0.85, 0.85, 0.85)]
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (*cols[0], 1)
    el[1].position, el[1].color = 1 / len(cols), (*cols[1], 1)
    for i, c in enumerate(cols[2:], start=2):
        e = el.new(i / len(cols))
        e.color = (*c, 1)
    L.new(oi.outputs["Random"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.35
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.03
    return m


def context_mat(night=False):
    """Çevre binaları: sıva rengi + prosedürel pencere ızgarası (gece: bazı pencereler yanık)."""
    m = bpy.data.materials.new("Cevre_Bina_Gece" if night else "Cevre_Bina")
    nt, N, L, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord")
    geo = N.new("ShaderNodeNewGeometry")
    oi = N.new("ShaderNodeObjectInfo")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs["Vector"])
    nsep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], nsep.inputs["Vector"])

    def math_(op, a=None, b_=None, v1=None, v2=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        if a is not None:
            L.new(a, n.inputs[0])
        elif v1 is not None:
            n.inputs[0].default_value = v1
        if b_ is not None:
            L.new(b_, n.inputs[1])
        elif v2 is not None:
            n.inputs[1].default_value = v2
        return n.outputs[0]
    # yüzey boyunca koordinat: |nx|>|ny| ise y, değilse x
    ax = math_("ABSOLUTE", nsep.outputs["X"])
    ay = math_("ABSOLUTE", nsep.outputs["Y"])
    sel = math_("GREATER_THAN", ax, ay)
    along = N.new("ShaderNodeMix")
    along.data_type = "FLOAT"
    L.new(sel, along.inputs["Factor"])
    L.new(sep.outputs["X"], along.inputs["A"])
    L.new(sep.outputs["Y"], along.inputs["B"])
    fa = math_("FRACT", math_("DIVIDE", along.outputs["Result"], v2=3.2))
    fz = math_("FRACT", math_("DIVIDE", sep.outputs["Z"], v2=3.0))
    wa = math_("MULTIPLY", math_("GREATER_THAN", fa, v2=0.22), math_("LESS_THAN", fa, v2=0.78))
    wz = math_("MULTIPLY", math_("GREATER_THAN", fz, v2=0.30), math_("LESS_THAN", fz, v2=0.82))
    vert = math_("LESS_THAN", math_("ABSOLUTE", nsep.outputs["Z"]), v2=0.5)
    above = math_("GREATER_THAN", sep.outputs["Z"], v2=1.0)
    win = math_("MULTIPLY", math_("MULTIPLY", wa, wz), math_("MULTIPLY", vert, above))
    ramp = N.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    ramp.color_ramp.interpolation = "CONSTANT"
    cols = [(0.78, 0.7, 0.56), (0.86, 0.85, 0.82), (0.7, 0.62, 0.5), (0.66, 0.67, 0.68), (0.8, 0.66, 0.52), (0.84, 0.8, 0.7)]
    el[0].color = (*cols[0], 1)
    el[1].position = 1 / len(cols)
    el[1].color = (*cols[1], 1)
    for i, c in enumerate(cols[2:], start=2):
        e = el.new(i / len(cols))
        e.color = (*c, 1)
    L.new(oi.outputs["Random"], ramp.inputs["Fac"])
    mixc = N.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    L.new(win, mixc.inputs["Factor"])
    L.new(ramp.outputs["Color"], mixc.inputs["A"])
    mixc.inputs["B"].default_value = (0.03, 0.04, 0.05, 1)
    L.new(mixc.outputs["Result"], b.inputs["Base Color"])
    mixr = N.new("ShaderNodeMix")
    mixr.data_type = "FLOAT"
    L.new(win, mixr.inputs["Factor"])
    mixr.inputs["A"].default_value = 0.85
    mixr.inputs["B"].default_value = 0.08
    L.new(mixr.outputs["Result"], b.inputs["Roughness"])
    if night:
        cell = N.new("ShaderNodeCombineXYZ")
        L.new(math_("FLOOR", math_("DIVIDE", along.outputs["Result"], v2=3.2)), cell.inputs["X"])
        L.new(math_("FLOOR", math_("DIVIDE", sep.outputs["Z"], v2=3.0)), cell.inputs["Y"])
        L.new(math_("MULTIPLY", oi.outputs["Random"], v2=97.0), cell.inputs["Z"])
        wn = N.new("ShaderNodeTexWhiteNoise")
        wn.noise_dimensions = "3D"
        L.new(cell.outputs["Vector"], wn.inputs["Vector"])
        lit = math_("MULTIPLY", win, math_("GREATER_THAN", wn.outputs["Value"], v2=0.5))
        b.inputs["Emission Color"].default_value = (1.0, 0.72, 0.45, 1)
        L.new(math_("MULTIPLY", lit, v2=2.5), b.inputs["Emission Strength"])
    return m


def make_materials():
    M = {
        "siva": textured("Cephe_Sivasi", "white_stucco", 2.0, tint=(1.0, 0.98, 0.94), bump=0.12),
        "kaplama": textured("Balkon_Terrakota_Kaplama", "exterior_wall_cladding_02", 2.0, bump=0.35),
        "zemin_kaplama": textured("Zemin_Kat_Panel", "concrete_tile_facade", 2.0, tint=(1.7, 1.7, 1.7), bump=0.3),
        "asfalt": textured("Asfalt", "asphalt_02", 3.0, tint=(0.8, 0.8, 0.82), bump=0.3, macro=0.12),
        "parke": textured("Beton_Parke", "concrete_pavers_02", 2.0, tint=(0.9, 1.12, 1.4), bump=0.4, macro=0.08),
        "cim": textured("Cim", "leafy_grass", 2.0, tint=(0.2, 0.5, 0.26), bump=0.5, macro=0.15),
        "arazi": textured("Arazi", "leafy_grass", 3.0, tint=(0.24, 0.48, 0.25), bump=0.3, macro=0.35),
        "cakil": textured("Cakil", "gravel_floor", 2.25, tint=(0.55, 0.8, 1.35), bump=0.4),
        "ic_duvar": plain("Ic_Duvar", (0.82, 0.8, 0.76), 0.9),
        "tavan": plain("Tavan", (0.88, 0.88, 0.86), 0.9),
        "doseme_bandi": plain("Doseme_Bandi", (0.55, 0.55, 0.54), 0.65),
        "parke_ic": plain("Ic_Zemin_Laminat", (0.42, 0.3, 0.2), 0.45),
        "beton_ic": plain("Dukkan_Zemini", (0.42, 0.42, 0.41), 0.25),
        "balkon_zemin": plain("Balkon_Zemini", (0.5, 0.48, 0.45), 0.6),
        "dograma": plain("Dograma_Antrasit", (0.035, 0.037, 0.04), 0.35, 0.6),
        "denizlik": plain("Denizlik_Tas", (0.72, 0.7, 0.66), 0.45),
        "harpusta": plain("Harpusta_Aluminyum", (0.55, 0.56, 0.57), 0.35, 1.0),
        "cam": glass("Pencere_Cami", (0.82, 0.9, 0.92), spec=1.6),
        "korkuluk_cam": glass("Korkuluk_Cami", (0.82, 0.92, 0.9)),
        "perde": curtain_mat(),
        "isik": emission("Tavan_Isigi", (1.0, 0.86, 0.7), 6.0),
        "spot": emission("Saçak_Spotu", (1.0, 0.9, 0.78), 12.0),
        "bordur": plain("Bordur", (0.62, 0.61, 0.58), 0.7),
        "boya": plain("Yol_Boyasi", (0.82, 0.82, 0.8), 0.55),
        "klima": plain("Klima_Unitesi", (0.78, 0.78, 0.77), 0.4, 0.2),
        "arac": car_paint(),
        "arac_cam": plain("Arac_Cami", (0.01, 0.012, 0.015), 0.05),
        "lastik": plain("Lastik", (0.02, 0.02, 0.02), 0.8),
        "jant": plain("Jant", (0.6, 0.6, 0.62), 0.3, 1.0),
        "far": plain("Far", (0.9, 0.9, 0.85), 0.1),
        "stop": plain("Stop", (0.5, 0.02, 0.02), 0.2),
        "cevre_bina": context_mat(),
        "cevre_bina_gece": context_mat(night=True),
        "oda_isigi": emission("Oda_Isigi", (1.0, 0.76, 0.5), 22.0),
        "cit": plain("Cit_Yaprak", (0.05, 0.12, 0.03), 0.8),
    }
    return M


# ======================================================================= yardımcılar

def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def mesh_obj(name, verts, faces, mats, coll_, face_mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    for m in mats:
        me.materials.append(m)
    if face_mat:
        idx = [face_mat(p) for p in me.polygons]
        me.polygons.foreach_set("material_index", idx)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    coll_.objects.link(ob)
    return ob


def builder_obj(mb, name, mat, coll_):
    return mesh_obj(name, mb.verts, mb.faces, [mat], coll_)


def apply_boolean(target, cutter_mb, name):
    cut = builder_obj(cutter_mb, name + "_kesici", None, bpy.context.scene.collection)
    mod = target.modifiers.new("kesim", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cut
    mod.solver = "EXACT"
    try:
        mod.material_mode = "INDEX"
    except Exception:
        pass
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.clear()
    old = target.data
    target.data = me
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cut)


def seg_frame(a, b):
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n_left = (-u[1], u[0])
    return L, u, n_left


def at(a, u, n, s, d):
    return (a[0] + u[0] * s + n[0] * d, a[1] + u[1] * s + n[1] * d)


def link_blend(path, names=None, collection=None):
    """Bir .blend dosyasından nesneleri ekler (append)."""
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if names is None or n in names]
    out = [o for o in dst.objects if o is not None]
    return out


# ===================================================================== bina: normal kat

def classify_wall_faces(me, enclosed, balcony_zone, interior_idx, exterior_idx, clad_idx):
    ext = enclosed.exterior
    res = []
    for p in me.polygons:
        n = p.normal
        c = p.center
        if abs(n.z) > 0.5:
            res.append(exterior_idx)
            continue
        pt = Point(c.x, c.y)
        if ext.distance(pt) < 0.04:
            res.append(clad_idx if balcony_zone.contains(pt) else exterior_idx)
        else:
            res.append(interior_idx)
    return res


def openings_outward(D, enclosed):
    out = []
    for o in D["normal"]["acikliklar"]:
        a, b = tuple(o["a"]), tuple(o["b"])
        L, u, nl = seg_frame(a, b)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        # n_out: dışa bakan normal
        n_out = (-nl[0], -nl[1])
        if enclosed.contains(Point(mid[0] + n_out[0] * 0.3, mid[1] + n_out[1] * 0.3)):
            n_out = nl
        out.append((a, b, o["tip"], n_out))
    return out


def window_parts(a, b, n_out, z0, sill, head, frame, glass_mb, sill_mb, mullion_every=1.3):
    """Doğrama çerçevesi, kayıt, cam ve dış denizlik."""
    L, u, _ = seg_frame(a, b)
    inset = 0.09        # camın cephe çizgisinden içeri mesafesi
    nin = (-n_out[0], -n_out[1])
    fw, fd = 0.06, 0.07
    za, zb = z0 + sill, z0 + head
    # çerçeve: iki dikme, alt-üst kayıt
    for s in (fw / 2, L - fw / 2):
        p = at(a, u, nin, s, inset)
        frame.box((p[0], p[1], (za + zb) / 2), (fw, fd, zb - za), math.atan2(u[1], u[0]))
    for z in (za + fw / 2, zb - fw / 2):
        p = at(a, u, nin, L / 2, inset)
        frame.box((p[0], p[1], z), (L, fd, fw), math.atan2(u[1], u[0]))
    nm = max(0, int(L / mullion_every))
    for i in range(1, nm + 1):
        s = L * i / (nm + 1)
        p = at(a, u, nin, s, inset)
        frame.box((p[0], p[1], (za + zb) / 2), (0.05, fd, zb - za), math.atan2(u[1], u[0]))
    if sill > 0.3:  # yatay kayıt (vasistas)
        p = at(a, u, nin, L / 2, inset)
        frame.box((p[0], p[1], zb - 0.45), (L, fd, 0.045), math.atan2(u[1], u[0]))
    p = at(a, u, nin, L / 2, inset)
    glass_mb.box((p[0], p[1], (za + zb) / 2), (L - 0.04, 0.012, zb - za - 0.04), math.atan2(u[1], u[0]))
    if sill > 0.3 and sill_mb is not None:
        p = at(a, u, nin, L / 2, 0.0)
        sill_mb.box((p[0] + n_out[0] * 0.02, p[1] + n_out[1] * 0.02, za - 0.02), (L + 0.1, 0.24, 0.04),
                    math.atan2(u[1], u[0]))


def build_typical_floor(D, M, C, rnd):
    """1. kat nesneleri; 2–7. katlar koleksiyon örneği (instance) olarak çoğaltılır."""
    z0 = ZEMIN_H
    z1 = z0 + KAT_H
    nrm = D["normal"]
    enclosed = P(nrm["kapali"])
    slab = unary_union([P(p) for p in nrm["doseme"]])
    balconies = [P(b) for b in nrm["balkonlar"]]
    bal_zone = unary_union([b.buffer(0.06, join_style=2) for b in balconies])
    walls = unary_union([P(p) for p in nrm["duvarlar"]])
    rooms = [P(r) for r in nrm["odalar"]]

    kat = coll("Kat_Tipik", C)
    # duvarlar
    mb = MeshBuilder()
    mb.prism(walls, z0, z1 - DOSEME)
    wall_ob = mesh_obj("Kat_Duvarlar", mb.verts, mb.faces, [M["siva"], M["ic_duvar"], M["kaplama"]], kat)
    idx = classify_wall_faces(wall_ob.data, enclosed, bal_zone, 1, 0, 2)
    wall_ob.data.polygons.foreach_set("material_index", idx)

    openings = openings_outward(D, enclosed)
    cut, frame, gl, sills = MeshBuilder(), MeshBuilder(), MeshBuilder(), MeshBuilder()
    for a, b, tip, n_out in openings:
        sill, head = (0.0, KAPI_UST) if tip == "door" else (PENCERE_ALT, PENCERE_UST)
        L, u, nl = seg_frame(a, b)
        c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        cut.box((c[0], c[1], z0 + (sill + head) / 2 + (0.0 if sill > 0 else -0.05)),
                (L, 1.0, head - sill + (0 if sill > 0 else 0.1)), math.atan2(u[1], u[0]))
        window_parts(a, b, n_out, z0, sill, head, frame, gl, sills)
    apply_boolean(wall_ob, cut, "pencere")
    builder_obj(frame, "Kat_Dograma", M["dograma"], kat)
    builder_obj(gl, "Kat_Camlar", M["cam"], kat)
    builder_obj(sills, "Kat_Denizlik", M["denizlik"], kat)

    # döşeme (üstteki kat döşemesi): kenar bandı + alt yüz tavan
    mb = MeshBuilder()
    mb.prism(slab.buffer(0.03, join_style=2), z1 - DOSEME, z1)
    slab_ob = mesh_obj("Kat_Dosemesi", mb.verts, mb.faces, [M["doseme_bandi"], M["tavan"]], kat,
                       face_mat=lambda p: 1 if abs(p.normal.z) > 0.5 else 0)
    # zemin kaplamaları
    mb = MeshBuilder()
    for r in rooms:
        mb.prism(r, z0, z0 + 0.02)
    builder_obj(mb, "Kat_Ic_Zemin", M["parke_ic"], kat)
    mb = MeshBuilder()
    for bl in balconies:
        mb.prism(bl, z0, z0 + 0.03)
    builder_obj(mb, "Kat_Balkon_Zemin", M["balkon_zemin"], kat)

    # balkon korkulukları: cam panel + küpeşte + dikmeler
    rail, metal = MeshBuilder(), MeshBuilder()
    for bl in balconies:
        for a, b in edge_list(bl):
            L, u, nl = seg_frame(a, b)
            if L < 0.3:
                continue
            mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if enclosed.distance(mid) < 0.12:
                continue
            n_out = (-nl[0], -nl[1])  # edge_list: iç solda
            if slab.contains(Point(mid.x + n_out[0] * 0.3, mid.y + n_out[1] * 0.3)):
                continue
            a2 = at(a, u, nl, 0.04, 0.08)
            b2 = at(a, u, nl, L - 0.04, 0.08)
            rail.segment_box(a2, b2, z0 + 0.08, z0 + 1.02, 0.015)
            metal.segment_box(a2, b2, z0 + 1.02, z0 + 1.08, 0.06)
            metal.segment_box(a2, b2, z0 + 0.03, z0 + 0.09, 0.05)
            npost = max(1, int(L / 1.2))
            for i in range(npost + 1):
                p = at(a2, u, nl, (L - 0.08) * i / npost, 0)
                metal.box((p[0], p[1], z0 + 0.55), (0.04, 0.04, 1.05), math.atan2(u[1], u[0]))
    builder_obj(rail, "Kat_Korkuluk_Cam", M["korkuluk_cam"], kat)
    builder_obj(metal, "Kat_Kupeste", M["dograma"], kat)

    # 2..7. katlar: koleksiyon örnekleri
    for i in range(1, KAT_SAYISI):
        e = bpy.data.objects.new(f"Kat_{i + 1}", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = kat
        e.location = (0, 0, i * KAT_H)
        C.objects.link(e)

    # perdeler: her kat ve pencere için rastgele
    cur = MeshBuilder()
    for f in range(KAT_SAYISI):
        zf = z0 + f * KAT_H
        for a, b, tip, n_out in openings:
            if rnd.random() < 0.35:
                continue
            L, u, nl = seg_frame(a, b)
            nin = (-n_out[0], -n_out[1])
            d = 0.42
            zt = zf + (KAPI_UST + 0.15)
            for side in (0, 1):
                if rnd.random() < 0.3:
                    continue
                w = L * rnd.uniform(0.2, 0.5) + 0.2
                s0 = -0.1 if side == 0 else L + 0.1 - w
                pa = at(a, u, nin, s0, d)
                pb = at(a, u, nin, s0 + w, d)
                cur.segment_box(pa, pb, zf + 0.03, zt, 0.02)
            if rnd.random() < 0.25:  # tül
                pa, pb = at(a, u, nin, 0.0, d + 0.06), at(a, u, nin, L, d + 0.06)
                cur.segment_box(pa, pb, zf + 0.03, zt, 0.01)
    builder_obj(cur, "Perdeler", M["perde"], C)
    return kat


# ===================================================================== bina: zemin kat

def build_ground(D, M, C, rnd):
    z = D["zemin"]
    body = P(z["govde"])
    fins = [P(p) for p in z["teras_bolmeleri"]]
    ground_fp = unary_union([P(p) for p in z["ayak_izi"]])
    terraces = [P(t) for t in z["teraslar"]]
    walls = unary_union([P(p) for p in z["duvarlar"]] + fins)
    gap = P(D["normal"]["giris_boslugu"]) if D["normal"].get("giris_boslugu") else None
    gap_zone = gap.buffer(0.5) if gap is not None else Polygon()
    rooms = [P(r) for r in z["mekanlar"]]
    top = ZEMIN_H - DOSEME
    zc = coll("Zemin_Kat", C)

    mb = MeshBuilder()
    mb.prism(walls, 0.0, top)
    ob = mesh_obj("Zemin_Duvarlar", mb.verts, mb.faces, [M["zemin_kaplama"], M["ic_duvar"]], zc)
    ext = body.exterior
    idx = []
    for p in ob.data.polygons:
        c = Point(p.center.x, p.center.y)
        if abs(p.normal.z) > 0.5:
            idx.append(0)
        else:
            idx.append(0 if (ext.distance(c) < 0.04 or any(f.buffer(0.03).contains(c) for f in fins)) else 1)
    ob.data.polygons.foreach_set("material_index", idx)

    # vitrinler: gövdenin dış kenarları boyunca ~3.4 m'lik bölmeler
    cut, frame, gl = MeshBuilder(), MeshBuilder(), MeshBuilder()
    for a, b in edge_list(body):
        L, u, nl = seg_frame(a, b)
        if L < 1.6:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        n_out = (-nl[0], -nl[1])
        probe = Point(mid[0] + n_out[0] * 0.3, mid[1] + n_out[1] * 0.3)
        if any(f.buffer(0.05).contains(probe) for f in fins):
            continue
        in_gap = gap_zone.contains(Point(mid))
        if in_gap and abs(u[0]) > abs(u[1]):
            continue                      # giriş geçidinin yan duvarları kapalı
        if in_gap:
            bays, hgt = [(max(0.3, L / 2 - 1.0), min(L - 0.3, L / 2 + 1.0))], 2.7   # bina giriş kapısı
        else:
            nb = max(1, round(L / 3.4))
            w = L / nb
            bays = [(i * w + 0.22, (i + 1) * w - 0.22) for i in range(nb)]
            hgt = VITRIN_UST
        for s0, s1 in bays:
            if s1 - s0 < 0.6:
                continue
            pa, pb = at(a, u, nl, s0, 0), at(a, u, nl, s1, 0)
            c = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            cut.box((c[0], c[1], hgt / 2 - 0.05), (s1 - s0, 0.7, hgt + 0.1), math.atan2(u[1], u[0]))
            window_parts(pa, pb, n_out, 0.0, 0.0, hgt, frame, gl, None, mullion_every=1.6)
            # vitrin üst kaydı (kapı yüksekliği)
            p = at(pa, u, (-n_out[0], -n_out[1]), (s1 - s0) / 2, 0.09)
            frame.box((p[0], p[1], 2.55), (s1 - s0, 0.07, 0.05), math.atan2(u[1], u[0]))
    apply_boolean(ob, cut, "vitrin")
    builder_obj(frame, "Zemin_Dograma", M["dograma"], zc)
    builder_obj(gl, "Zemin_Vitrin_Cam", M["cam"], zc)

    # dükkan zeminleri, tavan döşemesi (teraslar dahil), tavan ışıkları
    mb = MeshBuilder()
    for r in rooms:
        mb.prism(r, 0.0, 0.03)
    builder_obj(mb, "Dukkan_Zeminleri", M["beton_ic"], zc)
    mb = MeshBuilder()
    for t in terraces:
        mb.prism(t, 0.0, 0.04)
    builder_obj(mb, "Teras_Zeminleri", M["parke"], zc)
    mb = MeshBuilder()
    mb.prism(ground_fp.buffer(0.05, join_style=2), top, ZEMIN_H)
    mesh_obj("Zemin_Tavan_Dosemesi", mb.verts, mb.faces, [M["doseme_bandi"], M["tavan"]], zc,
             face_mat=lambda p: 1 if p.normal.z < -0.5 else 0)
    lights = MeshBuilder()
    for r in rooms:
        if r.area < 30:
            continue
        x0, y0, x1, y1 = r.bounds
        for x in [x0 + 1.5 + i * 3.0 for i in range(int((x1 - x0 - 1.5) / 3.0) + 1)]:
            for y in [y0 + 1.5 + j * 3.0 for j in range(int((y1 - y0 - 1.5) / 3.0) + 1)]:
                if r.buffer(-0.6).contains(Point(x, y)):
                    lights.box((x, y, top - 0.02), (1.2, 0.12, 0.02))
    for t in terraces:  # saçak altı spotları
        x0, y0, x1, y1 = t.bounds
        for x in (x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.7):
            for y in (y0 + (y1 - y0) * 0.3, y0 + (y1 - y0) * 0.7):
                lights.box((x, y, top - 0.015), (0.14, 0.14, 0.02))
    builder_obj(lights, "Tavan_Isiklari", M["isik"], zc)

    # gezilemeyen teras: çakıl + parapet + harpuşta
    tower = unary_union([P(p) for p in D["normal"]["doseme"]])
    roof_area = ground_fp.difference(tower.buffer(0.02, join_style=2))
    mb = MeshBuilder()
    mb.prism(roof_area, ZEMIN_H, ZEMIN_H + 0.06)
    builder_obj(mb, "Gezilemeyen_Teras_Cakil", M["cakil"], zc)
    ring = ground_fp.buffer(0.05, join_style=2).difference(ground_fp.buffer(-0.2, join_style=2))
    ring = ring.difference(tower.buffer(0.05, join_style=2))
    mb = MeshBuilder()
    mb.prism(ring, ZEMIN_H, ZEMIN_H + 0.55)
    builder_obj(mb, "Teras_Parapeti", M["siva"], zc)
    mb = MeshBuilder()
    mb.prism(ring.buffer(0.03, join_style=2), ZEMIN_H + 0.55, ZEMIN_H + 0.6)
    builder_obj(mb, "Teras_Harpusta", M["harpusta"], zc)
    return terraces, body


def build_roof(D, M, C, rnd):
    tower = unary_union([P(p) for p in D["normal"]["doseme"]])
    core = P(D["normal"]["cekirdek"])
    rc = coll("Cati", C)
    mb = MeshBuilder()
    mb.prism(tower.buffer(-0.2, join_style=2), TOPLAM_H, TOPLAM_H + 0.06)
    builder_obj(mb, "Cati_Cakil", M["cakil"], rc)
    ring = tower.buffer(0.03, join_style=2).difference(tower.buffer(-0.2, join_style=2))
    mb = MeshBuilder()
    mb.prism(ring, TOPLAM_H, TOPLAM_H + 1.0)
    builder_obj(mb, "Cati_Parapeti", M["siva"], rc)
    mb = MeshBuilder()
    mb.prism(ring.buffer(0.03, join_style=2), TOPLAM_H + 1.0, TOPLAM_H + 1.06)
    builder_obj(mb, "Cati_Harpusta", M["harpusta"], rc)
    mb = MeshBuilder()
    mb.prism(core, TOPLAM_H, TOPLAM_H + 2.8)
    builder_obj(mb, "Merdiven_Asansor_Kulesi", M["siva"], rc)
    mb = MeshBuilder()
    mb.prism(core.buffer(0.12, join_style=2), TOPLAM_H + 2.8, TOPLAM_H + 3.0)
    builder_obj(mb, "Kule_Harpusta", M["harpusta"], rc)
    # klima dış üniteleri
    mb = MeshBuilder()
    inner = tower.buffer(-1.2, join_style=2).difference(core.buffer(1.0))
    cands = []
    x0, y0, x1, y1 = inner.bounds
    for i in range(400):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if inner.contains(Point(x, y)) and all(math.dist((x, y), c) > 1.8 for c in cands):
            cands.append((x, y))
        if len(cands) >= 10:
            break
    for x, y in cands:
        mb.box((x, y, TOPLAM_H + 0.06 + 0.35), (0.9, 0.35, 0.7), rnd.choice((0, math.pi / 2)))
    builder_obj(mb, "Klima_Uniteleri", M["klima"], rc)


# ===================================================================== çevre

def make_car_meshes(M):
    """Üç gövde tipi: sedan, hatchback, SUV (yan profil + pah + tekerlek)."""
    profiles = {
        "sedan": [(-2.3, 0.32), (2.3, 0.32), (2.38, 0.55), (2.28, 0.78), (1.15, 0.9), (0.45, 1.38),
                  (-0.95, 1.4), (-1.75, 1.0), (-2.32, 0.95), (-2.38, 0.55)],
        "hatch": [(-2.0, 0.32), (2.05, 0.32), (2.12, 0.55), (2.02, 0.8), (1.0, 0.92), (0.35, 1.42),
                  (-1.55, 1.44), (-1.98, 1.15), (-2.06, 0.55)],
        "suv": [(-2.3, 0.4), (2.3, 0.4), (2.38, 0.65), (2.3, 0.95), (1.25, 1.08), (0.6, 1.68),
                (-2.05, 1.7), (-2.32, 1.3), (-2.38, 0.65)],
    }
    meshes = {}
    for name, prof in profiles.items():
        w = 1.84 if name != "suv" else 1.9
        bm = bmesh.new()
        n = len(prof)
        vs_l = [bm.verts.new((x, -w / 2, z)) for x, z in prof]
        vs_r = [bm.verts.new((x, w / 2, z)) for x, z in prof]
        bm.faces.new(vs_l[::-1])
        bm.faces.new(vs_r)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vs_l[i], vs_l[j], vs_r[j], vs_r[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        # kabin üst kenarlarını içeri çek (tavan daralsın)
        belt = prof[4][1] if name != "suv" else prof[4][1]
        for v in bm.verts:
            if v.co.z > belt + 0.02:
                t = (v.co.z - belt) / (max(p[1] for p in prof) - belt)
                v.co.y *= 1 - 0.13 * t
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.07, segments=3, affect="EDGES", clamp_overlap=True)
        me = bpy.data.meshes.new("Arac_" + name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M["arac"])
        me.materials.append(M["arac_cam"])
        top_z = max(p[1] for p in prof)
        idx = []
        for p in me.polygons:
            c = p.center
            if c.z > belt + 0.05 and abs(p.normal.z) < 0.85 and c.z < top_z - 0.06:
                idx.append(1)
            else:
                idx.append(0)
        me.polygons.foreach_set("material_index", idx)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        meshes[name] = me
    # tekerlek
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.33, radius2=0.33, depth=0.22)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    wme = bpy.data.meshes.new("Arac_Teker")
    bm.to_mesh(wme)
    bm.free()
    wme.materials.append(M["lastik"])
    return meshes, wme


def place_car(C, meshes, wheel, kind, x, y, ang, rnd, coll_):
    me = meshes[kind]
    ob = bpy.data.objects.new("Arac", me)
    ob.location = (x, y, 0.0)
    ob.rotation_euler = (0, 0, ang)
    coll_.objects.link(ob)
    hl = 1.45 if kind != "hatch" else 1.3
    rz = 0.33
    for sx in (-hl, hl):
        for sy in (-0.8, 0.8):
            w = bpy.data.objects.new("Teker", wheel)
            w.parent = ob
            w.location = (sx, sy if kind != "suv" else sy * 1.03, rz)
            coll_.objects.link(w)
    return ob


def build_site(D, M, C, rnd, avoid=()):
    sc = coll("Cevre", C)
    parcel = Polygon(D["parsel"])
    ground_fp = unary_union([P(p) for p in D["zemin"]["ayak_izi"]])
    smid, su, sn = street_frame(D)
    st = D["cadde"]
    street_edge = LineString([st["a"], st["b"]])

    def strip(d0, d1, ext=1100):
        pts = [(smid[0] + su[0] * s + sn[0] * d, smid[1] + su[1] * s + sn[1] * d)
               for s, d in ((-ext, d0), (ext, d0), (ext, d1), (-ext, d1))]
        return Polygon(pts)
    world = box(-1200, -1200, 1200, 1200)
    sw1, road, sw2 = strip(0, 3.5), strip(3.5, 17.5), strip(17.5, 21)

    # ---- parsel dışı arazi
    terrain = world.difference(unary_union([parcel, sw1, road, sw2]).buffer(0.01))
    mb = MeshBuilder()
    mb.prism(terrain, -0.15, 0.0)
    builder_obj(mb, "Arazi", M["arazi"], sc)
    mb = MeshBuilder()
    mb.prism(road.intersection(world), -0.15, -0.02)
    builder_obj(mb, "Odunluk_Caddesi", M["asfalt"], sc)
    mb = MeshBuilder()
    mb.prism(unary_union([sw1, sw2]).intersection(world).difference(parcel), -0.15, 0.13)
    builder_obj(mb, "Kaldirimlar", M["parke"], sc)
    curb = MeshBuilder()
    for d in (3.5, 17.5):
        a = (smid[0] - su[0] * 1100 + sn[0] * d, smid[1] - su[1] * 1100 + sn[1] * d)
        b = (smid[0] + su[0] * 1100 + sn[0] * d, smid[1] + su[1] * 1100 + sn[1] * d)
        curb.segment_box(a, b, -0.05, 0.15, 0.18)
    builder_obj(curb, "Cadde_Bordurleri", M["bordur"], sc)
    paint = MeshBuilder()
    for s in range(-400, 400, 9):           # orta kesikli çizgi
        c0 = (smid[0] + su[0] * s + sn[0] * 10.5, smid[1] + su[1] * s + sn[1] * 10.5)
        c1 = (c0[0] + su[0] * 4.5, c0[1] + su[1] * 4.5)
        paint.segment_box(c0, c1, -0.02, -0.005, 0.15)
    for d in (4.0, 17.0):                   # kenar çizgileri
        a = (smid[0] - su[0] * 400 + sn[0] * d, smid[1] - su[1] * 400 + sn[1] * d)
        b = (smid[0] + su[0] * 400 + sn[0] * d, smid[1] + su[1] * 400 + sn[1] * d)
        paint.segment_box(a, b, -0.02, -0.006, 0.12)
    for k in range(9):                      # yaya geçidi (binanın güneyinde)
        s = -22 + 0.0
        off = 4.6 + k * 1.4
        c0 = (smid[0] + su[0] * s + sn[0] * off, smid[1] + su[1] * s + sn[1] * off)
        paint.box((c0[0], c0[1], -0.013), (3.0, 0.6, 0.014), math.atan2(su[1], su[0]))

    # ---- parsel içi
    edge_strip = parcel.difference(parcel.buffer(-1.8, join_style=2)).difference(street_edge.buffer(4.0))
    apron = ground_fp.buffer(2.2, join_style=2).intersection(parcel)
    front = parcel.intersection(street_edge.buffer(3.0))
    asphalt = parcel.difference(unary_union([edge_strip, apron, front]).buffer(0.01))
    paved = unary_union([apron, front]).intersection(parcel).difference(ground_fp.buffer(-0.05))
    mb = MeshBuilder()
    mb.prism(edge_strip, -0.15, 0.1)
    builder_obj(mb, "Yesil_Serit", M["cim"], sc)
    mb = MeshBuilder()
    mb.prism(asphalt, -0.15, 0.0)
    builder_obj(mb, "Otopark_Asfalt", M["asfalt"], sc)
    mb = MeshBuilder()
    mb.prism(paved, -0.15, 0.04)
    builder_obj(mb, "Bina_Cevresi_Parke", M["parke"], sc)
    cb = MeshBuilder()
    for g_ in (edge_strip,):
        for p in parts(g_):
            for a, b in edge_list(p):
                if math.dist(a, b) > 0.3:
                    cb.segment_box(a, b, -0.05, 0.16, 0.15)
    builder_obj(cb, "Bordurler", M["bordur"], sc)

    # otopark çizgileri ve araçlar
    car_meshes, wheel = make_car_meshes(M)
    cars = coll("Araclar", sc)
    for s in D["otopark"]:
        cx, cy = s["c"]
        Lp, Wp, ang = s["uzunluk"], s["genislik"], s["aci"]
        ux, uy = math.cos(ang), math.sin(ang)
        vx, vy = -uy, ux
        corners = [(cx + ux * Lp / 2 * i + vx * Wp / 2 * j, cy + uy * Lp / 2 * i + vy * Wp / 2 * j)
                   for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for k in range(4):
            paint.segment_box(corners[k], corners[(k + 1) % 4], 0.0, 0.008, 0.11)
        if rnd.random() < 0.68 and all(math.dist((cx, cy), a[:2]) > 12 for a in avoid):
            kind = rnd.choices(["sedan", "hatch", "suv"], [0.45, 0.35, 0.2])[0]
            flip = math.pi if rnd.random() < 0.5 else 0
            j = rnd.uniform(-0.15, 0.15)
            place_car(C, car_meshes, wheel, kind, cx + ux * j, cy + uy * j, ang + flip + rnd.uniform(-0.03, 0.03), rnd, cars)
    # caddede seyreden araçlar
    for s_, lane in ((-60, 7.0), (-14, 14.0), (35, 7.0), (75, 14.0), (120, 7.0)):
        x = smid[0] + su[0] * s_ + sn[0] * lane
        y = smid[1] + su[1] * s_ + sn[1] * lane
        ang = math.atan2(su[1], su[0]) + (0 if lane > 10 else math.pi)
        if all(math.dist((x, y), a[:2]) > 18 for a in avoid):
            place_car(C, car_meshes, wheel, rnd.choice(["sedan", "hatch", "suv"]), x, y, ang, rnd, cars)
    builder_obj(paint, "Yol_Cizgileri", M["boya"], sc)

    # ---- ağaçlar, çalılar, lambalar (Poly Haven)
    trees = load_trees()
    tpos = []
    ring = parcel.buffer(-0.9, join_style=2).exterior
    d = 2.0
    while d < ring.length:
        p = ring.interpolate(d)
        if street_edge.distance(p) > 6 and ground_fp.distance(p) > 4.5:
            tpos.append((p.x, p.y, rnd.uniform(1.3, 1.7)))
        d += rnd.uniform(8.0, 10.5)
    for s_ in range(-130, 131, 10):
        for off in (1.7, 19.3):
            p = (smid[0] + su[0] * s_ + sn[0] * off, smid[1] + su[1] * s_ + sn[1] * off)
            if off < 5 and (ground_fp.distance(Point(p)) < 9 or abs(s_ + 22) < 4):
                continue
            tpos.append((p[0], p[1], rnd.uniform(1.25, 1.5)))
    blocked = unary_union([parcel.buffer(2), sw1.buffer(1), road, sw2.buffer(1)])
    for _ in range(140):   # parsel dışındaki arazide dağınık ağaç kümeleri
        r_ = rnd.uniform(28, 170)
        th = rnd.uniform(0, 2 * math.pi)
        cx, cy = r_ * math.cos(th) - 15, r_ * math.sin(th)
        for _k in range(rnd.randint(1, 4)):
            x, y = cx + rnd.uniform(-6, 6), cy + rnd.uniform(-6, 6)
            if not blocked.contains(Point(x, y)):
                tpos.append((x, y, rnd.uniform(1.2, 1.9)))
    tpos = [t for t in tpos if all(math.dist(t[:2], a[:2]) > 9 for a in avoid)]
    tc = coll("Agaclar", sc)
    for x, y, s_ in tpos:
        src = rnd.choice(trees)
        e = bpy.data.objects.new("Agac", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = src
        e.location = (x, y, 0.08)
        e.rotation_euler = (0, 0, rnd.uniform(0, 2 * math.pi))
        e.scale = (s_, s_, s_ * rnd.uniform(0.95, 1.1))
        tc.objects.link(e)
    # çalılar: küçük ölçekli ağaç örnekleri yeşil şerit boyunca
    d = 1.0
    while d < ring.length:
        p = ring.interpolate(d)
        if street_edge.distance(p) > 6 and ground_fp.distance(p) > 3 and all(math.dist((p.x, p.y), t[:2]) > 3 for t in tpos):
            e = bpy.data.objects.new("Cali", None)
            e.instance_type = "COLLECTION"
            e.instance_collection = trees[1]
            e.location = (p.x, p.y, 0.0)
            e.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
            s_ = rnd.uniform(0.28, 0.38)
            e.scale = (s_, s_, s_ * 0.8)
            tc.objects.link(e)
        d += rnd.uniform(2.2, 3.2)

    lamp = load_single("street_lamp_01")
    lc = coll("Lambalar", sc)
    lpos = []
    for s_ in range(-120, 121, 24):
        lpos.append((smid[0] + su[0] * s_ + sn[0] * 3.0, smid[1] + su[1] * s_ + sn[1] * 3.0, math.atan2(sn[1], sn[0])))
    d = 7.0   # otopark lambaları: yeşil şerit üzerinde, ağaçların arasında
    while d < ring.length:
        p = ring.interpolate(d)
        if street_edge.distance(p) > 12 and ground_fp.distance(p) > 6 and all(math.dist((p.x, p.y), t[:2]) > 3 for t in tpos):
            lpos.append((p.x, p.y, rnd.uniform(0, 6.28)))
        d += 17.0
    for x, y, a in lpos:
        if any(math.dist((x, y), q[:2]) < 6 for q in avoid):
            continue
        e = bpy.data.objects.new("Lamba", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = lamp
        e.location = (x, y, 0.1)
        e.rotation_euler = (0, 0, a)
        e.scale = (1.5, 1.5, 1.5)
        lc.objects.link(e)
    return sc


def load_collection_from(path, coll_name, new_name):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [coll_name]
    c = dst.collections[0]
    c.name = new_name
    return c


def load_trees():
    out = []
    for name in ("island_tree_01", "island_tree_02"):
        path = os.path.join(MODEL, name, f"{name}_1k.blend")
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [f"{name}_LOD1"]
        ob = dst.objects[0]
        c = bpy.data.collections.new("Kaynak_" + name)
        c.objects.link(ob)
        ob.location = (0, 0, 0)
        out.append(c)
    return out


def load_single(name, objects=None):
    path = os.path.join(MODEL, name, f"{name}_1k.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if objects is None or n in objects]
    c = bpy.data.collections.new("Kaynak_" + name)
    for ob in dst.objects:
        if ob is not None:
            c.objects.link(ob)
    return c


def furnish_terraces(D, M, C, terraces, rnd):
    tset = load_single("outdoor_table_chair_set_01")
    planter = load_single("planter_box_01")
    fc = coll("Teras_Mobilya", C)
    hedge = MeshBuilder()
    for i, t in enumerate(terraces):
        x0, y0, x1, y1 = t.bounds
        if i % 2 == 0:  # her iki terastan birinde masa
            for k, (fx, fy) in enumerate(((0.35, 0.3), (0.65, 0.7))):
                e = bpy.data.objects.new("Masa", None)
                e.instance_type = "COLLECTION"
                e.instance_collection = tset
                e.location = (x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy, 0.04)
                e.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
                fc.objects.link(e)
        # caddeye bakan kenarda saksılar
        for fy in (0.18, 0.5, 0.82):
            e = bpy.data.objects.new("Saksi", None)
            e.instance_type = "COLLECTION"
            e.instance_collection = planter
            px, py = x1 - 0.45, y0 + (y1 - y0) * fy
            e.location = (px, py, 0.04)
            e.rotation_euler = (0, 0, math.pi / 2)
            fc.objects.link(e)
            for j in range(6):
                hedge.box((px + rnd.uniform(-0.12, 0.12), py + rnd.uniform(-0.35, 0.35), 0.5 + rnd.uniform(0, 0.15)),
                          (0.3, 0.3, 0.3), rnd.uniform(0, 6.28))
    ob = builder_obj(hedge, "Saksi_Bitkileri", M["cit"], fc)
    sub = ob.modifiers.new("yumusat", "SUBSURF")
    sub.levels = sub.render_levels = 2
    dsp = ob.modifiers.new("yaprak", "DISPLACE")
    tex = bpy.data.textures.new("yaprak_doku", "CLOUDS")
    tex.noise_scale = 0.06
    dsp.texture = tex
    dsp.strength = 0.08


def context_building(M, cc, cx, cy, w, dpt, fl, rot, rnd):
    """Temsili çevre binası: gövde, kat bantları, zemin kat bandı ve parapet."""
    h = fl * 3.0
    b = MeshBuilder()
    b.box((0, 0, h / 2), (w, dpt, h))
    ob = builder_obj(b, "Cevre_Bina", M["cevre_bina"], cc)
    ob.location = (cx, cy, 0)
    ob.rotation_euler = (0, 0, rot)
    t = MeshBuilder()
    for k in range(1, fl):
        t.box((0, 0, k * 3.0 + 0.05), (w + 0.24, dpt + 0.24, 0.22))
    t.box((0, 0, h + 0.45), (w + 0.1, dpt + 0.1, 0.9))
    t.box((0, 0, h + 0.05), (w - 0.6, dpt - 0.6, 0.1))
    tb = builder_obj(t, "Cevre_Bina_Bant", M["doseme_bandi"], cc)
    tb.location = (cx, cy, 0)
    tb.rotation_euler = (0, 0, rot)


def build_context(D, M, C, rnd, avoid=()):
    """Temsili çevre binaları: caddenin karşısı ve uzak çevre (gerçek komşuluk değildir)."""
    cc = coll("Cevre_Binalar", C)
    smid, su, sn = street_frame(D)
    parcel = Polygon(D["parsel"])
    rot = math.atan2(su[1], su[0])
    s_ = -110.0
    while s_ < 130:
        w = rnd.uniform(16, 24)
        dpt = rnd.uniform(12, 15)
        fl = rnd.choice((4, 5, 5, 6))
        off = 29 + dpt / 2
        cx = smid[0] + su[0] * (s_ + w / 2) + sn[0] * off
        cy = smid[1] + su[1] * (s_ + w / 2) + sn[1] * off
        if all(math.dist((cx, cy), a[:2]) > max(w, dpt) / 2 + 22 for a in avoid):
            context_building(M, cc, cx, cy, w, dpt, fl, rot, rnd)
        s_ += w + rnd.uniform(10, 18)
    for cx, cy, w, dpt, fl in ((-35, -78, 22, 14, 5), (8, -82, 18, 14, 6), (-110, -22, 16, 20, 4),
                               (-115, 28, 18, 14, 5), (-55, 58, 30, 16, 4), (0, 62, 24, 18, 6), (-80, -55, 20, 14, 4)):
        if parcel.buffer(10).intersects(box(cx - w / 2, cy - dpt / 2, cx + w / 2, cy + dpt / 2)):
            continue
        if any(math.dist((cx, cy), a[:2]) < max(w, dpt) / 2 + 22 for a in avoid):
            continue
        context_building(M, cc, cx, cy, w, dpt, fl, 0.0, rnd)


# ===================================================================== ışık, kamera, render

def setup_world(strength=1.0, hdri=HDRI, sun=HDRI_SUN, heading=SUN_HEADING):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("HDRI")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    delta = heading - sun[0]
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(-delta))
    env = N.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdri, check_existing=True)
    bg = N.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = N.new("ShaderNodeOutputWorld")
    L.new(tc.outputs["Generated"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], env.inputs["Vector"])
    L.new(env.outputs["Color"], bg.inputs["Color"])
    L.new(bg.outputs["Background"], out.inputs["Surface"])
    try:
        w.cycles.sampling_method = "MANUAL"
        w.cycles.sample_map_resolution = 4096
    except Exception:
        pass
    return bg


def setup_dusk(D, M, rnd):
    """Akşam: kısık gökyüzü, rastgele aydınlık daireler, yanık sokak lambaları."""
    setup_world(0.16, HDRI_AKSAM, HDRI_AKSAM_SUN, AKSAM_HEADING)
    M["isik"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 16.0
    nrm = D["normal"]
    rooms = [(P(r), r["ad"]) for r in nrm["odalar"]]
    mb = MeshBuilder()
    for f in range(KAT_SAYISI):
        ztop = ZEMIN_H + f * KAT_H + KAT_H - DOSEME
        for r, ad in rooms:
            if r.area < 3 or any(k in ad for k in ("ASANS", "RIHT", "AFTLAR")):
                continue
            if rnd.random() > 0.55:
                continue
            c = r.representative_point()
            x0, y0, x1, y1 = r.bounds
            sz = max(0.35, min(0.9, 0.25 * min(x1 - x0, y1 - y0)))
            mb.box((c.x, c.y, ztop - 0.015), (sz, sz, 0.02))
    builder_obj(mb, "Daire_Isiklari", M["oda_isigi"], bpy.context.scene.collection)
    for ob in bpy.data.objects:
        if ob.name.startswith("Cevre_Bina") and ob.type == "MESH" and ob.data.materials and \
                ob.data.materials[0] == M["cevre_bina"]:
            ob.data.materials[0] = M["cevre_bina_gece"]
    for m in bpy.data.materials:
        if m.name.startswith("street_lamp_01_bulb") and m.node_tree:
            bs = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
            for b in bs:
                b.inputs["Emission Color"].default_value = (1.0, 0.78, 0.5, 1)
                b.inputs["Emission Strength"].default_value = 60.0
    lc = bpy.data.collections.get("Lambalar")
    if lc:
        for e in lc.objects:
            ld = bpy.data.lights.new("Lamba_Isigi", "POINT")
            ld.energy = 260
            ld.color = (1.0, 0.78, 0.52)
            ld.shadow_soft_size = 0.15
            lo = bpy.data.objects.new("Lamba_Isigi", ld)
            lo.location = (e.location.x, e.location.y, e.location.z + 3.3 * e.scale.z)
            bpy.context.scene.collection.objects.link(lo)


def setup_render(samples, scale):
    import addon_utils
    addon_utils.enable("cycles", default_set=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.015
    cy.use_denoising = True
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    cy.max_bounces = 8
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.transparent_max_bounces = 24
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.8
    cy.sample_clamp_indirect = 8.0
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except Exception:
            pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.resolution_percentage = int(100 * scale)


def camera(name, loc, target, lens=35, shift=(0, 0), ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.sensor_width = 36
    cd.shift_x, cd.shift_y = shift
    cd.clip_end = 3000
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


WEB_COLORS = {
    "Cephe_Sivasi": (0.86, 0.84, 0.8), "Balkon_Terrakota_Kaplama": (0.42, 0.2, 0.13),
    "Zemin_Kat_Panel": (0.1, 0.1, 0.11), "Asfalt": (0.16, 0.16, 0.17), "Beton_Parke": (0.52, 0.51, 0.49),
    "Cim": (0.2, 0.33, 0.12), "Arazi": (0.25, 0.36, 0.17), "Cakil": (0.45, 0.44, 0.41),
}
CAR_WEB = [(0.85, 0.85, 0.85), (0.6, 0.61, 0.63), (0.03, 0.03, 0.035), (0.22, 0.23, 0.25),
           (0.04, 0.08, 0.22), (0.5, 0.04, 0.04), (0.75, 0.73, 0.68)]


def export_web_glb(path, M, rnd):
    """Görüntüleyici için: örnekleri gerçek nesneye çevir, ağır modelleri hafifleriyle değiştir,
    dokulu malzemeleri düz renge indir ve GLB yaz."""
    sc = bpy.context.scene
    # örnekleri (kat kopyaları, ağaç, lamba, mobilya) gerçek nesnelere dönüştür
    tree_spots, lamp_spots = [], []
    for ob in list(sc.objects):
        if ob.type == "EMPTY" and ob.instance_type == "COLLECTION" and ob.instance_collection:
            cname = ob.instance_collection.name
            if cname.startswith("Kaynak_island_tree"):
                tree_spots.append((ob.location.copy(), ob.scale.z))
                bpy.data.objects.remove(ob)
            elif cname.startswith("Kaynak_street_lamp"):
                lamp_spots.append(ob.location.copy())
                bpy.data.objects.remove(ob)
            elif cname.startswith("Kaynak_outdoor") or cname.startswith("Kaynak_planter"):
                bpy.data.objects.remove(ob)
            else:  # kat kopyaları
                for src in ob.instance_collection.objects:
                    cp = src.copy()
                    cp.data = src.data
                    cp.location = src.location + ob.location
                    sc.collection.objects.link(cp)
                bpy.data.objects.remove(ob)
    # hafif ağaç ve lamba
    tr, cr, lp = MeshBuilder(), MeshBuilder(), MeshBuilder()
    bmi = bmesh.new()
    bmesh.ops.create_icosphere(bmi, subdivisions=1, radius=1.0)
    iv = [tuple(v.co) for v in bmi.verts]
    ifc = [tuple(v.index for v in f.verts) for f in bmi.faces]
    bmi.free()
    for loc, s_ in tree_spots:
        if s_ < 0.6:   # çalı
            cr.add([(loc.x + x * 0.9, loc.y + y * 0.9, 0.5 + z * 0.55) for x, y, z in iv], ifc)
            continue
        h = 2.2 * s_
        tr.box((loc.x, loc.y, h / 2), (0.3, 0.3, h))
        for k in range(3):
            ox, oy = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
            r = rnd.uniform(1.4, 2.0) * s_ / 1.5
            cr.add([(loc.x + ox + x * r, loc.y + oy + y * r, h + 0.8 + z * r * 0.8) for x, y, z in iv], ifc)
    for loc in lamp_spots:
        lp.box((loc.x, loc.y, 2.8), (0.14, 0.14, 5.6))
        lp.box((loc.x, loc.y, 5.6), (0.45, 0.45, 0.5))
    builder_obj(tr, "Web_Agac_Govde", plain("Web_Govde", (0.2, 0.15, 0.1), 0.9), sc.collection)
    builder_obj(cr, "Web_Agac_Tac", plain("Web_Tac", (0.16, 0.26, 0.08), 0.9), sc.collection)
    builder_obj(lp, "Web_Lamba", M["dograma"], sc.collection)
    for c in list(bpy.data.collections):
        if c.name.startswith("Kaynak_"):
            for o in list(c.objects):
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
    # dokulu malzemeleri düz renge çevir
    flat = {}
    for m in list(bpy.data.materials):
        base = m.name.split(".")[0]
        if base in WEB_COLORS:
            flat[m.name] = plain("Web_" + base, WEB_COLORS[base], 0.8)
    car_mats = [plain(f"Web_Arac_{i}", c, 0.3, 0.3) for i, c in enumerate(CAR_WEB)]
    for ob in sc.objects:
        if ob.type != "MESH":
            continue
        for slot in ob.material_slots:
            old = slot.material
            if old is None:
                continue
            new = None
            if old.name in flat:
                new = flat[old.name]
            elif old.name == "Arac_Boya":
                new = rnd.choice(car_mats)
            elif old.name.startswith("Cevre_Bina"):
                new = flat.setdefault("_cevre", plain("Web_Cevre", (0.78, 0.75, 0.7), 0.8))
            if new is not None:
                slot.link = "OBJECT"
                slot.material = new
    # zemini ve yolu parsel çevresine kırp
    x0, x1, y0, y1 = -190, 160, -160, 160
    for ob in sc.objects:
        if ob.type != "MESH" or ob.name not in ("Arazi", "Odunluk_Caddesi", "Kaldirimlar", "Cadde_Bordurleri", "Yol_Cizgileri"):
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        for co, no in (((x0, 0, 0), (-1, 0, 0)), ((x1, 0, 0), (1, 0, 0)), ((0, y0, 0), (0, -1, 0)), ((0, y1, 0), (0, 1, 0))):
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, clear_outer=True)
        bm.to_mesh(ob.data)
        bm.free()
    for ob in sc.objects:
        ob.select_set(ob.type == "MESH" and not ob.name.endswith("_kesici"))
    import addon_utils
    addon_utils.enable("io_scene_gltf2", default_set=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="NONE")
    print("Web GLB:", path, f"{os.path.getsize(path) / 1e6:.1f} MB", flush=True)


def main():
    args = parse_args()
    rnd = random.Random(args.seed)
    with open(args.json, encoding="utf-8") as fh:
        D = json.load(fh)
    os.makedirs(args.out, exist_ok=True)
    out = os.path.abspath(args.out)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = make_materials()

    smid, su, sn = street_frame(D)
    goz = eye_camera_pos(D)
    teras_kam = (23.5, -13.0, 1.65)

    B = coll("Bina")
    build_typical_floor(D, M, B, rnd)
    terraces, body = build_ground(D, M, B, rnd)
    build_roof(D, M, B, rnd)
    furnish_terraces(D, M, B, terraces, rnd)
    build_site(D, M, bpy.context.scene.collection, rnd, avoid=[goz, teras_kam])

    setup_world(1.0)
    setup_render(args.samples, args.scale)

    cams = {
        "cadde": (smid[0] + 46, -56, 33), "otopark": (-66, -56, 40), "kuzey": (smid[0] + 40, 62, 30),
    }
    views = {
        "cadde": (camera("Kamera_Cadde_Kusbakisi", cams["cadde"], (1, 1, 10.5), lens=33), "01_cadde_kusbakisi.png"),
        "otopark": (camera("Kamera_Otopark_Kusbakisi", cams["otopark"], (-8, 2, 9), lens=30), "02_otopark_kusbakisi.png"),
        "goz": (camera("Kamera_Cadde_Goz_Hizasi", goz, (-3, 1, 12.5), lens=20, shift=(0, 0.08)), "03_cadde_goz_hizasi.png"),
        "teras": (camera("Kamera_Dukkan_Teraslari", teras_kam, (11, 3, 4.6), lens=20, shift=(0, 0.06)), "04_dukkan_teraslari.png"),
        "kuzey": (camera("Kamera_Kuzeydogu", cams["kuzey"], (-2, 0, 11), lens=33), "05_kuzeydogu_kusbakisi.png"),
        "aksam": (camera("Kamera_Aksam_Goz", goz, (-3, 1, 12.5), lens=20, shift=(0, 0.08)), "06_aksam_goz_hizasi.png"),
        "aksam_kus": (camera("Kamera_Aksam_Kus", cams["cadde"], (1, 1, 10.5), lens=33), "07_aksam_kusbakisi.png"),
    }
    build_context(D, M, bpy.context.scene.collection, rnd, avoid=list(cams.values()) + [goz])
    sel = [v for v in args.only.split(",") if v] or list(views)
    if args.web_glb:
        export_web_glb(os.path.abspath(args.web_glb), M, rnd)
        return
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "proje_gercekci.blend"), relative_remap=True, compress=True)
    if args.no_render:
        return
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sel = [k for k in sel if not k.startswith("aksam")] + [k for k in sel if k.startswith("aksam")]
    dusk = False
    for key in sel:
        if key.startswith("aksam") and not dusk:
            setup_dusk(D, M, rnd)
            sc.view_settings.exposure = 0.6
            dusk = True
        cam, fname = views[key]
        sc.camera = cam
        sc.render.filepath = os.path.join(out, fname)
        bpy.ops.render.render(write_still=True)
        print("Render:", sc.render.filepath, flush=True)


if __name__ == "__main__":
    main()
