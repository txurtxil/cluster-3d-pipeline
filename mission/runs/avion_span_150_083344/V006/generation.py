"""gen_avion.py v2 — Avion parametrico, especificacion 747 (familia 7 v2).
Uso: blender -b --factory-startup -P gen_avion.py -- <params.json> <out.blend> <out.stl>

Criterios cubiertos (aprobacion 15-oct): fuselaje con morro/cola, JOROBA del
segundo nivel, 2 alas en flecha, 4 motores bajo las alas, TREN DE ATERRIZAJE
(3 conjuntos: morro + 2 principales, puntales y ruedas), cola (estab+timon),
winglets, malla valida, STL determinista.

Parametros: SPAN, LENGTH, ENGINES(2|4), SWEEP, FUSE_R, THICK_W, WING_POS,
TAIL(0/1), WINGLETS(0/1), HUMP(0/1), GEAR(0/1), CHAMFER.
Orientacion: fuselaje en X (morro +X), envergadura Y, vertical Z.
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

SPAN = float(P.get("SPAN", 150))
LENGTH = float(P.get("LENGTH", 180))
NE = int(P.get("ENGINES", 4))
SWEEP = math.radians(float(P.get("SWEEP", 30)))
FUSER = float(P.get("FUSE_R", 12))
THICK = float(P.get("THICK_W", 4))
WPOS = float(P.get("WING_POS", 0.45))
TAIL = int(P.get("TAIL", 1))
WINGLETS = int(P.get("WINGLETS", 1))
HUMP = int(P.get("HUMP", 1))
GEAR = int(P.get("GEAR", 1))
CH = float(P.get("CHAMFER", 1.0))

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene


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


def prism_z(radius, z0, z1, seg=32):
    v = [(radius * math.cos(2 * math.pi * i / seg), radius * math.sin(2 * math.pi * i / seg), z)
         for z in (z0, z1) for i in range(seg)]
    f = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    f.append(tuple(range(seg - 1, -1, -1))); f.append(tuple(range(seg, 2 * seg)))
    m = bpy.data.meshes.new("prisma"); m.from_pydata(v, [], f); m.update()
    o = bpy.data.objects.new("prisma", m); SC.collection.objects.link(o)
    return o


def cyl_x(radius, length, x, y, z, name):
    """Cilindro con eje en X."""
    o = prism_z(radius, -length / 2, length / 2, seg=24)
    o.rotation_euler = (0, math.pi / 2, 0)
    o.location = (x, y, z)
    o.name = name
    return o


def cyl_y(radius, length, x, y, z, name):
    """Cilindro con eje en Y (ruedas)."""
    o = prism_z(radius, -length / 2, length / 2, seg=24)
    o.rotation_euler = (math.pi / 2, 0, 0)
    o.location = (x, y, z)
    o.name = name
    return o


def cyl_v(radius, z0, z1, x, y, name):
    """Cilindro vertical (puntales)."""
    o = prism_z(radius, z0, z1, seg=16)
    o.location = (x, y, 0)
    o.name = name
    return o


# ---------- 1. fuselaje ----------
prof = [(0.0, 0.0), (FUSER, 0.06 * LENGTH), (FUSER, 0.72 * LENGTH),
        (0.35 * FUSER, LENGTH)]
SEGS = 48
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

# ---------- 2. joroba del segundo nivel ----------
if HUMP:
    cyl_x(0.62 * FUSER, 0.28 * LENGTH, 0.28 * LENGTH, 0, 0.95 * FUSER, "joroba")

# ---------- 3. alas en flecha ----------
xw = WPOS * LENGTH
cr = 0.30 * LENGTH
ct = 0.42 * cr
dy = 0.5 * SPAN
sweep_back = math.tan(SWEEP) * dy
for sgn in (1, -1):
    y0, y1 = 8 * sgn, dy * sgn
    le0, le1 = xw, xw - sweep_back
    extrude_poly([(le0, y0), (le1, y1), (le1 - ct, y1), (le0 - cr, y0)],
                 -THICK / 2, THICK / 2, "ala")

# ---------- 4. motores (pegados al intrados del ala) ----------
if NE:
    for i in range(NE):
        side = 1 if i % 2 == 0 else -1
        k = i // 2
        y = side * (dy * (0.35 + 0.45 * k))
        cyl_x(0.16 * FUSER, 0.20 * cr, xw - 0.5 * cr, y,
              -THICK / 2 - 0.16 * FUSER, "motor")

# ---------- 5. cola ----------
if TAIL:
    ct_ch = 0.16 * LENGTH
    span_t = 0.32 * SPAN
    xt = 0.88 * LENGTH
    for sgn in (1, -1):
        y1 = span_t * 0.5 * sgn
        extrude_poly([(xt, 6 * sgn), (xt - ct_ch * 0.3, y1),
                      (xt - ct_ch, y1), (xt - ct_ch, 6 * sgn)],
                     -THICK * 0.6, THICK * 0.6, "estab")
    extrude_poly([(xt, 0), (xt - ct_ch, 0), (xt - ct_ch * 0.55, 2.6 * FUSER),
                  (xt - ct_ch * 0.15, 2.6 * FUSER)],
                 -THICK * 0.6, THICK * 0.6, "timon")

# ---------- 6. winglets ----------
if WINGLETS:
    for sgn in (1, -1):
        y = dy * sgn
        wl = extrude_poly([(0, 0), (0.12 * LENGTH, 0), (0.10 * LENGTH, 14),
                           (0.02 * LENGTH, 14)], -1.5, 1.5, "winglet")
        wl.rotation_euler = (math.pi / 2, 0, 0)
        wl.location = (xw - sweep_back - ct * 0.5, y, 0)

# ---------- 7. tren de aterrizaje (morro + 2 principales) ----------
if GEAR:
    wr = 0.35 * FUSER          # radio rueda
    # morro
    cyl_v(1.2, -FUSER - 3 * wr, -FUSER, 0.10 * LENGTH, 0, "puntal_morro")
    cyl_y(wr, 2.4, 0.10 * LENGTH, 0, -FUSER - 3 * wr - wr, "rueda_morro")
    # principales (2 conjuntos separados, 2 ruedas visibles cada uno)
    for sgn in (1, -1):
        y = sgn * 1.15 * FUSER
        cyl_v(1.4, -FUSER - 4 * wr, -FUSER, 0.45 * LENGTH, y, "puntal_main")
        for sy in (0.8, -0.8):
            cyl_y(wr, 3.0, 0.45 * LENGTH, y + wr * 2.4 * sy,
                  -FUSER - 4 * wr - wr, "rueda_main")

# ---------- 8. chaflan + export ----------
if CH > 0:
    for o in list(SC.objects):
        if o.type != "MESH":
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
