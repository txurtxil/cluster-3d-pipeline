#!/usr/bin/env python3
# gen_petrolero_v2.py — PETROLERO_QUALITY_V2 (identidad oil/product tanker)
# Basado en gen_petrolero_stress (V1, 361 obj). Cambios de identidad naval:
#   V2-1: adios tapas tipo bodega (bulk carrier) -> 18 DOMOS de tanque circulares
#         (3 hileras x 6 tanques) con manhole; cubierta limpia y al ras
#   V2-2: SIN gruas de cubierta (las gruas son de granelero) -> derrick de
#         manifold pequeno (hose handling)
#   V2-3: manifold a media eslora AMBAS BANDAS con ruedas grandes (firma petrolero)
#   V2-4: 2 mastiles de ventilacion (vent masts) - silueta petrolera
#   V2-5: quillas de rolido (bilge keels); manga 42->40; mayor sheer de proa
#   V2-6: crossovers transversales de linea de carga en cada limite de tanque
# 1 BU = 1 mm. Uso: blender -b --factory-startup -P gen_petrolero_v2.py -- <salida.blend>
import bpy, math, sys, os
import numpy as np

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/petrolero_v2.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

P = dict(
    L=250.0, B=40.0, T=13.0, F=19.0,
    n_stations=21,
    tanks=6,
    rail_h=4.5, railing_d=0.5,
    pipe_d=1.8,
    lifeboat_scale=1.0,
    propeller_thickness=2.4, prop_blades=4,
    detail=1.0,
    min_printable_mm=0.4,
    scale=1.0,
)

L, B, T, F = P["L"], P["B"], P["T"], P["F"]
sc = bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

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
    # V3.4: sube hacia +X con pendiente correcta (antes 90-ang -> "del reves")
    h = z1 - z0
    run = h * 0.85
    ang = math.atan2(h, run)
    length = math.hypot(h, run)
    for side in (-1, 1):
        cube(f"{name}_larg_{side}", (x + run/2, y + side*width/2, z0 + h/2),
             (length, 0.35, 0.35), m, rot=(0, -ang, 0))
    steps = max(3, int(h / 1.4))
    for i in range(steps):
        t = (i + 0.5) / steps
        cube(f"{name}_peld_{i}", (x + run*t, y, z0 + h*t), (1.6, width, 0.35), m)
    # pasamano
    cube(f"{name}_mano", (x + run/2, y + width/2, z0 + h/2 + 1.2),
         (length, 0.18, 0.18), m, rot=(0, -ang, 0))

# ================= CASCO (manga 40, mayor sheer de proa) =================
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
    return F + 0.075 * F * (max(0.0, t - 0.5) / 0.5) ** 2   # V2: sheer mas marcado

def prof_y(fz, table):
    """interpola fy en la tabla prof_rel para un fz arbitrario."""
    if fz <= table[0][1]: return table[0][0]
    for k in range(1, len(table)):
        if fz <= table[k][1]:
            (y0, z0), (y1, z1) = table[k-1], table[k]
            return y0 + (y1 - y0) * (fz - z0) / max(z1 - z0, 1e-9)
    return table[-1][0]

def hull_band(z0f, z1f, m, name, inflate=0.0):
    # V3.1 (fix seccion invertida + continuidad en flotacion):
    # prof_rel describe la seccion COMPLETA de cubierta (fz=0, manga max) a
    # quilla (fz=1, 0.6b); g = 1 - fz mapea a altura (g=1 cubierta, g=0 quilla).
    # wl = g de la flotacion. La banda NEGRA toma fz in [0, 1-wl] (cubierta ->
    # flotacion), la ROJA fz in [1-wl, 1] (flotacion -> quilla). Ambas comparten
    # el punto de la flotacion -> casco continuo, manga decreciente hacia quilla.
    V, Fs = [], []
    table = [(1.0, 0.0), (0.995, 0.16), (0.98, 0.38), (0.945, 0.62),
             (0.885, 0.82), (0.78, 0.94), (0.60, 1.0)]
    NS = 8                                  # muestras por banda
    NP = NS * 2
    for i in range(P["n_stations"]):
        t = i / (P["n_stations"] - 1)
        x = t * L
        b = half_breadth(t) + inflate
        zlo, zhi = -depth_k(t), deck_z(t)
        wl = (0.0 - zlo) / (zhi - zlo)
        fz_lo, fz_hi = (0.0, 1.0 - wl) if z1f == 1.0 else (1.0 - wl, 1.0)
        base = len(V)
        for s in range(NS):
            fz = fz_lo + (fz_hi - fz_lo) * s / (NS - 1)
            g = 1.0 - fz
            y = prof_y(fz, table) * b
            V.append((x, y, zlo + (zhi - zlo) * g))
        for s in range(NS - 1, -1, -1):   # espejo en orden inverso: normal exterior
            fz = fz_lo + (fz_hi - fz_lo) * s / (NS - 1)
            g = 1.0 - fz
            y = prof_y(fz, table) * b
            V.append((x, -y, zlo + (zhi - zlo) * g))
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
# V3: cubierta como loft acoplado a estaciones (sin voladizos en proa/popa)
def deck_loft():
    V, Fs = [], []
    NP = 4
    for i in range(P["n_stations"]):
        t = i / (P["n_stations"] - 1)
        x = t * L
        b = half_breadth(t) + 0.35
        zt = deck_z(t) + 0.35
        zb = zt - 0.7
        V += [(x, b, zt), (x, -b, zt), (x, -b, zb), (x, b, zb)]
    for i in range(P["n_stations"] - 1):
        a = i * NP
        for j in range(NP):
            k = (j + 1) % NP
            Fs.append((a + j, a + k, a + NP + k, a + NP + j))
    # V3.4: tapar proa y popa de la cubierta (mismo metodo de abanico)
    for ring, dirx in ((0, -1), (P["n_stations"] - 1, +1)):
        base = ring * NP
        cy = sum(V[base+j][1] for j in range(NP)) / NP
        cz = sum(V[base+j][2] for j in range(NP)) / NP
        ci = len(V)
        V.append((V[base][0], cy, cz))
        for j in range(NP):
            k = (j + 1) % NP
            a, b = base + j, base + k
            ax, ay, az = V[a][0]-V[ci][0], V[a][1]-V[ci][1], V[a][2]-V[ci][2]
            bx, by, bz = V[b][0]-V[ci][0], V[b][1]-V[ci][1], V[b][2]-V[ci][2]
            if ((ay*bz - az*by) > 0) == (dirx > 0):
                Fs.append((ci, a, b))
            else:
                Fs.append((ci, b, a))
    me = bpy.data.meshes.new("Cubierta_m"); me.from_pydata(V, [], Fs); me.update()
    o = bpy.data.objects.new("Cubierta", me); sc.collection.objects.link(o)
    o.data.materials.append(M_DECK)
    return reg(o)
deck_loft()
# V3: bulbo integrado (mas dentro del casco, punta sobresale hacia proa)
sph("Bulbo_proa", (L * 0.978, 0, -T * 0.40), (L * 0.021, B * 0.10, T * 0.42), M_BOOT)
# V3.4: sin placa de transom aparte; popa y proa cerradas por las tapas del loft
# (cap() en hull_band) y la cubierta tambien tapada -> cero huecos en extremos.
cube("Quilla", (L * 0.45, 0, -T - 0.3), (L * 0.8, 1.6, 0.9), M_BOOT)
# V2-5: quillas de rolido (bilge keels)
for side in (-1, 1):
    cube(f"Bilge_keel_{side}", (L * 0.5, side * B * 0.485, -T * 0.55), (L * 0.62, 0.9, 2.2), M_BOOT)

# ================= POPA =================
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

# ================= V2-1: DOMOS DE TANQUE (18) + manholes =================
# 6 tanques x 3 hileras de domos: cubierta al ras, sin bodegas
tank_L = L * 0.088
gap = L * 0.020
x0 = L * 0.315
row_ys = (-B * 0.26, 0.0, B * 0.26)
for i in range(P["tanks"]):
    cx = x0 + i * (tank_L + gap) + tank_L / 2
    # franja de limite de tanque: linea baja longitudinal (acero)
    for ry in (B * 0.375, -B * 0.375):
        cube(f"Limite_tanque_{i}_{ry>0}", (cx, ry, F + 0.85), (tank_L + gap, 0.6, 0.5), M_METAL)
    for r, ry in enumerate(row_ys):
        for dx in (-tank_L * 0.22, tank_L * 0.22):
            dxr = cx + dx
            # domo: cilindro + sombrerete esferico
            cyl(f"Domo_{i}_{r}_{dx>0}", (dxr, ry, F + 2.2), 3.4, 2.6, M_TANK, verts=16)
            sph(f"Domo_cap_{i}_{r}_{dx>0}", (dxr, ry, F + 3.6), (3.4, 3.4, 1.5), M_TANK)
            cyl(f"Manhole_{i}_{r}_{dx>0}", (dxr, ry, F + 5.3), 1.0, 0.9, M_METAL, verts=12)
            tor(f"Manhole_ring_{i}_{r}_{dx>0}", (dxr, ry, F + 5.8), 1.0, 0.18, M_METAL)
# escalera de acceso a domo por tanque
for i in range(P["tanks"]):
    cx = x0 + i * (tank_L + gap) + tank_L / 2
    stairs(f"EscTanque_{i}", cx + tank_L/2 - 1.0, -B * 0.38, F + 0.7, F + 4.6, 2.2, M_METAL)

# ================= V2-6: lineas de carga + crossovers + soportes =================
for yy in (-B*0.16, B*0.16):
    cyl("Linea_long", (L * 0.52, yy, F + 1.9), P["pipe_d"]/2, L * 0.56, M_PIPE,
        rot=(0, math.radians(90), 0), verts=12)
for i in range(P["tanks"] + 1):   # crossover transversal en cada limite
    cx = x0 - gap/2 + i * (tank_L + gap)
    if L * 0.30 < cx < L * 0.90:
        cyl(f"Crossover_{i}", (cx, 0, F + 1.9), P["pipe_d"]*0.32, B * 0.34, M_PIPE,
            rot=(math.radians(90), 0, 0), verts=10)
for k in range(12):
    xx = L * 0.30 + k * L * 0.045
    for yy in (-B*0.16, B*0.16):
        cube(f"Soporte_{k}_{yy>0}", (xx, yy, F + 0.9), (0.7, 0.7, 1.2), M_METAL)

# ================= V2-3: MANIFOLD A MEDIA ESLORA AMBAS BANDAS =================
mm_x = L * 0.50
for side in (-1, 1):
    yy = side * B * 0.40
    cube(f"Manifold_{side}", (mm_x, yy, F + 2.6), (10, 2.6, 2.2), M_PIPE)
    cyl(f"Manifold_riser_{side}", (mm_x, yy, F + 4.6), 0.55, 2.4, M_PIPE, verts=10)
    for k in range(4):
        vx = mm_x - 3.6 + k * 2.4
        cyl(f"ValvM_stem_{side}_{k}", (vx, yy, F + 4.3), 0.32, 2.0, M_PIPE, verts=8)
        tor(f"ValvM_rueda_{side}_{k}", (vx, yy, F + 5.5), 1.0, 0.22, M_RUST,
            rot=(math.radians(90), 0, 0))
# tubo central que une ambas bandas
cyl("Manifold_cross", (mm_x, 0, F + 2.6), 0.55, B * 0.82, M_PIPE,
    rot=(math.radians(90), 0, 0), verts=12)
# V2-2: derrick pequeno de manifold (hose handling) - sustituye a las gruas
dmx = mm_x - 12
cube("Derrick_base", (dmx, 0, F + 1.4), (4, 4, 1.8), M_METAL)
cyl("Derrick_poste", (dmx, 0, F + 7), 0.9, 9.5, M_RUST, verts=12)
cyl("Derrick_brazo", (dmx + 3.5, 0, F + 10.5), 0.5, 8.5, M_RUST,
    rot=(0, math.radians(55), 0), verts=10)
cyl("Derrick_cable", (dmx + 7, 0, F + 7.5), max(0.18, P["min_printable_mm"]/2), 6.0, M_METAL, verts=6)
tor("Derrick_gancho", (dmx + 7, 0, F + 4.2), 0.7, 0.22, M_METAL, rot=(math.radians(90), 0, 0))

# ================= V2-4: MASTILES DE VENTILACION (2) =================
for vi, vx in enumerate((L * 0.335, L * 0.865)):
    cyl(f"VentMast_{vi}", (vx, 0, F + 12), 1.1, 22, M_RUST, verts=12)
    cyl(f"VentMast_brazo_{vi}", (vx, 0, F + 21), 0.45, 9, M_PIPE,
        rot=(math.radians(90), 0, 0), verts=8)
    for sy in (-1, 1):
        cyl(f"VentMast_tubo_{vi}_{sy}", (vx, sy * 4.2, F + 18), 0.4, 6.5, M_PIPE, verts=8)
        sph(f"VentMast_cap_{vi}_{sy}", (vx, sy * 4.2, F + 21.6), (0.8, 0.8, 0.5), M_METAL)
    sph(f"VentMast_luz_{vi}", (vx, 0, F + 23.4), (0.6, 0.6, 0.6), M_ORANGE)

# ================= CUBIERTA: pasarela, cajas, escotillas, bitas =================
cube("Pasarela", (L * 0.5, 0, F + 0.9), (L * 0.60, 3.2, 0.5), M_METAL)
for k in range(4):
    cube(f"Caja_tec_{k}", (L * (0.36 + 0.11 * k), B * 0.34, F + 1.9), (4.5, 3.5, 2.6), M_TANK)
for k in range(6):
    cyl(f"Escotilla_{k}", (L * (0.33 + 0.075 * k), -B * 0.30, F + 1.0), 1.4, 0.6, M_METAL, verts=12)
for k in range(5):
    xx = L * (0.10 + 0.17 * k)
    for side in (-1, 1):
        cyl(f"Bitas_{k}_{side}", (xx, side * B * 0.455, F + 1.8), 0.75, 3.0, M_HULL, verts=10)

# ================= SUPERESTRUCTURA (V3.2: castillo por gradines, sin flotantes) =================
ssx = L * 0.105
N1 = cube("SS_N1", (ssx, 0, F + 6.5), (L * 0.155, B * 0.72, 13), M_WHITE)
N2 = cube("SS_N2", (ssx + L*0.008, 0, F + 14.2), (L * 0.115, B * 0.64, 5.4), M_WHITE)
DH = cube("SS_DH", (ssx + L*0.016, 0, F + 18.2), (L * 0.085, B * 0.56, 3.4), M_WHITE)
PB = cube("Puente", (ssx + L*0.055, 0, F + 21.6), (L * 0.075, B * 0.88, 3.6), M_WHITE)
# alas de puente: cortas y con soporte diagonal (nada volado sin apoyo)
for side in (-1, 1):
    cube(f"Ala_{side}", (ssx + L*0.085, side*B*0.465, F + 21.3), (L*0.03, B*0.07, 3.0), M_WHITE)
    cyl(f"Ala_sop_{side}", (ssx + L*0.075, side*B*0.44, F + 19.8), 0.3, 4.5, M_WHITE,
        rot=(math.radians(35)*side, 0, 0), verts=8)
# cubierta superior a la huella de N2 (sin voladizos); railing inset dentro de la losa
cube("SS_cubierta_sup", (ssx + L*0.008, 0, F + 17.15), (L * 0.115, B * 0.64, 0.6), M_DECK)
N1_TOP = F + 13.0
N2_TOP = F + 17.15
for zi, zw, ww in ((F + 21.5, 1.2, B*0.84), (F + 18.4, 1.0, B*0.52),
                   (F + 14.0, 1.0, B*0.60), (F + 9.0, 1.0, B*0.68)):
    xoff = 0.093 if zi > F + 20 else (0.058 if zi > F + 16 else (0.066 if zi > F + 12 else 0.083))
    cube("Ventanas", (ssx + L*xoff, 0, zi), (0.7, ww, zw), M_DARK)
cube("Puerta_SS", (ssx + L*0.078, -B*0.2, F + 4.0), (0.8, 3.0, 5.0), M_DARK)
# escalera exterior apoyada en la cara de proa de N1
stairs("Escalera_SS", ssx + L*0.079, B * 0.26, F + 0.7, F + 13.0, 2.4, M_METAL)
rail_run("RailSS", ssx - L*0.045, ssx + L*0.06, B*0.27, N2_TOP + 0.3, M_WHITE)
rail_run("RailSS_b", ssx - L*0.045, ssx + L*0.06, -B*0.27, N2_TOP + 0.3, M_WHITE)

# ================= CHIMENEA (V3.3: APOYADA sobre cubierta de N2, no volando) =================
# Causa V3.2: fx = ssx-0.055L quedaba popa del puente (hueco de 8.5 mm sobre N1).
# Fix: base sobre el techo de N2 (SS_cubierta_sup, z=F+17.45) y x centrada en N2.
fx = ssx + L * 0.008            # eje de N2
FUN_BASE = F + 17.45
cyl("Chimenea_baja", (fx, 0, FUN_BASE + 4.5), 3.6, 9, M_FUNNEL, verts=20)
cyl("Chimenea_alta", (fx, 0, FUN_BASE + 10.5), 2.9, 5, M_FUNNEL, verts=20)
cyl("Chimenea_banda", (fx, 0, FUN_BASE + 8.0), 3.7, 2.0, M_HULL, verts=20)
cyl("Chimenea_plataforma", (fx, 0, FUN_BASE + 9.3), 4.4, 0.5, M_METAL, verts=20)
cyl("Chimenea_sombrero", (fx, 0, FUN_BASE + 13.7), 3.4, 1.0, M_HULL, verts=20)
for sx in (-1, 1):
    cyl(f"Escape_{sx}", (fx + sx * 1.2, 0, FUN_BASE + 15.0), 0.8, 2.4, M_METAL, verts=10)

# ================= MÁSTILES =================
cyl("Mastil_proa", (L * 0.905, 0, F + 9), 0.8, 18, M_RUST, verts=12)
cyl("Plataforma_proa", (L * 0.905, 0, F + 15.5), 2.2, 0.5, M_METAL, verts=12)
cyl("Barra_radar_proa", (L * 0.905, 0, F + 17.5), 0.3, 8.0, M_WHITE, rot=(math.radians(90), 0, 0), verts=8)
for sx in (-1, 1):
    cyl(f"Antena_proa_{sx}", (L * 0.905 + sx * 1.2, 0, F + 21), 0.12, 6, M_METAL, verts=6)
sph("Luz_proa", (L * 0.905, 0, F + 18.6), (0.5, 0.5, 0.5), M_ORANGE)
# V3.3: mastil de popa sobre el techo del puente (la chimenea ocupa su x antiguo)
_mastx = ssx + L * 0.085
_PB_TOP = F + 21.6 + 1.8
cyl("Mastil_popa", (_mastx, 0, _PB_TOP + 4.0), 0.35, 8, M_METAL, verts=8)
cyl("Antena_popa", (_mastx, 0, _PB_TOP + 8.7), 0.1, 3.5, M_METAL, verts=6)

# ================= BOTES SALVAVIDAS (V3.2: sobre cubierta de botes = techo de N2) =================
_lb = P["lifeboat_scale"]
BOAT_DECK = F + 17.45          # sobre SS_cubierta_sup (techo de N2)
for side in (-1, 1):
    yy = side * B * 0.24        # dentro de la huella de N2 (media manga 12.8)
    bx = ssx + L * 0.008
    cyl(f"Bote_{side}", (bx, yy, BOAT_DECK + 1.2*_lb), 1.5*_lb, 8.0*_lb, M_ORANGE,
        rot=(0, math.radians(90), 0), verts=12)
    sph(f"Bote_proa_{side}", (bx + 4.0*_lb, yy, BOAT_DECK + 1.2*_lb), (1.2*_lb, 1.5*_lb, 1.5*_lb), M_ORANGE)
    sph(f"Bote_popa_{side}", (bx - 4.0*_lb, yy, BOAT_DECK + 1.2*_lb), (1.2*_lb, 1.5*_lb, 1.5*_lb), M_ORANGE)
    cube(f"Bote_cabina_{side}", (bx, yy, BOAT_DECK + 2.5*_lb), (3.5*_lb, 1.6*_lb, 1.2*_lb), M_WHITE)
    for dx in (-3.2, 3.2):
        cyl(f"Davit_{side}_{dx}", (bx + dx, yy, BOAT_DECK + 3.0), 0.28, 6.0, M_WHITE, verts=8)
        cyl(f"Davit_brazo_{side}_{dx}", (bx + dx, yy, BOAT_DECK + 6.0), 0.24, 3.2, M_WHITE,
            rot=(math.radians(90), 0, 0), verts=6)

# ================= RAILING =================
rail_run("RailEstribor", L * 0.06, L * 0.955, B * 0.468, F + 0.7)
rail_run("RailBabor", L * 0.06, L * 0.955, -B * 0.468, F + 0.7)
for zz in (F + P["rail_h"] + 0.7, F + P["rail_h"]*0.55 + 0.7):
    cyl("Rail_proa_cierre", (L * 0.955, 0, zz), 0.22, B * 0.90, M_WHITE,
        rot=(math.radians(90), 0, 0), verts=6)

# ================= PROA =================
cube("Ancla_mango", (L * 0.955, 0, F + 2.2), (1.0, 1.0, 7.0), M_METAL, rot=(0, math.radians(20), 0))
cube("Ancla_brazo", (L * 0.945, 0, F - 0.8), (3.6, 1.2, 1.4), M_METAL, rot=(0, math.radians(20), 0))
for side in (-1, 1):
    cyl(f"Escoben_{side}", (L * 0.975, side * B * 0.30, F * 0.5), 1.1, 2.6, M_HULL,
        rot=(math.radians(90), 0, 0), verts=10)
for k in range(7):
    tor(f"Cadena_{k}", (L * 0.935 - k * 1.7, 0, F + 1.2 - k * 0.35),
        0.75, max(0.22, P["min_printable_mm"]/2), M_METAL,
        rot=(math.radians(90 if k % 2 else 0), 0, 0))
cyl("Cabrestante", (L * 0.90, 0, F + 1.8), 1.4, 3.0, M_METAL, rot=(0, math.radians(90), 0), verts=12)
for side in (-1, 1):
    cube(f"Cabrestante_sop_{side}", (L * 0.90, side * 1.9, F + 1.2), (1.0, 0.6, 2.4), M_METAL)

# ================= EXTRAS =================
stairs("Escalera_popa", L * 0.055, -B * 0.30, F + 0.7, F + 8.0, 2.4, M_METAL)
cube("Plataforma_tecnica", (L * 0.245, 0, F + 5.6), (7, B * 0.5, 0.6), M_METAL)

# ================= AUDIT =================
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

if P["scale"] != 1.0:
    bpy.ops.object.select_all(action='SELECT')
    for o in parts:
        o.scale = (P["scale"],) * 3
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
