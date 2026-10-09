import bpy, math
from mathutils import Vector
sc = bpy.context.scene
# borrar camaras/luces previas
for o in [o for o in sc.objects if o.type in ("CAMERA", "LIGHT")]:
    bpy.data.objects.remove(o, do_unlink=True)
# envolver vista: centrar en torre
import bpy as _b
mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
for o in sc.objects:
    if o.type == "MESH":
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mins = Vector(map(min, mins, w)); maxs = Vector(map(max, maxs, w))
ctr = (mins + maxs) / 2
size = max((maxs - mins).length, 1)
cam_d = size * 1.1
bpy.ops.object.camera_add(location=(ctr.x + cam_d * 0.8, ctr.y - cam_d, ctr.z + cam_d * 0.55))
cam = bpy.context.active_object
d = ctr - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
bpy.ops.object.light_add(type="SUN", location=ctr)
sun = bpy.context.active_object
sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(30))
sun.data.energy = 4
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x = 640
sc.render.resolution_y = 800
sc.render.filepath = "/tmp/tower_preview.png"
bpy.ops.render.render(write_still=True)
print("RENDER_OK /tmp/tower_preview.png")
