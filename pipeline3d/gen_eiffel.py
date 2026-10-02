# gen_eiffel.py — Torre Eiffel v5: silueta limpia y estructura esencial.
# 170.00 mm (~1:1940). ~450 elementos: patas conicas curvas, 4 arcos, 3 forjados,
# riel+diagonal escasos por cara, cumbre simple. Nada de ruido.
# Patron pipeline: PARAMS arriba, 1 BU = 1 mm, -- <salida.blend>, print GEN_OK
import bpy, math, sys, os
import numpy as np

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/pieza.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

PARAMS = dict(H=170.0, voxel=0.35, step=3.0)

# silueta real: semiancho de eje de pata w(z), semiancho de seccion s(z)
W_KEYS = np.array([(0,31.0),(8,30.9),(18,28.8),(24,23.0),(29.4,18.0),(36,15.0),
                   (44,13.6),(52,11.8),(59.3,10.4),(70,9.5),(80,8.6),(90,8.1),
                   (100,7.6),(110,7.0),(120,6.3),(130,5.6),(142,4.85),(152,4.0),
                   (160,2.6),(166,1.4),(169,0.5),(170,0.05)])
S_KEYS = np.array([(0,4.3),(29.4,3.1),(59.3,2.5),(142,1.05),(160,0.7),(170,0.4)])
Z1, Z2, Z3 = 29.4, 59.3, 142.0

def wprof(z): return float(np.interp(z, W_KEYS[:,0], W_KEYS[:,1]))
def sprof(z): return float(np.interp(z, S_KEYS[:,0], S_KEYS[:,1]))

bpy.ops.wm.read_factory_settings(use_empty=True)

V, F = [], []
def box_beam(p1, p2, w, d):
    """Prisma rectangular constante entre p1 y p2."""
    p1 = np.asarray(p1, float); p2 = np.asarray(p2, float)
    dv = p2 - p1; L = np.linalg.norm(dv)
    if L < 1e-6: return
    dv /= L
    ref = np.array([0.0,0,1]) if abs(dv[2]) < 0.9 else np.array([1.0,0,0])
    u = np.cross(dv, ref); u /= np.linalg.norm(u); v = np.cross(dv, u)
    base = len(V)
    for p in (p1, p2):
        for su, sv in ((-1,-1),(1,-1),(1,1),(-1,1)):
            V.append(tuple(p + su*w/2*u + sv*d/2*v))
    for k in range(4):
        k2 = (k+1) % 4
        F.append((base+k, base+k2, base+4+k2, base+4+k))
    F.append((base+0, base+1, base+2, base+3))
    F.append((base+4, base+7, base+6, base+5))

def frustum(p1, p2, r1, r2, n=8):
    p1 = np.asarray(p1, float); p2 = np.asarray(p2, float)
    dv = p2 - p1; L = np.linalg.norm(dv)
    if L < 1e-6: return
    dv /= L
    ref = np.array([0.0,0,1]) if abs(dv[2]) < 0.9 else np.array([1.0,0,0])
    u = np.cross(dv, ref); u /= np.linalg.norm(u); v = np.cross(dv, u)
    base = len(V)
    for p, rr in ((p1,r1),(p2,r2)):
        for k in range(n):
            a = 2*math.pi*k/n
            V.append(tuple(p + rr*(math.cos(a)*u + math.sin(a)*v)))
    for k in range(n):
        k2 = (k+1) % n
        F.append((base+k, base+k2, base+n+k2, base+n+k))
    c1 = len(V); V.append(tuple(p1)); c2 = len(V); V.append(tuple(p2))
    for k in range(n):
        k2 = (k+1) % n
        F.append((c1, base+k2, base+k))
        F.append((c2, base+n+k, base+n+k2))

def slab(x0, y0, x1, y1, z0, z1):
    base = len(V)
    for z in (z0, z1):
        for x, y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):
            V.append((x, y, z))
    F.extend([(base+0,base+1,base+2,base+3),(base+4,base+7,base+6,base+5),
              (base+0,base+4,base+5,base+1),(base+1,base+5,base+6,base+2),
              (base+2,base+6,base+7,base+3),(base+3,base+7,base+4,base+0)])

def leg_pt(sx, sy, z): return (sx*wprof(z), sy*wprof(z), z)

# --- 1) cuatro patas: columnas conicas que siguen la curva de la silueta ---
zs = np.arange(0, PARAMS["H"] + PARAMS["step"], PARAMS["step"])
for sx, sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
    for i in range(len(zs)-1):
        z0, z1 = zs[i], zs[i+1]
        box_beam(leg_pt(sx,sy,z0), leg_pt(sx,sy,z1), 2*sprof(z0), 2*sprof(z1) if False else 2*sprof((z0+z1)/2))

# --- 2) arcos parabolicos limpios (uno por cara y nivel) ---------------------
def arch(z0, zapex, npts, sec):
    t = np.linspace(-1, 1, npts)
    span = wprof(z0) - sprof(z0)
    for axis in 'xy':
        for sign in (-1, 1):
            prev = None
            for tt in t:
                y = tt * span
                z = z0 + (zapex - z0) * (1 - tt*tt)
                p = (sign*wprof(z), y, z) if axis == 'x' else (y, sign*wprof(z), z)
                if prev is not None: box_beam(prev, p, sec, sec)
                prev = p
arch(7.0, Z1, 15, 1.3)
arch(62.0, 73.0, 9, 1.0)

# --- 3) forjados: losa + fascia (bandeja simple, sin balaustres) -------------
def deck(zc, half):
    slab(-half, -half, half, half, zc-0.5, zc+0.4)
    ring = [(-half,-half),(half,-half),(half,half),(-half,half)]
    for k in range(4):
        box_beam((ring[k][0],ring[k][1],zc-0.9),(ring[(k+1)%4][0],ring[(k+1)%4][1],zc-0.9), 1.4, 1.4)
deck(Z1, 20.5)
deck(Z2, 12.5)
deck(Z3, 6.5)

# --- 4) alma del fuste: un riel + una diagonal por cara y tramo -------------
def face_infill(axis, sign, z0, z1, rails):
    for z in np.linspace(z0, z1, rails):
        ya = wprof(z) - sprof(z)
        if axis == 'x':
            box_beam((sign*wprof(z),-ya,z),(sign*wprof(z),ya,z), 0.9, 0.9)
        else:
            box_beam((-ya,sign*wprof(z),z),(ya,sign*wprof(z),z), 0.9, 0.9)
    za, zb = z0 + 1.2, z1 - 1.2
    # una diagonal continua por cara y tramo (limpia, no enrejado)
    for zz in (z0,):
        ya, yb = wprof(za)-sprof(za), wprof(zb)-sprof(zb)
        if axis == 'x':
            box_beam((sign*wprof(za),-ya,za),(sign*wprof(zb), yb,zb), 0.9, 0.9)
            box_beam((sign*wprof(za), ya,za),(sign*wprof(zb),-yb,zb), 0.9, 0.9)
        else:
            box_beam((-ya,sign*wprof(za),za),( yb,sign*wprof(zb),zb), 0.9, 0.9)
            box_beam(( ya,sign*wprof(za),za),(-yb,sign*wprof(zb),zb), 0.9, 0.9)
for axis in 'xy':
    for sign in (-1, 1):
        face_infill(axis, sign, Z1+1.5, Z2-1.5, rails=3)
        face_infill(axis, sign, Z2+1.5, Z3-1.5, rails=6)
        face_infill(axis, sign, Z3+1.5, 160, rails=3)

# --- 5) platinas de 2 escalones por pata --------------------------------------
for sx, sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
    cx, cy = sx*wprof(0), sy*wprof(0)
    slab(cx-6.8, cy-6.8, cx+6.8, cy+6.8, 0, 1.5)
    slab(cx-5.2, cy-5.2, cx+5.2, cy+5.2, 1.5, 3.0)

# --- 6) cumbre: cabina achaflanada + aguja ------------------------------------
zc0 = 160.0
frustum((0,0,zc0),(0,0,166.0), 2.4, 1.7, 8)          # cabina
frustum((0,0,166.0),(0,0,170.0), 1.7, 0.12, 8)       # aguja

# --- ensamblar + remesh voxel + normalizar a 170.00 ---------------------------
mesh = bpy.data.meshes.new("eiffel_v5")
mesh.from_pydata(V, [], F)
mesh.update()
obj = bpy.data.objects.new("TorreEiffel_170mm", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
mod = obj.modifiers.new("FusionVoxel", 'REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = PARAMS["voxel"]
mod.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier="FusionVoxel")
s = PARAMS["H"] / obj.dimensions.z
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

mat = bpy.data.materials.new("Hierro_gris")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.60, 0.61, 0.63, 1)
b.inputs["Metallic"].default_value = 0.8
b.inputs["Roughness"].default_value = 0.4
obj.data.materials.append(mat)

sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001
bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK")
