"""measure_caja_roscada.py — Metrologia del tarro roscado (autoridad geometrica).
Uso: blender -b <modelo.blend> -P measure_caja_roscada.py

· D_body/H/wall/lid_height: por rayos y fiduciales (borde cuerpo, borde tapa, techo).
· thread_pitch: MUESTREO RADIAL vs z + FFT. La helice cruza cada angulo fijo
  una vez por vuelta -> el radio medido tiene muescas espaciadas EXACTAMENTE
  un paso. Se muestrea r(z) a angulo fijo en la zona roscada y se extrae el
  periodo dominante (busqueda restringida 0.5x..2x del esperado... aqui: 1..12 mm).
  Misma idea en la cresta de la tapa.
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
MARK = [fidu[0].matrix_world @ v.co for v in fidu[0].data.vertices]
Z_RIM = MARK[0].z          # borde superior del cuerpo (= H)
Z_LIDBOT = MARK[1].z       # fondo de la tapa (se hunde 0.5 en el cuello)
Z_LIDTOP = MARK[2].z       # techo de la tapa
H = Z_RIM
LID_H = Z_LIDTOP - Z_RIM   # altura UTIL de la tapa (la parte que se ve: = spec)

manifold_all = True
for o in piece:
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    if any(v != 2 for v in ec.values()):
        manifold_all = False

sc = bpy.context.scene


def ray_r(z, r_from):
    """Radio del primer impacto desde (r_from,0,z) hacia el eje (-X)."""
    hit, loc, *_ = sc.ray_cast(dg, Vector((r_from, 0.0, z)), Vector((-1, 0, 0)))
    return math.hypot(loc.x, loc.y) if hit else None


R_OUT = ray_r(H * 0.5, 80.0)
# pared: 2º rayo DESDE DENTRO (x=R_OUT-0.2 hacia el eje) -> pared interior
R_IN_HIT = None
if R_OUT:
    hit2, loc2, *_ = sc.ray_cast(dg, Vector((R_OUT - 0.2, 0.0, H * 0.5)), Vector((-1, 0, 0)))
    R_IN_HIT = math.hypot(loc2.x, loc2.y) if hit2 else None
wall = (R_OUT - R_IN_HIT) if (R_OUT and R_IN_HIT) else None
D_body = 2 * R_OUT if R_OUT else None

# ---------- paso de rosca: espaciado MEDIANO de muescas ----------
# La helice cruza un angulo fijo una vez por vuelta -> las muescas estan
# espaciadas EXACTAMENTE un paso; con 2-3 vueltas el FFT es pobre, pero la
# mediana de los espaciados es exacta.
def pitch_from_zone(z_lo, z_hi, from_center):
    zs, rs = [], []
    z = z_lo
    while z <= z_hi:
        if from_center:
            # direccion ligeramente desviada del eje: asi no roza la arista
            # del prisma (los vertices del cilindro caen exactamente en y=0)
            hit, loc, *_ = sc.ray_cast(dg, Vector((0.0, 0.0, z)), Vector((1, 0.02, 0)).normalized())
        else:
            hit, loc, *_ = sc.ray_cast(dg, Vector((R_OUT + 2.0, 0.0, z)), Vector((-1, 0, 0)))
        if hit:
            zs.append(z); rs.append(math.hypot(loc.x, loc.y))
        z += 0.1
    print("DIAG zone n=%d amp=%.3f" % (len(rs), (max(rs) - min(rs)) if rs else 0.0), flush=True)
    if len(rs) < 20:
        return None, len(rs)
    mean = sum(rs) / len(rs)
    amp = max(rs) - min(rs)
    if amp < 0.05:
        return None, len(rs)
    print("DIAG zone n=%d amp=%.3f" % (len(rs), amp), flush=True)
    # muescas: CRUCES de la media (los flancos). Los extremos son mesetas
    # (la derivada no cambia de signo ahi) -> cruce de media es robusto.
    # El paso = suma de dos medias medias consecutivas.
    cross = []
    for i in range(1, len(rs)):
        if (rs[i - 1] - mean) * (rs[i] - mean) <= 0 and rs[i] != rs[i - 1]:
            cross.append(zs[i])
    if len(cross) < 4:
        return None, len(rs)
    dd = [cross[k + 1] - cross[k] for k in range(len(cross) - 1)]
    pers = [dd[k] + dd[k + 1] for k in range(len(dd) - 1)]
    pers.sort()
    return pers[len(pers) // 2], len(rs)


# cuerpo: DESDE EL CENTRO (la rosca hembra esta en la pared interior);
# zona por debajo de la falda de la tapa para no verla
tp_body, nb = pitch_from_zone(H - 14.0, H - 4.0, True)
# tapa: desde fuera (la cresta macho esta en la superficie exterior)
tp_lid, nl = pitch_from_zone(Z_LIDBOT + 1.5, Z_LIDTOP - 1.0, False)

print("MEASURE_JSON " + json.dumps({
    "dims": {"D_body": round(D_body, 2) if D_body else None,
             "H": round(H, 2), "wall": round(wall, 3) if wall else None,
             "lid_height": round(LID_H, 2),
             "thread_pitch": round(tp_body, 2) if tp_body else None},
    "thread_pitch_lid": round(tp_lid, 2) if tp_lid else None,
    "manifold": {"ok": manifold_all}, "components": len(piece),
    "not_measured": ["SEAL_GROOVE (reservado v2)",
                     "tapa/falda/cresta son solidos solapados: el slicer los une"],
}))
