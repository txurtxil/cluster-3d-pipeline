# gen_chasis.py — Chasis EXACTO para cluster 2x AMD BC-250 + 2x FlexATX
# Medidas verificadas (fuentes en respuesta):
#   BC-250: 340 x 115 mm (theretroweb: 340x145x32 con PCB), agujeros cada 95 mm,
#           220W TDP por 1x PCIe 8-pin (J1000). SIN puntos de ventilador propios.
#   Ventilacion: 1x fan 120x25mm (Arctic P12 Max) por placa, agujeros 105x105 mm.
#   FlexATX: 150 x 81.5 x 40.5 mm (ej. FSP500-30AS). 1 PSU por placa (300W+ 12V).
# 1 BU = 1 mm. -- <salida.blend>
import bpy, math, sys, os

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    n_boards=2,
    # --- BC-250 (real) ---
    board_len=340.0,       # PCB real
    board_w=115.0,         # PCB real
    board_margin=8.0,      # holgura por lado -> hueco 356x131
    board_hole_spacing=95.0,  # separacion de agujeros de la placa (documentado)
    # --- Ventilacion (real: la placa NO trae mounts) ---
    fan_size=120.0,        # Arctic P12 Max / Pro
    fan_hole_spacing=105.0,   # estandar 120mm (esquinas 7.5mm)
    fan_post=30.0,         # altura poste sobre base
    # --- PSU FlexATX (real) ---
    psu_len=150.0, psu_w=81.5, psu_h=40.5,
    psu_margin=6.0,
    # --- Estructura ---
    base_t=5.0,
    wall=4.0,
    hole_d=4.5,            # M4
    margin=10.0,
)
P = PARAMS

slot_len = P["board_len"] + 2*P["board_margin"]     # 356
slot_w   = P["board_w"] + 2*P["board_margin"]       # 131
slot_pitch = slot_w + P["margin"]                   # 141
psu_len_h = P["psu_len"] + 2*P["psu_margin"]        # 162
psu_w_h   = P["psu_w"] + 2*P["psu_margin"]          # 93.5
zone_boards_x = P["margin"] + slot_len              # 10..366
zone_psu_x = zone_boards_x + P["margin"]            # 376
total_x = zone_psu_x + psu_len_h + P["margin"]      # 548
total_y = P["margin"] + P["n_boards"]*slot_pitch + P["margin"]  # 302

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

def drill(target, x, y, z, depth):
    bpy.ops.mesh.primitive_cylinder_add(radius=P["hole_d"]/2, depth=depth+2, location=(x, y, z))
    h = bpy.context.active_object
    m = target.modifiers.new("T", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.object = h
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="T")
    bpy.data.objects.remove(h, do_unlink=True)

parts = []
# Base + muros laterales
parts.append(cube_obj("Chasis_Base", (total_x/2, total_y/2, P["base_t"]/2), (total_x, total_y, P["base_t"])))
for y in (P["wall"]/2, total_y - P["wall"]/2):
    parts.append(cube_obj("Chasis_Muro", (total_x/2, y, P["base_t"]+P["wall"]*2), (total_x, P["wall"], P["wall"]*4)))

# --- Zona placas: cuna con 4 apoyos (agujeros placa a 95mm) + 4 postes fan 120mm ---
for n in range(P["n_boards"]):
    cy = P["margin"] + slot_w/2 + n*slot_pitch
    cx = zone_boards_x - slot_len/2
    # 4 apoyos bajos en esquinas del hueco (agujeros M4 a spacing 95)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ax = cx + sx*P["board_hole_spacing"]/2
            ay = cy + sy*P["board_hole_spacing"]/2
            post_h = 12.0
            post = cube_obj(f"Apoyo_Placa_{n+1}", (ax, ay, P["base_t"]+post_h/2), (25, 25, post_h))
            drill(post, ax, ay, P["base_t"]+post_h/2, post_h)
            parts.append(post)
    # 4 postes de ventilador 120mm (hueco 105x105 en la cruz del heatsink)
    hs = P["fan_hole_spacing"]/2
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = cx + sx*hs; py = cy + sy*hs
            post = cube_obj(f"Poste_Fan_{n+1}", (px, py, P["base_t"]+P["fan_post"]/2), (18, 18, P["fan_post"]))
            drill(post, px, py, P["base_t"]+P["fan_post"]/2, P["fan_post"])
            parts.append(post)

# --- Zona PSUs: compartimentos FlexATX ---
for n in range(P["n_boards"]):
    cy = P["margin"] + slot_w/2 + n*slot_pitch
    cx = zone_psu_x + psu_len_h/2
    z0 = P["base_t"]
    parts.append(cube_obj(f"PSU_{n+1}_Suelo", (cx, cy, z0+P["wall"]/2), (psu_len_h, psu_w_h, P["wall"])))
    for sx in (-1, 1):
        parts.append(cube_obj(f"PSU_{n+1}_Lat", (cx+sx*(psu_len_h/2-P["wall"]/2), cy, z0+P["psu_h"]/2), (P["wall"], psu_w_h, P["psu_h"])))
    for sy in (-1, 1):
        parts.append(cube_obj(f"PSU_{n+1}_Fondo", (cx, cy+sy*(psu_w_h/2-P["wall"]/2), z0+P["psu_h"]/2), (psu_len_h, P["wall"], P["psu_h"])))

mat = bpy.data.materials.new("Mat_PETG_Negro")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.10, 0.10, 0.12, 1)
b.inputs["Roughness"].default_value = 0.55
for o in parts:
    o.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
