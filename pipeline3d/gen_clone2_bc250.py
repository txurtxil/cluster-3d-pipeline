# gen_clone2_bc250.py — Clon v2 segun FOTOS del anuncio (aproximaciones parametricas)
# Referencia visual (3 fotos): caja larga con:
#   - tapa frontal en CUÑA con 3 ranuras de ventilacion en la pendiente
#   - tapa trasera plana: apertura redonda Ø118 (fan 120mm, 4 tornillos a 105mm)
#     + ventana rectangular de I/O en la parte baja
#   - placa superior "skin" con 2 rieles y medallón circular (cosmetico)
#   - canal interior escalonado 305x140 (CAD usuario) con apoyos a 95mm
#   - compartimento PSU FlexATX Apevia ITX-PFC500W 160x73.66x41.2 (bc250.info)
# 1 BU = 1 mm. -- <salida.blend>
import bpy, math, sys, os
from mathutils import Vector

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    env_len=305.0, env_w=140.0, main_w=115.0, step_len=105.0, clearance=3.0,
    wall=4.0, floor_t=4.0, body_h=90.0,
    nose_len=70.0, nose_h=130.0, slot_w=36.0, slot_h=10.0, slot_pitch_y=40.0,
    cap_t=4.0, fan_d=118.0, fan_hole_spacing=105.0,
    io_win_w=120.0, io_win_h=45.0,
    skin_t=3.0, rail_w=6.0, rail_h=5.0, medallion_d=80.0, ring_t=4.0,
    psu_len=160.0, psu_w=73.66, psu_h=41.2, psu_margin=6.0, psu_under=True,
    board_hole_spacing=95.0, hole_d=4.5,
)
P = PARAMS

L = P["env_len"] + 2*P["clearance"]              # 311 canal
w_main = P["main_w"] + 2*P["clearance"]          # 121
w_full = P["env_w"] + 2*P["clearance"]           # 146
Wout = w_full + 2*P["wall"]                      # 154 exterior
x_step = L - (P["step_len"] + P["clearance"])    # 203
NL, NH = P["nose_len"], P["nose_h"]
FT, W, H = P["floor_t"], P["wall"], P["body_h"]
slope = math.atan2(NH - H, NL)                   # pendiente de la cuña

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

def prism_xy(name, pts, z0, h):   # poligono en XY extruido en Z
    n = len(pts)
    verts = [(x, y, z0) for x, y in pts] + [(x, y, z0+h) for x, y in pts]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name+"_m"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o

def prism_xz(name, pts, y0, y1):  # poligono en XZ extruido en Y
    n = len(pts)
    verts = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name+"_m"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o

def drill(target, x, y, z, depth, dia=None, rot_y=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=(dia or P["hole_d"])/2, depth=depth+2,
                                        location=(x, y, z), rotation=(0, rot_y, 0))
    h = bpy.context.active_object
    m = target.modifiers.new("T", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=h
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="T")
    bpy.data.objects.remove(h, do_unlink=True)

parts = []
# Suelo escalonado + muros (canal slide-in exacto)
floor_pts = [(0,-w_main/2),(x_step,-w_main/2),(x_step,-w_full/2),(L,-w_full/2),
             (L,w_full/2),(x_step,w_full/2),(x_step,w_main/2),(0,w_main/2)]
parts.append(prism_xy("Suelo_Canal", floor_pts, 0, FT))
for sy in (-1, 1):
    parts.append(cube_obj("Muro_Principal", (x_step/2, sy*(w_main/2+W/2), FT+H/2), (x_step, W, H)))
    parts.append(cube_obj("Muro_Ancho", ((x_step+L)/2, sy*(w_full/2+W/2), FT+H/2), (L-x_step, W, H)))
    parts.append(cube_obj("Muro_Escalon", (x_step, sy*(w_main/2+(w_full-w_main)/4+W/4), FT+H/2),
                         (W, (w_full-w_main)/2+W, H)))

# Apoyos de placa (agujeros a 95 mm)
pcx = x_step*0.5
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = pcx + sx*P["board_hole_spacing"]/2, sy*P["board_hole_spacing"]/2
        post = cube_obj("Apoyo_Placa", (px, py, FT+6), (25, 25, 12))
        drill(post, px, py, FT+6, 12)
        parts.append(post)

# Cuña frontal (nose) con 3 ranuras en la pendiente
nose_pts = [(-NL,-W/2,0),(-NL,W/2,0),(0,W/2,0),(0,-W/2,0)]  # placeholder (no usar)
nose_xz = [(-NL, 0), (-NL, FT+NH), (0, FT+H), (0, 0)]
nose = prism_xz("Cuna_Frontal", nose_xz, -Wout/2, Wout/2)
parts.append(nose)
zc = FT + H + (NH-H)*0.55   # centro de la pendiente
for sy in (-1, 0, 1):
    bpy.ops.mesh.primitive_cube_add(location=(-NL*0.45, sy*P["slot_pitch_y"], zc),
        rotation=(0, -slope, 0))
    s = bpy.context.active_object
    s.scale = (P["slot_w"]/2, P["slot_h"]/2, W+2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m = nose.modifiers.new("Ranura", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=s
    bpy.context.view_layer.objects.active = nose
    bpy.ops.object.modifier_apply(modifier="Ranura")
    bpy.data.objects.remove(s, do_unlink=True)

# Tapa trasera: fan Ø118 arriba + ventana I/O abajo + 4 tornillos
cap = cube_obj("Tapa_Trasera", (L+P["cap_t"]/2, 0, FT+H/2), (P["cap_t"], Wout, H))
drill(cap, L+P["cap_t"]/2, 0, FT+H*0.62, P["cap_t"], dia=P["fan_d"])
for sx in (-1, 1):
    for sy in (-1, 1):
        drill(cap, L+P["cap_t"]/2, sx*P["fan_hole_spacing"]/2, FT+H*0.62 + sy*P["fan_hole_spacing"]/2, P["cap_t"])
# Ventana I/O rectangular en la parte baja de la tapa trasera
bpy.ops.mesh.primitive_cube_add(location=(L+P["cap_t"]/2, 0, FT+P["io_win_h"]/2))
io_box = bpy.context.active_object
io_box.scale = (P["cap_t"]/2+1, P["io_win_w"]/2, P["io_win_h"]/2)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
mio = cap.modifiers.new("VentanaIO", 'BOOLEAN'); mio.operation='DIFFERENCE'; mio.solver='EXACT'; mio.object=io_box
bpy.context.view_layer.objects.active = cap
bpy.ops.object.modifier_apply(modifier="VentanaIO")
bpy.data.objects.remove(io_box, do_unlink=True)
parts.append(cap)

# Skin superior + rieles + medallón
skin = cube_obj("Skin_Top", (L/2, 0, FT+H+P["skin_t"]/2), (L+2*W, Wout, P["skin_t"]))
parts.append(skin)
for sy in (-1, 1):
    parts.append(cube_obj("Skin_Riel", (L/2, sy*(Wout/2-P["rail_w"]/2), FT+H+P["skin_t"]+P["rail_h"]/2),
                 (L+2*W, P["rail_w"], P["rail_h"])))
bpy.ops.mesh.primitive_torus_add(major_radius=P["medallion_d"]/2-P["ring_t"]/2,
    minor_radius=P["ring_t"]/2, location=(L/2, 0, FT+H+P["skin_t"]+P["rail_h"]+2),
    rotation=(0, 0, 0))
ring = bpy.context.active_object
ring.name = "Skin_Medallon"
parts.append(ring)

# PSU bajo el suelo (Apevia FlexATX exacta de bc250.info)
if P["psu_under"]:
    pl = P["psu_len"]+2*P["psu_margin"]; pw = P["psu_w"]+2*P["psu_margin"]; ph = P["psu_h"]+8
    px0 = 30.0
    pcx, pcy = px0+pl/2, 0
    parts.append(cube_obj("PSU_Suelo", (pcx, pcy, -ph+W/2), (pl, pw, W)))
    for sx in (-1, 1):
        parts.append(cube_obj("PSU_Lat", (pcx+sx*(pl/2-W/2), pcy, -ph/2), (W, pw, ph)))
    for sy in (-1, 1):
        parts.append(cube_obj("PSU_Fondo", (pcx, pcy+sy*(pw/2-W/2), -ph/2), (pl, W, ph)))

mat = bpy.data.materials.new("Mat_PETG")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.10, 0.10, 0.12, 1)
b.inputs["Roughness"].default_value = 0.55
for o in parts:
    if hasattr(o.data, "materials"):
        o.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
