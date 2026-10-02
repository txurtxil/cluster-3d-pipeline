#!/usr/bin/env python3
# export_parts.py — exporta el chasis en grupos de impresion STL separados.
# Uso: blender -b pieza.blend -P export_parts.py -- <out_dir>
# Grupos por prefijo de nombre; cada grupo un STL propio (sin intersecciones
# entre ficheros -> cada uno es manifold y imprimible por separado).
import bpy, sys, os, json

out_dir = sys.argv[sys.argv.index("--")+1]
os.makedirs(out_dir, exist_ok=True)

GROUPS = [
    ("01_suelo_canales",  ["Suelo_Canal"]),
    ("02_muros",          ["Muro_"]),
    ("03_apoyos_placa",   ["Apoyo_"]),
    ("04_cuna_frontal",   ["Cuna_Frontal"]),
    ("05_torre_trasera",  ["Pared_IO", "Tapa_Trasera"]),
    ("06_compartimento_psu0", ["PSU0_"]),
    ("07_compartimento_psu1", ["PSU1_"]),
    ("08_skin_medallones", ["Skin_", "Medallon_"]),
    ("09_patas",          ["Pata"]),
]

report = {}
for fname, prefixes in GROUPS:
    objs = [o for o in bpy.data.objects
            if o.type == 'MESH' and any(o.name.startswith(p) for p in prefixes)]
    if not objs:
        report[fname] = "SIN_PIEZAS"
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    path = os.path.join(out_dir, fname + ".stl")
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    report[fname] = dict(piezas=len(objs), bytes=os.path.getsize(path))

json.dump(report, open(os.path.join(out_dir, "parts_report.json"), "w"), indent=1)
print("PARTS_OK", json.dumps({k: (v if isinstance(v, str) else v["piezas"]) for k, v in report.items()}))
