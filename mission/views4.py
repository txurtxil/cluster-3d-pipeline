"""views4.py — Genera 4 variantes rotadas del STL para vistas de inspeccion.
Uso: blender -b --factory-startup -P views4.py -- <in.stl> <out_dir>
Vistas: lateral (original), frontal (rotZ 90), superior (rotX 90),
isometrica (rotZ 45 + rotX 35). CPU puro (sin render GL).
"""
import bpy, sys, os, math

argv = sys.argv[sys.argv.index("--") + 1:]
IN, OUTD = argv[0], argv[1]
os.makedirs(OUTD, exist_ok=True)

VISTAS = [
    ("v1_lateral", (0, 0, 0)),
    ("v2_frontal", (0, 0, math.radians(90))),
    ("v3_superior", (math.radians(90), 0, 0)),
    ("v4_isometrica", (math.radians(35), 0, math.radians(45))),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
for name, (rx, ry, rz) in VISTAS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.stl_import(filepath=IN)
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.rotation_euler = (rx, ry, rz)
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    out = os.path.join(OUTD, name + ".stl")
    bpy.ops.wm.stl_export(filepath=out)
    print("VISTA_OK", name)
print("VIEWS4_DONE")
