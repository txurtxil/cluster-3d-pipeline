# gen_cluster2_bc250.py — Chasis inteligente 2x BC-250 (v3.1)
# CORRECCIONES v3.1:
#   - Flujo de aire real: torre trasera por canal (Hv=140) con ventana fan 122x80
#     + taladros fan a 105mm en pared interior; los fans 120mm (25mm) montan DENTRO
#     del plenum de 30mm; tapa trasera con REJILLA de escape (antes el muro solido
#     bloqueaba el paso de aire: bug detectado en revision de diseno).
#   - PSUs FlexATX ventiladas: 3 ranuras de admision en suelo de cada compartimento.
#   - Base estable: patas de altura = fondo de PSU (antes las patas quedaban en el aire).
#   Resto igual: 2 canales aislados por divisor, cuña frontal 6 ranuras, apoyos 95mm,
#   escalon 305x140/115, skin + medallones, canal cables trasero.
# 1 BU = 1 mm. -- <salida.blend>
import bpy, math, sys, os

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    env_len=305.0, env_w=140.0, main_w=115.0, step_len=105.0, clearance=3.0,
    wall=4.0, floor_t=4.0, body_h=90.0,
    divider_t=8.0, cable_ch=30.0,
    nose_len=70.0, nose_h=130.0, slot_w=36.0, slot_h=10.0, slot_pitch_y=40.0,
    cap_t=4.0, fan_d=118.0, fan_hole_spacing=105.0,
    fan_win_w=122.0, fan_win_h=80.0, hv=140.0,          # torre trasera
    grille_slot_w=100.0, grille_slot_h=8.0, grille_pitch=14.0, grille_n=5,
    io_win_w=120.0, io_win_h=45.0,
    psu_len=160.0, psu_w=73.66, psu_h=41.2, psu_margin=6.0,
    psu_vent_w=60.0, psu_vent_h=8.0,
    skin_t=3.0, rail_w=6.0, rail_h=5.0, medallion_d=80.0, ring_t=4.0,
    foot=20.0,
    board_hole_spacing=95.0, hole_d=4.5,
)
P = PARAMS

L = P["env_len"] + 2*P["clearance"]
w_main = P["main_w"] + 2*P["clearance"]
w_full = P["env_w"] + 2*P["clearance"]
Wout = w_full + 2*P["wall"]
x_step = L - (P["step_len"] + P["clearance"])
NL, NH = P["nose_len"], P["nose_h"]
FT, W, H = P["floor_t"], P["wall"], P["body_h"]
CC = P["cable_ch"]
HV = P["hv"]
slope = math.atan2(NH - H, NL)

chan_pitch = w_full + P["divider_t"]
c0, c1 = -chan_pitch/2, chan_pitch/2
total_y = chan_pitch + w_full + 2*W

ph = P["psu_h"] + 8                    # 49.2: profundidad PSU bajo el suelo
foot_h = ph                            # patas alineadas con el fondo de las PSUs

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

def prism_xy(name, pts, z0, h):
    n = len(pts)
    verts = [(x, y, z0) for x, y in pts] + [(x, y, z0+h) for x, y in pts]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name+"_m"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o

def prism_xz(name, pts, y0, y1):
    n = len(pts)
    verts = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name+"_m"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o

def drill(target, x, y, z, depth, dia=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=(dia or P["hole_d"])/2, depth=depth+2, location=(x, y, z))
    h = bpy.context.active_object
    m = target.modifiers.new("T", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=h
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="T")
    bpy.data.objects.remove(h, do_unlink=True)

def box_cut(target, loc, dims):
    b = cube_obj("cut", loc, dims)
    m = target.modifiers.new("C", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=b
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="C")
    bpy.data.objects.remove(b, do_unlink=True)

parts = []

# Suelos escalonados por canal
for ci, cy in enumerate((c0, c1)):
    pts = [(x, y+cy) for x, y in
           [(0,-w_main/2),(x_step,-w_main/2),(x_step,-w_full/2),(L,-w_full/2),
            (L,w_full/2),(x_step,w_full/2),(x_step,w_main/2),(0,w_main/2)]]
    parts.append(prism_xy(f"Suelo_Canal{ci}", pts, 0, FT))

# Muros laterales + divisor central
for sy in (-1, 1):
    parts.append(cube_obj("Muro_Lateral", ((L+CC)/2, sy*(total_y/2-W/2), FT+H/2), (L+CC, W, H)))
parts.append(cube_obj("Muro_Divisor", ((L+CC)/2, 0, FT+H/2), (L+CC, P["divider_t"], H)))

# Apoyos de placa (95 mm)
for ci, cy in enumerate((c0, c1)):
    pcx = x_step*0.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = pcx + sx*P["board_hole_spacing"]/2
            py = cy + sy*P["board_hole_spacing"]/2
            post = cube_obj(f"Apoyo_C{ci}", (px, py, FT+6), (25, 25, 12))
            drill(post, px, py, FT+6, 12)
            parts.append(post)

# Cuña frontal con 6 ranuras
nose = prism_xz("Cuna_Frontal", [(-NL,0),(-NL,FT+NH),(0,FT+H),(0,0)], -total_y/2, total_y/2)
parts.append(nose)
zc = FT + H + (NH-H)*0.55
for cy in (c0, c1):
    for sy in (-1, 0, 1):
        bpy.ops.mesh.primitive_cube_add(location=(-NL*0.45, cy + sy*P["slot_pitch_y"], zc),
            rotation=(0, -slope, 0))
        s = bpy.context.active_object
        s.scale = (P["slot_w"]/2, P["slot_h"]/2, W+2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        m = nose.modifiers.new("Ranura", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=s
        bpy.context.view_layer.objects.active = nose
        bpy.ops.object.modifier_apply(modifier="Ranura")
        bpy.data.objects.remove(s, do_unlink=True)

# --- Pared interior trasera (torre HV): ventana I/O + ventana fan + 4 taladros fan ---
inner = cube_obj("Pared_IO", (L+W/2, 0, FT+HV/2), (W, total_y-2*W, HV))
for cy in (c0, c1):
    box_cut(inner, (L+W/2, cy, FT+P["io_win_h"]/2), (W+2, P["io_win_w"], P["io_win_h"]))
    fcz = FT + P["io_win_h"] + 8 + P["fan_win_h"]/2      # fan sobre la ventana I/O
    box_cut(inner, (L+W/2, cy, fcz), (W+2, P["fan_win_w"], P["fan_win_h"]))
    hs = P["fan_hole_spacing"]/2
    for sx in (-1, 1):
        for sy in (-1, 1):
            drill(inner, L+W/2, cy + sx*hs, fcz + sy*hs, W)
parts.append(inner)

# --- Tapa trasera con rejilla de escape por canal ---
cap = cube_obj("Tapa_Trasera", (L+CC+P["cap_t"]/2, 0, FT+HV/2), (P["cap_t"], total_y, HV))
for cy in (c0, c1):
    for i in range(P["grille_n"]):
        gz = FT + P["io_win_h"] + 14 + i*P["grille_pitch"]
        box_cut(cap, (L+CC+P["cap_t"]/2, cy, gz), (P["cap_t"]+2, P["grille_slot_w"], P["grille_slot_h"]))
parts.append(cap)

# --- PSUs ventiladas bajo el frontal ---
for ci, cy in enumerate((c0, c1)):
    pl = P["psu_len"]+2*P["psu_margin"]; pw = P["psu_w"]+2*P["psu_margin"]
    pcx = NL + pl/2 - 10
    suelo = cube_obj(f"PSU{ci}_Suelo", (pcx, cy, -ph+W/2), (pl, pw, W))
    for k in range(3):  # admision de aire por debajo
        box_cut(suelo, (pcx + (k-1)*45, cy, -ph+W/2), (P["psu_vent_w"], P["psu_vent_h"], W+2))
    parts.append(suelo)
    for sx in (-1, 1):
        parts.append(cube_obj(f"PSU{ci}_Lat", (pcx+sx*(pl/2-W/2), cy, -ph/2), (W, pw, ph)))
    for sy in (-1, 1):
        parts.append(cube_obj(f"PSU{ci}_Fondo", (pcx, cy+sy*(pw/2-W/2), -ph/2), (pl, W, ph)))

# --- Skin + rieles + medallones + patas alineadas ---
skin = cube_obj("Skin_Top", ((L+CC)/2 - NL/2, 0, FT+H+P["skin_t"]/2), (L+CC+NL, total_y, P["skin_t"]))
parts.append(skin)
for sy in (-1, 1):
    parts.append(cube_obj("Skin_Riel", ((L+CC)/2 - NL/2, sy*(total_y/2-P["rail_w"]/2), FT+H+P["skin_t"]+P["rail_h"]/2),
                 (L+CC+NL, P["rail_w"], P["rail_h"])))
for ci, cy in enumerate((c0, c1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=P["medallion_d"]/2-P["ring_t"]/2,
        minor_radius=P["ring_t"]/2, location=(L/2, cy, FT+H+P["skin_t"]+P["rail_h"]+2))
    ring = bpy.context.active_object
    ring.name = f"Medallon_C{ci}"
    parts.append(ring)
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(cube_obj("Pata", (sx*((L+CC)/2-P["foot"]/2-5), sy*(total_y/2-P["foot"]/2-5), -foot_h/2),
                     (P["foot"], P["foot"], foot_h)))

mat = bpy.data.materials.new("Mat_PETG_Negro")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.10, 0.10, 0.12, 1)
b.inputs["Roughness"].default_value = 0.55
for o in parts:
    if hasattr(o.data, "materials"):
        o.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
