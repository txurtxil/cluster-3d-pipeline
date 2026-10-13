"""gen_helice.py — Helice de barco parametrica (B-series simplificada). v2
Uso (dentro de Blender):
  blender -b --factory-startup -P gen_helice.py -- <params.json> <out.blend> <out.stl>

Parametros:
  DIAM, BLADES, PITCH_RATIO (P/D), BAR (blade area ratio ~0.35-0.6),
  HUB_D, HUB_LEN, RAKE (mm, +popa), SKEW (grados), SHAFT_D

Arquitectura (misma leccion que el engranaje v4):
· Palas solidas CERRADAS por from_pydata (secciones NACA simetricas
  interpoladas) => manifold por construccion, DETERMINISTA, sin booleanos
  sobre la pieza compleja.
· Nucleo liso (cubo + taladro) lleva los booleanos EXACT.
· Solapa pala-nucleo de 1.5 mm en la raiz: el slicer une shells solapadas.
· FIDUCIALES de metrologia: vertice por eje de estacion (xu=0.4, y=0).
  Se crean DESPUES del export STL: viven en el .blend, NO en la pieza.
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

D = float(P["DIAM"]); R = D / 2.0
B = int(round(float(P["BLADES"])))
PD = float(P["PITCH_RATIO"])
BAR = float(P.get("BAR", 0.5))
RH = float(P["HUB_D"]) / 2.0
HUB_LEN = float(P["HUB_LEN"])
RAKE = float(P.get("RAKE", 0.0))
SKEW = math.radians(float(P.get("SKEW", 0.0)))
SHAFT = float(P["SHAFT_D"]) / 2.0
EMBED = 1.5

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ---------- 1. distribucion de cuerda (area de palas ~ BAR) ----------
def fshape(t):
    return 0.35 + 0.65 * math.sin(math.pi * (0.15 + 0.85 * t))

NT = 40
s = sum(fshape(i / NT) for i in range(NT + 1)) / (NT + 1)
R_IN = RH + EMBED
SPAN = R - R_IN
area_blade = BAR * (math.pi * D * D / 4.0) / B
C0 = area_blade / (SPAN * s)

# ---------- 2. secciones NACA simetricas ----------
def naca_half(t_thick):
    N = 10
    up = []
    for i in range(N + 1):
        x = i / N
        yt = 5 * t_thick * (0.2969 * math.sqrt(x) - 0.1260 * x
                            - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        up.append((x, yt))
    return up + [(x, -y) for x, y in reversed(up[1:-1])]

S = 9
verts, faces, MARKERS = [], [], []
m = len(naca_half(0.05))
for b in range(B):
    th0 = b * 2 * math.pi / B
    base = len(verts)
    for k in range(S):
        r = R_IN + SPAN * k / (S - 1)
        t = (r - RH) / (R - RH)
        beta = math.atan(PD * D / (2 * math.pi * r))
        th = th0 + SKEW * t
        z0 = RAKE * t
        c = C0 * fshape(t)
        tt = 0.055 * (1.2 - 0.7 * t)
        er = (math.cos(th), math.sin(th), 0.0)
        et = (-math.sin(th), math.cos(th), 0.0)
        ech = [math.cos(beta) * et[j] + math.sin(beta) * (0, 0, 1)[j] for j in range(3)]
        eth = [-math.sin(beta) * et[j] + math.cos(beta) * (0, 0, 1)[j] for j in range(3)]
        cx, cy, cz = er[0] * r, er[1] * r, z0
        # fiduciales: EJE (xu=0.4), BORDE DE ATAQUE (xu=0) y BORDE DE SALIDA
        # (xu=1). El eje no codifica el paso (la seccion gira SOBRE el);
        # LE->TE miden el paso exacto: tan(beta) = dz/du tangencial.
        le = (cx - 0.4 * c * ech[0], cy - 0.4 * c * ech[1], cz - 0.4 * c * ech[2])
        te = (cx + 0.6 * c * ech[0], cy + 0.6 * c * ech[1], cz + 0.6 * c * ech[2])
        MARKERS.extend([(cx, cy, cz), le, te])
        for (xu, yu) in naca_half(tt):
            wx = cx + (xu - 0.4) * c * ech[0] + yu * c * eth[0]
            wy = cy + (xu - 0.4) * c * ech[1] + yu * c * eth[1]
            wz = cz + (xu - 0.4) * c * ech[2] + yu * c * eth[2]
            verts.append((wx, wy, wz))
    for k in range(S - 1):
        for i in range(m):
            j = (i + 1) % m
            faces.append((base + k * m + i, base + k * m + j,
                          base + (k + 1) * m + j, base + (k + 1) * m + i))
    faces.append(tuple(base + i for i in range(m - 1, -1, -1)))
    faces.append(tuple(base + (S - 1) * m + i for i in range(m)))

me = bpy.data.meshes.new("palas"); me.from_pydata(verts, [], faces); me.update()
blades = bpy.data.objects.new("palas", me); SC.collection.objects.link(blades)

# ---------- 3. nucleo liso: cubo + taladro (booleanos EXACT) ----------
def prism_z(radius, z0, z1, seg=48):
    v = [(radius * math.cos(2 * math.pi * i / seg), radius * math.sin(2 * math.pi * i / seg), z)
         for z in (z0, z1) for i in range(seg)]
    f = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    f.append(tuple(range(seg - 1, -1, -1))); f.append(tuple(range(seg, 2 * seg)))
    m2 = bpy.data.meshes.new("prisma"); m2.from_pydata(v, [], f); m2.update()
    o = bpy.data.objects.new("prisma", m2); SC.collection.objects.link(o)
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


core = prism_z(RH + 1.0, -HUB_LEN / 2.0, HUB_LEN / 2.0)
bore = prism_z(SHAFT, -HUB_LEN, HUB_LEN, seg=64)
boolean(core, bore, "DIFFERENCE")

# ---------- 4. exportar STL (SOLO palas+nucleo; fiduciales NO van al STL)
bpy.ops.wm.stl_export(filepath=OUT_STL)

mm = bpy.data.meshes.new("fiduciales"); mm.from_pydata(MARKERS, [], []); mm.update()
mo = bpy.data.objects.new("fiduciales", mm); SC.collection.objects.link(mo)

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("GEN_OK", json.dumps({"parts": len([o for o in SC.objects if o.type == "MESH" and o.name != "fiduciales"])}))
