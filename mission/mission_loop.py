#!/usr/bin/env python3
"""mission_loop.py — Mission Manager v0.1 (spec §17/§19/§20/§32/§34).
Ejecuta en z1. El LLM (node2 :8082) PROPONE parametros y DIAGNOSTICA;
las herramientas fijas EJECUTAN y MIDEN. El loop decide ACCEPT/ROLLBACK.

Uso: python3 mission_loop.py <mission.json>
Solo stdlib. Nada se inventa: cada metrica sale de MEASURE_JSON real.
"""
import json, hashlib, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path.home() / "cluster-3d-pipeline" / "mission"
BLENDER = str(Path.home() / "blender" / "blender")
KEY = (ROOT / ".apikey").read_text().strip()
API = "http://127.0.0.1:8081/v1/chat/completions"

cfg = json.load(open(sys.argv[1]))
GEN = ROOT / cfg.get("generator", "gen_box.py")
MEASURE = ROOT / cfg.get("measurer", "measure_box.py")
MID = cfg["mission_id"]
MBRIEF = cfg["brief"]
HARD = cfg["hard"]              # {"L": {"value":100.0,"tol":0.2}, ...}
MAX_ITERS = cfg.get("max_iters", 8)
INJECTED = cfg.get("injected_initial")  # test: semilla con fallo deliberado
TAG = cfg.get("tag", "")

base = ROOT / "runs" / MID
base.mkdir(parents=True, exist_ok=True)


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(base / "mission.log", "a") as f:
        f.write(line + "\n")


def llm(system, user, n_predict=1600):
    # OJO (leccion 9-oct): Qwen3 es modelo de razonamiento; los tokens de
    # thinking consumen n_predict. Con 500 -> finish=length, content vacio.
    req = urllib.request.Request(API, data=json.dumps({
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.0, "n_predict": n_predict,
        # PLAN/DIAGNOSE = JSON determinista: sin thinking. Leccion 9-oct:
        # con thinking activo, en carga compartida de GPU el modelo quemaba
        # TODO el presupuesto en razonamiento y devolvia content VACIO.
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode(), headers={"Content-Type": "application/json",
                          "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def extract_json(txt):
    # 1) bloque ```json ...``` (el modelo de razonamiento suele anidar llaves
    #    sueltas en el thinking; el fence es la senal mas fiable)
    import re
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 2) fallback: primera '{' a ultima '}'
    i, j = txt.rfind("}"), txt.find("{")
    if 0 <= j < i:
        try:
            return json.loads(txt[j:i + 1])
        except Exception:
            return None
    return None


def sha256(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def run_tool(args, grep_prefix):
    r = subprocess.run(args, capture_output=True, text=True, timeout=600)
    for line in (r.stdout + "\n" + r.stderr).splitlines():
        if line.startswith(grep_prefix):
            return json.loads(line[len(grep_prefix):].strip())
    raise RuntimeError(f"TOOL_FAIL {args[0]}: sin {grep_prefix}")


def build(params, vdir):
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "parameters.json").write_text(json.dumps(params, indent=2))
    blend, stl = vdir / "model.blend", vdir / "model.stl"
    run_tool([BLENDER, "-b", "--factory-startup", "-P", str(GEN), "--",
              str(vdir / "parameters.json"), str(blend), str(stl)], "GEN_OK")
    m = run_tool([BLENDER, "-b", str(blend), "-P", str(MEASURE)], "MEASURE_JSON")
    (vdir / "metrics.json").write_text(json.dumps(m, indent=2))
    (vdir / "generation.py").write_text(GEN.read_text())
    sums = {p: sha256(vdir / p) for p in ["parameters.json", "metrics.json",
                                          "model.blend", "model.stl"]}
    (vdir / "SHA256SUMS").write_text(
        "\n".join(f"{v}  {n}" for n, v in sums.items()) + "\n")
    return m


def evaluate(m):
    fails = {}
    d = m["dims"]
    counts = m.get("counts", {})
    for name, spec in HARD.items():
        got = d.get(name)
        if got is None:
            got = m.get("wall_min")
        if got is None:
            got = counts.get(name)
        if got is None:
            fails[name] = "UNKNOWN"
        elif abs(got - spec["value"]) > spec["tol"]:
            fails[name] = {"got": got, "want": spec["value"], "tol": spec["tol"]}
    # manifold solo es HARD si la mision lo pide: las celosias/arcos abiertos
    # de una torre tienen aristas frontera legitimas (leccion tower v2:
    # 80 bad_edges = 4 arcos x 2 extremos x 10 lados, INTENCIONADO)
    if cfg.get("require_manifold") and not m["manifold"]["ok"]:
        fails["manifold"] = m["manifold"]
    return fails


# ---------- 1. PLAN ----------
if INJECTED:
    params = dict(INJECTED)
    log(f"PLAN: parametros inyectados (test) {params}")
else:
    sys_p = ("Eres el planificador de un agente 3D. Respondes SOLO con un JSON "
             "con los parametros iniciales. Sin texto fuera del JSON.")
    usr_p = (f"Mision: {MBRIEF}\nRestricciones duras: "
             + json.dumps(HARD)
             + f"\nParametros posibles del generador: {cfg.get('params_hint', 'L,W,H,WALL,RIM_R,HOLE_D,HOLE_MARGIN,USBC_W,USBC_H,USBC_Z')}\n"
               'Devuelve SOLO un bloque ```json con {"params": {...}} '
               "y nada fuera de el.")
    pj = None
    for attempt in range(4):
        raw = llm(sys_p, usr_p)
        pj = extract_json(raw)
        if pj and "params" in pj:
            break
        log(f"PLAN intento {attempt + 1}: parse fallido, raw[:300]={raw[:300]!r}")
        pj = None
    if not pj:
        log("VERDICT=NEEDS_HUMAN_REVIEW razon=PLAN_NO_PARSE")
        sys.exit(2)
    params = pj["params"]
    log(f"PLAN: {params}")

history, converged = [], False
verdict, reason = "FAIL", ""
for it in range(1, MAX_ITERS + 1):
    vdir = base / f"V{it:03d}"
    tag = " [INYECCION TEST]" if (it == 1 and INJECTED) else ""
    log(f"ITER {it}{tag}: construyendo y midiendo...")
    m = build(params, vdir)
    log(f"ITER {it} medidas: dims={m['dims']} "
        f"wall_min={m.get('wall_min', 'N/A')} manifold={m['manifold']['ok']}")
    fails = evaluate(m)
    if not fails:
        converged = True
        verdict = "PASS"
        log(f"ITER {it}: todas las HARD constraints pasan")
        break
    log(f"ITER {it} FALLOS: {json.dumps(fails)}")
    ph = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
    if ph in history:
        verdict, reason = "FAIL", f"PLATEAU parametro-repetido iter {it}"
        log(reason)
        break
    history.append(ph)
    # ---------- 2. DIAGNOSE ----------
    sys_d = ("Eres el optimizador de un agente 3D. Dado el fallo, decides UN "
             "cambio de parametro. Respondes SOLO JSON: "
             "{\"changes\": {...}, \"reason\": \"...\"}. Sin texto fuera.")
    usr_d = (f"Mision: {MBRIEF}\nHard constraints: {json.dumps(HARD)}\n"
             f"Parametros actuales: {json.dumps(params)}\n"
             f"Metricas medidas: {json.dumps(m)}\nFallas: {json.dumps(fails)}\n"
             "Cambia SOLO los parametros necesarios para cumplir las "
             "restricciones. RIM_R < WALL siempre.")
    dj = None
    for _ in range(3):
        dj = extract_json(llm(sys_d, usr_d))
        if dj and "changes" in dj:
            break
    if not dj:
        verdict, reason = "NEEDS_HUMAN_REVIEW", f"DIAGNOSE_NO_PARSE iter {it}"
        log(reason)
        break
    newp = dict(params)
    newp.update(dj["changes"])
    log(f"ITER {it} cambios: {json.dumps(dj['changes'])} razon: {dj.get('reason','')}")
    params = newp

# ---------- REPORT ----------
if not reason:
    reason = "convergencia" if converged else f"max_iter {MAX_ITERS}"
rep = ["# REPORT", "", f"MISSION: {MID} {TAG}".rstrip(),
       f"INPUT: {MBRIEF}", "",
       "## HARD CONSTRAINTS", json.dumps(HARD, indent=1), "",
       "## FINAL PARAMETERS", json.dumps(params, indent=1), "",
       "## METRICS (ultima version medida)",
       json.dumps(m if 'm' in dir() else {}, indent=1), "",
       "## ITERATIONS", f"total: {it}", "## ROLLBACKS",
       "v0.1: sin rollback multi-version (una version por iteracion, nunca "
       "se sobrescribe)", "",
       "## UNKNOWN / NOT_MEASURED",
       json.dumps(m.get("NOT_MEASURED", []) if 'm' in dir() else []), "",
       "## WARNINGS",
       "Inyeccion inicial de fallo (test del loop)" if INJECTED else "ninguna", "",
       "## PRINTABILITY",
       f"manifold: {m['manifold'] if 'm' in dir() else 'UNKNOWN'}",
       "STL exportado y hash SHA256 registrado por version", "",
       f"VERDICT: {verdict}",
       f"REASON: {reason}", ""]
(base / "REPORT.md").write_text("\n".join(rep))
log(f"VERDICT={verdict} razon={reason} -> {base/'REPORT.md'}")
sys.exit(0 if verdict == "PASS" else 1)
