"""gen_box.py — Generador determinista de la caja de mision caja_001.
Uso (dentro de Blender):
  blender -b --factory-startup -P gen_box.py -- <params.json> <out.blend> <out.stl>
Parametros (PARAMETERS.json, spec §12): L, W, H, WALL, RIM_R, HOLE_D,
HOLE_MARGIN, USBC_W, USBC_H, USBC_Z (centro del puerto respecto a base).
Nada de valores quemados aqui: todo llega por JSON.
"""
import bpy
import json
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
params = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

L = float(params["L"]); W = float(params["W"]); H = float(params["H"])
WALL = float(params["WALL"])
RIM_R = min(float(params.get("RIM_R", 1.5)), WALL - 0.5)
HOLE_D = float(params.get("HOLE_D", 3.2))          # M3 pasante
HOLE_MARGIN = float(params.get("HOLE_MARGIN", 12.0))
USBC_W = float(params.get("USBC_W", 9.0))
USBC_H = float(params.get("USBC_H", 3.5))
USBC_Z = float(params.get("USBC_Z", 8.0))

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene


def cube(name, dims, loc):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (dims[0] / 2, dims[1] / 2, dims[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    return o


def cyl(name, d, depth, loc):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=d / 2, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    return o


def boolean_diff(target, cutter):
    m = target.modifiers.new("cut", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


# --- Cuerpo
box = cube("caja", (L, W, H), (0, 0, H / 2))

# --- Cavidad abierta por arriba (fondo WALL, sin tapa)
cav = cube("cutter_cav", (L - 2 * WALL, W - 2 * WALL, H + 2),
           (0, 0, WALL + (H + 2) / 2))
boolean_diff(box, cav)

# --- 4 agujeros M3 pasantes por el fondo
hx, hy = L / 2 - HOLE_MARGIN, W / 2 - HOLE_MARGIN
for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
    h = cyl(f"cutter_hole{i}", HOLE_D, WALL + 2, (sx * hx, sy * hy, WALL / 2))
    boolean_diff(box, h)

# --- Puerto USB-C lateral (pared -Y)
usb = cube("cutter_usb", (USBC_W, WALL + 2, USBC_H), (0, -W / 2, USBC_Z))
boolean_diff(box, usb)

# --- Filo superior redondeado (RIM_R < WALL para no romper paredes)
if RIM_R > 0.2:
    bev = box.modifiers.new("rim", "BEVEL")
    bev.width = RIM_R
    bev.segments = 3
    bev.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = box
    bpy.ops.object.modifier_apply(modifier=bev.name)

# --- Manifold check interno (informa; la autoridad es measure_box.py)
mesh = box.data
bad = 0
edge_count = {}
for p in mesh.polygons:
    for e in p.edge_keys:
        edge_count[e] = edge_count.get(e, 0) + 1
bad = sum(1 for v in edge_count.values() if v != 2)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.wm.stl_export(filepath=OUT_STL)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

print("GEN_OK", json.dumps({
    "params": {"L": L, "W": W, "H": H, "WALL": WALL, "RIM_R": RIM_R},
    "mesh_bad_edges": bad,
    "verts": len(mesh.vertices), "faces": len(mesh.polygons),
}))
