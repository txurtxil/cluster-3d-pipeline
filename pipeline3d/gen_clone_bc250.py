# gen_clone_bc250.py — Clon del chasis LegendaryMakes para 1x BC-250 (push/pull + PSU)
# Geometria EXACTA segun CAD comunitario (usuario):
#   envolvente 305 x 140 mm (304.66 x 139.98), zona principal 115 mm,
#   ESCALON: extremo de conectores mas ancho (140 mm). PCB ~400 g c/ disipador.
# Ventilacion: push/pull 2x fan 120 mm (agujeros 105x105 mm estandar).
# PSU: FlexATX 150 x 81.5 x 40.5 mm integrada (compartimento lateral).
# 1 BU = 1 mm. -- <salida.blend>
import bpy, math, sys, os

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(
    env_len=305.0, env_w=140.0, main_w=115.0,
    step_len=105.0,          # longitud del extremo ancho (conectores)
    clearance=3.0,           # holgura por lado del canal
    base_t=4.0, wall=4.0, channel_h=45.0,   # disipador ~32 + margen aire
    fan_size=120.0, fan_hole_spacing=105.0, vent_d=110.0,
    psu_len=150.0, psu_w=81.5, psu_h=40.5, psu_margin=6.0,
    board_hole_spacing=95.0, hole_d=4.5,
)
P = PARAMS

L = P["env_len"] + 2*P["clearance"]            # 311 canal X
w_main = P["main_w"] + 2*P["clearance"]        # 121 zona estrecha
w_full = P["env_w"] + 2*P["clearance"]         # 146 zona ancha
x_step = L - (P["step_len"] + P["clearance"])  # inicio del escalon = 311-108=203
H = P["channel_h"]; W = P["wall"]; B = P["base_t"]

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

def prism(name, pts2d, z0, h):
    n = len(pts2d)
    verts = [(x, y, z0) for x, y in pts2d] + [(x, y, z0+h) for x, y in pts2d]
    faces = []
    faces.append(tuple(range(n-1, -1, -1)))
    faces.append(tuple(range(n, 2*n)))
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    mesh = bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(o)
    return o

def drill(target, x, y, z, depth, dia=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=(dia or P["hole_d"])/2, depth=depth+2, location=(x, y, z))
    h = bpy.context.active_object
    m = target.modifiers.new("T", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=h
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="T")
    bpy.data.objects.remove(h, do_unlink=True)

parts = []

# Suelo escalonado (canal slide-in)
floor_pts = [(0,-w_main/2),(x_step,-w_main/2),(x_step,-w_full/2),(L,-w_full/2),
             (L,w_full/2),(x_step,w_full/2),(x_step,w_main/2),(0,w_main/2)]
parts.append(prism("Suelo_Canal", floor_pts, 0, B))

# Muros laterales siguiendo el escalon
for sy in (-1, 1):
    parts.append(cube_obj("Muro_Principal", (x_step/2, sy*(w_main/2+W/2), B+H/2), (x_step, W, H)))
    parts.append(cube_obj("Muro_Ancho", ((x_step+L)/2, sy*(w_full/2+W/2), B+H/2), (L-x_step, W, H)))
    parts.append(cube_obj("Muro_Escalon", (x_step, sy*(w_main/2+(w_full-w_main)/4+W/4), B+H/2),
                         (W, (w_full-w_main)/2+W, H)))

# Tapas extremo con fan 120 mm (push/pull): ventilacion central + 4 agujeros
hs = P["fan_hole_spacing"]/2
for label, cx, cw in (("Entrada", 0.0, w_main), ("Salida", L, w_full)):
    cap = cube_obj(f"Tapa_{label}", (cx, 0, B+H/2), (W, cw, H))
    drill(cap, cx, 0, B+H/2, W, dia=P["vent_d"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            drill(cap, cx, sx*hs, B+H/2 + sy*hs, W)
    parts.append(cap)

# Travesanos superiores (retienen la placa al deslizar + guia shroud)
for i, tx in enumerate((x_step*0.45, x_step + (L-x_step)*0.55), 1):
    parts.append(cube_obj(f"Travesano_{i}", (tx, 0, B+H-3), (12, w_full, 6)))

# Apoyos de placa: agujeros M4 a 95 mm (documentado comunidad)
pcx = x_step*0.5
for sx in (-1, 1):
    for sy in (-1, 1):
        px = pcx + sx*P["board_hole_spacing"]/2
        py = sy*P["board_hole_spacing"]/2
        post = cube_obj("Apoyo_Placa", (px, py, B+6), (25, 25, 12))
        drill(post, px, py, B+6, 12)
        parts.append(post)

# Compartimento FlexATX lateral (zona ancha, lado +Y)
psu_l = P["psu_len"]+2*P["psu_margin"]; psu_w = P["psu_w"]+2*P["psu_margin"]
pcx2 = (x_step+L)/2
pcy2 = w_full/2 + W + psu_w/2
parts.append(cube_obj("PSU_Suelo", (pcx2, pcy2, B+W/2), (psu_l, psu_w, W)))
for sx in (-1, 1):
    parts.append(cube_obj("PSU_Lat", (pcx2+sx*(psu_l/2-W/2), pcy2, B+P["psu_h"]/2), (W, psu_w, P["psu_h"])))
for sy in (-1, 1):
    parts.append(cube_obj("PSU_Fondo", (pcx2, pcy2+sy*(psu_w/2-W/2), B+P["psu_h"]/2), (psu_l, W, P["psu_h"])))

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
