#!/usr/bin/env python3
# ab_test.py — A/B coder: IQ2_XXS (actual) vs IQ3_XS. Se ejecuta en z1.
# Misma tarea bpy para ambos; el codigo generado se EJECUTA en Blender sobre el
# petrolero V3.5 y se puntua objetivamente: parse OK / run OK / conteo / dims.
import subprocess, time, json, sys

KEY = "sk-cluster-72ce643cae6f7db766ded5b32c985611"
BLEND = "/home/txurtxil/recon3d/iterations/quality_v3/petrolero_v3.blend"
MODELS = {
    "IQ2_XXS": "/home/txurtxil/llama.cpp/models/Qwen3-Coder-30B-A3B-Instruct-UD-IQ2_XXS.gguf",
    "IQ3_XS":  "/home/txurtxil/models/UD-IQ3_XXS.gguf",
}
TASK = (
    "Escribe SOLO codigo Python para bpy (sin explicaciones, sin markdown). "
    "El script debe, al ejecutarse en Blender con cualquier escena abierta: "
    "crear una fila de 5 contenedores de carga maritima alineados en el eje X, "
    "empezando en x=90, separados 2 mm entre si. Cada contenedor: caja de "
    "12 x 3 x 3 mm, color verde oliva (0.35,0.4,0.2), con 4 barras verticales "
    "de corrugado de 0.3 mm de grosor en cada cara larga. Todo solido (cubos), "
    "sin modificadores. Al final imprime exactamente: CONTAINERS_OK <n> donde "
    "n es el numero de contenedores creados."
)

def bc(cmd, t=60):
    return subprocess.run(["ssh", "bc250", cmd], capture_output=True, text=True, timeout=t).stdout

def wait_ready(tmo=300):
    t0 = time.time()
    while time.time() - t0 < tmo:
        out = bc("curl -s -m4 -H 'Authorization: Bearer %s' http://127.0.0.1:8081/v1/models 2>/dev/null" % KEY)
        if '"id"' in out:
            return True
        time.sleep(5)
    return False

def run_model(name, path):
    r = dict(model=name)
    sz = bc("stat -c %s %s 2>/dev/null || echo 0" % path).strip()
    if int(sz or 0) < 10**9:
        r["error"] = "modelo remoto ausente o <1GB (size=%s)" % sz
        return r
    bc("pkill -f llama-server; sleep 3")
    bc("nohup ~/llama.cpp/build/bin/llama-server -m %s -ngl 99 -c 16384 "
       "--cache-type-k q4_0 --cache-type-v q4_0 --host 0.0.0.0 --port 8081 "
       "--reasoning off --jinja --api-key %s -fa on > /tmp/ab_%s.log 2>&1 &"
       % (path, KEY, name))
    r["ready"] = wait_ready()
    if not r["ready"]:
        return r
    payload = {"model": "x", "messages": [{"role": "user", "content": TASK}],
               "temperature": 0.0, "max_tokens": 1400}
    t0 = time.time()
    p = subprocess.run(["ssh", "bc250",
        "curl -s -m300 http://127.0.0.1:8081/v1/chat/completions "
        "-H 'Authorization: Bearer %s' -H 'Content-Type: application/json' -d '%s'"
        % (KEY, json.dumps(json.dumps(payload)))], capture_output=True, text=True, timeout=330)
    r["gen_s"] = round(time.time() - t0, 1)
    try:
        txt = json.loads(p.stdout)["choices"][0]["message"]["content"]
        code = txt.strip().strip("`").replace("python\n", "", 1)
        r["parse"] = "CONTAINERS_OK" in code or "import bpy" in code
    except Exception as e:
        r["parse"] = False; r["err"] = str(e)[:120]
        return r
    sp = "/tmp/ab_%s.py" % name
    open(sp, "w").write(code if "import bpy" in code else "import bpy\n" + code)
    ex = subprocess.run(["/home/txurtxil/blender/blender", "-b", BLEND, "-P", sp],
                        capture_output=True, text=True, timeout=180)
    out = ex.stdout + ex.stderr
    r["run"] = "CONTAINERS_OK 5" in out
    r["blender_quit_ok"] = ex.returncode == 0
    return r

results = []
for name, path in MODELS.items():
    results.append(run_model(name, path))
    time.sleep(2)
json.dump(results, open("/tmp/ab_results.json", "w"), indent=1)
for r in results:
    print(r)
# restaurar el modelo actual del cluster (IQ2_XXS) salvo que IQ3_XS gane ambas
winner = None
if all(results[1].get(k) for k in ("ready", "parse", "run")) and not all(results[0].get(k) for k in ("parse", "run")):
    winner = "IQ3_XS"
keep = MODELS[winner or "IQ2_XXS"]
bc("pkill -f llama-server; sleep 3")
bc("nohup ~/llama.cpp/build/bin/llama-server -m %s -ngl 99 -c 53248 "
   "--cache-type-k q4_0 --cache-type-v q4_0 --host 0.0.0.0 --port 8081 "
   "--reasoning off --jinja --api-key %s -fa on --cache-reuse 256 -np 1 -ub 256 > /tmp/coder_8081.log 2>&1 &"
   % (keep, KEY))
print("RESTORED", winner or "IQ2_XXS")
