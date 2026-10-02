#!/usr/bin/env python3
# camera_calibration.py <reference.png> <blend> <salida_camera.json> [--budget N]
# Fase de camara (prioridad 1 del refactor): optimiza az/cam_h/dist/lens minimizando
# la DIFERENCIA DE SILUETA (IoU de mascaras) contra la foto de referencia.
# NUNCA toca geometria. Estrategia: coarse (dist x lens) -> fine (az x cam_h).
# Renderiza con render_ref_cam.py (camara calibrada, resolucion de la foto).
import sys, json, os, subprocess, cv2, numpy as np

ref_p, blend, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
budget = int(sys.argv[sys.argv.index("--budget")+1]) if "--budget" in sys.argv else 18
work = os.path.expanduser("~/recon3d/work/calib")
os.makedirs(work, exist_ok=True)
BLENDER = os.path.expanduser("~/blender/blender")
RENDERCAM = os.path.expanduser("~/pipeline3d/render_ref_cam.py")

from seg import mask_of, normalize  # segmentacion UNICA compartida con compare_images
mask_photo = mask_render = mask_of

def iou(a, b):
    W = max(a.shape[1], b.shape[1])
    def pad(m):
        l = (W-m.shape[1])//2
        return np.pad(m, ((0, 0), (l, W-m.shape[1]-l)))
    A, B = pad(a), pad(b)
    inter = (A & B).sum(); union = (A | B).sum()
    return inter/union if union else 0.0

ref_mask = normalize(mask_photo(ref_p))
history = []

def try_cam(az, h, dist, lens, tag):
    png = os.path.join(work, "cand_%s.png" % tag)
    subprocess.run([BLENDER, "-b", blend, "-P", RENDERCAM, "--",
                    png, "NONE", str(az), str(h), str(dist), str(lens), "512", "896"],
                   check=True, capture_output=True)
    score = iou(ref_mask, normalize(mask_render(png)))
    history.append(dict(az=az, cam_h=h, dist=dist, lens=lens, iou=round(score, 4)))
    print("  cam az=%g h=%g d=%g lens=%g -> IoU %.4f" % (az, h, dist, lens, score), flush=True)
    return score

best = dict(az=28.0, cam_h=42.0, dist=760.0, lens=55.0, iou=0.0)
n = 0
# coarse: dist x lens (az/h fijos al valor historico)
for dist in (400.0, 580.0, 760.0):
    for lens in (45.0, 60.0, 75.0):
        if n >= budget: break
        s = try_cam(best["az"], best["cam_h"], dist, lens, "c%d" % n); n += 1
        if s > best["iou"]:
            best.update(dist=dist, lens=lens, iou=s)
    if n >= budget: break
# fine: az x cam_h alrededor del mejor coarse
for az in (12.0, 28.0, 44.0):
    for h in (30.0, 42.0, 56.0):
        if n >= budget: break
        s = try_cam(az, h, best["dist"], best["lens"], "f%d" % n); n += 1
        if s > best["iou"]:
            best.update(az=az, cam_h=h, iou=s)

out = dict(camera=dict(az_deg=best["az"], cam_h=best["cam_h"], dist=best["dist"],
                       lens=best["lens"], resolution=[512, 896],
                       renderer="render_ref_cam.py"),
           score=dict(silhouette_iou=round(best["iou"], 4)),
           history=history, note="geometria intacta: solo camara")
json.dump(out, open(out_json, "w"), indent=1)
print("CALIB_OK iou=%.4f -> %s" % (best["iou"], out_json))
