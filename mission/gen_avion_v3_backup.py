"""gen_avion.py v3 — Gramatica parametrica Boeing 747 (familia 7 v3).
Uso: blender -b --factory-startup -P gen_avion.py -- <params.json> <out.blend> <out.stl>

Criterios del juez (v2.2): fuselaje de seccion variable con morro redondeado
y cola afilada; cubierta superior con transicion suave; motores COMPLETOS
(entrada, gondola, salida, pilon) con separacion longitudinal+transversal
realista; tren con bogies multipieza; alas/estab/deriva proporcionados;
uniones solapadas (tangencia prohibida). Cotas terminadas: L=180, W=150.

Parametros: SPAN, LENGTH, ENGINES(4), SWEEP, FUSE_R, THICK_W, WING_POS,
TAIL, WINGLETS, HUMP(1), GEAR(1), CHAMFER.
Orientacion: fuselaje eje X (morro +X), envergadura Y, vertical Z.
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

SPAN = float(P.get("SPAN", 150))
LENGTH = float(P.get("LENGTH", 180))
NE = int(P.get("ENGINES", 4))
SWEEP = math.radians(float(P.get("SWEEP", 30)))
F = float(P.get("FUSE_R", 12))
THICK = float(P.get("THICK_W", 4))
WPOS = float(P.get("WING_POS", 0.45))
TAIL = int(P.get("TAIL", 1))
WINGLETS = int(P.get("WINGLETS", 1))
HUMP = int(P.get("HUMP", 1))
GEAR = int(P.get("GEAR", 1))
CH = float(P.get("CHAMFER", 1.0))

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene


def box3(x0, x1, y0, y1, z0, z1, name):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    m = bpy.data.meshes.new(name); m.from_pydata(v, [], f); m.update()
    o = bpy.data.objects.new(name, m); SC.collection.objects.link(o)
    return o


def extrude_poly(points, z0, z1, name):
    n = len(points)
    v = [(x, y, z0) for (x, y) in points] + [(x, y, z1) for (x, y) in points]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    m = bpy.data.meshes.new(name); m.from_pydata(v, [], f); m.update()
    o = bpy.data.objects.new(name, m); SC.collection.objects.link(o)
    return o


def prism_cone_z(r1, r2, z0, z1, seg=32):
    v = []
    for z, r in ((z0, r1), (z1, r2)):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            v.append((r * math.cos(a), r * math.sin(a), z))
    f = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    f.append(tuple(range(seg - 1, -1, -1))); f.append(tuple(range(seg, 2 * seg)))
    m = bpy.data.meshes.new("cono"); m.from_pydata(v, [], f); m.update()
    o = bpy.data.objects.new("cono", m); SC.collection.objects.link(o)
    return o


def cyl_x(r, length, x, y, z, name):
    o = prism_cone_z(r, r, -length / 2, length / 2, 24)
    o.rotation_euler = (0, math.pi / 2, 0); o.location = (x, y, z); o.name = name
    return o


def cone_x(r1, r2, length, x, y, z, name):
    o = prism_cone_z(r1, r2, -length / 2, length / 2, 24)
    o.rotation_euler = (0, math.pi / 2, 0); o.location = (x, y, z); o.name = name
    return o


def cyl_y(r, length, x, y, z, name):
    o = prism_cone_z(r, r, -length / 2, length / 2, 20)
    o.rotation_euler = (math.pi / 2, 0, 0); o.location = (x, y, z); o.name = name
    return o


def cyl_v(r, z0, z1, x, y, name):
    o = prism_cone_z(r, r, z0, z1, 16)
    o.location = (x, y, 0); o.name = name
    return o


# ---------- 1. fuselaje: seccion variable (morro redondeado, cola afilada) ----------
prof = [(0.06 * F, 0.0), (0.55 * F, 0.04 * LENGTH), (0.88 * F, 0.10 * LENGTH),
        (F, 0.20 * LENGTH), (F, 0.60 * LENGTH), (0.88 * F, 0.74 * LENGTH),
        (0.55 * F, 0.90 * LENGTH), (0.22 * F, LENGTH)]
SEGS = 64
n = len(prof)
verts, faces = [], []
for i in range(SEGS):
    a = 2 * math.pi * i / SEGS
    ca, sa = math.cos(a), math.sin(a)
    for r, z in prof:
        verts.append((r * ca, r * sa, z))
for i in range(SEGS):
    j = (i + 1) % SEGS
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((i * n + k, j * n + k, j * n + k2, i * n + k2))
me = bpy.data.meshes.new("fuselaje"); me.from_pydata(verts, [], faces); me.update()
fuse = bpy.data.objects.new("fuselaje", me); SC.collection.objects.link(fuse)
fuse.rotation_euler = (0, math.pi / 2, 0)

# ---------- 2. cubierta superior: cono de transicion + cilindro + cono de salida ----------
if HUMP:
    rdeck = 0.62 * F
    zdeck = 0.80 * F
    cone_x(0.35 * F, rdeck, 0.07 * LENGTH, 0.155 * LENGTH, 0, zdeck, "joroba_frente")
    cyl_x(rdeck, 0.20 * LENGTH, 0.29 * LENGTH, 0, zdeck, "joroba_cubierta")
    cone_x(rdeck, 0.30 * F, 0.09 * LENGTH, 0.435 * LENGTH, 0, zdeck, "joroba_salida")

# ---------- 3. alas en flecha ----------
xw = WPOS * LENGTH
cr = 0.30 * LENGTH
ct = 0.42 * cr
dy = 0.5 * SPAN - 1.5
sweep_back = math.tan(SWEEP) * dy
for sgn in (1, -1):
    y0, y1 = 8 * sgn, dy * sgn
    le0, le1 = xw, xw - sweep_back
    extrude_poly([(le0, y0), (le1, y1), (le1 - ct, y1), (le0 - cr, y0)],
                 -THICK / 2, THICK / 2, "ala")

# ---------- 4. motores COMPLETOS: entrada + gondola + salida + pilon ----------
# dos por ala, separacion transversal (0.32/0.60 de media envergadura) y
# longitudinal escalonada (el exterior 0.18*cr mas atras, como el 747 real)
if NE:
    nac_r = 0.17 * F
    nac_l = 0.17 * cr
    for i in range(NE):
        side = 1 if i % 2 == 0 else -1
        inner = (i % 4) < 2
        k = 0 if inner else 1
        y = side * (dy * (0.32 + 0.28 * k))
        xe = xw - cr * (0.30 + 0.20 * k)
        ez = -THICK / 2 - nac_r + 1.5          # solape 1.5 mm en el intrados
        cone_x(0.21 * F, nac_r, 0.05 * cr, xe + nac_l / 2, y, ez, "entrada")
        cyl_x(nac_r, nac_l, xe, y, ez, "gondola")
        cone_x(nac_r, 0.12 * F, 0.04 * cr, xe - nac_l / 2 - 0.02 * cr, y, ez, "salida")
        # pilon: caja del ala al nacelle, con solape en ambos extremos
        box3(xe - 0.30 * cr, xe + 0.10 * cr, y - 1.3, y + 1.3,
             ez - 0.2, -THICK / 2 + 0.8, "pilon")

# ---------- 5. cola proporcionada ----------
if TAIL:
    ct_ch = 0.15 * LENGTH
    span_t = 0.34 * SPAN
    xt = 0.87 * LENGTH
    for sgn in (1, -1):
        y1 = span_t * 0.5 * sgn
        extrude_poly([(xt + 0.05 * LENGTH, 6 * sgn), (xt - ct_ch * 0.3, y1),
                      (xt - ct_ch, y1), (xt - ct_ch, 6 * sgn)],
                     -THICK * 0.6, THICK * 0.6, "estab")
    # deriva VERTICAL: poligono (x, altura) girado 90 grados sobre X
    tim = extrude_poly([(xt + 0.04 * LENGTH, 0), (xt - ct_ch, 0),
                        (xt - ct_ch * 0.55, 2.7 * F), (xt - ct_ch * 0.15, 2.7 * F)],
                       -THICK * 0.6, THICK * 0.6, "timon")
    tim.rotation_euler = (math.pi / 2, 0, 0)

# ---------- 6. winglets ----------
if WINGLETS:
    for sgn in (1, -1):
        y = dy * sgn
        wl = extrude_poly([(0, 0), (0.12 * LENGTH, 0), (0.10 * LENGTH, 14),
                           (0.02 * LENGTH, 14)], -1.5, 1.5, "winglet")
        wl.rotation_euler = (math.pi / 2, 0, 0)
        wl.location = (xw - sweep_back - ct * 0.5, y, 0)

# ---------- 7. tren: morro (2 ruedas) + 2 bogies principales de 4 ruedas ----------
if GEAR:
    wr = 0.30 * F
    # morro
    xn, zn = 0.07 * LENGTH, -F - 2.6 * wr
    cyl_v(1.3, zn + wr, -F + 1.5, xn, 0, "puntal_morro")
    cyl_y(0.35 * wr, wr * 2.8, xn, 0, zn, "eje_morro")
    for sy in (1, -1):
        cyl_y(wr, 2.2, xn, sy * wr * 1.1, zn, "rueda_morro")
    # principales: bogie de 4 ruedas (2 ejes x 2 ruedas) por lado
    for sgn in (1, -1):
        ym = sgn * 1.05 * F
        xm = 0.42 * LENGTH
        zm = -F - 2.8 * wr
        cyl_v(1.6, zm + wr, -F + 1.5, xm, ym, "puntal_main")
        box3(xm - 0.38 * F, xm + 0.38 * F, ym - 0.6, ym + 0.6, zm - 0.5, zm + 0.5, "bogie")
        for dx in (-0.30 * F, 0.30 * F):
            cyl_y(0.35 * wr, wr * 2.9, xm + dx, ym, zm, "eje_main")
            for sy in (1, -1):
                cyl_y(wr, 2.2, xm + dx, ym + sy * wr * 1.1, zm, "rueda_main")

# ---------- 8. chaflan (fuselaje excluido) + export ----------
if CH > 0:
    for o in list(SC.objects):
        if o.type != "MESH" or o.name == "fuselaje":
            continue
        for q in SC.objects:
            q.select_set(False)
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bv = o.modifiers.new("chaflan", "BEVEL"); bv.width = CH; bv.segments = 2
        bv.limit_method = "ANGLE"
        try:
            bpy.ops.object.modifier_apply(modifier="chaflan")
        except Exception:
            pass

bpy.ops.wm.stl_export(filepath=OUT_STL)
print("GEN_OK", json.dumps({"parts": len([o for o in SC.objects if o.type == "MESH"])}))
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
