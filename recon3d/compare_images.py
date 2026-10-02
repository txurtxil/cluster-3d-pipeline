#!/usr/bin/env python3
# compare_images.py <ref.png> <render.png> <out_dir>
# Metricas OBJETIVAS: IoU, Dice, distancia de contorno (px), error bbox,
# error de eje, metricas por 5 zonas, huecos. Escribe metrics.json + difference.png
# FIX alpha: solo se usa el canal alpha si el fondo es transparente DE VERDAD
# (recortes tipo refcam.png). Los renders RGBA llevan fondo opaco (alpha=255)
# y deben umbralizarse en gris. Antes: mascara todo-a-unos -> IoU siempre 1.0.
import sys, json, os, cv2, numpy as np
from scipy.spatial import cKDTree
from seg import mask_of, normalize

def openings_of(m):
    h, w = m.shape
    inv = (1 - m).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(inv, 8)
    out = []
    for i in range(1, n):
        x, y, ww, hh, ar = stats[i]
        if ar > 0.015*h*w and ww > 6 and hh > 6:
            out.append(dict(width=int(ww), height=int(hh), area_pct=round(float(ar)/(h*w), 4)))
    return sorted(out, key=lambda o: -o["area_pct"])[:8]

ref_p, ren_p, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)
refn = normalize(mask_of(ref_p))
renn = normalize(mask_of(ren_p))
W = max(refn.shape[1], renn.shape[1])
def pad(m):
    l = (W-m.shape[1])//2
    return np.pad(m, ((0, 0), (l, W-m.shape[1]-l)))
refp, renp = pad(refn), pad(renn)

inter = int((refp & renp).sum()); union = int((refp | renp).sum())
iou = inter/union
dice = 2*inter/(refp.sum()+renp.sum())
c1, _ = cv2.findContours(refp*255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c2, _ = cv2.findContours(renp*255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
p1 = c1[0][:, 0, :].astype(float); p2 = c2[0][:, 0, :].astype(float)
contour_px = float((cKDTree(p2).query(p1)[0].mean() + cKDTree(p1).query(p2)[0].mean())/2)

def centroid(m):
    ys, xs = np.where(m > 0)
    return xs.mean(), ys.mean()
crx, cry = centroid(refp); cex, cey = centroid(renp)
axis_err = abs(crx-cex)/W

zones = {}
for i in range(5):
    z0, z1 = 512*i//5, 512*(i+1)//5
    a, b = refp[z0:z1], renp[z0:z1]
    ia = int((a & b).sum()); ua = int((a | b).sum())
    def wd(m):
        ys, xs = np.where(m > 0)
        return int(xs.max()-xs.min()+1) if len(xs) else 0
    wr, we = wd(a), wd(b)
    zones["zone_%d" % (i+1)] = dict(
        iou=round(ia/ua, 4) if ua else None,
        width_ref=wr, width_render=we,
        width_err=round(abs(we-wr)/wr, 4) if wr else None)

ref_op = openings_of(refp); ren_op = openings_of(renp)
op_metrics = dict(
    count_ref=len(ref_op), count_render=len(ren_op),
    area_ref=round(sum(o["area_pct"] for o in ref_op), 4),
    area_render=round(sum(o["area_pct"] for o in ren_op), 4))
op_metrics["area_delta_pct"] = round(
    100*(op_metrics["area_render"]-op_metrics["area_ref"])/max(op_metrics["area_ref"], 1e-9), 1)

metrics = dict(
    silhouette_iou=round(iou, 4),
    dice=round(dice, 4),
    contour_error_px=round(contour_px, 2),
    bbox_width_err=round(abs(renn.shape[1]-refn.shape[1])/refn.shape[1], 4),
    bbox_height_err=0.0,
    center_axis_error=round(axis_err, 4),
    zones=zones,
    openings=op_metrics,
    convergence_thresholds=dict(iou_min=0.92, contour_px_max=6.0,
                                bbox_err_max=0.06, axis_err_max=0.03,
                                zone_width_err_max=0.10, opening_area_delta_max=15.0))
json.dump(metrics, open(os.path.join(out_dir, "metrics.json"), "w"), indent=1)

rgb = np.ones((512, W, 3), np.uint8)*255
both = (refp & renp).astype(bool); only_r = (refp & ~renp).astype(bool); only_e = (renp & ~refp).astype(bool)
rgb[both] = (255, 255, 255); rgb[only_r] = (255, 60, 60); rgb[only_e] = (60, 200, 255)
cv2.imwrite(os.path.join(out_dir, "difference.png"), rgb)
print("COMPARE_OK iou=%.4f dice=%.4f contour=%.1fpx bbox_err=%.3f axis=%.3f openings_delta=%+.1f%%" %
      (iou, dice, contour_px, metrics["bbox_width_err"], axis_err, op_metrics["area_delta_pct"]))
