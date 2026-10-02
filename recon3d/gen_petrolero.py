#!/usr/bin/env python3
# gen_petrolero.py — Petrolero parametrico con detalle (modelo de exposicion, 1 BU = 1 mm)
# Uso: blender -b --factory-startup -P gen_petrolero.py -- <salida.blend>
import bpy, math, sys, os
import numpy as np

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/petrolero.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

P = dict(
    L=250.0,        # eslora total
    B=40.0,         # manga (ancho)
    T=12.0,         # calado
    F=18.0,         # francobordo
    n_stations=15,
    tanks=4,
    rail_h=5.0,
    # --- parametros de detalle/impresion (auditoria 2026-10-02; valores = estado
    #     actual, NO se han alterado; sirven para robustecer sin tocar geometria) ---
    detail=1.0,             # multiplicador global de detalle fino
    railing_d=0.44,         # diametro postes railing (mm) -> radio 0.22
    pipe_d=1.6,             # diametro tuberia principal -> radio 0.8
    lifeboat_scale=1.0,     # escala de botes salvavidas
    propeller_thickness=2.2,  # grosor de palas de helice
    min_printable_mm=0.4,   # umbral de auditoria FDM (reporte, no corta geometria)
)

L, B, T, F = P["L"], P["B"], P["T"], P["F"]

sc = bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

# ---------- materiales ----------
def mat(name, color, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

M_HULL   = mat("Casco_negro", (0.03, 0.03, 0.035), 0.45)
M_BOOT   = mat("Banda_roja", (0.45, 0.04, 0.03), 0.5)
M_DECK   = mat("Cubierta", (0.35, 0.30, 0.22), 0.8)
M_WHITE  = mat("Superestructura", (0.85, 0.86, 0.88), 0.5)
M_DARK   = mat("Ventanas", (0.05, 0.08, 0.10), 0.2)
M_FUNNEL = mat("Chimenea", (0.75, 0.12, 0.08), 0.5)
M_TANK   = mat("Tanques", (0.42, 0.44, 0.46), 0.6, 0.3)
M_PIPE   = mat("Tuberia", (0.55, 0.56, 0.58), 0.35, 0.7)
M_ORANGE = mat("Botes", (0.95, 0.35, 0.02), 0.5)
M_RUST   = mat("Antena_mastil", (0.55, 0.10, 0.05), 0.6)

parts = []

def cube(name, loc, dims, m):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    parts.append(o)
    return o

def cyl(name, loc, r, h, m, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(m)
    parts.append(o)
    return o

def sphere(name, loc, scale, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    parts.append(o)
    return o

# ---------- casco: loft por estaciones (banda roja abajo, negro arriba) ----------
def half_breadth(t):
    # t = x/L en [0,1]; popa redondeada, manga llena, proa fina con rake
    if t < 0.12:
        return (B/2) * (0.55 + 0.45 * math.sin(math.pi * t / 0.24))
    if t < 0.78:
        return B/2
    u = (t - 0.78) / 0.22
    return (B/2) * max(0.04, (1 - u**1.6) ** 0.75)

def keel_depth(t):
    if t < 0.08:
        return T * (0.5 + 0.5 * t / 0.08)
    if t < 0.85:
        return T
    u = (t - 0.85) / 0.15
    return T * max(0.15, 1 - u**1.4)

def deck_z(t):
    return F + 0.06 * F * (max(0.0, t - 0.6) / 0.4) ** 2   # sheer hacia proa

def hull_band(z0, z1, material, name, inflate=0.0):
    """Franja del casco entre alturas z0 (abs, fraccion de T/F) y z1."""
    V, F_ = [], []
    for i in range(P["n_stations"]):
        t = i / (P["n_stations"] - 1)
        x = t * L
        b = half_breadth(t) + inflate
        dz = deck_z(t)
        za, zb = z0 * dz, z1 * dz
        # media seccion (babor): (y, z) interpolados costado->rizado
        prof = [
            (b, za),
            (b * 0.97, za + (zb - za) * 0.35),
            (b * 0.88, za + (zb - za) * 0.75),
            (b * 0.62, zb),
        ]
        base = len(V)
        for (y, z) in prof:
            V.append((x, y, z))
        for (y, z) in reversed(prof):
            V.append((x, -y, z))
    n2 = 8  # puntos por estacion
    for i in range(P["n_stations"] - 1):
        a = i * n2
        for j in range(n2 - 1):
            F_.append((a + j, a + j + 1, a + n2 + j + 1, a + n2 + j))
    me = bpy.data.meshes.new(name + "_m")
    me.from_pydata(V, [], F_)
    me.update()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.data.materials.append(material)
    parts.append(o)
    return o

# bandas del casco: roja (bajo flotacion), negra (sobre flotacion hasta cubierta)
hull_band(-1.0, 0.0, M_BOOT, "Casco_banda_roja")
hull_band(0.0, 1.0, M_HULL, "Casco_negro", inflate=0.25)
# plano de cubierta (cierra la U por arriba)
cube("Cubierta", (L/2, 0, F + 0.35), (L * 0.985, B * 0.97, 0.7), M_DECK)

# bulbous bow
sphere("Bulbo", (L * 0.985, 0, -T * 0.45), (L * 0.02, B * 0.10, T * 0.38), M_BOOT)

# ---------- popa: timon y helice ----------
cube("Timon", (-2.5, 0, -T * 0.4), (5, 1.2, T * 1.3), M_HULL)
cyl("Eje_helice", (-4.0, 0, -T * 0.45), 1.0, 4.0, M_PIPE, rot=(0, math.radians(90), 0))
cyl("Helice_hub", (-6.0, 0, -T * 0.45), 1.6, 2.0, M_PIPE, rot=(0, math.radians(90), 0))
for k in range(3):
    ang = k * 2 * math.pi / 3
    blade = cube("Helice_pala", (-6.0, 0, -T * 0.45), (0.8, 6.5, P["propeller_thickness"]), M_PIPE)
    blade.rotation_euler = (math.radians(25), math.radians(90), ang)
    bpy.ops.object.select_all(action='DESELECT')
    blade.select_set(True)
    bpy.context.view_layer.objects.active = blade
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    blade.rotation_euler = (math.radians(25), 0, ang)
    blade.location = (-6.0, math.sin(ang) * 0.0, -T * 0.45)

# ---------- tanques de carga + cofres ----------
tank_L = L * 0.11
gap = L * 0.022
x0 = L * 0.30
for i in range(P["tanks"]):
    cx = x0 + i * (tank_L + gap) + tank_L / 2
    cube(f"Tanque_{i+1}", (cx, 0, F + 3.5), (tank_L, B * 0.72, 6.0), M_TANK)
    # cofre (aro perimetral)
    cw, cd = 0.9, 0.7
    cube(f"Cofre_{i+1}_a", (cx,  B*0.36 + cd/2, F + 6.9), (tank_L + 1.6, cd, 1.1), M_TANK)
    cube(f"Cofre_{i+1}_b", (cx, -B*0.36 - cd/2, F + 6.9), (tank_L + 1.6, cd, 1.1), M_TANK)
    cube(f"Cofre_{i+1}_c", (cx + tank_L/2 + 0.8, 0, F + 6.9), (cw, B*0.72, 1.1), M_TANK)
    cube(f"Cofre_{i+1}_d", (cx - tank_L/2 - 0.8, 0, F + 6.9), (cw, B*0.72, 1.1), M_TANK)
    cube(f"Tapa_{i+1}", (cx, 0, F + 7.6), (tank_L * 0.55, B * 0.4, 0.8), M_TANK)

# ---------- tuberia: linea longitudinal + manifold popero con valvulas ----------
for yy in (-B * 0.14, B * 0.14):
    cyl("Linea_carga", (L * 0.5, yy, F + 2.2), 0.8, L * 0.52, M_PIPE, rot=(0, math.radians(90), 0), verts=12)
# manifold + valvulas
mx = L * 0.245
cube("Manifold", (mx, 0, F + 2.2), (4, B * 0.5, 2.4), M_PIPE)
for k in range(4):
    yy = -B * 0.18 + k * (B * 0.12)
    cyl(f"Valvula_stem_{k}", (mx - 2.5, yy, F + 3.8), 0.35, 2.2, M_PIPE, verts=10)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.22,
        location=(mx - 2.5, yy, F + 5.1), rotation=(math.radians(90), 0, 0))
    w = bpy.context.active_object; w.name = f"Valvula_rueda_{k}"
    w.data.materials.append(M_RUST)
    parts.append(w)

# ---------- superestructura (popa) + puente + ventanas ----------
ss_x = L * 0.115
cube("Superestructura", (ss_x, 0, F + 9), (L * 0.17, B * 0.82, 15), M_WHITE)
cube("Puente", (ss_x + L * 0.095, 0, F + 14.5), (L * 0.075, B * 0.96, 5.5), M_WHITE)
# alas de puente
cube("Ala_estribor", (ss_x + L * 0.13,  B * 0.47, F + 14.5), (L * 0.03, B * 0.06, 4.5), M_WHITE)
cube("Ala_babor",   (ss_x + L * 0.13, -B * 0.47, F + 14.5), (L * 0.03, B * 0.06, 4.5), M_WHITE)
# ventanas (franjas oscuras)
for zrow in (F + 14.2, F + 15.8):
    cube("Ventanas_puente", (ss_x + L * 0.133, 0, zrow), (0.6, B * 0.9, 1.1), M_DARK)
cube("Ventanas_popa", (ss_x - L * 0.002, 0, F + 12.5), (0.6, B * 0.75, 1.0), M_DARK)
# chimenea con banda negra
cyl("Chimenea", (ss_x - L * 0.055, 0, F + 22), 3.4, 11, M_FUNNEL, verts=20)
cyl("Chimenea_banda", (ss_x - L * 0.055, 0, F + 26), 3.5, 2.2, M_HULL, verts=20)
# mastil de radar
cyl("Mastil", (ss_x + L * 0.095, 0, F + 22.5), 0.5, 6.5, M_RUST, verts=10)
cyl("Barra_radar", (ss_x + L * 0.095, 0, F + 24.5), 0.28, 7.0, M_WHITE, rot=(math.radians(90), 0, 0), verts=8)

# ---------- botes salvavidas en brazos ----------
for side in (-1, 1):
    yy = side * B * 0.44
    bx = ss_x + L * 0.19
    cyl(f"Bote_{side}", (bx, yy, F + 12.8), 1.5, 7.5, M_ORANGE, rot=(0, math.radians(90), 0), verts=12)
    sphere(f"Bote_proa_{side}", (bx + 3.7, yy, F + 12.8), (1.2, 1.5, 1.5), M_ORANGE)
    sphere(f"Bote_popa_{side}", (bx - 3.7, yy, F + 12.8), (1.2, 1.5, 1.5), M_ORANGE)
    for dx in (-2.5, 2.5):
        cyl(f"Davits_{side}_{dx}", (bx + dx, yy, F + 15.5), 0.3, 5.5, M_WHITE, verts=8)

# ---------- grua/mastil de proa + winch ----------
cyl("Mastil_proa", (L * 0.87, 0, F + 8), 0.9, 16, M_RUST, verts=12)
cyl("Pluma_proa", (L * 0.87 - 5, 0, F + 13), 0.55, 12, M_RUST, rot=(0, math.radians(62), 0), verts=10)
cyl("Winch", (L * 0.94, 0, F + 1.6), 1.3, 2.5, M_PIPE, rot=(0, math.radians(90), 0), verts=12)

# ---------- bitas y railing ----------
for k in range(6):
    xx = L * (0.12 + 0.14 * k)
    for side in (-1, 1):
        cyl(f"Bitas_{k}_{side}", (xx, side * B * 0.44, F + 1.7), 0.7, 2.6, M_HULL, verts=10)
# railing: postes + dos tubos continuos por banda
post_xs = [L * 0.06 + i * (L * 0.88 / 22) for i in range(23)]
for side in (-1, 1):
    yy = side * B * 0.465
    for i, xx in enumerate(post_xs):
        cyl(f"Rail_post_{side}_{i}", (xx, yy, F + P["rail_h"]/2 + 0.7), 0.22, P["rail_h"], M_WHITE, verts=6)
    for zz in (F + P["rail_h"] + 0.2, F + P["rail_h"] * 0.55 + 0.2):
        cyl(f"Rail_tubo_{side}_{int(zz)}", (L * 0.5, yy, zz), 0.2, L * 0.88, M_WHITE, rot=(0, math.radians(90), 0), verts=6)

# ---------- auditoria de impresion (reporte; no altera geometria) ----------
def audit_small_parts():
    small = []
    for o in parts:
        if o.type != 'MESH':
            continue
        import mathutils
        dims = o.dimensions
        mn = min(dims.x, dims.y, dims.z) * 1000  # BU->mm
        if mn < P["min_printable_mm"]:
            small.append((o.name, round(mn, 2)))
    return small

small = audit_small_parts()
print("AUDIT_SMALL_PARTS (< %g mm): %d" % (P["min_printable_mm"], len(small)),
      sorted(small, key=lambda x: x[1])[:10])

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
