"""gen_caja_roscada.py — Tarro con tapa de rosca (v2: SIN booleanos en roscas).
Uso: blender -b --factory-startup -P gen_caja_roscada.py -- <params.json> <out.blend> <out.stl>

Parametros: DIAM, HEIGHT, WALL, THREAD_PITCH, LID_HEIGHT, SEAL_GROOVE (reservado), CHAMFER

Lecciones aplicadas (12-13 oct):
· El booleano EXACT con tubos helicoidales NO corta (silencioso). Las roscas
  van como CRESTAS incrustadas: hembra = cresta helicoidal que sobresale al
  interior del cuello (0.3 incrustada en la pared); macho = cresta en la tapa.
  Solidos solapados => el slicer une (misma tecnica que corona/hélice: 3 PASS).
· Holguras de tarro de cocina: hembra prot. 0.55 (26.45..27.3), macho raiz
  26.7 (0.25 sobre puntas hembra), cresta 26.7..26.85 (0.15 a la pared).
· Fiduciales: borde cuerpo (H), fondo de tapa, techo de tapa.
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

DIAM = float(P["DIAM"]); R_OUT = DIAM / 2.0
H = float(P["HEIGHT"])
WALL = float(P["WALL"]); R_IN = R_OUT - WALL
PITCH = float(P["THREAD_PITCH"])
LID_H = float(P["LID_HEIGHT"])
CH = float(P.get("CHAMFER", 0.5))

PROTR_F = 0.55                        # protusion de la hembra hacia la cavidad
ROOT_M = 0.25                         # holgura raiz macho sobre puntas hembra
CREST_M = 0.15                        # altura de la cresta del macho
R_LT = R_IN - PROTR_F + ROOT_M        # 26.7 en el tarro estandar: la cresta
                                      # queda a (PROTR_F-ROOT_M-CREST_M)=0.15 de la pared
Z_RIB0 = H - min(12.0, 0.35 * H) - 1.0
TURNS = (H - 1.0 - Z_RIB0) / PITCH
Z_LID0 = H - 0.5                      # la tapa se hunde 0.5 en el cuello
HW_F = 0.275 * PITCH
HW_M = 0.7

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene


def prism_z(radius, z0, z1, seg=64):
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


def helix_tube(r_c, z0, pitch, turns, a_min, a_max, hw, m=10, seg_deg=12):
    total = 2 * math.pi * turns
    n = max(8, int(math.degrees(total) / seg_deg))
    prof = [(a_min + (a_max - a_min) * (1 + math.cos(2 * math.pi * i / m)) / 2.0,
             hw * math.sin(2 * math.pi * i / m)) for i in range(m)]
    verts, faces = [], []
    for k in range(n + 1):
        th = total * k / n
        z = z0 + pitch * th / (2 * math.pi)
        cx, cy = r_c * math.cos(th), r_c * math.sin(th)
        e1 = (math.cos(th), math.sin(th), 0.0)
        for a, b in prof:
            verts.append((cx + a * e1[0], cy + a * e1[1], z + b))
    for k in range(n):
        for i in range(m):
            j = (i + 1) % m
            faces.append((k * m + i, k * m + j, (k + 1) * m + j, (k + 1) * m + i))
    faces.append(tuple(range(m - 1, -1, -1)))
    faces.append(tuple(n * m + i for i in range(m)))
    me = bpy.data.meshes.new("rosca"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new("rosca", me); SC.collection.objects.link(o)
    return o


# ---------- 1. cuerpo (unico booleano: cavidad, probado) ----------
body = prism_z(R_OUT, 0.0, H)
inner = prism_z(R_IN, WALL, H + 2.0)
boolean(body, inner, "DIFFERENCE")
if CH > 0:
    for o in SC.objects:
        o.select_set(False)
    body.select_set(True); bpy.context.view_layer.objects.active = body
    bv = body.modifiers.new("chaflan", "BEVEL"); bv.width = CH; bv.segments = 2
    bv.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier="chaflan")

# ---------- 2. hembra: cresta incrustada en la pared, sobresale a la cavidad
r_rib = R_IN - PROTR_F / 2.0
ribF = helix_tube(r_rib, Z_RIB0, PITCH, TURNS, -PROTR_F / 2.0, PROTR_F / 2.0 + 0.3, HW_F)

# ---------- 3. tapa + cresta macho ----------
lid = prism_z(R_LT, Z_LID0, H + LID_H)
r_crest = R_LT + CREST_M / 2.0
turns_m = min(TURNS, (LID_H - 2.0) / PITCH)
ridgeM = helix_tube(r_crest, Z_LID0 + 1.5, PITCH, turns_m, -CREST_M / 2.0 - 0.1, CREST_M / 2.0, HW_M)

# ---------- 4. STL + fiduciales ----------
bpy.ops.wm.stl_export(filepath=OUT_STL)
MARK = [(R_OUT, 0.0, H), (R_LT, 0.0, Z_LID0), (0.0, 0.0, H + LID_H)]
mm = bpy.data.meshes.new("fiduciales"); mm.from_pydata(MARK, [], []); mm.update()
mo = bpy.data.objects.new("fiduciales", mm); SC.collection.objects.link(mo)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("GEN_OK", json.dumps({"parts": len([o for o in SC.objects if o.type == "MESH" and o.name != "fiduciales"])}))
