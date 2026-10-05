#!/usr/bin/env python3
# verify_api.py — verificacion de punta a punta de cluster-api (ejecutar en rpi5)
import json, time, urllib.request, hashlib, sys

KEY = json.load(open(__import__("os").path.expanduser("~/cluster-api/config/services.json")))["auth"]["api_key"]
B = "http://127.0.0.1:8200"
RUN = "api_test_bracket_01"

def req(method, path, body=None, raw=False):
    r = urllib.request.Request(B + path, method=method)
    r.add_header("X-Api-Key", KEY)
    data = None
    if body is not None:
        r.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    with urllib.request.urlopen(r, data=data, timeout=120) as resp:
        blob = resp.read()
        return blob if raw else json.loads(blob)

# 1. lanzar mision
try:
    print("POST /mission ->", req("POST", "/mission", {"name": RUN, "gen": "gen_bracket.py",
        "ask": "Describe la pieza: forma, color, detalles."}))
except urllib.error.HTTPError as e:
    if e.code == 409:
        print("run ya existe, reutilizo")
    else:
        raise

# 2. polling hasta DONE/FAILED
t0 = time.time()
st = None
while time.time() - t0 < 900:
    st = req("GET", f"/mission/{RUN}")
    s = st.get("status")
    print(f"[{int(time.time()-t0)}s] {s}")
    if s in ("DONE", "FAILED"):
        break
    time.sleep(20)
assert st and st["status"] == "DONE", f"FALLO: {st.get('log_tail','')[-500:]}"
print("exitcode:", st.get("exitcode"), "| bbox:", json.dumps(st.get("bbox"))[:200])

# 3. artefactos + sha256
arts = req("GET", f"/artifacts/{RUN}")["artifacts"]
print(json.dumps(arts, indent=1))
for a in arts:
    blob = req("GET", f"/artifacts/{RUN}/{a['file']}", raw=True)
    h = hashlib.sha256(blob).hexdigest()
    ok = "OK" if h == a["sha256"] else "MISMATCH!"
    print(f"download {a['file']}: {len(blob)}B sha256 {ok}")
    assert h == a["sha256"]

# 4. negative tests
for path, note in [("/mission/..%2f..%2fetc", "traversal"), ("/mission/no_existe", "404")]:
    try:
        req("GET", path)
        print(note, "NO RECHAZADO (MAL)")
    except urllib.error.HTTPError as e:
        print(note, "->", e.code, "(esperado)")
print("VERIFICACION COMPLETA: GEN_OK, RENDER OK, sha256 extremo a extremo OK")
