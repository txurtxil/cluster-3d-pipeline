#!/usr/bin/env python3
# render_model.py — render del proyecto recon3d.
# Uso: blender -b current.blend -P render_model.py -- <salida.png> [--camera camera.json]
# Con --camera: camara calibrada fija (render_ref_cam.py, resolucion de la foto).
# Sin --camera: auto-encuadre (render_export.py) — solo para demos autocontenidas.
import bpy, sys, os, json
argv = sys.argv
out = argv[argv.index("--")+1]
if "--camera" in argv:
    cam = json.load(open(argv[argv.index("--camera")+1]))["camera"]
    rc = os.path.expanduser("~/pipeline3d/render_ref_cam.py")
    sys.argv = ["blender", "-b", "-P", rc, "--", out, "NONE",
                str(cam["az_deg"]), str(cam["cam_h"]), str(cam["dist"]), str(cam["lens"]),
                str(cam["resolution"][0]), str(cam["resolution"][1])]
    exec(compile(open(rc).read(), rc, "exec"))
else:
    pipeline = os.path.expanduser("~/pipeline3d/render_export.py")
    sys.argv = ["blender", "-b", "-P", pipeline, "--", out]
    exec(compile(open(pipeline).read(), pipeline, "exec"))
