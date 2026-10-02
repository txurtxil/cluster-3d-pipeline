#!/usr/bin/env python3
# audit_hull.py — auditoria geometrica del casco (blender -b blend -P audit_hull.py -- out.json)
# Diagnostico RIGUROSO: coordenadas, orientacion, simetria, normales, voladizos.
import bpy, sys, json, math

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else ["/tmp/audit.json"]
out_path = argv[0]

rep = {}

def bbox(o):
    xs, ys, zs = [], [], []
    for c in o.bound_box:
        w = o.matrix_world @ bpy.mathutils.Vector(c) if hasattr(bpy, "mathutils") else None
    import mathutils
    mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mn = mathutils.Vector(map(min, mn, w)); mx = mathutils.Vector(map(max, mx, w))
    return mn, mx

objs = {o.name: o for o in bpy.data.objects}
hull = [o for o in objs.values() if o.name.startswith(("Casco_", "Bulbo", "Quilla", "Timon", "Helice", "Eje", "Espejo", "Cubierta", "Bilge"))]

# 1) Sistema de coordenadas y extremos
mn, mx = bbox(objs["Casco_obra_viva"])
rep["coord"] = dict(
    hull_x_range=[round(mn.x,2), round(mx.x,2)],
    hull_y_range=[round(mn.y,2), round(mx.y,2)],
    hull_z_range=[round(mn.z,2), round(mx.z,2)],
    note="+X=proa si Bulbo x >> Helice x")

# 2) Orientacion: bulb vs helice/timon
def cx(n):
    m, M = bbox(objs[n]); return (m+M)/2
rep["orientation"] = dict(
    bulbo_x=round(cx("Bulbo_proa").x,2),
    helice_x=round(cx("Helice_buje").x,2),
    timon_x=round(cx("Timon").x,2),
    ancla_x=round(cx("Ancla_mango").x,2),
    puente_x=round(cx("Puente").x,2),
    PROA="+X" if cx("Bulbo_proa").x > cx("Helice_buje").x else "-X")

# 3) Bulbo: forma, posicion vertical, protuberancia
b_mn, b_mx = bbox(objs["Bulbo_proa"])
rep["bulb"] = dict(
    x=[round(b_mn.x,2), round(b_mx.x,2)],
    y_half_width=round(max(abs(b_mn.y), abs(b_mx.y)),2),
    z=[round(b_mn.z,2), round(b_mx.z,2)],
    below_waterline=b_mx.z < 0,
    protrudes_past_bow=b_mx.x > mx.x - 1.0,
    centered=abs(cx("Bulbo_proa").y) < 0.5,
    size=[round(b_mx.x-b_mn.x,2), round(b_mx.y-b_mn.y,2), round(b_mx.z-b_mn.z,2)])

# 4) Simetria babor/estribor de las bandas del casco (muestreo de vertices)
def symmetry_err(o, n=400):
    import mathutils
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    step = max(1, len(vs)//n)
    errs = [abs(v.y + min(vs, key=lambda w: abs(w.x-v.x)+abs(w.z-v.z) and -w.y).y)
            for v in vs[::step]]
    return round(max(errs), 3) if errs else None
sym = {}
for name in ("Casco_obra_viva", "Casco_obra_muerta"):
    if name in objs:
        vs = objs[name].data.vertices
        import mathutils
        ws = [objs[name].matrix_world @ v.co for v in vs]
        best = 0.0
        import random
        random.seed(7)
        for v in random.sample(ws, min(300, len(ws))):
            w = min(ws, key=lambda q: (q.x-v.x)**2 + (q.z-v.z)**2 + (q.y+v.y)**2)
            best = max(best, abs(abs(v.y)-abs(w.y)))
        sym[name] = round(best, 3)
rep["symmetry_y"] = sym

# 5) Normales: % de caras del casco con normal apuntando al interior
def inward_stats(o):
    import mathutils
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    cen = mathutils.Vector((0,0,0))
    for w in ws: cen += w
    cen /= len(ws)
    inward = 0; tot = 0
    for p in o.data.polygons:
        c = mathutils.Vector((0,0,0))
        for i in p.vertices: c += ws[i]
        c /= len(p.vertices)
        if (c - cen).dot(p.normal) < 0:
            inward += 1
        tot += 1
    return dict(faces=tot, inward=inward, pct=round(100*inward/tot,1))
rep["normals"] = {n: inward_stats(objs[n]) for n in ("Casco_obra_viva","Casco_obra_muerta") if n in objs}

# 6) Voladizo de cubierta: cubierta vs manga del casco en extremos
deck_mn, deck_mx = bbox(objs["Cubierta"])
rep["deck_overhang"] = dict(
    deck_half_width=round(deck_mx.y,2),
    hull_max_half_width=round(mx.y,2),
    deck_x=[round(deck_mn.x,2), round(deck_mx.x,2)],
    hull_x=[round(mn.x,2), round(mx.x,2)],
    overhang_mm=round(deck_mx.y - mx.y, 2))

# 7) Transom vs seccion de popa
t_mn, t_mx = bbox(objs["Espejo_popa"])
rep["transom"] = dict(
    width=round(t_mx.y-t_mn.y,2),
    hull_stern_width=round(2*abs(mn.y),2),
    wider_than_stern=(t_mx.y-t_mn.y) > 2*abs(mn.y)+0.5)

# 8) Tabla proa/popa de elementos clave
E = [("Bulbo_proa","proa"),("Ancla_mango","proa"),("Mastil_proa","proa"),
     ("Timon","popa"),("Helice_buje","popa"),("Puente","popa"),("Chimenea_baja","popa")]
tbl = []
for n, esperado in E:
    if n in objs:
        x = cx(n).x
        mid = (mn.x+mx.x)/2
        actual = "proa" if x > mid else "popa"
        tbl.append(dict(elemento=n, esperado=esperado, actual=actual,
                        x=round(x,1), estado="PASS" if actual==esperado else "FAIL"))
rep["element_table"] = tbl

json.dump(rep, open(out_path, "w"), indent=1)
print("AUDIT_OK", out_path)
for k in ("coord","orientation","symmetry_y","deck_overhang","transom"):
    print(k, json.dumps(rep[k]))
print("normals", json.dumps(rep["normals"]))
for r in tbl: print(r["elemento"], r["esperado"], "->", r["actual"], r["estado"])
