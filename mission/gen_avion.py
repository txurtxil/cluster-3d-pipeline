"""gen_avion.py — Avion de ala fija parametrico (familia 7 del pipeline).
Uso: blender -b --factory-startup -P gen_avion.py -- <params.json> <out.blend> <out.stl>

Fase "no se duerme hasta solucionar": la geometria del avion ES ingenieria
(sweep, perfiles, estabilidad) -> va en codigo deterministico, como la taza
o el engranaje. El cerebro local solo elige PARAMETROS (datos), que es lo
suyo. /pide un avion de 150 de envergadura con 4 motores -> avion real.

Parametros: SPAN, LENGTH, ENGINES(2|4), SWEEP(grados), FUSE_R, THICK_W,
WING_POS (0..1 posicion del ala), TAIL(0/1), WINGLETS(0/1), CHAMFER.
Orientacion final: fuselaje en X (morro +X), envergadura en Y, vertical Z.
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
CH = float(P.get("CHAMFER", 1.0))

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene


def extrude_poly(points, z0, z1, name):
    """Poligono 2D (x,y) extruido en Z."""
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


# ---------- 1. fuselaje: perfil (r, z) revolucionado, luego girado a X ----------
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
fuse.rotation_euler = (0, math.pi / 2, 0)          # eje Z -> eje X (morro +X)

# ---------- 2. ala: poligono en flecha (envergadura Y, cuerda X) ----------
xw = WPOS * LENGTH                     # posicion del borde de ataque del ala
cr = 0.30 * LENGTH                     # cuerda en raiz
ct = 0.42 * cr                         # cuerda en punta
dy = 0.5 * SPAN
sweep_back = math.tan(SWEEP) * dy      # retraso de la punta (hacia -X)
pts = []
for sgn in (1, -1):
    y0, y1 = 8 * sgn, dy * sgn
    le0, le1 = xw, xw - sweep_back
    pts.append([(le0, y0), (le1, y1), (le1 - ct, y1), (le0 - cr, y0)])
    wing = extrude_poly(pts[-1], -THICK / 2, THICK / 2, "ala")

# ---------- 3. motores: cilindros bajo el ala (eje X) ----------
engines = []
if NE:
    for i in range(NE):
        side = 1 if i % 2 == 0 else -1
        k = i // 2
        y = side * (dy * (0.35 + 0.45 * k))
        e = prism_z(0.16 * FUSER, -THICK / 2, THICK / 2 + 0.02 * cr, seg=24)
        e.rotation_euler = (0, math.pi / 2, 0)
        e.location = (xw - 0.5 * cr, y, -FUSER - 0.12 * cr)
        engines.append(e)

# ---------- 4. cola ----------
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

if WINGLETS:
    for sgn in (1, -1):
        y = dy * sgn
        wl = extrude_poly([(0, 0), (0.12 * LENGTH, 0), (0.10 * LENGTH, 14),
                           (0.02 * LENGTH, 14)], -1.5, 1.5, "winglet")
        wl.rotation_euler = (math.pi / 2, 0, 0)   # de pie en la punta
        wl.location = (xw - sweep_back - ct * 0.5, y, 0)

# ---------- 5. chaflan + export ----------
if CH > 0:
    for o in SC.objects:
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
