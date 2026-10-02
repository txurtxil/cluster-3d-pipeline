# bbox_check.py — Checkpoint: dimensiones por objeto (verificacion fisica)
# Uso: blender -b <blend> -P bbox_check.py
import bpy, mathutils, json

report = {}
scale_mm = bpy.context.scene.unit_settings.scale_length * 1000.0  # BU -> mm
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    mins = mathutils.Vector((1e9, 1e9, 1e9))
    maxs = mathutils.Vector((-1e9, -1e9, -1e9))
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mins = mathutils.Vector(map(min, mins, w))
        maxs = mathutils.Vector(map(max, maxs, w))
    dim = maxs - mins
    report[o.name] = {
        "dim_xyz_mm": [round(dim.x * scale_mm, 3), round(dim.y * scale_mm, 3), round(dim.z * scale_mm, 3)],
        "verts": len(o.data.vertices),
        "polygons": len(o.data.polygons),
        "manifold": all(len(p.vertices) > 2 for p in o.data.polygons),
    }

print("BBOX_REPORT_JSON " + json.dumps(report))
print("BBOX_OK")
