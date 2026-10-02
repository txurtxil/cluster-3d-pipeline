# gen_bracket.py — Pieza de prueba parametrica: escuadra en L con taladro M5
# LECCION del doc: geometria dimensional precisa = script DETERMINISTA.
# Unidades: 1 BU = 1 mm (scale_length 0.001 en la escena)
import bpy, math, sys, os

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    leg_x=40.0,   # longitud pata horizontal
    leg_z=40.0,   # altura pata vertical
    width=20.0,   # ancho (eje Y)
    wall=3.0,     # espesor
    hole_d=5.5,   # taladro M5
)

sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001  # 1 BU = 1 mm
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

def cube_obj(name, loc, scale):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o

# Placa horizontal (base)
base = cube_obj("Bracket_Base", (PARAMS["leg_x"] / 2, 0, PARAMS["wall"] / 2),
                (PARAMS["leg_x"], PARAMS["width"], PARAMS["wall"]))
# Placa vertical
vert = cube_obj("Bracket_Vert", (PARAMS["wall"] / 2, 0, PARAMS["wall"] + PARAMS["leg_z"] / 2),
                (PARAMS["wall"], PARAMS["width"], PARAMS["leg_z"]))

# Taladro M5 a traves de la placa vertical (eje X), centrado
bpy.ops.mesh.primitive_cylinder_add(radius=PARAMS["hole_d"] / 2, depth=PARAMS["wall"] + 2,
                                    location=(PARAMS["wall"] / 2, 0, PARAMS["wall"] + PARAMS["leg_z"] / 2),
                                    rotation=(0, math.radians(90), 0))
hole = bpy.context.active_object
hole.name = "Hole_M5"

mod = vert.modifiers.new("HoleM5", 'BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'
mod.object = hole
bpy.context.view_layer.objects.active = vert
bpy.ops.object.modifier_apply(modifier="HoleM5")
bpy.data.objects.remove(hole, do_unlink=True)

# Material sencillo para el render
mat = bpy.data.materials.new("Mat_PLA_Gris")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1)
bsdf.inputs["Roughness"].default_value = 0.6
for o in (base, vert):
    o.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK")
