"""test_metrology.py — Tests del metrologo con ground truth sintetico (spec §36).
Si cualquier metrica falla: METROLOGY_INVALID y esa metrica queda PROHIBIDA
para optimizar hasta repararla.
"""
import numpy as np
import cv2
import sys
sys.path.insert(0, '.')
from metrology2d import (bbox, silhouette_iou, contour_error,
                         zone_metrics, density, openings_count, ZONES)

fails = []


def reference_contour_error(a, b):
    """Implementacion de referencia INDEPENDIENTE: cv2.findContours +
    distancia euclidea punto a punto. Si ambas coinciden, la metrica es valida."""
    def pts(m):
        cs, _ = cv2.findContours((m * 255).astype(np.uint8),
                                 cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return cs[0].reshape(-1, 2).astype(float) if cs else np.zeros((0, 2))
    pa, pb = pts(a), pts(b)
    if len(pa) == 0 or len(pb) == 0:
        return float('nan')
    da = np.sqrt(((pa[:, None, :] - pb[None, :, :]) ** 2).sum(-1)).min(1).mean()
    db = np.sqrt(((pb[:, None, :] - pa[None, :, :]) ** 2).sum(-1)).min(1).mean()
    return float(0.5 * (da + db))


def check(name, got, want, tol):
    ok = abs(got - want) <= tol
    print(f"{'OK ' if ok else 'FAIL'} {name}: got={got} want={want} tol={tol}")
    if not ok:
        fails.append(name)


# --- Ground truth 1: rectangulo conocido 100x200 en (100,50) sobre 400x400
A = np.zeros((400, 400), bool)
A[50:250, 100:200] = True                      # 100 ancho x 200 alto, area 20000
check("bbox.A", 0, 0, 0) if False else None
x, y, w, h = bbox(A)
print(f"OK  bbox.A = {(x,y,w,h)}")
assert (x, y, w, h) == (100, 50, 100, 200), "bbox.A FUERA DE SPEC"
check("area.A", A.sum(), 20000, 0)

# --- Identico -> IoU 1.0, contour error 0
check("iou.identico", silhouette_iou(A, A), 1.0, 1e-9)
check("contour.identico", contour_error(A, A), 0.0, 1e-9)

# --- Rectangulo desplazado +10 en x: IoU analitico 18000/22000
B = np.zeros((400, 400), bool)
B[50:250, 110:210] = True
check("iou.desplazado", silhouette_iou(A, B), 18000 / 22000, 1e-9)
# Validacion cruzada contra implementacion de referencia (cv2):
# mi expectativa fija de 10.0 era analiticamente incorrecta (6.68 es lo correcto)
ref = reference_contour_error(A, B)
got = contour_error(A, B)
ok = abs(got - ref) <= 0.5
print(f"{'OK ' if ok else 'FAIL'} contour.desplazado: metrica={got:.3f} referencia={ref:.3f}")
if not ok:
    fails.append("contour.desplazado")
# Caso adicional: desplazamiento diagonal +5,+8
B2 = np.zeros((400, 400), bool)
B2[58:258, 105:205] = True
ref2 = reference_contour_error(A, B2)
got2 = contour_error(A, B2)
ok2 = abs(got2 - ref2) <= 0.5
print(f"{'OK ' if ok2 else 'FAIL'} contour.diagonal: metrica={got2:.3f} referencia={ref2:.3f}")
if not ok2:
    fails.append("contour.diagonal")

# --- Densidad por zonas: mitad inferior llena
C = np.zeros((400, 400), bool)
C[200:, :] = True
zm = zone_metrics(C, C)
dens_gt = {0: 0.0, 1: 0.0, 2: 0.0, 3: 1.0, 4: 1.0, 5: 1.0}
for z, d in dens_gt.items():
    check(f"zona.Z{z}.densidad", zm[f"Z{z}"]["mod_density"], d, 1e-9)
    check(f"zona.Z{z}.iou", zm[f"Z{z}"]["iou"], 1.0, 1e-9)

# --- Zona parcialmente ocupada: objeto solo en 35-50% de altura
D = np.zeros((400, 400), bool)
D[int(400*0.35):int(400*0.50), :] = True
zm2 = zone_metrics(D, D)
check("zona.Z2.ocupada", zm2["Z2"]["mod_density"], 1.0, 1e-9)
check("zona.Z3.vacia", zm2["Z3"]["mod_density"], 0.0, 1e-9)

# --- Openings: un agujero interior conocido
E = np.ones((200, 200), bool)
E[80:120, 80:120] = False                       # hueco 40x40 interior
check("openings.1", openings_count(E), 1, 0)
E[140:160, 30:50] = False                       # segundo hueco
check("openings.2", openings_count(E), 2, 0)

# --- Zonas segun spec §15: 6 zonas exactas
assert len(ZONES) == 6 and ZONES[0] == (0.0, 0.15) and ZONES[5] == (0.90, 1.0)
print("OK  zonas.6 = spec §15")

print("=" * 50)
if fails:
    print("METROLOGY_INVALID ->", fails)
    sys.exit(1)
print("METROLOGY_PASS: bbox, IoU, contour, zonas, densidad, openings validadas")
