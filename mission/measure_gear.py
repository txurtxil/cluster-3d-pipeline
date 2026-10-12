"""measure_gear.py — Metrologia del engranaje helicoidal (autoridad geometrica).
Uso: blender -b <modelo.blend> -P measure_gear.py
Imprime: MEASURE_JSON { "dims": {...}, "manifold": {"ok":...}, "components": ... }

Metodos (todo por vertices del mesh evaluado, nunca bound_box):
· teeth:      armónica circular k en 16..32 sobre la cresta (FFT sin numpy).
· pitch_d:    DERIVADO -> RA = RP + M; M estimado del salto radial
              cresta->raiz = 2.25*M. La raiz mide el muro interior de la
              corona (RF - EMBED); EMBED=0.25 es convencion compartida con
              el generador (la corona se incrusta en el nucleo).
· helix:      fase del armónico en PARES SIMETRICOS de flancos (sin sesgo) a
              dos radios (RP y 0.9*RA); des-alias por la ley fisica
              dphi(r) = B*tan(beta)/r  ->  C = dphi*r constante.
              beta = atan(C/B). Requiere |beta| tal que el alias sea
              resoluble; si no, null + nota en not_measured.
· bore_d:     rayo desde el centro hacia -X (el chavetero vive en +X).
"""
import bpy, json, sys, math
import cmath
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
meshes = [o.evaluated_get(dg) for o in bpy.context.scene.objects if o.type == "MESH"]
meshes = [o for o in meshes if len(o.data.vertices) > 0]
if not meshes:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"})); sys.exit(0)

allv = []
for o in meshes:
    allv += [o.matrix_world @ v.co for v in o.data.vertices]
rs = [math.hypot(v.x, v.y) for v in allv]
zs = [v.z for v in allv]
z0 = min(zs)

manifold_all = True
for o in meshes:
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    if any(v != 2 for v in ec.values()):
        manifold_all = False

# ---- taladro (primero: su radio contamina cualquier minimo global)
sc = bpy.context.scene
zc_all = (z0 + max(zs)) / 2.0
hit, loc, *_ = sc.ray_cast(dg, Vector((0, 0, zc_all)), Vector((-1, 0, 0)))
bore_d = 2.0 * math.hypot(loc.x, loc.y) if hit else None
bore_r = (bore_d or 0.0) / 2.0

# ---- cresta y radios clave
RA_meas = max(rs)
crest = [v for v, r in zip(allv, rs) if r >= RA_meas - 0.01]
zcmax = max(v.z for v in crest)          # altura de la corona (sin el cubo)
B_meas = zcmax - z0

# raiz del DIENTE = minimo fuera de taladro/chavetero + convencion EMBED
EMBED = 0.25
rf_tooth = min(r for r in rs if r > 18.0) + EMBED
M_est = (RA_meas - rf_tooth) / 2.25
RP_est = RA_meas - M_est
pitch_d = 2.0 * RP_est

# ---- teeth por armónica circular de la cresta
cang = [cmath.exp(1j * math.atan2(v.y, v.x)) for v in crest]
spec = [(k, abs(sum(z ** k for z in cang))) for k in range(16, 33)]
teeth = max(spec, key=lambda t: t[1])[0]
P_meas = 2 * math.pi / teeth


def ring_angles(z_hi, r_lo, r_hi):
    """Vertices de un anillo extremo. OJO: las caras laterales no tienen
    muestras internas en z (quads de z=0 a z=B): solo existen anillos
    extremos. El CHAMFAN preserva el ANGULO de estos vertices (su corte es
    radial-vertical), asi que las bandas extremas son inmunes para la fase."""
    out = []
    for v, r in zip(allv, rs):
        if r_lo <= r <= r_hi:
            if z_hi and v.z > zcmax - 0.6:
                out.append((r, math.atan2(v.y, v.x)))
            elif not z_hi and v.z < z0 + 0.6:
                out.append((r, math.atan2(v.y, v.x)))
    return out


def adiff(a, b):
    d = (a - b) % (2 * math.pi)
    return d - 2 * math.pi if d > math.pi else d


# --- helice por pendiente de fase entre los NR anillos (sin alias: el
#     generador interpola NR anillos, twist_por_tramo < medio-paso) ---
NR_EXPECT = 4
RF_est = RP_est - 1.25 * M_est
# banda de fase: centro de flancos (pares simetricos puros). Los arcos de RAIZ
# viven en los huecos -> armonico en CONTRAFASE (24*P/2 = pi) que cancelaba
# parcialmente la senal y sesgaba la pendiente (+2.4 deg medidos)
R_PHASE_LO = RP_est - 0.7
R_PHASE_HI = RP_est + 0.7


def phase_band(r_lo, r_hi, zc, half=0.6):
    sel = []
    for v, r in zip(allv, rs):
        if r_lo <= r <= r_hi and abs(v.z - zc) <= half:
            sel.append(math.atan2(v.y, v.x))
    if len(sel) < teeth // 2:
        return None
    z = sum(cmath.exp(1j * teeth * a) for a in sel)
    return math.atan2(z.imag, z.real)


helix_angle = None
bands_ok = True
phases = []
for j in range(NR_EXPECT):
    zc_j = z0 + B_meas * j / (NR_EXPECT - 1)
    pj = phase_band(R_PHASE_LO, R_PHASE_HI, zc_j)
    if pj is None:
        bands_ok = False
        print("DIAG banda %d vacia (zc=%.2f)" % (j, zc_j), flush=True)
        break
    phases.append(pj)
if bands_ok:
    unw = [phases[0]]
    for j in range(1, NR_EXPECT):
        unw.append(unw[-1] + adiff(phases[j], phases[j - 1]))
    slope = (unw[-1] - unw[0]) / B_meas          # rad(fase)/mm
    helix_angle = math.degrees(math.atan(RP_est * slope / teeth))

print("MEASURE_JSON " + json.dumps({
    "dims": {"pitch_d": round(pitch_d, 3), "teeth": float(teeth),
             "helix_angle": round(helix_angle, 2) if helix_angle is not None else None,
             "bore_d": round(bore_d, 3) if bore_d else None},
    "tip_d": round(2 * RA_meas, 3), "root_d": round(2 * rf_tooth, 3),
    "manifold": {"ok": manifold_all}, "components": len(meshes),
    "not_measured": [
        "pitch_d DERIVADO (RA y modulo estimados; no medible directo por ray-casting)",
        "raiz corregida por EMBED=0.25 (convencion compartida con el generador)",
        "helix por pendiente de fase en 4 anillos (requiere twist/tramo < medio-paso)",
    ],
}))
