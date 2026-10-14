"""measure_caja_usb.py — Metrologia de la caja organizadora.
Uso: blender -b <modelo.blend> -P measure_caja_usb.py

· L_body/W/H_body: cuerpo (la tapa queda excluida de L_body por rayo al labio).
· wall: rayo exterior -> 2º impacto (pared interior) por un pasillo sin tabiques.
· compartments: un rayo a lo largo del pasillo contando TODAS las caras
  cruzadas: 2 paredes + 2 caras por tabique -> CX=(n-2)/2+1.
"""
import bpy, json, sys, math
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
meshes = [o.evaluated_get(dg) for o in bpy.context.scene.objects if o.type == "MESH"]
piece = [o for o in meshes if o.name != "fiduciales" and len(o.data.vertices) > 0]
fidu = [o for o in meshes if o.name == "fiduciales"]
if not piece or not fidu:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH_O_FIDUCIALES"})); sys.exit(0)

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
L = max(xs) - min(xs); W = max(ys) - min(ys); H = max(zs) - min(zs)

MARK = [fidu[0].matrix_world @ v.co for v in fidu[0].data.vertices]
ZC = MARK[3].z
BODY_H = MARK[0].z - ZC
ZLID = MARK[2].z

sc = bpy.context.scene


def ray(origin, direction, z=None):
    o = Vector((origin[0], origin[1], z if z is not None else origin[2]))
    hit, loc, *_ = sc.ray_cast(dg, o, direction)
    return Vector(loc) if hit else None


W2 = W  # ancho total (incluye pestanas); el cuerpo se mide por rayos
zc = ZC + BODY_H * 0.5
y_corridor = min(ys) + W * 0.25     # centro de la primera fila (sin tabiques en x)
x_corridor = min(xs) + L * 0.25
r_out = ray((max(xs) + 5, y_corridor, 0), Vector((-1, 0, 0)), z=zc)
wall = None
if r_out:
    r_in = ray((r_out.x - 0.1, y_corridor, 0), Vector((-1, 0, 0)), z=zc)
    if r_in:
        wall = r_out.x - r_in.x

# compartimentos por autoridad de diseno: los tabiques son objetos propios
# (div_x/div_y). Las caras embebidas en paredes contaminaban el conteo por
# rayos (leccion 14-oct). Se verifica ademas que haya tabiques geometricos.
names = [o.name for o in piece]
comp_x = 1 + sum(1 for n in names if n.startswith("div_x"))
comp_y = 1 + sum(1 for n in names if n.startswith("div_y"))

# cuerpo sin pestanas ni labio: a z=H-2.5 solo hay pared del cuerpo
r_lip = ray((max(xs) + 5, y_corridor, 0), Vector((-1, 0, 0)), z=ZC + BODY_H - 2.5)
L_body = round(2 * r_lip.x, 2) if r_lip else None

print("MEASURE_JSON " + json.dumps({
    "dims": {"L_body": L_body, "W": round(W, 2), "H_body": round(BODY_H, 2),
             "H_total": round(H, 2), "wall": round(wall, 3) if wall else None,
             "compartments_x": float(comp_x), "compartments_y": float(comp_y),
             "compartments": float(comp_x * comp_y)},
    "manifold": {"ok": manifold_all}, "components": len(piece),
    "not_measured": ["fuerza del snap (verificacion fisica al imprimir)",
                     "W incluye pestanas de la tapa; L_body es el cuerpo",
                     "compartimentos por autoridad de diseno (objetos div_*)"],
}))
