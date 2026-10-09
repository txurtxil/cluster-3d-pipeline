"""measure_tower.py — Metrologia de la torre (autoridad geometrica).
Uso: blender -b <torre.blend> -P measure_tower.py
Imprime: MEASURE_JSON { dims, counts, manifold, NOT_MEASURED }
"""
import bpy
import json
import sys
from mathutils import Vector

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"}))
    sys.exit(0)

# Leccion 9-oct (§36): bound_box de un objeto rotado es la bbox de su
# CUADRADO circunscrito local: sobrestima cilindros inclinados hasta x sqrt(2)
# (visto fisicamente: 300.316 vs 300.000). Se mide desde los VERTICES REALES.
dg = bpy.context.evaluated_depsgraph_get()
xs, ys, zs = [], [], []
leg_x = []   # BASE = envolvente de PATAS (las zapatas ensanchan la huella;
             # esa huella total queda en NOT_MEASURED)
PREFIX = {"LEGS": "LEG", "PADS": "PAD", "PLATFORMS": "PLAT", "BARS": "BAR",
          "RINGS": "RING", "ARCHES": "ARCH", "CROWN": "CROWN", "SPIRE": "SPIRE",
          "SPRINGS": "SPRING", "RAILS": "RAIL", "RAILPOSTS": "RPOST",
          "CORNICES": "CORN"}
counts = {k: 0 for k in PREFIX}
bad_total, worst = 0, ("", 0)
for o in objs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    is_leg = o.name.startswith("LEG")
    for v in me.vertices:
        w = ev.matrix_world @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
        if is_leg:
            leg_x.append(w.x)
    ev.to_mesh_clear()
    for k, pre in PREFIX.items():
        if o.name.startswith(pre):
            counts[k] += 1
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    bad = sum(1 for v in ec.values() if v != 2)
    bad_total += bad
    if bad > worst[1]:
        worst = (o.name, bad)

# v4: patas = nº de indices de pata unicos (LEG0s3, LEG0s4... -> pata 0)
import re as _re
_leg_ids = set()
for o in objs:
    m = _re.match(r"LEG(\d+)", o.name)
    if m:
        _leg_ids.add(m.group(1))
counts["LEGS"] = len(_leg_ids)
dims = {"H": round(max(zs) - min(zs), 3),
        "BASE": round(max(leg_x) - min(leg_x), 3)}
print("MEASURE_JSON " + json.dumps({
    "dims": dims,
    "counts": counts,
    "manifold": {"ok": bad_total == 0, "bad_edges": bad_total,
                 "worst_object": worst[0], "components": len(objs)},
    "NOT_MEASURED": ["footprint_incl_pads", "lattice_spacing", "leg_wall",
                     "arch_opening_dims", "zone_density_2d"],
}))
