"""gen_taza.py — Generador determinista de taza (mug) parametrica.
Uso (dentro de Blender):
  blender -b --factory-startup -P gen_taza.py -- <params.json> <out.blend> <out.stl>
Parametros (todo por JSON, nada quemado):
  H            altura total (mm)
  D_OUT        diametro exterior (mm)
  WALL         grosor de pared (mm)
  BOTTOM       grosor de fondo (mm, default=WALL)
  RIM_R        radio del filete de borde (mm, tope WALL-0.4)
  HANDLE       0/1, default 1
  HANDLE_D     diametro de la seccion del asa (mm)
  HANDLE_Z_LOW/HANDLE_Z_HIGH  alturas de anclaje del asa (mm)
  HANDLE_REACH cuanto sobresale el asa de la pared (mm)
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
params = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

H = float(params["H"])
D_OUT = float(params["D_OUT"])
WALL = float(params["WALL"])
BOTTOM = float(params.get("BOTTOM", WALL))
RIM_R = max(0.0, min(float(params.get("RIM_R", 1.2)), WALL - 0.4))
HANDLE = int(params.get("HANDLE", 1))
HANDLE_D = float(params.get("HANDLE_D", 9.0))
HANDLE_Z_LOW = float(params.get("HANDLE_Z_LOW", round(H * 0.30, 2)))
HANDLE_Z_HIGH = float(params.get("HANDLE_Z_HIGH", round(H * 0.72, 2)))
# auto-ajuste: el asa (radio HANDLE_D/2) debe caber DENTRO del cuerpo o su
# superficie sobresale del borde y la H medida = asa, no cuerpo (leccion
# 13-oct: taza H=70 media 72.964 = centro del arco 68.5 + radio 4.5).
if HANDLE:
    HANDLE_Z_HIGH = min(HANDLE_Z_HIGH, H - HANDLE_D / 2.0 - 1.0)
    HANDLE_Z_LOW = max(HANDLE_Z_LOW, HANDLE_D / 2.0 + 1.0)
    if HANDLE_Z_HIGH - HANDLE_Z_LOW < HANDLE_D:
        mid = (HANDLE_Z_LOW + HANDLE_Z_HIGH) / 2.0
        HANDLE_Z_LOW = mid - HANDLE_D
        HANDLE_Z_HIGH = mid + HANDLE_D
HANDLE_REACH = float(params.get("HANDLE_REACH", 22.0))

R_OUT = D_OUT / 2.0
R_IN = R_OUT - WALL

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
SEGS = 64

# --- cuerpo: perfil cerrado (r,z) revolucionado 360º [manifold por construccion]
prof = [(0.0, 0.0), (R_OUT, 0.0), (R_OUT, H), (R_IN, H), (R_IN, BOTTOM), (0.0, BOTTOM)]
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
me = bpy.data.meshes.new("cuerpo"); me.from_pydata(verts, [], faces); me.update()
body = bpy.data.objects.new("cuerpo", me); SC.collection.objects.link(body)

if RIM_R > 0:
    bev = body.modifiers.new("filete", "BEVEL"); bev.width = RIM_R; bev.segments = 2
    bev.limit_method = "ANGLE"

if HANDLE:
    # asa: tubo de seccion redonda siguiendo un arco circular (plano XZ, lado +X)
    from mathutils import Vector
    xa = R_OUT - 1.5  # anclaje ligeramente hundido en la pared
    zc = (HANDLE_Z_LOW + HANDLE_Z_HIGH) / 2.0
    half = (HANDLE_Z_HIGH - HANDLE_Z_LOW) / 2.0
    bulge = HANDLE_REACH
    R = (half * half + bulge * bulge) / (2.0 * bulge)
    th = math.atan2(half, R - bulge)
    cx = xa - R + bulge
    NPTS, SIDES = 25, 12
    rr = HANDLE_D / 2.0
    pts = [Vector((cx + R * math.cos(-th + 2 * th * i / (NPTS - 1)), 0.0,
                   zc + R * math.sin(-th + 2 * th * i / (NPTS - 1)))) for i in range(NPTS)]
    up = Vector((0, 1, 0))
    hv, hf = [], []
    for i, p in enumerate(pts):
        if i == 0: tang = (pts[1] - pts[0]).normalized()
        elif i == NPTS - 1: tang = (pts[-1] - pts[- 2]).normalized()
        else: tang = (pts[i + 1] - pts[i - 1]).normalized()
        nrm = tang.cross(up).normalized()
        for j in range(SIDES):
            a = 2 * math.pi * j / SIDES
            hv.append(tuple(p + rr * (math.cos(a) * nrm + math.sin(a) * up)))
    for i in range(NPTS - 1):
        for j in range(SIDES):
            j2 = (j + 1) % SIDES
            hf.append((i * SIDES + j, (i + 1) * SIDES + j, (i + 1) * SIDES + j2, i * SIDES + j2))
    c0 = len(hv); hv.append(tuple(pts[0]))
    c1 = len(hv); hv.append(tuple(pts[-1]))
    for j in range(SIDES):
        j2 = (j + 1) % SIDES
        hf.append((c0, j2, j))
        a = (NPTS - 1) * SIDES
        hf.append((c1, a + j, a + j2))
    hm = bpy.data.meshes.new("asa"); hm.from_pydata(hv, [], hf); hm.update()
    handle = bpy.data.objects.new("asa", hm); SC.collection.objects.link(handle)
    try:
        for o in SC.objects: o.select_set(False)
        body.select_set(True)
        bpy.context.view_layer.objects.active = body
        mod = body.modifiers.new("union", "BOOLEAN"); mod.operation = "UNION"
        mod.solver = "EXACT"; mod.object = handle
        bpy.ops.object.modifier_apply(modifier="union")
        bpy.data.objects.remove(handle, do_unlink=True)
    except Exception as e:
        print("BOOLEAN_FALLBACK:", e)

# exportar STL (mm, +Z arriba) y guardar blend

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.wm.stl_export(filepath=OUT_STL)
print("GEN_OK", json.dumps({"parts": len([o for o in SC.objects if o.type == "MESH"])}))
