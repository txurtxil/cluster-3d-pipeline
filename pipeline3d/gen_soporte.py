# gen_soporte.py — Soporte de pared parametrico: base + placa vertical + 2 taladros M4
# Patron del pipeline: PARAMS arriba, 1 BU = 1 mm, -- <salida.blend>
import bpy, math, sys, os

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    leg_x=60.0,    # longitud base
    width=30.0,    # ancho
    wall=4.0,      # espesor
    leg_z=50.0,    # altura placa vertical
    hole_d=4.5,    # taladro M4
    holes_z=(15.0, 35.0),  # posiciones de los taladros (desde la base)
)

sc = bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

def cube_obj(name, loc, dims):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o

base = cube_obj("Soporte_Base",
                (PARAMS["leg_x"]/2, 0, PARAMS["wall"]/2),
                (PARAMS["leg_x"], PARAMS["width"], PARAMS["wall"]))
vert = cube_obj("Soporte_Vert",
                (PARAMS["wall"]/2, 0, PARAMS["wall"] + PARAMS["leg_z"]/2),
                (PARAMS["wall"], PARAMS["width"], PARAMS["leg_z"]))

# Taladros a traves de la placa vertical (eje X)
for i, z in enumerate(PARAMS["holes_z"], 1):
    zp = PARAMS["wall"] + z
    bpy.ops.mesh.primitive_cylinder_add(radius=PARAMS["hole_d"]/2,
                                        depth=PARAMS["wall"] + 2,
                                        location=(PARAMS["wall"]/2, 0, zp),
                                        rotation=(0, math.radians(90), 0))
    hole = bpy.context.active_object
    hole.name = f"Hole_M4_{i}"
    mod = vert.modifiers.new(f"Hole{i}", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = hole
    bpy.context.view_layer.objects.active = vert
    bpy.ops.object.modifier_apply(modifier=f"Hole{i}")
    bpy.data.objects.remove(hole, do_unlink=True)

mat = bpy.data.materials.new("Mat_PLA_Gris")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1)
b.inputs["Roughness"].default_value = 0.6
for o in (base, vert):
    o.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
