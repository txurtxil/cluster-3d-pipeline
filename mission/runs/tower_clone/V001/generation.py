"""gen_clone.py — Clon parametrico fiel de la torre de referencia (Ruta B).
Reconstruye la torre instanciando el KIT extraido del Eiffel_Resin_09.blend
(50 piezas unicas / 334 instancias) y la normaliza a altura H exacta.
Uso: blender -b --factory-startup -P gen_clone.py -- <params.json> <out.blend> <out.stl>
Parametros: H (altura objetivo mm), KIT (ruta al kit json).
"""
import bpy
import json
import sys
from mathutils import Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]
H = float(P.get("H", 300.0))
KIT = P.get("KIT", "/home/txurtxil/cluster-3d-pipeline/mission/kit_eiffel.json")

kit = json.load(open(KIT))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# 1) mallas unicas (datos enlazados -> memoria eficiente, como el original)
bm = []
for m in kit["meshes"]:
    me = bpy.data.meshes.new(m["name"])
    me.from_pydata(m["verts"], [], m["faces"])
    me.update()
    bm.append(me)

# 2) seleccion de la estructura principal (el .blend contiene piezas
# sueltas: una torre pequena y un ornamento). Criterio: conservar las piezas
# cuyo centroide 2D esta cerca del eje de la pieza MAS ALTA (la aguja de la
# torre principal). Radio = 0.35 x altura del modelo (~medio ancho torre).
import math as _m
cents3 = []
for mi, mat in kit["instances"]:
    c = kit["meshes"][mi]["center"]
    v = Matrix(mat) @ __import__("mathutils").Vector((c[0], c[1], c[2]))
    cents3.append(v)
zs_all = [v.z for v in cents3]
span_z = max(zs_all) - min(zs_all)
i_top = max(range(len(cents3)), key=lambda i: cents3[i].z)
R = 0.35 * span_z
keep = {i for i, v in enumerate(cents3)
        if _m.hypot(v.x - cents3[i_top].x, v.y - cents3[i_top].y) <= R}

for i, (mi, mat) in enumerate(kit["instances"]):
    if i not in keep:
        continue
    ob = bpy.data.objects.new(f"PART{i:03d}", bm[mi])
    sc.collection.objects.link(ob)
    ob.matrix_world = Matrix(mat)
n_kept = len(keep)

# 3) normalizar: centrado xy, suelo en 0, altura EXACTA H (escala uniforme)
#    bbox SOLO del cluster principal (medido de los objetos creados)
zs_k, xs_k, ys_k = [], [], []
for o in sc.objects:
    if o.type != "MESH":
        continue
    for c in o.bound_box:
        w = o.matrix_world @ __import__("mathutils").Vector(c)
        xs_k.append(w.x); ys_k.append(w.y); zs_k.append(w.z)
bb = {"x": [min(xs_k), max(xs_k)], "y": [min(ys_k), max(ys_k)],
      "z": [min(zs_k), max(zs_k)]}
span = bb["z"][1] - bb["z"][0]
S = H / span
cx = (bb["x"][0] + bb["x"][1]) / 2.0
cy = (bb["y"][0] + bb["y"][1]) / 2.0

bpy.ops.object.empty_add(location=(0, 0, 0))
root = bpy.context.active_object
root.name = "TOWER_ROOT"
for o in list(sc.objects):
    if o == root or o.type == "EMPTY":
        continue
    if o.parent is None:
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw
root.scale = (S, S, S)
root.location = (-cx * S, -cy * S, -bb["z"][0] * S)

# 4) exportar
bpy.ops.object.select_all(action="SELECT")
bpy.ops.wm.stl_export(filepath=OUT_STL)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

base_pred = (bb["x"][1] - bb["x"][0]) * S
uniq_kept = len({kit["instances"][i][0] for i in keep})
print("GEN_OK", json.dumps({
    "params": {"H": H, "S": round(S, 5)},
    "counts": {"PARTS": n_kept, "UNIQ": uniq_kept},
    "base_predicha": round(base_pred, 2),
}))
