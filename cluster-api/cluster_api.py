#!/usr/bin/env python3
# cluster_api.py — API minima del cluster TXURTXIL (Fase 1, 2026-10-05)
# Wrapper FINO sobre lo probado: mision_3d.sh, recon3d (z1), config unica.
# Regla de oro: el LLM propone, Blender construye, LAS METRICAS DECIDEN.
# Auth: X-Api-Key == config/services.json auth.api_key (config UNICa en z1, sync al arrancar).
import json, os, re, subprocess, time, hashlib, pathlib
from fastapi import FastAPI, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

BASE = pathlib.Path.home() / "cluster-api"
CFG_DIR = BASE / "config"
UPLOADS = BASE / "uploads"
PIPE = pathlib.Path.home() / "pipeline3d"
RUNS = PIPE / "runs"
Z1 = "z1"
ZRECON = "/home/txurtxil/recon3d"
# Regla del cluster (auditoria 1-oct): recon3d/vision -> venv-recon; bpy -> Blender interno.
ZPY = "/home/txurtxil/.venv-recon/bin/python"
CFG_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="cluster-api", version="0.1.0")


def sh(cmd, timeout=30):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)


def sync_config():
    """Config unica vive en z1:~/recon3d/config/services.json. La copiamos (scp)."""
    r = sh(f"scp -q -o BatchMode=yes {Z1}:{ZRECON}/config/services.json {CFG_DIR}/services.json", 30)
    if r.returncode != 0 and not (CFG_DIR / "services.json").exists():
        raise RuntimeError("sin config local y fallo scp desde z1: " + r.stderr[-200:])


def cfg():
    return json.load(open(CFG_DIR / "services.json"))


def require_key(x_api_key: str | None):
    want = cfg().get("auth", {}).get("api_key", "")
    if not x_api_key or x_api_key != want:
        raise HTTPException(401, "api-key invalida o ausente (header X-Api-Key)")


@app.on_event("startup")
def _boot():
    sync_config()


def run_dir(rid: str) -> pathlib.Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", rid):
        raise HTTPException(400, "run_id invalido")
    d = RUNS / rid
    if not d.is_dir():
        raise HTTPException(404, "run no existe")
    return d


def run_state(d: pathlib.Path) -> dict:
    st = {"run": d.name, "status": "RUNNING"}
    ec = d / "exitcode"
    sf = d / "state.json"
    if sf.exists():
        try:
            st.update(json.load(open(sf)))
        except Exception:
            pass
    if ec.exists():
        code = ec.read_text().strip()
        st["status"] = "DONE" if code == "0" else "FAILED"
        st["exitcode"] = code
    for extra in ("bbox.json",):
        f = d / extra
        if f.exists():
            try:
                st[extra.split(".")[0]] = json.load(open(f))
            except Exception:
                pass
    v = d / "verificacion.txt"
    if v.exists():
        st["verificacion"] = v.read_text()[:800]
    j = d / "juez.txt"
    if j.exists():
        st["juez"] = j.read_text()[-600:]
    log = d / "api.log"
    if log.exists():
        st["log_tail"] = log.read_text(errors="replace")[-1500:]
    return st


@app.get("/health")
def health(x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    # pipeline_health.py vive en z1 (auditoria 2026-10-02); lo ejecutamos ahi y retransmitimos.
    r = sh(f"ssh -o BatchMode=yes {Z1} '{ZPY} {ZRECON}/pipeline_health.py --json /tmp/ph.json > /dev/null; "
           f"cat /tmp/ph.json'", 90)
    out = {"cluster_api": "OK", "ts": time.time()}
    try:
        out["pipeline"] = json.loads(r.stdout.strip())
    except Exception:
        out["pipeline"] = {"status": "FAIL", "detail": (r.stderr or r.stdout)[-300:]}
    return out


@app.get("/missions")
def missions(x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    RUNS.mkdir(exist_ok=True)
    return sorted((p.name for p in RUNS.iterdir() if p.is_dir()), reverse=True)


@app.get("/gens")
def gens(x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    return sorted(p.name for p in PIPE.glob("gen_*.py"))


@app.post("/mission")
def mission(body: dict, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    name = str(body.get("name", "")).strip()
    gen = os.path.basename(str(body.get("gen", "")))  # nada de paths: basename solo
    ask = str(body.get("ask", "Describe la pieza renderizada: forma, color y detalles. Una frase."))
    ask = ask.replace('"', "'")[:300]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
        raise HTTPException(400, "name invalido [A-Za-z0-9_-]{1,64}")
    if not re.fullmatch(r"gen_[A-Za-z0-9_]+\.py", gen):
        raise HTTPException(400, "gen invalido (debe ser gen_*.py en ~/pipeline3d)")
    genp = PIPE / gen
    gen_code = body.get("gen_code")
    if gen_code:
        # FASE 2-C: el Coder del cluster escribe el generador; lo materializamos
        # en disco (whitelist gen_*.py ya validada) con chequeo de sintaxis previo.
        if genp.exists():
            raise HTTPException(409, f"generador ya existe en disco: {gen}")
        genp.write_text(str(gen_code)[:200000])
        chk = sh(f"python3 -m py_compile {genp}", 30)
        if chk.returncode != 0:
            genp.unlink()
            raise HTTPException(400, "gen_code no compila: " + chk.stderr[-300:])
    elif not genp.is_file():
        raise HTTPException(404, f"generador no encontrado: {gen}")
    d = RUNS / name
    if d.exists():
        raise HTTPException(409, f"run ya existe: {name}")
    d.mkdir(parents=True)
    (d / "state.json").write_text(json.dumps(
        {"run": name, "gen": gen, "ask": ask, "started": time.time(),
         "status": "RUNNING", "launcher": "mision_3d.sh"}, indent=2))
    cmd = (f"cd {PIPE} && setsid bash -c "
           f"'bash mision_3d.sh {gen} {name} \"{ask}\"; echo $? > {d}/exitcode' "
           f"> {d}/api.log 2>&1 < /dev/null &")
    sh(cmd, 10)
    return {"run_id": name, "status": "RUNNING", "gen": gen}


@app.get("/mission/{rid}")
def mission_status(rid: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    return run_state(run_dir(rid))


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@app.get("/artifacts/{rid}")
def artifacts(rid: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    d = run_dir(rid)
    out = []
    for f in sorted(d.iterdir()):
        if f.is_file():
            out.append({"file": f.name, "size": f.stat().st_size, "sha256": sha256(f)})
    return {"run": rid, "artifacts": out}


@app.get("/artifacts/{rid}/{fname}")
def artifact_file(rid: str, fname: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    d = run_dir(rid)
    f = (d / os.path.basename(fname)).resolve()
    if not str(f).startswith(str(d.resolve()) + os.sep) or not f.is_file():
        raise HTTPException(404, "artefacto no existe")
    return FileResponse(f)


@app.post("/reference")
async def reference(photo: UploadFile, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    ext = os.path.splitext(photo.filename or "ref.png")[1].lower() or ".png"
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise HTTPException(400, "formato no soportado")
    ts = time.strftime("%Y%m%d_%H%M%S")
    local = UPLOADS / f"ref_{ts}{ext}"
    local.write_bytes(await photo.read())
    # analisis en z1 (recon3d probado); REFERENCE_GEOMETRY.json vuelve a rpi5.
    zimg = f"{ZRECON}/work/{local.name}"
    zjson = zimg.rsplit(".", 1)[0] + ".REFERENCE_GEOMETRY.json"
    r = sh(f"scp -q -o BatchMode=yes {local} {Z1}:{zimg}", 60)
    if r.returncode != 0:
        raise HTTPException(502, "scp foto->z1 fallo: " + r.stderr[-200:])
    r = sh(f"ssh -o BatchMode=yes {Z1} '{ZPY} {ZRECON}/analyze_reference.py "
           f"{zimg} {zjson}'", 180)
    if r.returncode != 0:
        raise HTTPException(502, "analyze_reference fallo: " + (r.stderr or r.stdout)[-300:])
    r = sh(f"scp -q -o BatchMode=yes {Z1}:{zjson} {local}.geometry.json", 60)
    if r.returncode != 0:
        raise HTTPException(502, "scp json->rpi5 fallo: " + r.stderr[-200:])
    return {"photo": local.name, "geometry": json.load(open(str(local) + ".geometry.json")),
            "stored": [str(local), str(local) + ".geometry.json"]}


# --- VLM proxy (FASE 2): el VLM de z1 escucha en 127.0.0.1:8084 y es secuencial
# respecto a Blender (bajo demanda). El movil NO le habla directo: pasa por aqui.
VLM_URL = "http://127.0.0.1:8084"


def vlm_models():
    r = sh(f"ssh -o BatchMode=yes {Z1} 'curl -s -m6 {VLM_URL}/v1/models'", 20)
    if r.returncode != 0 or '"id"' not in r.stdout:
        return None
    try:
        return json.loads(r.stdout)["data"][0]["id"]
    except Exception:
        return None


def vlm_wake(timeout_s=240):
    if vlm_models():
        return False
    sh(f"ssh -o BatchMode=yes {Z1} 'bash ~/start_vlm_z1.sh'", 30)
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        time.sleep(5)
        if vlm_models():
            return True
    raise HTTPException(504, "VLM no arranco en %ds (start_vlm_z1.sh)" % timeout_s)


@app.get("/vlm/status")
def vlm_status(x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    m = vlm_models()
    return {"running": m is not None, "model": m,
            "expected": cfg().get("vlm", {}).get("model")}


@app.post("/vlm/ask")
def vlm_ask(body: dict, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    b64 = str(body.get("image_b64", ""))
    prompt = str(body.get("prompt", "Describe la pieza renderizada: forma, color y detalles. Una frase."))[:2000]
    if len(b64) < 100 or not b64.startswith("/9j") and "base64," not in b64[:30] and not b64[:1].isalnum():
        raise HTTPException(400, "image_b64 invalido")
    if len(b64) > 25_000_000:
        raise HTTPException(413, "imagen demasiado grande (>~18MB b64)")
    woken = vlm_wake()
    model = vlm_models()
    mime = str(body.get("mime", "image/png"))
    if "/" not in mime or len(mime) > 30:
        mime = "image/png"
    payload = {"model": model, "temperature": 0.2, "max_tokens": 300, "messages": [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}
    pf = BASE / "uploads" / ("vlm_payload_%d.json" % time.time())
    pf.write_text(json.dumps(payload))
    zf = f"/tmp/{pf.name}"
    r = sh(f"scp -q -o BatchMode=yes {pf} {Z1}:{zf} && ssh -o BatchMode=yes {Z1} "
           f"\"curl -s -m300 {VLM_URL}/v1/chat/completions -H 'Content-Type: application/json' -d @{zf}; rm -f {zf}\"", 360)
    pf.unlink(missing_ok=True)
    if r.returncode != 0 or '"choices"' not in r.stdout:
        raise HTTPException(502, "VLM no respondio: " + (r.stderr or r.stdout)[-300:])
    try:
        ans = json.loads(r.stdout)["choices"][0]["message"]["content"]
    except Exception:
        raise HTTPException(502, "respuesta VLM inparseable: " + r.stdout[-200:])
    return {"answer": ans, "model": model, "vlm_woken": woken}


@app.post("/coder/ask")
def coder_ask(body: dict, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    system = str(body.get("system", ""))[:4000]
    prompt = str(body.get("prompt", ""))[:16000]
    if not prompt:
        raise HTTPException(400, "prompt vacio")
    c = cfg().get("coder", {})
    url = f"http://{c.get('host', '192.168.10.23')}:{c.get('port', 8081)}/v1/chat/completions"
    payload = {"model": c.get("model"), "temperature": 0.2, "messages": [
        {"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    if body.get("json_mode"):
        payload["response_format"] = {"type": "json_object"}
    pf = BASE / "uploads" / ("coder_payload_%d.json" % time.time())
    pf.write_text(json.dumps(payload))
    # el llama-server del coder exige --api-key = la MISMA api-key del cluster
    ckey = cfg().get("auth", {}).get("api_key", "")
    r = sh(f"curl -s -m180 {url} -H 'Content-Type: application/json' "
           f"-H 'Authorization: Bearer {ckey}' -d @{pf}; rm -f {pf}", 200)
    if r.returncode != 0 or '"choices"' not in r.stdout:
        raise HTTPException(502, "coder no respondio: " + (r.stderr or r.stdout)[-300:])
    try:
        ans = json.loads(r.stdout)["choices"][0]["message"]["content"]
    except Exception:
        raise HTTPException(502, "respuesta coder inparseable: " + r.stdout[-200:])
    return {"answer": ans, "model": c.get("model")}
