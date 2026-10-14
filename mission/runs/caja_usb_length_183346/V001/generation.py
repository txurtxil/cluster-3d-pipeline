"""gen_caja_usb.py — Caja organizadora USB/NVMe con tapa snap (v1).
Uso: blender -b --factory-startup -P gen_caja_usb.py -- <params.json> <out.blend> <out.stl>

Fase 5 del pipeline: generador INICIADO por Qwen3-30B local (8.4KB de codigo;
las gates detectaron: (1) salida truncada por max_tokens, (2) paredes de
espesor cero). Completado y corregido bajo el playbook (sin booleanos,
solidos por from_pydata solapados, fiduciales, GEN_OK JSON).

Parametros: LENGTH, WIDTH, HEIGHT, WALL, COMP_X, COMP_Y, DIVIDER_W, DEPTH,
TAB_W, TAB_T, CHAMFER
"""
import bpy, json, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
P = json.load(open(argv[0]))
OUT_BLEND, OUT_STL = argv[1], argv[2]

L = float(P["LENGTH"]); W = float(P["WIDTH"]); H = float(P["HEIGHT"])
WALL = float(P["WALL"]); CX = int(round(float(P.get("COMP_X", 3))))
CY = int(round(float(P.get("COMP_Y", 2))))
DW = float(P.get("DIVIDER_W", 2)); DEPTH = float(P.get("DEPTH", 20))
TAB_W = float(P.get("TAB_W", 8)); TAB_T = float(P.get("TAB_T", 1.2))
CH = float(P.get("CHAMFER", 0.5))
GAP = 0.15          # holgura snap
LID_Z = H + 2.0

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene


def box(x0, x1, y0, y1, z0, z1, name):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    m = bpy.data.meshes.new(name); m.from_pydata(v, [], f); m.update()
    o = bpy.data.objects.new(name, m); SC.collection.objects.link(o)
    return o


def bevel(obj):
    if CH <= 0:
        return
    for o in SC.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bv = obj.modifiers.new("chaflan", "BEVEL"); bv.width = CH; bv.segments = 2
    bv.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier="chaflan")


# ---------- 1. cuerpo: 4 paredes solidas + fondo ----------
hx, hy = L / 2.0, W / 2.0
parts = []
parts.append(box(-hx, hx, hy - WALL, hy, 0, H, "wall_front"))
parts.append(box(-hx, hx, -hy, -hy + WALL, 0, H, "wall_back"))
parts.append(box(-hx, -hx + WALL, -hy + WALL, hy - WALL, 0, H, "wall_left"))
parts.append(box(hx - WALL, hx, -hy + WALL, hy - WALL, 0, H, "wall_right"))
parts.append(box(-hx, hx, -hy, hy, 0, WALL, "floor"))
# labio perimetral para el snap: banda fina en la zona superior, sobresale GAP+0.45
lip = 0.6
parts.append(box(-hx - lip, hx + lip, hy - WALL, hy + lip, H - 1.2, H, "lip_front"))
parts.append(box(-hx - lip, hx + lip, -hy - lip, -hy + WALL, H - 1.2, H, "lip_back"))
parts.append(box(-hx - lip, -hx + WALL, -hy, hy, H - 1.2, H, "lip_left"))
parts.append(box(hx - WALL, hx + lip, -hy, hy, H - 1.2, H, "lip_right"))

# ---------- 2. tabiques interiores ----------
ix0, ix1 = -hx + WALL, hx - WALL
iy0, iy1 = -hy + WALL, hy - WALL
for i in range(1, CX):
    x = ix0 + (ix1 - ix0) * i / CX
    parts.append(box(x - DW / 2.0, x + DW / 2.0, iy0 - 0.5, iy1 + 0.5, WALL, WALL + DEPTH, "div_x"))
for j in range(1, CY):
    y = iy0 + (iy1 - iy0) * j / CY
    parts.append(box(ix0 - 0.5, ix1 + 0.5, y - DW / 2.0, y + DW / 2.0, WALL, WALL + DEPTH, "div_y"))

# ---------- 3. tapa: plano + pestanas EXTERNAS con resaltes (snap real) ----------
parts.append(box(-hx, hx, -hy, hy, LID_Z, LID_Z + WALL, "lid"))
tw = TAB_W
tab_z0 = H - 1.2 - GAP - 0.5          # envuelve el labio (labio: H-1.2..H)
# pestanas colgando FUERA de cada pared
parts.append(box(-hx + tw, hx - tw, hy + GAP, hy + GAP + TAB_T, tab_z0, LID_Z, "tab_f"))
parts.append(box(-hx + tw, hx - tw, -hy - GAP - TAB_T, -hy - GAP, tab_z0, LID_Z, "tab_b"))
parts.append(box(-hx - GAP - TAB_T, -hx - GAP, -hy + tw, hy - tw, tab_z0, LID_Z, "tab_l"))
parts.append(box(hx + GAP, hx + GAP + TAB_T, -hy + tw, hy - tw, tab_z0, LID_Z, "tab_r"))
# resaltes hacia DENTRO, bajo el labio -> el snap engancha al presionar
bump = 0.55
zb0, zb1 = H - 1.2 - 0.9, H - 1.2
parts.append(box(-hx + tw, hx - tw, hy + GAP - bump, hy + GAP, zb0, zb1, "bump_f"))
parts.append(box(-hx + tw, hx - tw, -hy - GAP, -hy - GAP + bump, zb0, zb1, "bump_b"))
parts.append(box(-hx - GAP, -hx - GAP + bump, -hy + tw, hy - tw, zb0, zb1, "bump_l"))
parts.append(box(hx + GAP - bump, hx + GAP, -hy + tw, hy - tw, zb0, zb1, "bump_r"))

for o in parts:
    bevel(o)

# ---------- 4. export STL + fiduciales ----------
bpy.ops.wm.stl_export(filepath=OUT_STL)
MARK = [(hx, 0, H), (0, hy, H), (0, 0, LID_Z + WALL), (0, 0, 0)]
mm = bpy.data.meshes.new("fiduciales"); mm.from_pydata(MARK, [], []); mm.update()
mo = bpy.data.objects.new("fiduciales", mm); SC.collection.objects.link(mo)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("GEN_OK", json.dumps({"parts": len([o for o in SC.objects if o.type == "MESH" and o.name != "fiduciales"])}))
