#!/usr/bin/env python3
# analyze_reference.py <imagen> <salida.json> -> REFERENCE_GEOMETRY.json
# bbox, silueta, 5 zonas, eje central, huecos, plataformas, keypoints.
# FIX alpha: solo si el fondo es transparente de verdad; si no, grabcut.
import sys, json, cv2, numpy as np

img_path, out_json = sys.argv[1], sys.argv[2]
img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
if img is None:
    sys.exit("no image: " + img_path)
h, w = img.shape[:2]

has_alpha = img.shape[-1] == 4 and img[:, :, 3].min() < 10
if has_alpha:
    mask = (img[:, :, 3] > 10).astype(np.uint8)
else:
    m = np.zeros((h, w), np.uint8)
    rect = (int(w*0.08), int(h*0.04), int(w*0.84), int(h*0.92))
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(img[:, :, :3], m, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    mask = np.where((m == 2) | (m == 0), 0, 1).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

ys, xs = np.where(mask > 0)
if len(xs) < 50:
    sys.exit("foreground too small")
bbox = dict(x=int(xs.min()), y=int(ys.min()),
            width=int(xs.max()-xs.min()+1), height=int(ys.max()-ys.min()+1))

contours, _ = cv2.findContours(mask*255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cnt = max(contours, key=cv2.contourArea)[:, 0, :]
step = max(1, len(cnt)//200)
silhouette = cnt[::step].tolist()

zones = {}
for i in range(5):
    z0 = bbox["y"] + bbox["height"]*i//5
    z1 = bbox["y"] + bbox["height"]*(i+1)//5
    band = mask[z0:z1, :]
    colsum = band.sum(axis=0)
    cols = np.where(colsum > 0)[0]
    zones["zone_%d" % (i+1)] = dict(
        y0=int(z0), y1=int(z1),
        width=int(cols.max()-cols.min()+1) if len(cols) else 0,
        cx=int((cols.max()+cols.min())/2) if len(cols) else None)

cys = np.array([(zones["zone_%d" % i]["y0"]+zones["zone_%d" % i]["y1"])/2 for i in range(1, 6)])
cxs = np.array([zones["zone_%d" % i]["cx"] if zones["zone_%d" % i]["cx"] is not None else w/2
                for i in range(1, 6)])
A = np.vstack([cys, np.ones(5)]).T
slope, intercept = np.linalg.lstsq(A, cxs, rcond=None)[0]
center_axis = dict(slope=float(slope), intercept=float(intercept))

sub = mask[bbox["y"]:bbox["y"]+bbox["height"], bbox["x"]:bbox["x"]+bbox["width"]]
inv = (1 - sub).astype(np.uint8)
n, lab, stats, cent = cv2.connectedComponentsWithStats(inv, 8)
area_bbox = bbox["width"]*bbox["height"]
openings = []
for i in range(1, n):
    x, y, ww, hh, ar = stats[i]
    if ar > 0.015*area_bbox and ww > 6 and hh > 6:
        openings.append(dict(x=int(x+bbox["x"]), y=int(y+bbox["y"]),
                             width=int(ww), height=int(hh),
                             area_pct=round(float(ar)/area_bbox, 4)))
openings.sort(key=lambda o: -o["area_pct"])

roww = mask.sum(axis=1).astype(float)
sm = np.convolve(roww, np.ones(9)/9, mode="same")
peak_thr = 0.75*sm[bbox["y"]:bbox["y"]+bbox["height"]].max()
platforms = []
for y in range(bbox["y"]+10, bbox["y"]+bbox["height"]-10):
    if sm[y] >= sm[max(0, y-8):y+8].max() and sm[y] > peak_thr:
        if platforms and y - platforms[-1]["y"] < bbox["height"]*0.04:
            continue
        platforms.append(dict(y=int(y), width=int(sm[y]),
                              rel_z=round(float(bbox["y"]+bbox["height"]-y)/bbox["height"], 3)))
        if len(platforms) >= 6:
            break

keypoints = dict(
    top=[int(cnt[:, 0].mean()), int(ys.min())],
    bottom_left=[bbox["x"], bbox["y"]+bbox["height"]],
    bottom_right=[bbox["x"]+bbox["width"], bbox["y"]+bbox["height"]],
    base_center_x=float(cxs[-1]))

out = dict(
    image=dict(width=int(w), height=int(h), source=img_path),
    object_bbox=bbox,
    aspect_wh=round(bbox["width"]/bbox["height"], 4),
    keypoints=keypoints,
    platforms=platforms,
    legs=[], arches=[],
    openings=openings[:12],
    silhouette_points=silhouette,
    center_axis=center_axis,
    zones=zones,
    top_structure=dict(status="unknown"),
    confidence=dict(overall=0.95 if has_alpha else 0.7,
                    segmentation="alpha" if has_alpha else "grabcut"),
    unknown_geometry=["rear_depth", "thickness", "hidden_elements"],
    view="single_image")
json.dump(out, open(out_json, "w"), indent=1)
print("ANALYZE_OK", out_json, "| openings:", len(openings), "| platforms:", len(platforms),
      "| conf:", out["confidence"]["segmentation"])
