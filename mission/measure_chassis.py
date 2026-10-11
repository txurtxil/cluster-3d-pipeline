"""measure_chassis.py — metrologia del chasis cluster 2x BC250.
Imprime MEASURE_JSON { dims, counts, supports_spacing_mm, fan_holes }.
Convencion: 1 BU = 1 mm. Medir por vertices evaluados (nunca bound_box).
"""
import bpy
import json
import sys

dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"}))
    sys.exit(0)

xs, ys, zs = [], [], []
uniq = set()
bad = 0
for o in objs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    ws = [ev.matrix_world @ v.co for v in me.vertices]
    for w in ws:
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    uniq.add(o.data.name)
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    bad += sum(1 for v in ec.values() if v != 2)
    ev.to_mesh_clear()

# spacing de apoyos de placa (canales C0/C1): distancia x entre postes opuestos
sup = [o for o in objs if o.name.startswith("Apoyo")]
sup_x = sorted(set(round(o.location.x, 2) for o in sup))
sup_spacing = round(sup_x[-1] - sup_x[0], 2) if len(sup_x) >= 2 else None

print("MEASURE_JSON " + json.dumps({
    "dims": {"X": round(max(xs) - min(xs), 2), "Y": round(max(ys) - min(ys), 2),
             "Z": round(max(zs) - min(zs), 2)},
    "counts": {"PARTS": len(objs), "UNIQ": len(uniq),
               "supports": len(sup)},
    "supports_spacing_mm": sup_spacing,
    "manifold": {"ok": bad == 0, "bad_edges": bad},
}))
