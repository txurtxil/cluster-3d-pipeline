#!/usr/bin/env python3
# seg.py — segmentacion UNICA del pipeline (regla del refactor: una sola verdad).
# - alpha solo si el fondo es transparente de verdad (recortes)
# - si no: Otsu sobre gris (renders: fondo ~64/255; fotos con contraste)
# Usada por compare_images.py y camera_calibration.py para que el score de
# calibracion y el de comparacion midan EXACTAMENTE lo mismo.
import sys, os, cv2, numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def mask_of(p):
    img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if img is None:
        sys.exit("no image: " + p)
    if img.shape[-1] == 4 and img[:, :, 3].min() < 10:
        return (img[:, :, 3] > 10).astype(np.uint8)
    g = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(g, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8))
    return m

def normalize(m, H=512):
    ys, xs = np.where(m > 0)
    if len(xs) < 50:
        sys.exit("empty mask after segmentation")
    c = m[ys.min():ys.max()+1, xs.min():xs.max()+1]*255
    s = H/c.shape[0]
    return (cv2.resize(c, (max(1, int(round(c.shape[1]*s))), H),
                       interpolation=cv2.INTER_NEAREST) > 127).astype(np.uint8)
