"""measure_box.py — Metrologia 3D de la caja (autoridad geometrica, spec §14).
Uso: blender -b <modelo.blend> -P measure_box.py
Imprime una linea: MEASURE_JSON { ... }
Mide: dims (bbox), paredes por ray-casting en las 4 caras (independiente
de los parametros del generador), manifold, componentes.
Lo que NO mide lo declara (regla anti-alucinacion §34).
"""
import bpy
import json
import sys
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"}))
    sys.exit(0)

box = max(objs, key=lambda o: len(o.data.vertices))

# --- bbox mundial
verts = [box.matrix_world @ v.co for v in box.data.vertices]
xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
bmin = Vector((min(xs), min(ys), min(zs)))
bmax = Vector((max(xs), max(ys), max(zs)))
dims = bmax - bmin

# --- manifold + componentes
edge_count = {}
for p in box.data.polygons:
    for e in p.edge_keys:
        edge_count[e] = edge_count.get(e, 0) + 1
bad_edges = sum(1 for v in edge_count.values() if v != 2)
components = len(objs)

# --- grosor de pared por ray-casting (4 caras, a H/2, en y=0 / x=0)
# Origen fuera, direccion hacia dentro; 1er impacto = cara ext., 2o = cara int.
def wall_thickness(origin, direction):
    o = Vector(origin); d = Vector(direction)
    hits = []
    for _ in range(4):
        ok, loc, _, _, _, _ = bpy.context.scene.ray_cast(dg, o, d)
        if not ok:
            break
        hits.append(loc.copy())
        o = loc + d * 0.01   # re-lanzar tras el impacto
    if len(hits) >= 2:
        return float((hits[1] - hits[0]).dot(Vector(d).normalized()))
    return None

L, W, H = dims.x, dims.y, dims.z
zmid = H / 2
walls = {
    "-X": wall_thickness((bmin.x - 5, 0, zmid), (1, 0, 0)),
    "+X": wall_thickness((bmax.x + 5, 0, zmid), (-1, 0, 0)),
    "-Y": wall_thickness((0, bmin.y - 5, zmid), (0, 1, 0)),
    "+Y": wall_thickness((0, bmax.y + 5, zmid), (0, -1, 0)),
}
vals = [v for v in walls.values() if v is not None]

print("MEASURE_JSON " + json.dumps({
    "dims": {"L": round(L, 3), "W": round(W, 3), "H": round(H, 3)},
    "walls": {k: (round(v, 3) if v is not None else None) for k, v in walls.items()},
    "wall_min": round(min(vals), 3) if vals else None,
    "wall_max": round(max(vals), 3) if vals else None,
    "manifold": {"ok": bad_edges == 0 and components == 1, "bad_edges": bad_edges,
                 "components": components},
    "NOT_MEASURED": ["holes_count", "usbc_dims", "normals_orientation"],
}))
