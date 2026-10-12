"""measure_taza.py — Metrologia 3D de la taza (autoridad geometrica).
Uso: blender -b <modelo.blend> -P measure_taza.py
Imprime: MEASURE_JSON { ... }
Mide por vertices del mesh evaluado (nunca bound_box, leccion 3) y ray-casting.
Lo que NO puede medir lo declara (regla anti-alucinacion).
"""
import bpy, json, sys, math
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
meshes = [o.evaluated_get(dg) for o in bpy.context.scene.objects if o.type == "MESH"]
meshes = [o for o in meshes if len(o.data.vertices) > 0]
if not meshes:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"})); sys.exit(0)

# vertices mundo de TODOS los shells (asisa posible separada)
allv = []
for o in meshes:
    allv += [o.matrix_world @ v.co for v in o.data.vertices]
xs = [v.x for v in allv]; ys = [v.y for v in allv]; zs = [v.z for v in allv]
bmin = Vector((min(xs), min(ys), min(zs))); bmax = Vector((max(xs), max(ys), max(zs)))
dims = bmax - bmin

# manifold + componentes por shell
manifold_all = True
for o in meshes:
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    if any(v != 2 for v in ec.values()):
        manifold_all = False

big = max(meshes, key=lambda o: len(o.data.vertices))
sc = bpy.context.scene

def cast(origin, direction):
    hit, loc, *_ = sc.ray_cast(dg, origin, direction)
    return Vector(loc) if hit else None

zc = (bmin.z + bmax.z) / 2.0
# pared: desde fuera hacia el centro a media altura (lado -X, lejos del asa)
out_y = Vector((0, bmax.y + 10, zc))          # aspa en +X: rayo por +Y (cuerpo limpio)
r1 = cast(out_y, Vector((0, -1, 0)))          # superficie exterior del cuerpo
wall = inner_r = D_body = None
if r1:
    r2 = cast(r1 + Vector((0, -0.1, 0)), Vector((0, -1, 0)))   # superficie interior
    if r2:
        wall = round((r1.y - r2.y), 3); inner_r = round(r2.y, 3)
        D_body = round(r1.y * 2, 3)
# profundidad interior: desde arriba hacia abajo por el eje
top = Vector((0, 0, bmax.z + 5))
dhit = cast(top, Vector((0, 0, -1)))
inner_depth = round(bmax.z - dhit.z, 3) if dhit else None
# capacidad aprox (cilindro equivalente, declarado como aprox)
capacity = None
if inner_r and inner_depth:
    capacity = round(math.pi * inner_r ** 2 * inner_depth / 1000.0, 1)  # ml aprox

print("MEASURE_JSON " + json.dumps({
    "dims": {"H": round(dims.z, 3), "D_body": D_body, "WALL": wall},
    "D_body": D_body, "D_total_con_asa": round(max(dims.x, dims.y), 3), "H": round(dims.z, 3),
    "wall": wall, "D_int": round(inner_r * 2, 3) if inner_r else None,
    "inner_depth": inner_depth, "capacity_ml_aprox": capacity,
    "manifold": manifold_all, "components": len(meshes),
    "not_measured": ["redondeo del filete", "seccion exacta del asa"] if len(meshes) > 1 else ["redondeo del filete"],
}))
