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

# 2) instancias con su transformada de colocacion original
for i, (mi, mat) in enumerate(kit["instances"]):
    ob = bpy.data.objects.new(f"PART{i:03d}", bm[mi])
    sc.collection.objects.link(ob)
    ob.matrix_world = Matrix(mat)

# 3) normalizar: centrado xy, suelo en 0, altura EXACTA H (escala uniforme)
bb = kit["bbox"]
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
print("GEN_OK", json.dumps({
    "params": {"H": H, "S": round(S, 5)},
    "counts": {"PARTS": kit["n_instances"], "UNIQ": kit["n_unique"]},
    "base_predicha": round(base_pred, 2),
}))
