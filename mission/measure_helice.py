"""measure_helice.py — Metrologia de la helice via FIDUCIALES (v2).
Uso: blender -b <modelo.blend> -P measure_helice.py

Los fiduciales son vertices-sueltos que el generador emite por eje de
estacion (punto xu=0.4, y=0 de cada seccion). Miden el EJE teorico:
sin sesgo de distribucion de cuerda ni de muestreo de la superficie.
No estan en el STL; viven solo en el .blend (metrologia, no pieza).

· D:           2 * radio maximo de fiduciales.
· blades:      grupos angulares de fiduciales (FFT k en 2..6).
· pitch_ratio: por pala, u_j = posicion tangencial acumulada (sum r*dtheta);
               regresion z vs u => tan(beta); P/D = 2*pi*r07*tan(beta)/D.
· rake/skew:   diferencias punta-raiz del eje (z / theta).
· hub_d/shaft_d: rayos horizontales en angulo entre palas (theta=pi/B).
"""
import bpy, json, sys, math
import cmath
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
meshes = [o.evaluated_get(dg) for o in bpy.context.scene.objects if o.type == "MESH"]
piece = [o for o in meshes if o.name != "fiduciales" and len(o.data.vertices) > 0]
fidu = [o for o in meshes if o.name == "fiduciales"]
if not piece or not fidu:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH_O_FIDUCIALES"})); sys.exit(0)

fv = [fidu[0].matrix_world @ v.co for v in fidu[0].data.vertices]
fr = [math.hypot(v.x, v.y) for v in fv]

manifold_all = True
for o in piece:
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    if any(v != 2 for v in ec.values()):
        manifold_all = False

# D se mide sobre los EJES (fv[::3]): LE/TE sobrepasan el radio de punta
axes_r = [math.hypot(fv[i].x, fv[i].y) for i in range(0, len(fv), 3)]
D_meas = 2.0 * max(axes_r)
R = D_meas / 2.0
fz = [cmath.exp(1j * math.atan2(v.y, v.x)) for v in fv]
spec = [(k, abs(sum(z ** k for z in fz))) for k in range(2, 7)]
blades = max(spec, key=lambda t: t[1])[0]

# Los fiduciales se emiten en orden determinista: por pala b, por estacion k:
# (eje, LE, TE) = fv[(b*S+k)*3 + {0,1,2}]. S lo inferimos: S = n/(3*B).
n = len(fv)
S = n // (3 * blades)
stations = []
for k in range(S):
    stations.append([fv[(b * S + k) * 3:(b * S + k) * 3 + 3] for b in range(blades)])

def adiff(a, b):
    d = (a - b) % (2 * math.pi)
    return d - 2 * math.pi if d > math.pi else d

# ---- pitch_ratio: del vector LE->TE de la estacion mas cercana a 0.7R
#     tan(beta) = dz / du  (du = separacion tangencial = r * dtheta)
# rake/skew: del EJE entre estacion de raiz y de punta
pds, rakes, skews = [], [], []
for b in range(blades):
    axis = [stations[k][b][0] for k in range(S)]
    rr = [math.hypot(a.x, a.y) for a in axis]
    k07 = min(range(S), key=lambda k: abs(rr[k] - 0.7 * R))
    le, te = stations[k07][b][1], stations[k07][b][2]
    du = 0.5 * (math.hypot(le.x, le.y) + math.hypot(te.x, te.y)) * adiff(
        math.atan2(te.y, te.x), math.atan2(le.y, le.x))
    dz = te.z - le.z
    if abs(du) > 1e-6:
        pds.append(2 * math.pi * rr[k07] * (dz / du) / D_meas)
    rakes.append(axis[-1].z - axis[0].z)
    dth = adiff(math.atan2(axis[-1].y, axis[-1].x), math.atan2(axis[0].y, axis[0].x))
    skews.append(math.degrees(dth))

pitch_ratio = round(sorted(pds)[len(pds) // 2], 3) if pds else None
rake = round(sorted(rakes)[len(rakes) // 2], 2) if rakes else None
skew = round(sorted(skews)[len(skews) // 2], 1) if skews else None

# ---- cubo y taladro por rayos en angulo entre palas
sc = bpy.context.scene
ang = math.pi / blades
dvec = Vector((math.cos(ang), math.sin(ang), 0))
hits = []
o = Vector((0, 0, 0.0))
for i in range(3):
    hit, loc, *_ = sc.ray_cast(dg, o, dvec)
    if not hit:
        break
    hits.append(math.hypot(loc.x, loc.y))
    o = Vector((loc.x + 0.05 * dvec.x, loc.y + 0.05 * dvec.y, 0.0))
shaft_d = round(2 * hits[0], 2) if hits else None
hub_d = round(2 * hits[1], 2) if len(hits) > 1 else None

print("MEASURE_JSON " + json.dumps({
    "dims": {"D": round(D_meas, 2), "blades": float(blades),
             "pitch_ratio": pitch_ratio, "rake": rake, "skew": skew,
             "hub_d": hub_d, "shaft_d": shaft_d},
    "manifold": {"ok": manifold_all}, "components": len(piece),
    "not_measured": ["BAR (area de palas): estimado por construccion, no por vertices"],
}))
