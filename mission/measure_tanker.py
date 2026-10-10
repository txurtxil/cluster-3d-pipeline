"""measure_tanker.py — metrologia del petrolero v2 (autoridad geometrica).
Imprime MEASURE_JSON { dims, counts, manifold, nautical {...} }

Convencion nautica: linea de agua en z=0 (obra viva por debajo, obra muerta
por encima). TOL = tolerancia de flotacion en mm para "sumergido".

draft        = -z_min global (punto mas hondo; quilla manda sobre appendices)
freeboard    = z_min de "Cubierta" (cara inferior de la cubierta de babor/estribor)
hull_volume  = integracion por anillos de estacion de la obra viva (z<=TOL)
               + volumen de solidos cerrados completamente sumergidos
               (quilla, bulbo). Mallas abiertas en proa/pop: sin tapas.
displacement = hull_volume_mm3 * 1.025e-9  (agua de mar, toneladas)
"""
import bpy
import json
import sys
import math
from mathutils import Vector

TOL = 0.5  # mm bajo la linea de agua cuenta como sumergido

WATERLINE_BAND = "Casco_obra_viva"
DECK = "Cubierta"


def world_mesh(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    return ev, ev.to_mesh()


def ring_area(points):
    """Area de poligono (y,z) convexo: orden angular alrededor del centroide."""
    if len(points) < 3:
        return 0.0
    cy = sum(p[0] for p in points) / len(points)
    cz = sum(p[1] for p in points) / len(points)
    pts = sorted(points, key=lambda p: math.atan2(p[1] - cz, p[0] - cy))
    a = 0.0
    for i in range(len(pts)):
        y1, z1 = pts[i]
        y2, z2 = pts[(i + 1) % len(pts)]
        a += y1 * z2 - y2 * z1
    return abs(a) / 2.0


def submerged_ring_area(verts):
    """Anillo de estacion (mismo x) recortado por la linea de agua z=TOL."""
    pts = [(v.y, v.z) for v in verts if v.z <= TOL]
    n = len(verts)
    for i in range(n):
        a, b = verts[i], verts[(i + 1) % n]
        if (a.z > TOL) != (b.z > TOL):
            t = (TOL - a.z) / (b.z - a.z)
            pts.append((a.y + (b.y - a.y) * t, TOL))
    return ring_area(pts)


def signed_volume(me, mat):
    """Volumen cerrado (divergencia) en coords de mundo; exige malla watertight."""
    V = 0.0
    for t in me.loop_triangles:
        v = [mat @ me.vertices[i].co for i in t.vertices]
        V += v[0].dot(v[1].cross(v[2])) / 6.0
    return abs(V)


objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    print("MEASURE_JSON " + json.dumps({"error": "NO_MESH"}))
    sys.exit(0)

xs, ys, zs = [], [], []
bad = 0
uniq = set()
obj_data = {}  # name -> {zmin, zmax, watertight}
for o in objs:
    ev, me = world_mesh(o)
    wverts = [ev.matrix_world @ v.co for v in me.vertices]
    for w in wverts:
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    uniq.add(o.data.name)
    ec = {}
    for p in o.data.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    obj_bad = sum(1 for v in ec.values() if v != 2)
    bad += obj_bad
    obj_data[o.name] = {
        "zmin": min(v.z for v in wverts) if wverts else 0.0,
        "zmax": max(v.z for v in wverts) if wverts else 0.0,
        "watertight": obj_bad == 0,
        "wverts": wverts,
    }
    ev.to_mesh_clear()

# --- metricas nauticas ---
draft = round(-min(zs), 3)

freeboard = None
if DECK in obj_data:
    freeboard = round(obj_data[DECK]["zmin"], 3)

hull_volume = 0.0
if WATERLINE_BAND in obj_data:
    by_x = {}
    for v in obj_data[WATERLINE_BAND]["wverts"]:
        by_x.setdefault(round(v.x, 4), []).append(v)
    stations = sorted(by_x.keys())
    areas = [submerged_ring_area(by_x[x]) for x in stations]
    for i in range(len(stations) - 1):
        dx = stations[i + 1] - stations[i]
        hull_volume += (areas[i] + areas[i + 1]) / 2.0 * dx
    for name, d in obj_data.items():
        if name == WATERLINE_BAND or not d["watertight"]:
            continue
        if d["zmax"] <= TOL and d["zmin"] < -1.0:
            o = bpy.data.objects[name]
            ev, me = world_mesh(o)
            hull_volume += signed_volume(me, ev.matrix_world)
            ev.to_mesh_clear()

displacement = round(hull_volume * 1.025e-9, 4)

print("MEASURE_JSON " + json.dumps({
    "dims": {"L": round(max(xs) - min(xs), 3), "B": round(max(ys) - min(ys), 3),
             "H": round(max(zs) - min(zs), 3)},
    "counts": {"PARTS": len(objs), "UNIQ": len(uniq)},
    "manifold": {"ok": bad == 0, "bad_edges": bad},
    "nautical": {
        "draft": draft,
        "freeboard": freeboard,
        "hull_volume_mm3": round(hull_volume, 1),
        "displacement_kg": round(hull_volume * 1.025e-6, 3),
        "displacement_m3": round(hull_volume * 1.025e-9, 6),
        "displacement_t": displacement,
        "method": "rings(Casco_obra_viva,z<=0.5mm)+closed-submerged-solids; open bow/stern caps excluded",
    },
}))
