# render_export.py — Pipeline determinista: render Cycles + export STL
# Adaptado del pipeline validado en z1 (doc ESTADO-CLUSTER 2026-09-30):
#   Cycles 32 samples, 512x512, camara + sol. NO usar EEVEE headless en z1.
# Uso: blender -b <blend> -P render_export.py -- <salida.png> <salida.stl>
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_png = argv[0] if len(argv) > 0 else "/tmp/render.png"
out_stl = argv[1] if len(argv) > 1 else ""
if out_stl == "NONE":   # convencion del pipeline: NONE = no exportar STL
    out_stl = ""

sc = bpy.context.scene

# ---- Motor: Cycles CPU (portable, deterministico) ----
sc.render.engine = 'CYCLES'
sc.cycles.samples = 32
sc.cycles.use_denoising = False
sc.cycles.device = 'CPU'
_res = int(os.environ.get("RENDER_RES", "512"))
sc.render.resolution_x = sc.render.resolution_y = _res
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'

# ---- Fondo gris neutro ----
if sc.world is None:
    sc.world = bpy.data.worlds.new("Pipeline_World")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.05, 1)

# ---- Luz: sol determinista ----
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "Pipeline_Sun"
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(30))

# ---- Camara: encuadre automatico de la bbox total ----
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
if not meshes:
    print("PIPELINE_ERROR: sin mallas en la escena")
    sys.exit(2)

import mathutils
mins = mathutils.Vector((1e9, 1e9, 1e9))
maxs = mathutils.Vector((-1e9, -1e9, -1e9))
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mins = mathutils.Vector(map(min, mins, w))
        maxs = mathutils.Vector(map(max, maxs, w))
center = (mins + maxs) / 2
size = max((maxs - mins).length, 1e-6)

# argv[2]: azimut en grados | "top" (cenital). argv[3]: elevacion (fraccion de size, default 0.6)
_az_raw = argv[2] if len(argv) > 2 else None
_elev = float(argv[3]) if len(argv) > 3 else 0.6
_top = (_az_raw == "top")
az = None if (_az_raw is None or _top) else math.radians(float(_az_raw))

for o in list(bpy.data.objects):
    if o.type == 'CAMERA':
        bpy.data.objects.remove(o, do_unlink=True)
if _top:
    loc = (center.x, center.y, center.z + size * 1.6)
elif az is not None:
    r = size * 1.0
    loc = (center.x + r * math.cos(az), center.y + r * math.sin(az), center.z + size * _elev)
else:
    loc = (center.x + size * 0.9, center.y - size * 1.1, center.z + size * _elev)
bpy.ops.object.camera_add(location=loc)
cam = bpy.context.active_object
cam.name = "Pipeline_Cam"

def point_at(obj, target):
    d = target - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

point_at(cam, center)
cam.data.lens = 50
sc.camera = cam

# ---- Render ----
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("PIPELINE_RENDER_OK", out_png)

# ---- Export STL (solo mallas, transformadas) ----
if out_stl:
    for o in list(bpy.data.objects):
        o.select_set(o.type == 'MESH')
    if hasattr(bpy.ops.wm, "stl_export"):
        # Blender 4.x: operador nativo C++
        bpy.ops.wm.stl_export(filepath=out_stl, export_selected_objects=True)
    else:
        bpy.ops.export_mesh.stl(filepath=out_stl, use_selection=True)
    print("PIPELINE_STL_OK", out_stl, os.path.getsize(out_stl))
