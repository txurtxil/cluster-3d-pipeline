"""gen_tower.py v3 — Replica de la torre Eiffel de referencia del usuario.
Elementos: 4 patas curvas (3 segmentos, base->corona), zapatas, arcos de
media-torus, celosia X + anillos, 3 plataformas con BARANDILLA y CORNISA,
corona con chapitel (cono + anillos + bola).
Uso: blender -b --factory-startup -P gen_tower.py -- <params.json> <out.blend> <out.stl>
"""
import bpy
import bmesh
import json
import math
import sys
import numpy as np
from mathutils import Vector, Matrix

# --- PERFIL REAL DE LA TORRE EIFFEL (medido, del gen_eiffel.py validado):
# W_KEYS: semiancho de EJES de patas a 14 alturas (escala 170 mm ~1:1940)
# S_KEYS: semitamano de pata (grosor decrece con la altura)
# Z1/Z2/Z3: alturas de las 3 plantas reales (29.4 / 59.3 / 142)
W_KEYS = np.array([(0, 32.2), (8, 31.4), (18, 29.2), (29.4, 18.0), (44, 13.6),
                   (59.3, 10.4), (80, 8.6), (100, 7.6), (142, 4.85), (152, 4.0),
                   (160, 2.6), (166, 1.4), (169, 0.5), (170, 0.05)])
S_KEYS = np.array([(0, 4.2), (29.4, 3.3), (59.3, 2.6), (142, 1.0), (160, 0.75),
                   (170, 0.45)])

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

H = float(P["H"]); BASE = float(P["BASE"]); TOP = float(P.get("TOP", 10))
LEVELS = int(P.get("LEVELS", 3)); N_BAYS = int(P.get("N_BAYS", 6))
LEG_R = float(P.get("LEG_R", 6.0)); BAR_R = float(P.get("BAR_R", 1.0))
RING_R = float(P.get("RING_R", 1.0))
ARCH_SPRING = float(P.get("ARCH_SPRING", 8.0))   # z de arranque de los arcos
ARCH_TUBE = float(P.get("ARCH_TUBE", 3.0))
PAD = bool(P.get("PAD", True)); PAD_SIZE = float(P.get("PAD_SIZE", 24.0))
PAD_T = float(P.get("PAD_T", 4.0))
CURVE = float(P.get("CURVE", 1.0))
CAP = bool(P.get("CAP", True))
SPIRE_R = float(P.get("SPIRE_R", 5.0))
PLATFORM_T = float(P.get("PLATFORM_T", 2.5))
OVERHANG = float(P.get("OVERHANG", 6.0))
RAILING = bool(P.get("RAILING", True))
RAIL_H = float(P.get("RAIL_H", 7.0))
RAIL_R = float(P.get("RAIL_R", 0.6))
POST_SPACING = float(P.get("POST_SPACING", 10.0))
CORNICE_T = float(P.get("CORNICE_T", 1.5))
MID_Z = H * 0.45
LEG_TOP_Z = H * 0.92
CROWN_Z = H * 0.96

bpy.ops.wm.read_factory_settings(use_empty=True)


def beam(name, p1, p2, r):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=d.length,
                                        location=(p1 + p2) / 2)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return o


# --- perfiles. "resin" = W2 medido EMPIRICAMENTE del Eiffel_Resin_09.blend
# del usuario (semiancho de envolvente normalizado w/w0; dos tramos con
# escalon en z/H=0.5 y meseta de plataforma en 0.875).
# "eiffel" = W_KEYS/S_KEYS de la torre real (escala 170 mm ~1:1940).
W2 = np.array([(0.0, 1.0), (0.042, 0.971), (0.083, 0.958), (0.167, 0.935),
               (0.25, 0.914), (0.333, 0.901), (0.417, 0.891), (0.5, 0.885),
               (0.52, 0.085), (0.583, 0.075), (0.667, 0.060), (0.75, 0.050),
               (0.833, 0.042), (0.875, 0.065), (0.917, 0.055), (0.958, 0.015),
               (1.0, 0.007)])
PROFILE = str(P.get("PROFILE", "resin"))
ZS = H / 170.0


def sraw(z):
    return float(np.interp(z / ZS, S_KEYS[:, 0], S_KEYS[:, 1]))


def leg_r(z):
    """grosor de pata: S_KEYS (SIN escalar, era el bug doble-escalado) con
    LEG_R como radio efectivo en la base (sraw(0)=4.2)"""
    return sraw(z) * (LEG_R / 4.2)


if PROFILE == "resin":
    CLB = BASE / 2 - leg_r(0)   # superficie de pata = BASE exacta

    def cl(z):
        z = max(0.0, min(z, LEG_TOP_Z))
        return CLB * float(np.interp(z / H, W2[:, 0], W2[:, 1]))

    ZLEVELS = [0.50 * H, 0.875 * H]
else:
    WS = BASE / 72.8

    def wprof(z):
        return float(np.interp(z / ZS, W_KEYS[:, 0], W_KEYS[:, 1])) * WS

    def cl(z):
        z = max(0.0, min(z, LEG_TOP_Z))
        return wprof(z)

    ZLEVELS = [29.4 * ZS, 59.3 * ZS, 142.0 * ZS]


def leg_pt(sx, sy, z):
    w = cl(z)
    return (sx * w, sy * w, z)


SYMS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

# --- patas: polilinea muestreando el PERFIL REAL (14 puntos W_KEYS + corona),
#     con grosor decreciente segun S_KEYS -> silueta de la torre autentica
SAMP = [kz * ZS for kz, _ in W_KEYS] + [CROWN_Z]
SAMP = sorted(set(round(z, 3) for z in SAMP if z <= CROWN_Z))
for i, (sx, sy) in enumerate(SYMS):
    for j in range(len(SAMP) - 1):
        za, zb = SAMP[j], SAMP[j + 1]
        r = (leg_r(za) + leg_r(zb)) / 2.0
        beam(f"LEG{i}s{j}", leg_pt(sx, sy, za), leg_pt(sx, sy, zb), r)

# --- zapatas
if PAD:
    for i, (sx, sy) in enumerate(SYMS):
        p = leg_pt(sx, sy, 0)
        bpy.ops.mesh.primitive_cube_add(location=(p[0], p[1], PAD_T / 2))
        o = bpy.context.active_object
        o.name = f"PAD{i}"
        o.scale = (PAD_SIZE / 2, PAD_SIZE / 2, PAD_T / 2)
        bpy.ops.object.transform_apply(scale=True)

# --- plataformas: alturas segun el perfil elegido (resin: 0.5H y 0.875H)
z_levels = ZLEVELS
LEVELS = len(ZLEVELS)
n_rails = 0
n_posts = 0
n_corn = 0


def deck(z, w, name):
    """cubierta + cornisa + barandilla en un cuadrado de semilado w a altura z"""
    global n_rails, n_posts, n_corn
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, z))
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, w, PLATFORM_T / 2)
    bpy.ops.object.transform_apply(scale=True)
    # cornisa: 4 vigas finas ligeramente mas anchas, bajo la cubierta
    cz = z - PLATFORM_T / 2 - CORNICE_T / 2
    cw = w + 1.5
    cs = [(cw, cw, cz), (cw, -cw, cz), (-cw, -cw, cz), (-cw, cw, cz)]
    for f in range(4):
        beam(f"CORN{n_corn}", cs[f], cs[(f + 1) % 4], CORNICE_T)
        n_corn += 1
    if not RAILING:
        return
    # barandilla: rail superior + posts alrededor del perimetro
    rz = z + PLATFORM_T / 2 + RAIL_H
    rs = [(w, w, rz), (w, -w, rz), (-w, -w, rz), (-w, w, rz)]
    for f in range(4):
        beam(f"RAIL{n_rails}", rs[f], rs[(f + 1) % 4], RAIL_R)
        n_rails += 1
    edge = 2 * w
    nseg = max(2, int(round(edge / POST_SPACING)))
    for f in range(4):
        a = Vector(rs[f]); b = Vector(rs[(f + 1) % 4])
        for k in range(nseg + 1):
            p = a.lerp(b, k / nseg)
            p.z = z + PLATFORM_T / 2
            beam(f"RPOST{n_posts}", p, Vector((p.x, p.y, rz)), RAIL_R)
            n_posts += 1


for i, z in enumerate(z_levels):
    deck(z, cl(z) + OVERHANG / 2, f"PLAT{i}")

if CAP:
    deck(CROWN_Z, TOP / 2 + OVERHANG / 2, "CROWN")
    # chapitel AJUSTADO A H EXACTO (leccion §36: medido por vertices):
    # bola tangente a H por arriba; anillos y cono bajo ella sin solapes
    r_ball = max(1.0, SPIRE_R * 0.20)
    ball_c = H - r_ball                      # bola ocupa [H-2r, H]
    ring_tube = 0.7
    ring1_z = ball_c - r_ball - ring_tube    # tope <= H-2r (soporte bola)
    ring0_z = ring1_z - 1.6 - ring_tube
    cone_top = ring0_z - ring_tube - 0.5
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=SPIRE_R, radius2=0.4,
                                    depth=cone_top - CROWN_Z,
                                    location=(0, 0, (cone_top + CROWN_Z) / 2))
    bpy.context.active_object.name = "SPIRE"
    for ri, (rz, rr) in enumerate(((ring0_z, SPIRE_R * 0.45),
                                   (ring1_z, SPIRE_R * 0.28))):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=ring_tube,
                                         major_segments=16, minor_segments=8,
                                         location=(0, 0, rz))
        bpy.context.active_object.name = f"SPRING{ri}"
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10,
                                         radius=r_ball, location=(0, 0, ball_c))
    bpy.context.active_object.name = "TIP"

# --- anillos de celosia (el primero flota a RING_R para ser tangente al
#     suelo: asi el z minimo de toda la pieza es EXACTAMENTE 0)
Z_BASE = RING_R
n_rings = 0
ring_levels = [Z_BASE] + z_levels + [LEG_TOP_Z]
for zr in ring_levels:
    c = [leg_pt(sx, sy, zr) for sx, sy in SYMS]
    for f in range(4):
        beam(f"RING{n_rings}", c[f], c[(f + 1) % 4], RING_R)
        n_rings += 1

# --- celosia X
n_bars = 0
for i in range(LEVELS):
    z0 = Z_BASE if i == 0 else z_levels[i - 1]
    z1 = z_levels[i]
    for b in range(N_BAYS):
        za = z0 + (z1 - z0) * b / N_BAYS
        zb = z0 + (z1 - z0) * (b + 1) / N_BAYS
        ca = [leg_pt(sx, sy, za) for sx, sy in SYMS]
        cb = [leg_pt(sx, sy, zb) for sx, sy in SYMS]
        for f in range(4):
            beam(f"BAR{n_bars}", ca[f], cb[(f + 1) % 4], BAR_R); n_bars += 1
            beam(f"BAR{n_bars}", ca[(f + 1) % 4], cb[f], BAR_R); n_bars += 1

# --- arcos (media-torus entre patas adyacentes)
n_arches = 0
if ARCH_SPRING > 0:
    faces = [((1, 1), (1, -1)), ((1, -1), (-1, -1)),
             ((-1, -1), (-1, 1)), ((-1, 1), (1, 1))]
    for a, b in faces:
        pa = Vector(leg_pt(*a, ARCH_SPRING))
        pb = Vector(leg_pt(*b, ARCH_SPRING))
        mid = (pa + pb) / 2
        d = pb - pa
        major = d.length / 2
        bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=ARCH_TUBE,
                                         major_segments=32, minor_segments=10,
                                         location=mid)
        t = bpy.context.active_object
        t.name = f"ARCH{n_arches}"
        bpy.context.view_layer.objects.active = t
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bm = bmesh.from_edit_mesh(t.data)
        for v in bm.verts:
            v.select = v.co.x > 1e-6
        bmesh.update_edit_mesh(t.data)
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.object.mode_set(mode="OBJECT")
        d_h = d.normalized()
        m = Matrix.Identity(3)
        m.col[0] = -Vector((0, 0, 1))
        m.col[1] = d_h
        m.col[2] = m.col[0].cross(m.col[1])
        t.rotation_mode = "QUATERNION"
        t.rotation_quaternion = m.to_quaternion()
        n_arches += 1

# --- normalizacion z (leccion §36): tras construir TODO, medir el z minimo
# real (caps de patas/arcos se cuelan bajo 0) y trasladar la torre entera
# para que el suelo sea EXACTAMENTE z=0. Determinista y honesta.
_dg = bpy.context.evaluated_depsgraph_get()
_zmin = 1e9
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    _ev = o.evaluated_get(_dg)
    _me = _ev.to_mesh()
    for _v in _me.vertices:
        _zmin = min(_zmin, (_ev.matrix_world @ _v.co).z)
    _ev.to_mesh_clear()
# normalizar afín a [0, H] EXACTO: escalado uniforme en z mediante un
# empty raiz (correcto con objetos rotados), traslacion del minimo a 0
_zmax = -1e9
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    _ev = o.evaluated_get(_dg)
    _me = _ev.to_mesh()
    for _v in _me.vertices:
        _zmax = max(_zmax, (_ev.matrix_world @ _v.co).z)
    _ev.to_mesh_clear()
_span = _zmax - _zmin
_s = H / _span if _span > 0 else 1.0
z_shift = round(-_zmin * _s, 3)
bpy.ops.object.empty_add(location=(0, 0, 0))
_root = bpy.context.active_object
_root.name = "TOWER_ROOT"
for o in list(bpy.context.scene.objects):
    if o == _root or o.type == "EMPTY":
        continue
    if o.parent is None:
        _mw = o.matrix_world.copy()
        o.parent = _root
        o.matrix_world = _mw
_root.scale = (1.0, 1.0, _s)
_root.location.z = z_shift

# --- informe
total_bad = 0
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    total_bad += sum(1 for v in ec.values() if v != 2)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.wm.stl_export(filepath=OUT_STL)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

print("GEN_OK", json.dumps({
    "params": {"H": H, "BASE": BASE, "TOP": TOP, "LEVELS": LEVELS,
               "N_BAYS": N_BAYS, "ARCH_SPRING": ARCH_SPRING, "CAP": CAP,
               "PAD": PAD, "RAILING": RAILING},
    "counts": {"LEGS": 4, "PADS": 4 if PAD else 0, "PLATFORMS": LEVELS,
               "CROWN": 1 if CAP else 0, "SPIRE": 1 if CAP else 0,
               "SPRINGS": 2 if CAP else 0, "ARCHES": n_arches,
               "BARS": n_bars, "RINGS": n_rings, "RAILS": n_rails,
               "RAILPOSTS": n_posts, "CORNICES": n_corn},
    "z_shift": round(z_shift, 3),
    "mesh_bad_edges": total_bad,
}))
