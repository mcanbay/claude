"""
GLB modelini SketchUp'ın doğrudan içe aktarabildiği Collada (.dae) dosyasına çevirir.

    python dae_yaz.py cikti/proje_kutle.glb cikti/proje_kutle.dae

Her nesne kendi adıyla ayrı bir geometri/düğüm olur; malzemeler düz renk olarak taşınır.
Eksen Z yukarı, birim metredir (SketchUp ile aynı).
"""

import sys

import collada
import numpy as np
import trimesh
from collada import asset, geometry, material, scene, source


def color_of(mesh):
    try:
        m = mesh.visual.material
        if hasattr(m, "baseColorFactor") and m.baseColorFactor is not None:
            c = np.asarray(m.baseColorFactor, float)
            if c.max() > 1.0:
                c = c / 255.0
            return tuple(c[:3]) + (float(c[3]) if len(c) > 3 else 1.0,)
        if hasattr(m, "diffuse"):
            c = np.asarray(m.diffuse, float) / 255.0
            return tuple(c[:4])
    except Exception:
        pass
    return (0.8, 0.8, 0.8, 1.0)


def glb_to_dae(src, dst):
    sc = trimesh.load(src, force="scene")
    dae = collada.Collada()
    dae.assetInfo.upaxis = asset.UP_AXIS.Z_UP
    dae.assetInfo.unitname = "meter"
    dae.assetInfo.unitmeter = 1.0
    nodes = []
    mats = {}
    for i, name in enumerate(sc.graph.nodes_geometry):
        T, gname = sc.graph[name]
        mesh = sc.geometry[gname].copy()
        mesh.apply_transform(T)
        # glTF Y-yukarı -> Z-yukarı: (x, y, z) -> (x, -z, y)
        v = mesh.vertices
        verts = np.column_stack([v[:, 0], -v[:, 2], v[:, 1]]).astype(np.float32)
        faces = np.asarray(mesh.faces, np.int32)
        if len(faces) == 0:
            continue
        rgba = color_of(mesh)
        key = tuple(round(c, 3) for c in rgba)
        if key not in mats:
            mid = f"mat{len(mats)}"
            eff = material.Effect(f"{mid}-fx", [], "lambert", diffuse=rgba,
                                  transparency=rgba[3] if rgba[3] < 1 else None)
            mat = material.Material(mid, mid, eff)
            dae.effects.append(eff)
            dae.materials.append(mat)
            mats[key] = mat
        mat = mats[key]
        normals = mesh.face_normals.astype(np.float32)
        normals = np.column_stack([normals[:, 0], -normals[:, 2], normals[:, 1]])
        gid = f"geom{i}"
        vsrc = source.FloatSource(f"{gid}-v", verts.ravel(), ("X", "Y", "Z"))
        nsrc = source.FloatSource(f"{gid}-n", normals.ravel(), ("X", "Y", "Z"))
        geom = geometry.Geometry(dae, gid, str(name), [vsrc, nsrc])
        il = source.InputList()
        il.addInput(0, "VERTEX", f"#{gid}-v")
        il.addInput(1, "NORMAL", f"#{gid}-n")
        fn = np.repeat(np.arange(len(faces)), 3)
        idx = np.column_stack([faces.ravel(), fn]).ravel()
        geom.primitives.append(geom.createTriangleSet(idx, il, "m"))
        dae.geometries.append(geom)
        mn = scene.MaterialNode("m", mat, inputs=[])
        gn = scene.GeometryNode(geom, [mn])
        nodes.append(scene.Node(str(name).replace(" ", "_"), children=[gn]))
    myscene = scene.Scene("Sahne", nodes)
    dae.scenes.append(myscene)
    dae.scene = myscene
    dae.write(dst)
    return len(nodes)


if __name__ == "__main__":
    n = glb_to_dae(sys.argv[1], sys.argv[2])
    print(f"{n} nesne yazıldı: {sys.argv[2]}")
