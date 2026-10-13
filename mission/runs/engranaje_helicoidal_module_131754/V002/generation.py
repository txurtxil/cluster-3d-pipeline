"""gen_gear_helical.py — Engranaje cilindrico helicoidal de involutas. v4
Uso (dentro de Blender):
  blender -b --factory-startup -P gen_gear_helical.py -- <params.json> <out.blend> <out.stl>

Arquitectura SIN booleanos sobre la malla dentada (lecciones 12-oct):
· El solver EXACT CORROMPE la malla dentada (union -> 163 verts imposibles);
  el FAST es NO-determinista (md5 distintos entre corridas).
· Por tanto: la CORONA DENTADA es un solido anular cerrado (superficie helicoidal
  + muro interior + tapas anulares), construido 100% por from_pydata.
· El NUCLEO (disco liso r=RF-0.25 z[0,B] + cubo) lleva TODOS los booleanos
  EXACT sobre mallas lisas (clase probada con gen_taza: determinista).
· Corona y nucleo se solapan 0.25 mm en el circulo de raiz: el slicer une
  shells solapadas de forma nativa. Declarado en not_measured.
· Taladro y chavetero: DIFFERENCE EXACT sobre el nucleo liso (lejos de los dientes).
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
params = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

M = float(params["MODULE"])
Z = int(round(float(params["TEETH"])))
BETA = math.radians(float(params["HELIX_ANGLE"]))
B = float(params["FACE_WIDTH"])
R_BORE = float(params["BORE_D"]) / 2.0
R_HUB = float(params["HUB_D"]) / 2.0
HUB_LEN = float(params["HUB_LEN"])
KW = float(params["KEYWAY"])
CH = float(params.get("CHAMFER", 0.5))

RP = M * Z / 2.0
RA = RP + M
RF = RP - 1.25 * M
R_RING_IN = RF - 0.25          # muro interior de la corona (bajo el circulo de raiz)
R_CORE = RF - 0.125            # nucleo: traspasa el muro 0.125 => solapa real
RB = RP * math.cos(math.radians(20.0))
P = 2.0 * math.pi / Z
GAMMA = math.pi / (2.0 * Z)


def inv(a):
    return math.tan(a) - a


INV_P = inv(math.radians(20.0))


def psi(r):
    if r <= RB:
        return GAMMA - INV_P
    return GAMMA + inv(math.acos(min(1.0, RB / r))) - INV_P


bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ---------- 1. perfil transversal ----------
NFL, NRA, NTA = 14, 6, 4
prof = []
for k in range(Z):
    c = k * P
    for i in range(NRA):
        a = (c - P + psi(RF)) + (P - 2 * psi(RF)) * i / NRA
        prof.append((RF, a))
    for i in range(NFL):
        r = RF + (RA - RF) * i / (NFL - 1)
        prof.append((r, c - psi(r)))
    for i in range(1, NTA + 1):
        prof.append((RA, c - psi(RA) + 2 * psi(RA) * i / NTA))
    fl = [(RF + (RA - RF) * i / (NFL - 1), psi(RF + (RA - RF) * i / (NFL - 1)))
          for i in range(NFL)]
    for r, a in reversed(fl[1:]):
        prof.append((r, c + a))
a0, a1 = (Z - 1) * P + psi(RF), Z * P - psi(RF)
for i in range(1, 7):
    prof.append((RF, a0 + (a1 - a0) * i / 6))

clean = []
for pt in prof:
    if not clean or abs(pt[0] - clean[-1][0]) > 1e-9 or abs(pt[1] - clean[-1][1]) > 1e-9:
        clean.append(pt)
prof = clean

# ---------- 2. corona dentada: anillo cerrado con NR anillos en z ----------
# NR anillos: (a) helioide verdadero (mejor impresion que un solo quad
# retorcido), (b) la metrologia mide la pendiente de fase entre anillos
# consecutivos: twist/NR < medio-paso => SIN ALIAS geometrico.
TWIST = B * math.tan(BETA) / RP
NR = 4
n = len(prof)

# circulo interior con MISMO conteo y MISMO parametro de longitud de arco:
xy = [(r * math.cos(a), r * math.sin(a)) for r, a in prof]
arc = [0.0]
for i in range(1, n + 1):
    arc.append(arc[-1] + math.hypot(xy[i % n][0] - xy[i - 1][0], xy[i % n][1] - xy[i - 1][1]))
L = arc[n]
inner = []
for i in range(n):
    t = arc[i] / L
    ang = 2 * math.pi * t
    inner.append((R_RING_IN * math.cos(ang), R_RING_IN * math.sin(ang)))

verts = []
for j in range(NR):                  # NR anillos exteriores (bloques de n)
    off = TWIST * j / (NR - 1)
    zj = B * j / (NR - 1)
    for (r, a) in prof:
        verts.append((r * math.cos(a + off), r * math.sin(a + off), zj))
for (x, y) in inner:                 # NR*n..NR*n+n-1   interior abajo
    verts.append((x, y, 0.0))
for (x, y) in inner:                 # interior arriba (muro vertical)
    verts.append((x, y, B))

i0 = NR * n
faces = []
for j in range(NR - 1):              # lados helicoidales entre anillos
    for i in range(n):
        k = (i + 1) % n
        faces.append((j * n + i, j * n + k, (j + 1) * n + k, (j + 1) * n + i))
for i in range(n):                   # muro interior
    j = (i + 1) % n
    faces.append((i0 + j, i0 + i, i0 + n + i, i0 + n + j))
for i in range(n):                   # tapa inferior (normal -Z)
    j = (i + 1) % n
    faces.append((i0 + i, i0 + j, j, i))
for i in range(n):                   # tapa superior (normal +Z)
    j = (i + 1) % n
    faces.append(((NR - 1) * n + i, (NR - 1) * n + j, i0 + n + j, i0 + n + i))

me = bpy.data.meshes.new("corona"); me.from_pydata(verts, [], faces); me.update()
ring = bpy.data.objects.new("corona", me); SC.collection.objects.link(ring)

# ---------- 3. nucleo liso: disco + cubo, booleanos EXACT (mallas lisas) ----------
def prism_z(radius, z0, z1, seg=48):
    v = [(radius * math.cos(2 * math.pi * i / seg), radius * math.sin(2 * math.pi * i / seg), z)
         for z in (z0, z1) for i in range(seg)]
    f = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    f.append(tuple(range(seg - 1, -1, -1))); f.append(tuple(range(seg, 2 * seg)))
    m = bpy.data.meshes.new("prisma"); m.from_pydata(v, [], f); m.update()
    o = bpy.data.objects.new("prisma", m); SC.collection.objects.link(o)
    return o


def boolean(active, other, op):
    for o in SC.objects:
        o.select_set(False)
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    md = active.modifiers.new(op.lower(), "BOOLEAN"); md.operation = op
    md.solver = "EXACT"; md.object = other
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(other, do_unlink=True)


core = prism_z(R_CORE, 0.0, B, seg=64)
hub = prism_z(R_HUB, B - 0.5, B + HUB_LEN)
boolean(core, hub, "UNION")

ZTOP = B + HUB_LEN + 1.0
bore = prism_z(R_BORE, -1.0, ZTOP, seg=64)
boolean(core, bore, "DIFFERENCE")

kw_v = [(x, y, z) for z in (-1.0, ZTOP) for (x, y) in
        ((-KW / 2, R_BORE - 0.5), (KW / 2, R_BORE - 0.5), (KW / 2, R_HUB + 1.0), (-KW / 2, R_HUB + 1.0))]
kw_f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
kwm = bpy.data.meshes.new("chavetero"); kwm.from_pydata(kw_v, [], kw_f); kwm.update()
kw_o = bpy.data.objects.new("chavetero", kwm); SC.collection.objects.link(kw_o)
boolean(core, kw_o, "DIFFERENCE")

# ---------- 4. chaflanes ----------
if CH > 0:
    for target in (ring, core):
        for o in SC.objects:
            o.select_set(False)
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        bv = target.modifiers.new("chaflan", "BEVEL"); bv.width = CH; bv.segments = 2
        bv.limit_method = "ANGLE"
        bpy.ops.object.modifier_apply(modifier="chaflan")

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.wm.stl_export(filepath=OUT_STL)
print("GEN_OK", json.dumps({"parts": len([o for o in SC.objects if o.type == "MESH"])}))
