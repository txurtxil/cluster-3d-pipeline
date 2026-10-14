"""measure_generic.py — Metrologia generica para piezas /nueva (fase QWEN3-100).
Uso: blender -b <modelo.blend> -P measure_generic.py
Reporta bbox (L/W/H), manifold y componentes. Declara lo especifico como
no medido: la validacion fina llega cuando la pieza se registra como familia.
"""
import bpy, json, sys

dg = bpy.context.evaluated_depsgraph_get()
meshes = [o.evaluated_get(dg) for o in bpy.context.scene.objects if o.type == "MESH"]
piece = [o for o in meshes if o.name != "fiduciales" and len(o.data.vertices) > 0]
if not piece:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"})); sys.exit(0)

allv = []
for o in piece:
    allv += [o.matrix_world @ v.co for v in o.data.vertices]

manifold_all = True
for o in piece:
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    if any(v != 2 for v in ec.values()):
        manifold_all = False

xs = [v.x for v in allv]; ys = [v.y for v in allv]; zs = [v.z for v in allv]
print("MEASURE_JSON " + json.dumps({
    "dims": {"L": round(max(xs) - min(xs), 2), "W": round(max(ys) - min(ys), 2),
             "H": round(max(zs) - min(zs), 2)},
    "manifold": {"ok": manifold_all}, "components": len(piece),
    "not_measured": ["metrologia especifica: la pieza aun no es familia registrada"],
}))
