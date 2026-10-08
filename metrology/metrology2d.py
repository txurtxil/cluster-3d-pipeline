"""metrology2d.py — Metrologia 2D del pipeline RECON3D.
Todas las metricas operan sobre mascaras binarias (numpy bool).
Regla del proyecto: metric(INPUT) == GROUND_TRUTH en tests sinteticos
o METROLOGY_INVALID. Nunca optimizar con una metrica no validada.
"""
import numpy as np
import cv2
from scipy import ndimage

# Zonas de altura segun spec §15
ZONES = [(0.0, 0.15), (0.15, 0.35), (0.35, 0.50),
         (0.50, 0.70), (0.70, 0.90), (0.90, 1.0)]


def binarize(img):
    """BGR/gray -> mascara bool. Umbral fijo 127 (sintetico: sin ruido)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    _, m = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return m > 0


def bbox(mask):
    """Bounding box (x, y, w, h) en px. None si vacia."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def silhouette_iou(a, b):
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / union) if union else 1.0


def mask_to_contour(m):
    """Contorno = mascara menos erosion."""
    er = ndimage.binary_erosion(m)
    return m & ~er


def contour_error(a, b):
    """Error de contorno: distancia simetrica media entre contornos (px).
    NaN si alguna mascara esta vacia."""
    ca, cb = mask_to_contour(a), mask_to_contour(b)
    if ca.sum() == 0 or cb.sum() == 0:
        return float('nan')
    dtb = ndimage.distance_transform_edt(~cb)
    dta = ndimage.distance_transform_edt(~ca)
    return float(0.5 * (dtb[ca].mean() + dta[cb].mean()))


def zone_slice(mask, z0, z1):
    h = mask.shape[0]
    return mask[int(h * z0):int(h * z1), :]


def zone_metrics(ref, mod, zones=ZONES):
    """Comparacion por zonas -> dict ZONE_METRICS (spec §15)."""
    out = {}
    for i, (z0, z1) in enumerate(zones):
        r = zone_slice(ref, z0, z1)
        m = zone_slice(mod, z0, z1)
        out[f"Z{i}"] = {
            "range": [z0, z1],
            "iou": silhouette_iou(r, m),
            "ref_area": int(r.sum()),
            "mod_area": int(m.sum()),
            "ref_density": float(r.mean()),
            "mod_density": float(m.mean()),
        }
    return out


def density(mask):
    """Fraccion de area ocupada (spec §16: REFERENCE_DENSITY vs MODEL_DENSITY)."""
    return float(mask.mean())


def openings_count(mask):
    """Componentes conexas de fondo interiores (agujeros)."""
    inv = ~mask
    lab, n = ndimage.label(inv)
    border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    return sum(1 for i in range(1, n + 1) if i not in border)
