# gen_shroud.py — CLON parametrico del "BC-250 3D Printed Shroud Mod" (Legendary Makes)
# Video: "Ultimate Cooling: How to Install the AMD BC-250 3D Printed Shroud Mod"
# Diseno: ducto que envuelve el disipador stock y ventilador servidor 120x38mm
# (~10.000 RPM, 80 CFM) empujando aire a traves de las aletas.
# Envuelta placa segun CAD 2D comunitario: 304.66 x 139.98 mm CON ESCALON
# (zona de conectores ancha ~140mm, resto ~115mm).
# 1 BU = 1 mm. -- <salida.blend>
import bpy, math, sys, os
from mathutils import Vector

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    # --- Envuelta placa (CAD 2D comunitario) ---
    board_len=305.0,       # 304.66
    board_w=140.0,         # 139.98 (zona ancha, lado conectores)
    step_w=115.0,          # zona estrecha (resto de la placa)
    step_start=205.0,      # donde empieza la zona ancha (lado conectores)
    # --- Ducto ---
    wall=3.0,
    cavity_floor=6.0,      # altura sobre la PCB (componentes)
    duct_h=40.0,           # pared del ducto (disipador stock ~32mm)
    # --- Ventilador servidor 120x38 ---
    fan_size=120.0,
    fan_hole_spacing=105.0,
    fan_open_d=118.0,      # abertura del ducto bajo el fan
    plate=150.0,           # brida del fan
    plate_t=4.0,
    # --- Centros (ajustar al disipador real) ---
    hs_center=(120.0, 57.5),   # centro disipador (zona estrecha)
    hole_d=4.5,            # M4
    foot_h=10.0,
)
P = PARAMS

# Poligono escalon de la envuelta (visto desde arriba, X=largo, Y=ancho)
def board_poly(expand=0.0):
    e = expand
    L, W, sw, ss = P["board_len"]+e, P["board_w"]+e, P["step_w"]+e, P["step_start"]
    return [(-e,-e), (L,-e), (L,W), (ss,W), (ss,sw), (-e,sw)]

def prism(name, poly, z0, z1):
    n = len(poly)
    verts = [(x,y,z0) for x,y in poly] + [(x,y,z1) for x,y in poly]
    faces = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def boolean_diff(target, cutter):
    m = target.modifiers.new("B", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="B")
    bpy.data.objects.remove(cutter, do_unlink=True)

def cyl(name, d, depth, loc):
    bpy.ops.mesh.primitive_cylinder_add(radius=d/2, depth=depth, location=loc)
    o = bpy.context.active_object; o.name = name
    return o

sc = bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

parts = []

# 1. Anillo del ducto: prisma exterior - prisma interior (cavity)
outer = prism("DuctoExt", board_poly(P["wall"]), P["cavity_floor"], P["duct_h"])
inner = prism("DuctoInt", board_poly(0.0), P["cavity_floor"]-1, P["duct_h"]+1)
boolean_diff(outer, inner)
outer.name = "Shroud_Ducto"
parts.append(outer)

# 2. Brida del ventilador (placa superior con abertura y 4 taladros M4)
hx, hy = P["hs_center"]
plate = prism("FanPlate_tmp", [(hx-P["plate"]/2, hy-P["plate"]/2), (hx+P["plate"]/2, hy-P["plate"]/2),
                               (hx+P["plate"]/2, hy+P["plate"]/2), (hx-P["plate"]/2, hy+P["plate"]/2)],
              P["duct_h"], P["duct_h"]+P["plate_t"])
fan_hole = cyl("FanHole", P["fan_open_d"], P["plate_t"]+4, (hx, hy, P["duct_h"]+P["plate_t"]/2))
boolean_diff(plate, fan_hole)
hs2 = P["fan_hole_spacing"]/2
for i,(sx,sy) in enumerate([(-1,-1),(1,-1),(1,1),(-1,1)],1):
    boolean_diff(plate, cyl(f"FH{i}", P["hole_d"], P["plate_t"]+4,
                            (hx+sx*hs2, hy+sy*hs2, P["duct_h"]+P["plate_t"]/2)))
plate.name = "Shroud_BridaFan"
parts.append(plate)

# 3. Pies de montaje en esquinas (taladro M4, separacion de agujeros placa 95mm)
for i,(fx,fy) in enumerate([(30,20),(30,95),(275,20),(275,95)],1):
    if fx > P["step_start"] and fy > P["step_w"]:
        continue
    foot = prism(f"Pie_{i}", [(fx-12,fy-12),(fx+12,fy-12),(fx+12,fy+12),(fx-12,fy+12)],
                 0, P["foot_h"])
    boolean_diff(foot, cyl(f"PF{i}", P["hole_d"], P["foot_h"]+2, (fx,fy,P["foot_h"]/2)))
    parts.append(foot)

mat = bpy.data.materials.new("Mat_PETG_Negro")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.08, 0.08, 0.10, 1)
b.inputs["Roughness"].default_value = 0.6
for o in parts:
    o.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
