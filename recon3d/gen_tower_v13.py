#!/usr/bin/env python3
# gen_tower_v13.py -- <salida.blend> [--params parameters.json]
# Generador PARAMETRICO del pipeline recon3d: reutiliza la arquitectura geométrica
# validada de gen_tower_v12 inyectando un bloque de parámetros cargado desde
# parameters.json. El optimizador (optimize_parameters.py) modifica ese JSON;
# NUNCA se reescribe el generador por iteración.
# Semántica de parámetros (todos opcionales, por defecto = v12):
#   W_SCALE                factor global de anchura
#   BASE_WIDTH, P2_WIDTH, MID_WIDTH, UPPER_SHAFT_WIDTH, TOP_WIDTH
#                          factor por zona (anclado en z=0, Z1, media, Z2, Z3)
#   Z1, Z2, Z3             alturas de plataformas (o PLATFORM_1_Z/2_Z/3_Z)
#   ARCH_WIDTH, ARCH_HEIGHT  factores del arco principal (ancho, alto del hueco)
#   LATTICE_DENSITY        1.0=defecto; <1 menos celosía (VOXEL mayor); >1 más
#   DECKS_OVERRIDE         {"z": ancho} anchos de plataforma concretos
# MUY IMPORTANTE (restricción de dominio, sección 19 del refactor):
#   las 4 patas y los huecos principales NO se rellenan: la arquitectura de v12
#   ya los mantiene abiertos; este generador solo ESCALA parámetros, nunca
#   cierra huecos.
import sys, os

argv = sys.argv
out = argv[argv.index("--")+1] if "--" in argv else "/tmp/pieza_v13.blend"
params_path = argv[argv.index("--params")+1] if "--params" in argv else os.environ.get("TOWER_PARAMS", "")
os.environ["TOWER_PARAMS"] = params_path

SRC = os.path.expanduser("~/pipeline3d/runs/tower_v12/gen_tower_v12.py")
src = open(SRC).read()
TOP = "# ---------------- PARAMETROS ----------------"
BOT = "def wprof"
head = src[:src.index(TOP)] + TOP + "\n"
body = src[src.index(BOT):]

BLOCK = '''
# ===== BLOQUE PARAMETRICO v13 (reemplaza al bloque fijo de v12) =====
import json as _json
_pj = __import__("os").environ.get("TOWER_PARAMS", "")
PARAMS = _json.load(open(_pj)) if _pj and __import__("os").path.exists(_pj) else {}
def _p(k, d): return PARAMS.get(k, d)

H         = _p("H", 170.0)
VOXEL     = _p("VOXEL", 0.35)
STEP      = _p("STEP", 3.0)
BAR       = _p("BAR", 0.6)
LEG_BAR   = _p("LEG_BAR", 0.6)
LEG_BAY   = _p("LEG_BAY", 10.0)
POST0, POST1 = _p("POST0", 1.5), _p("POST1", 0.6)
W_KEYS    = np.array(_p("W_KEYS", [(0,32.0),(8,31.8),(20,31.4),(35,30.2),(51,24.4),(65,18.5),
                      (78,12.7),(95,11.0),(112,9.6),(130,7.6),(142,6.3),(155,4.9),
                      (163,3.2),(167,1.6),(170,0.3)]), float)
S_KEYS    = np.array(_p("S_KEYS", [(0,3.6),(51,2.6),(78,2.0),(155,0.9),(170,0.45)]), float)
Z1 = _p("PLATFORM_1_Z", _p("Z1", 51.0))
Z2 = _p("PLATFORM_2_Z", _p("Z2", 78.0))
Z3 = _p("PLATFORM_3_Z", _p("Z3", 155.0))
DECKS = {float(k): v for k, v in _p("DECKS", {str(Z1): 27.5, str(Z2): 15.0, str(Z3): 6.8}).items()}
RAIL  = {float(k): v for k, v in _p("RAIL", {str(Z1): 3.2, str(Z2): 3.0}).items()}
ARCH1 = tuple(_p("ARCH1", [20.0, Z1]))
ARCH2 = tuple(_p("ARCH2", [80.0, 90.0]))
PLINTH = [tuple(x) for x in _p("PLINTH", [[6.5,1.6],[5.2,1.6]])]
SEC_ARCH1, SEC_ARCH2 = _p("SEC_ARCH1", 2.0), _p("SEC_ARCH2", 1.1)
LANTERN_R = _p("LANTERN_R", 1.8)

# ---- semantica del optimizador (factores, no valores absolutos) ----
_ws = _p("W_SCALE", 1.0)
if _ws != 1.0:
    W_KEYS[:,1] *= _ws
    DECKS = {k: v*_ws for k, v in DECKS.items()}
_zone_anchor = dict(BASE_WIDTH=0.0, P2_WIDTH=Z1, MID_WIDTH=(Z1+Z2)/2,
                    UPPER_SHAFT_WIDTH=Z2, TOP_WIDTH=Z3)
for _k, _z in _zone_anchor.items():
    if _k in PARAMS:
        _i = int(np.argmin(abs(W_KEYS[:,0]-_z)))
        W_KEYS[_i,1] *= PARAMS[_k]
if "ARCH_WIDTH" in PARAMS or "ARCH_HEIGHT" in PARAMS:
    ARCH1 = (ARCH1[0]*_p("ARCH_WIDTH",1.0), ARCH1[1]*_p("ARCH_HEIGHT",1.0))
if "LATTICE_DENSITY" in PARAMS:
    _d = min(max(PARAMS["LATTICE_DENSITY"], 0.3), 2.5)
    VOXEL = 0.35/_d
    BAR = min(max(0.6*(1.0/_d)**0.5, 0.4), 1.0)
if "DECKS_OVERRIDE" in PARAMS:
    for _k, _v in PARAMS["DECKS_OVERRIDE"].items():
        DECKS[float(_k)] = _v
print("V13_PARAMS applied:", {k: PARAMS[k] for k in PARAMS})
'''

program = head + BLOCK + "\n" + body
os.makedirs(os.path.dirname(out), exist_ok=True)
g = {"__name__": "__main__", "__file__": SRC}
exec(compile(program, SRC + ":v13", "exec"), g)
