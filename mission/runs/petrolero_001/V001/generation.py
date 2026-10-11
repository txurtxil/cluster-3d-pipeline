#!/usr/bin/env python3
# gen_petrolero_stress.py — Petrolero oceánico hiperdetallado (STRESS TEST del pipeline)
# Modelo de exposición 1:1000 (250 mm = 250 m). 1 BU = 1 mm. 100% paramétrico via P.
# Uso: blender -b --factory-startup -P gen_petrolero_stress.py -- <salida.blend>
import bpy, math, sys, os
import numpy as np

import json
_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
_par, _out, _stl = (_args + [None, None, None])[:3] if len(_args) >= 3 else (None, (_args + ["/tmp/petrolero.blend"])[0], None)
os.makedirs(os.path.dirname(_out) or ".", exist_ok=True)

P = dict(
    L=250.0, B=42.0, T=13.0, F=19.0,          # eslora, manga, calado, francobordo
    n_stations=21,                             # estaciones del casco (curvas reales)
    tanks=6,
    rail_h=4.5, railing_d=0.5,                 # barandilla
    pipe_d=1.8,                                # tuberia principal
    lifeboat_scale=1.0,
    propeller_thickness=2.4, prop_blades=4,
    detail=1.0,                                # multiplicador de detalle fino
    min_printable_mm=0.4,
    scale=1.0,                                 # escala de impresion (1.0 = 1:1000)
)

if _par:
    P.update(json.load(open(_par)))
L, B, T, F = P["L"], P["B"], P["T"], P["F"]
sc = bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

# ---------------- materiales (distinción de regiones para el VLM) ----------------
def mat(name, c, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

M_HULL  = mat("Casco_negro", (0.025, 0.025, 0.03), 0.42)
M_BOOT  = mat("Obra_viva_roja", (0.48, 0.04, 0.03), 0.5)
M_DECK  = mat("Cubierta_gris", (0.36, 0.35, 0.33), 0.85)
M_WHITE = mat("Superestructura", (0.88, 0.89, 0.91), 0.45)
M_DARK  = mat("Ventanas", (0.04, 0.07, 0.09), 0.15)
M_TANK  = mat("Tanques", (0.45, 0.47, 0.5), 0.6, 0.35)
M_PIPE  = mat("Tuberias", (0.6, 0.61, 0.63), 0.3, 0.75)
M_ORANGE= mat("Botes", (0.95, 0.32, 0.02), 0.5)
M_RUST  = mat("Gruas_mastiles", (0.62, 0.28, 0.05), 0.55, 0.2)
M_METAL = mat("Metal", (0.5, 0.52, 0.55), 0.35, 0.8)
M_FUNNEL= mat("Chimenea", (0.78, 0.12, 0.08), 0.5)

parts = []
def reg(o):
    parts.append(o); return o

def cube(name, loc, dims, m, rot=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    if rot: o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return reg(o)

def cyl(name, loc, r, h, m, rot=(0, 0, 0), verts=14):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(m)
    return reg(o)

def sph(name, loc, scale, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=7, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return reg(o)

def tor(name, loc, R, r, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(m)
    return reg(o)

def rail_run(name, x0, x1, y, z_base, m=M_WHITE):
    """Tramo de barandilla: postes + 2 tubos (diametros desde P)."""
    post_r = max(P["railing_d"]/2, P["min_printable_mm"]/2) * P["detail"]
    tube_r = max(P["railing_d"]*0.45, P["min_printable_mm"]/2) * P["detail"]
    span = x1 - x0
    n = max(2, int(span / 7))
    for i in range(n+1):
        x = x0 + span * i / n
        cyl(f"{name}_post_{i}", (x, y, z_base + P["rail_h"]/2), post_r, P["rail_h"], m, verts=6)
    for zz in (z_base + P["rail_h"], z_base + P["rail_h"]*0.55):
        cyl(f"{name}_tubo_{int(zz*10)}", ((x0+x1)/2, y, zz), tube_r, span, m, rot=(0, math.radians(90), 0), verts=6)

def stairs(name, x, y, z0, z1, width, m=M_METAL):
    """Escalera exterior: 2 largueros + peldaños (>= min_printable)."""
    h = z1 - z0
    run = h * 0.85
    ang = math.atan2(h, run)
    length = math.hypot(h, run)
    for side in (-1, 1):
        cyl(f"{name}_larg_{side}", (x + run/2, y + side*width/2, z0 + h/2), 0.3, length, m,
            rot=(0, math.radians(90) - ang, 0), verts=6)
    steps = max(3, int(h / 1.4))
    for i in range(steps):
        t = (i + 0.5) / steps
        cube(f"{name}_peld_{i}", (x + run*t, y, z0 + h*t), (1.6, width, 0.35), m)

# ================= CASCO: loft 3 franjas, 21 estaciones, secciones redondeadas =================
def half_breadth(t):
    if t < 0.10:  return (B/2) * (0.50 + 0.50 * math.sin(math.pi * t / 0.20))
    if t < 0.80:  return B/2
    u = (t - 0.80) / 0.20
    return (B/2) * max(0.035, (1 - u**1.55) ** 0.8)

def depth_k(t):
    if t < 0.07:  return T * (0.45 + 0.55 * t / 0.07)
    if t < 0.86:  return T
    u = (t - 0.86) / 0.14
    return T * max(0.12, 1 - u**1.35)

def deck_z(t):
    return F + 0.05 * F * (max(0.0, t - 0.55) / 0.45) ** 2

def hull_band(z0f, z1f, m, name, inflate=0.0):
    """Franja del casco entre fracciones z0f..z1f de la altura local (neg=bajo flotacion)."""
    V, Fs = [], []
    prof_rel = [(1.0, 0.0), (0.985, 0.28), (0.94, 0.62), (0.83, 0.88), (0.60, 1.0)]  # (y/b, avance z)
    NP = len(prof_rel) * 2
    for i in range(P["n_stations"]):
        t = i / (P["n_stations"] - 1)
        x = t * L
        b = half_breadth(t) + inflate
        zlo, zhi = -depth_k(t), deck_z(t)
        base = len(V)
        for (fy, fz) in prof_rel:
            frac = z0f + (z1f - z0f) * fz
            zz = frac * zhi if frac >= 0 else -frac * zlo
            V.append((x, fy * b, zz))
        for (fy, fz) in reversed(prof_rel):
            frac = z0f + (z1f - z0f) * fz
            zz = frac * zhi if frac >= 0 else -frac * zlo
            V.append((x, -fy * b, zz))
    for i in range(P["n_stations"] - 1):
        a = i * NP
        for j in range(NP - 1):
            Fs.append((a + j, a + j + 1, a + NP + j + 1, a + NP + j))
    me = bpy.data.meshes.new(name + "_m"); me.from_pydata(V, [], Fs); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m)
    return reg(o)

hull_band(-1.0, 0.0, M_BOOT, "Casco_obra_viva")
hull_band(0.0, 1.0, M_HULL, "Casco_obra_muerta", inflate=0.22)
# cubierta completa
cube("Cubierta", (L/2, 0, F + 0.35), (L * 0.988, B * 0.975, 0.7), M_DECK)
# bulbo de proa + espejo de popa (transom) + quilla
sph("Bulbo_proa", (L * 0.985, 0, -T * 0.42), (L * 0.018, B * 0.105, T * 0.4), M_BOOT)
cube("Espejo_popa", (-0.4, 0, F * 0.35), (0.8, B * 0.99, F * 0.75), M_HULL)
cube("Quilla", (L * 0.45, 0, -T - 0.3), (L * 0.8, 1.6, 0.9), M_BOOT)

# ================= POPA: timon, eje, helice =================
cube("Timon", (-2.6, 0, -T * 0.35), (4.6, 1.1, T * 1.25), M_HULL)
cyl("Eje", (-4.2, 0, -T * 0.5), 0.9, 5.0, M_METAL, rot=(0, math.radians(90), 0))
cyl("Helice_buje", (-6.6, 0, -T * 0.5), 1.5, 2.2, M_METAL, rot=(0, math.radians(90), 0))
for k in range(P["prop_blades"]):
    ang = k * 2 * math.pi / P["prop_blades"]
    bl = cube(f"Helice_pala_{k}", (-6.6, 0, -T * 0.5),
              (0.7, 7.2, P["propeller_thickness"]), M_METAL)
    bl.rotation_euler = (math.radians(22), 0, ang)
cyl("Bocina_popa", (-1.2, B * 0.42, F * 0.55), 0.8, 1.6, M_METAL)
cyl("Bocina_popa_b", (-1.2, -B * 0.42, F * 0.55), 0.8, 1.6, M_METAL)

# ================= 6 TANQUES con cofre, tapa, respiradero, valvula, escalera =================
tank_L = L * 0.088
gap = L * 0.020
x0 = L * 0.315
for i in range(P["tanks"]):
    cx = x0 + i * (tank_L + gap) + tank_L / 2
    cy = 0
    cube(f"Tanque_{i+1}", (cx, cy, F + 4.2), (tank_L, B * 0.74, 7.6), M_TANK)
    cw = 1.0
    cube(f"CofreA_{i}", (cx, cy + B*0.37 + cw/2, F + 8.3), (tank_L + 1.8, cw, 1.3), M_TANK)
    cube(f"CofreB_{i}", (cx, cy - B*0.37 - cw/2, F + 8.3), (tank_L + 1.8, cw, 1.3), M_TANK)
    cube(f"CofreC_{i}", (cx + tank_L/2 + 0.9, cy, F + 8.3), (cw, B*0.74, 1.3), M_TANK)
    cube(f"CofreD_{i}", (cx - tank_L/2 - 0.9, cy, F + 8.3), (cw, B*0.74, 1.3), M_TANK)
    cube(f"Tapa_{i}", (cx, cy, F + 9.3), (tank_L * 0.5, B * 0.42, 0.9), M_TANK)
    # respiraderos (2 tubos verticales con sombrerete)
    for sx in (-1, 1):
        vx = cx + sx * tank_L * 0.32
        cyl(f"Respiradero_{i}_{sx}", (vx, cy + B*0.2, F + 11.5), 0.55, 4.4, M_PIPE, verts=10)
        cyl(f"Respiradero_cap_{i}_{sx}", (vx, cy + B*0.2, F + 13.9), 0.9, 0.6, M_METAL, verts=10)
    # valvula de fondo + pequeña tuberia lateral
    cyl(f"ValvTanque_stem_{i}", (cx - tank_L/2 - 1.6, cy, F + 5.5), 0.35, 2.4, M_PIPE, verts=8)
    tor(f"ValvTanque_rueda_{i}", (cx - tank_L/2 - 1.6, cy, F + 7.0), 0.85, 0.2, M_RUST,
        rot=(math.radians(90), 0, 0))
    # escalera de acceso al tanque
    stairs(f"EscTanque_{i}", cx + tank_L/2 - 1.2, cy - B*0.40, F + 0.7, F + 8.2, 2.2, M_METAL)

# ================= CUBIERTA: pasarela, manifold, cajas, bitas =================
cube("Pasarela", (L * 0.5, 0, F + 1.0), (L * 0.60, 3.2, 0.5), M_METAL)
mx = L * 0.265
cube("Manifold_cuerpo", (mx, 0, F + 2.4), (4.5, B * 0.55, 2.6), M_PIPE)
for yy in (-B*0.16, B*0.16):
    cyl("Linea_long", (L * 0.52, yy, F + 2.4), P["pipe_d"]/2, L * 0.56, M_PIPE,
        rot=(0, math.radians(90), 0), verts=12)
for k in range(5):  # derivaciones + ruedas
    yy = -B * 0.22 + k * (B * 0.11)
    cyl(f"Deriv_{k}", (mx - 1.5, yy, F + 4.0), 0.35, 2.6, M_PIPE, verts=8)
    tor(f"Rueda_{k}", (mx - 1.5, yy, F + 5.5), 0.85, 0.2, M_RUST, rot=(math.radians(90), 0, 0))
    # soportes de tuberia cada poco
for k in range(12):
    xx = L * 0.30 + k * L * 0.045
    for yy in (-B*0.16, B*0.16):
        cube(f"Soporte_{k}_{yy>0}", (xx, yy, F + 1.3), (0.7, 0.7, 1.4), M_METAL)
# cajas tecnicas + registros + escotillas
for k in range(4):
    cube(f"Caja_tec_{k}", (L * (0.36 + 0.11 * k), B * 0.34, F + 2.2), (5, 4, 3.4), M_TANK)
for k in range(6):
    cyl(f"Escotilla_{k}", (L * (0.33 + 0.075 * k), -B * 0.30, F + 1.1), 1.5, 0.6, M_METAL, verts=12)
for k in range(5):  # bitas/bolardos
    xx = L * (0.10 + 0.17 * k)
    for side in (-1, 1):
        cyl(f"Bitas_{k}_{side}", (xx, side * B * 0.455, F + 1.8), 0.75, 3.0, M_HULL, verts=10)

# ================= SUPERESTRUCTURA 3 niveles + puente + ventanas =================
ssx = L * 0.105
cube("SS_N1", (ssx, 0, F + 8.5), (L * 0.19, B * 0.84, 16), M_WHITE)
cube("SS_N2", (ssx + L*0.01, 0, F + 15.5), (L * 0.15, B * 0.80, 6.5), M_WHITE)
cube("Puente", (ssx + L*0.075, 0, F + 20.5), (L * 0.085, B * 0.97, 5.0), M_WHITE)
cube("Ala_E", (ssx + L*0.115, B*0.475, F + 20.0), (L*0.035, B*0.07, 4.2), M_WHITE)
cube("Ala_B", (ssx + L*0.115, -B*0.475, F + 20.0), (L*0.035, B*0.07, 4.2), M_WHITE)
cube("SS_cubierta_sup", (ssx, 0, F + 23.3), (L * 0.13, B * 0.78, 0.7), M_DECK)
for zi, zw in ((F + 20.2, 1.3), (F + 21.6, 1.2), (F + 14.8, 1.1), (F + 11.0, 1.0)):
    w = B * 0.90 if zi > F + 19 else B * 0.72
    cube("Ventanas", (ssx + L * (0.118 if zi > F + 19 else 0.048), 0, zi), (0.7, w, zw), M_DARK)
cube("Puerta_SS", (ssx + L*0.096, -B*0.2, F + 5.0), (0.8, 3.2, 5.5), M_DARK)
stairs("Escalera_SS", ssx + L*0.10, B * 0.30, F + 0.7, F + 15.5, 2.6, M_METAL)
rail_run("RailSS", ssx - L*0.06, ssx + L*0.10, B*0.40, F + 23.6, M_WHITE)
rail_run("RailSS_b", ssx - L*0.06, ssx + L*0.10, -B*0.40, F + 23.6, M_WHITE)

# ================= CHIMENEA =================
fx = ssx - L * 0.055
cyl("Chimenea_baja", (fx, 0, F + 26), 3.6, 9, M_FUNNEL, verts=20)
cyl("Chimenea_alta", (fx, 0, F + 32), 2.9, 5, M_FUNNEL, verts=20)
cyl("Chimenea_banda", (fx, 0, F + 29.5), 3.7, 2.0, M_HULL, verts=20)
cyl("Chimenea_sombrero", (fx, 0, F + 35.2), 3.4, 1.0, M_HULL, verts=20)
for sx in (-1, 1):
    cyl(f"Escape_{sx}", (fx + sx * 1.2, 0, F + 36.5), 0.8, 2.4, M_METAL, verts=10)
cyl("Chimenea_plataforma", (fx, 0, F + 30.8), 4.4, 0.5, M_METAL, verts=20)

# ================= MÁSTILES =================
cyl("Mastil_proa", (L * 0.875, 0, F + 10), 0.8, 20, M_RUST, verts=12)
cyl("Plataforma_proa", (L * 0.875, 0, F + 17.5), 2.2, 0.5, M_METAL, verts=12)
cyl("Barra_radar_proa", (L * 0.875, 0, F + 19.5), 0.3, 8.0, M_WHITE, rot=(math.radians(90), 0, 0), verts=8)
for sx in (-1, 1):
    cyl(f"Antena_proa_{sx}", (L * 0.875 + sx * 1.2, 0, F + 23), 0.12, 6, M_METAL, verts=6)
sph("Luz_proa", (L * 0.875, 0, F + 20.6), (0.5, 0.5, 0.5), M_ORANGE)
cyl("Mastil_popa", (fx + 2, 0, F + 39), 0.35, 8, M_METAL, verts=8)
cyl("Antena_popa", (fx + 2, 0, F + 43.5), 0.1, 3.5, M_METAL, verts=6)

# ================= 2 GRÚAS =================
def crane(name, cx):
    cube(f"{name}_base", (cx, 0, F + 1.6), (6, 6, 2.4), M_METAL)
    cyl(f"{name}_columna", (cx, 0, F + 8.5), 1.5, 12, M_RUST, verts=14)
    cyl(f"{name}_pluma", (cx + 7, 0, F + 13.5), 0.8, 16, M_RUST,
        rot=(0, math.radians(68), 0), verts=10)
    cyl(f"{name}_cilindro", (cx + 3.2, 0, F + 10.5), 0.45, 7, M_METAL,
        rot=(0, math.radians(50), 0), verts=8)
    cyl(f"{name}_cable", (cx + 13.5, 0, F + 9.5), max(0.18, P["min_printable_mm"]/2), 7.5, M_METAL, verts=6)
    tor(f"{name}_gancho", (cx + 13.5, 0, F + 5.2), 0.8, 0.25, M_METAL, rot=(math.radians(90), 0, 0))
crane("Grua_popa", L * 0.245)
crane("Grua_proa", L * 0.76)

# ================= BOTES SALVAVIDAS =================
_lb = P["lifeboat_scale"]
for side in (-1, 1):
    yy = side * B * 0.44
    bx = ssx + L * 0.205
    cyl(f"Bote_{side}", (bx, yy, F + 17.0), 1.5*_lb, 8.0*_lb, M_ORANGE,
        rot=(0, math.radians(90), 0), verts=12)
    sph(f"Bote_proa_{side}", (bx + 4.0*_lb, yy, F + 17.0), (1.2*_lb, 1.5*_lb, 1.5*_lb), M_ORANGE)
    sph(f"Bote_popa_{side}", (bx - 4.0*_lb, yy, F + 17.0), (1.2*_lb, 1.5*_lb, 1.5*_lb), M_ORANGE)
    cube(f"Bote_cabina_{side}", (bx, yy, F + 18.3), (3.5*_lb, 1.6*_lb, 1.2*_lb), M_WHITE)
    for dx in (-3.2, 3.2):
        cyl(f"Davit_{side}_{dx}", (bx + dx, yy, F + 20.2), 0.28, 6.0, M_WHITE, verts=8)
        cyl(f"Davit_brazo_{side}_{dx}", (bx + dx, yy, F + 23.0), 0.24, 3.2, M_WHITE,
            rot=(math.radians(90), 0, 0), verts=6)

# ================= RAILING completo =================
rail_run("RailEstribor", L * 0.06, L * 0.955, B * 0.468, F + 0.7)
rail_run("RailBabor", L * 0.06, L * 0.955, -B * 0.468, F + 0.7)
# proa: travesaño
for zz in (F + P["rail_h"] + 0.7, F + P["rail_h"]*0.55 + 0.7):
    cyl("Rail_proa_cierre", (L * 0.955, 0, zz), 0.22, B * 0.90, M_WHITE,
        rot=(math.radians(90), 0, 0), verts=6)

# ================= PROA: ancla, escobenes, cadena, cabrestante =================
cube("Ancla_mango", (L * 0.955, 0, F + 2.2), (1.0, 1.0, 7.0), M_METAL, rot=(0, math.radians(20), 0))
cube("Ancla_brazo", (L * 0.945, 0, F - 0.8), (3.6, 1.2, 1.4), M_METAL, rot=(0, math.radians(20), 0))
for side in (-1, 1):
    cyl(f"Escoben_{side}", (L * 0.975, side * B * 0.30, F * 0.5), 1.1, 2.6, M_HULL,
        rot=(math.radians(90), 0, 0), verts=10)
for k in range(7):  # cadena: eslabones torus >= min_printable
    tor(f"Cadena_{k}", (L * 0.935 - k * 1.7, 0, F + 1.2 - k * 0.35),
        0.75, max(0.22, P["min_printable_mm"]/2), M_METAL,
        rot=(math.radians(90 if k % 2 else 0), 0, 0))
cyl("Cabrestante", (L * 0.90, 0, F + 1.8), 1.4, 3.0, M_METAL, rot=(0, math.radians(90), 0), verts=12)
for side in (-1, 1):
    cube(f"Cabrestante_sop_{side}", (L * 0.90, side * 1.9, F + 1.2), (1.0, 0.6, 2.4), M_METAL)

# ================= ESCALERAS adicionales + plataformas =================
stairs("Escalera_popa", L * 0.055, -B * 0.30, F + 0.7, F + 8.0, 2.4, M_METAL)
cube("Plataforma_tecnica", (L * 0.245, 0, F + 5.6), (7, B * 0.5, 0.6), M_METAL)

# ================= AUDIT de impresión (reporte, no altera geometria) =================
import mathutils
def audit():
    small, empty = [], []
    for o in parts:
        if o.type != 'MESH':
            continue
        if len(o.data.polygons) == 0:
            empty.append(o.name); continue
        dims = o.dimensions
        mn = min(dims.x, dims.y, dims.z) * 1000
        if mn < P["min_printable_mm"]:
            small.append((o.name, round(mn, 2)))
    return small, empty

small, empty = audit()
print("AUDIT_SMALL (<%.2g mm): %d" % (P["min_printable_mm"], len(small)), sorted(small, key=lambda x: x[1])[:12])
print("AUDIT_EMPTY:", len(empty), empty[:6])
print("OBJECT_COUNT:", len(parts))

# escala de impresion
if P["scale"] != 1.0:
    bpy.ops.object.select_all(action='SELECT')
    for o in parts:
        o.scale = (P["scale"],) * 3
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

bpy.ops.wm.save_as_mainfile(filepath=_out)

# --- adaptacion mission-loop: metricas fisicas + STL ---
dgf = bpy.context.evaluated_depsgraph_get()
xs, ys, zs = [], [], []
bad = 0
for o in parts:
    if o.type != "MESH":
        continue
    ev = o.evaluated_get(dgf)
    me = ev.to_mesh()
    for v in me.vertices:
        w = ev.matrix_world @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    ev.to_mesh_clear()
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    bad += sum(1 for vv in ec.values() if vv != 2)
if _stl:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.wm.stl_export(filepath=_stl)
print("GEN_OK", json.dumps({
    "params": {k: P[k] for k in ("L", "B", "T", "F", "tanks", "detail", "scale")},
    "counts": {"PARTS": len([o for o in parts if o.type == "MESH"])},
    "dims": {"L": round(max(xs) - min(xs), 3), "B": round(max(ys) - min(ys), 3),
             "H": round(max(zs) - min(zs), 3)},
    "manifold_bad_edges": bad,
    "audit_small": len(small), "audit_empty": len(empty),
}))
