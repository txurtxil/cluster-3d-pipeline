#!/usr/bin/env python3
# mission3d_api.py — API v0.1 del Mission Manager autonomo (RECON3D).
# Servicio NUEVO en puerto 8201. NO toca cluster_api.py (:8200, pipeline viejo).
# Reglas: el brief se parsea con regex determinista (nada de LLM en la API);
# los parametros viajan en JSON por scp (nada de interpolacion shell);
# mission_id con whitelist estricta; hard constraints con whitelist de claves.
import json, pathlib, re, subprocess, time
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

BASE = pathlib.Path.home() / "cluster-api"          # misma convencion que cluster_api
CFG = BASE / "config" / "services.json"
TMP = BASE / "tmp_mission3d"; TMP.mkdir(exist_ok=True)
Z1 = "bc250"
ZMISSION = "/home/txurtxil/cluster-3d-pipeline/mission"

app = FastAPI(title="mission3d-api", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"], allow_credentials=False)

HARD_KEYS = ("L", "W", "H", "WALL", "D_body", "teeth", "helix_angle", "bore_d",
             "D", "blades", "pitch_ratio", "rake", "skew", "shaft_d")

# Rutas por tipo de pieza (leccion 12-oct: la API siempre mandaba gen_box;
# un brief de taza explotaba por WALL ausente y no dejaba STL).
PIECES = (
    (r"taza|mug", {
        "generator": "gen_taza.py",
        "measurer": "measure_taza.py",
        "params_hint": "H,D_OUT,WALL,BOTTOM,RIM_R,HANDLE,HANDLE_D,"
                       "HANDLE_Z_LOW,HANDLE_Z_HIGH,HANDLE_REACH",
        "gen_params": ("H", "D_OUT", "WALL", "BOTTOM", "RIM_R", "HANDLE_D",
                       "HANDLE_Z_LOW", "HANDLE_Z_HIGH", "HANDLE_REACH"),
        "hard_map": {"H": "H", "D_OUT": "D_body", "WALL": "WALL"},
    }),
    (r"helice|hélice|propeller|propulsor", {
        "generator": "gen_helice.py",
        "measurer": "measure_helice.py",
        "params_hint": "DIAM,BLADES,PITCH_RATIO,BAR,HUB_D,HUB_LEN,RAKE,SKEW,SHAFT_D",
        "gen_params": ("DIAM", "BLADES", "PITCH_RATIO", "BAR", "HUB_D",
                       "HUB_LEN", "RAKE", "SKEW", "SHAFT_D"),
        "hard_map": {"DIAM": "D", "BLADES": "blades", "PITCH_RATIO": "pitch_ratio",
                     "RAKE": "rake", "SKEW": "skew", "SHAFT_D": "shaft_d"},
    }),
    (r"engranaje|gear", {
        "generator": "gen_gear_helical.py",
        "measurer": "measure_gear.py",
        "params_hint": "MODULE,TEETH,HELIX_ANGLE,FACE_WIDTH,BORE_D,HUB_D,"
                       "HUB_LEN,KEYWAY,CHAMFER",
        "gen_params": ("MODULE", "TEETH", "HELIX_ANGLE", "FACE_WIDTH",
                       "BORE_D", "HUB_D", "HUB_LEN", "KEYWAY", "CHAMFER"),
        "hard_map": {"TEETH": "teeth", "HELIX_ANGLE": "helix_angle",
                     "BORE_D": "bore_d"},
    }),
)


def piece_route(brief):
    b = brief.lower()
    for pat, route in PIECES:
        if re.search(pat, b):
            return route
    return None


def sh(cmd, timeout=30):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        class R:
            returncode, stdout, stderr = 124, e.stdout or "", f"TIMEOUT {timeout}s"
        return R()


def require_key(x):
    auth = json.load(open(CFG)).get("auth", {}) if CFG.exists() else {}
    if auth.get("lan_trust"):
        return
    if not x or x != auth.get("api_key", ""):
        raise HTTPException(401, "api-key invalida (X-Api-Key)")


def sync_cfg():
    r = sh(f"scp -q -o BatchMode=yes {Z1}:/home/txurtxil/recon3d/config/services.json {CFG}", 30)
    if r.returncode != 0 and not CFG.exists():
        raise RuntimeError("sin config: " + r.stderr[-200:])


@app.on_event("startup")
def _boot():
    sync_cfg()


def parse_brief(brief):
    """Parser determinista: piezas enrutadas por KEY=NUM; caja LxWxH + pared.
    Devuelve (hard, params|None). Sin LLM aqui."""
    route = piece_route(brief)
    if route:
        params, hard = {}, {}
        for k in route["gen_params"]:
            m = re.search(r"\b" + k + r"\s*=\s*(\d+(?:\.\d+)?)", brief, re.I)
            if m:
                params[k] = float(m.group(1))
        for pk, hk in route["hard_map"].items():
            if pk in params:
                # leccion 13-oct: la pendiente de fase mide 20.0 cuando el
                # angulo real es 19 en ruedas de muchos dientes (sesgo
                # sistematico documentado en not_measured del measurer)
                tol = 0.15 if hk == "WALL" else (1.5 if hk == "helix_angle" else 0.5)
                hard[hk] = {"value": params[pk], "tol": tol}
        return hard, params
    hard = {}
    m = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)", brief)
    if m:
        hard["L"] = {"value": float(m.group(1)), "tol": 0.2}
        hard["W"] = {"value": float(m.group(2)), "tol": 0.2}
        hard["H"] = {"value": float(m.group(3)), "tol": 0.2}
    p = re.search(r"pared\s+(\d+(?:\.\d+)?)", brief, re.I)
    if p:
        hard["WALL"] = {"value": float(p.group(1)), "tol": 0.15}
    return hard, None


def mid_from_brief(brief):
    words = re.findall(r"[a-z0-9]+", brief.lower())[:3]
    slug = "_".join(words) or "pieza"
    return f"{slug}_{time.strftime('%H%M%S')}"


@app.get("/health")
def health(x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    r = sh(f"ssh -o BatchMode=yes {Z1} 'pgrep -f mission_loop.py >/dev/null && echo UP || echo IDLE; "
           f"ls ~/cluster-3d-pipeline/mission/mission_loop.py >/dev/null && echo LOOP_OK'", 15)
    return {"mission3d_api": "OK", "bc250-1": r.stdout.split()}


@app.post("/mission3d")
def create(body: dict, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    brief = str(body.get("brief", "")).strip()[:500]
    if len(brief) < 8:
        raise HTTPException(400, "brief demasiado corto")
    mid = str(body.get("mission_id") or mid_from_brief(brief))
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", mid):
        raise HTTPException(400, "mission_id invalido")
    route = piece_route(brief)
    parsed = None if body.get("hard") else parse_brief(brief)
    hard = body.get("hard") or (parsed[0] if parsed else {})
    if not hard:
        return JSONResponse({"mission_id": mid, "status": "NEEDS_HUMAN_REVIEW",
                             "reason": "sin dimensiones LxWxH en el brief; "
                                       "pasa hard explicito o dimelo en mm"})
    for k, v in hard.items():
        if k not in HARD_KEYS or not isinstance(v, dict) \
           or not isinstance(v.get("value"), (int, float)):
            raise HTTPException(400, f"hard invalido: {k}")
    mission = {"mission_id": mid, "brief": brief, "hard": hard,
               "max_iters": int(body.get("max_iters", 6)),
               "tag": "api-8201"}
    if route:
        mission["generator"] = route["generator"]
        mission["measurer"] = route["measurer"]
        mission["params_hint"] = route["params_hint"]
    # Medidas completas en el brief -> saltar el PLAN del LLM (ahorra 2-3 min)
    ini = {k: hard[k]["value"] for k in ("L", "W", "H", "WALL") if k in hard}
    if all(k in ini for k in ("L", "W", "H")):
        mission["injected_initial"] = ini
    elif route and parsed and parsed[1]:
        mission["injected_initial"] = parsed[1]
    local = TMP / f"{mid}.json"
    local.write_text(json.dumps(mission, ensure_ascii=False))
    r = sh(f"scp -q -o BatchMode=yes {local} {Z1}:{ZMISSION}/{mid}.json", 30)
    if r.returncode != 0:
        raise HTTPException(502, "scp a z1 fallo: " + r.stderr[-200:])
    r = sh(f"ssh -o BatchMode=yes {Z1} 'test -d {ZMISSION}/runs/{mid} && echo SI || echo NO'", 15)
    if "SI" in r.stdout:
        raise HTTPException(409, f"mision ya existe en z1: {mid}")
    # Lanzamiento NO bloqueante: el ssh corre en primer plano remoto (es la
    # mision entera) pero el cliente ssh se backgrounda en rpi5 con nohup.
    # Leccion 9-oct: 'ssh host \"cmd &\"' cuelga el canal pese a setsid+nohup.
    launcher = (f"nohup ssh -o BatchMode=yes {Z1} "
                f"'cd {ZMISSION} && python3 mission_loop.py {mid}.json "
                f"> runs/{mid}.out 2>&1' >/dev/null 2>&1 &")
    subprocess.Popen(launcher, shell=True, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    return {"mission_id": mid, "status": "RUNNING", "hard": hard,
            "nota": "estado real en GET /mission3d/{id}"}


@app.get("/mission3d/{mid}")
def status(mid: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", mid):
        raise HTTPException(400, "mission_id invalido")
    r = sh(f"ssh -o BatchMode=yes {Z1} 'D={ZMISSION}/runs/{mid}; "
           f"test -d $D || echo NOEXISTE; "
           f"tail -8 $D/mission.log 2>/dev/null; "
           f"grep -h \"VERDICT\" $D/REPORT.md 2>/dev/null'", 20)
    if "NOEXISTE" in r.stdout:
        raise HTTPException(404, "mision no existe")
    return {"mission_id": mid, "raw": r.stdout}


@app.get("/mission3d/{mid}/report")
def report(mid: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", mid):
        raise HTTPException(400, "mission_id invalido")
    dst = TMP / f"{mid}_REPORT.md"
    r = sh(f"scp -q -o BatchMode=yes {Z1}:{ZMISSION}/runs/{mid}/REPORT.md {dst}", 30)
    if r.returncode != 0:
        raise HTTPException(404, "REPORT.md aun no existe (mision en curso?)")
    return FileResponse(dst, media_type="text/markdown", filename=f"{mid}_REPORT.md")


@app.get("/mission3d/{mid}/file/{fname}")
def file(mid: str, fname: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", mid) \
       or not re.fullmatch(r"[A-Za-z0-9_.]{1,40}", fname):
        raise HTTPException(400, "nombre invalido")
    for cand in (f"V001/{fname}", fname):
        dst = TMP / f"{mid}_{fname}"
        r = sh(f"scp -q -o BatchMode=yes {Z1}:{ZMISSION}/runs/{mid}/{cand} {dst}", 30)
        if r.returncode == 0:
            return FileResponse(dst, filename=f"{mid}_{fname}")
    raise HTTPException(404, f"fichero no encontrado: {fname}")
