# render_export_fit.py — Variante de render_export.py SOLO para encuadre.
# Motivo: piezas esbeltas (ratio >2:1) quedan cortadas con r=size*1.0.
# Cambio unico: distancia de camara x1.35 y elevacion 0.55*size.
# Todo lo demas identico al pipeline (Cycles 32, 5122, sol, STL). Uso:
#   blender -b <blend> -P render_export_fit.py -- <salida.png> <salida.stl|NONE> [azimut]
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_png = argv[0] if len(argv) > 0 else "/tmp/render.png"
out_stl = argv[1] if len(argv) > 1 else ""

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 32
sc.cycles.use_denoising = False
sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'

if sc.world is None:
    sc.world = bpy.data.worlds.new("Pipeline_World")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.05, 1)

for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "Pipeline_Sun"
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(30))

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

az = math.radians(float(argv[2])) if len(argv) > 2 else None

for o in list(bpy.data.objects):
    if o.type == 'CAMERA':
        bpy.data.objects.remove(o, do_unlink=True)
if az is not None:
    r = size * 1.35   # <-- unico cambio: margen de encuadre
    loc = (center.x + r * math.cos(az), center.y + r * math.sin(az), center.z + size * 0.55)
else:
    loc = (center.x + size * 1.2, center.y - size * 1.4, center.z + size * 0.75)
bpy.ops.object.camera_add(location=loc)
cam = bpy.context.active_object
cam.name = "Pipeline_Cam"

def point_at(obj, target):
    d = target - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

point_at(cam, center)
cam.data.lens = 50
sc.camera = cam

sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("PIPELINE_RENDER_OK", out_png)

if out_stl:
    for o in list(bpy.data.objects):
        o.select_set(o.type == 'MESH')
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=out_stl, export_selected_objects=True)
    else:
        bpy.ops.export_mesh.stl(filepath=out_stl, use_selection=True)
    print("PIPELINE_STL_OK", out_stl, os.path.getsize(out_stl))
