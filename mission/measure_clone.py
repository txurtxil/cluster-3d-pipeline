"""measure_clone.py — metrologia del clon (autoridad geometrica).
Imprime MEASURE_JSON { dims, counts, manifold }
"""
import bpy
import json
import sys
from mathutils import Vector

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"}))
    sys.exit(0)

dg = bpy.context.evaluated_depsgraph_get()
xs, ys, zs = [], [], []
bad = 0
uniq = set()
for o in objs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    for v in me.vertices:
        w = ev.matrix_world @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    ev.to_mesh_clear()
    uniq.add(o.data.name)
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    bad += sum(1 for v in ec.values() if v != 2)

print("MEASURE_JSON " + json.dumps({
    "dims": {"H": round(max(zs) - min(zs), 3), "BASE": round(max(xs) - min(xs), 3)},
    "counts": {"PARTS": len(objs), "UNIQ": len(uniq)},
    "manifold": {"ok": bad == 0, "bad_edges": bad},
    "NOT_MEASURED": ["internal_fit", "feature_positions"],
}))
