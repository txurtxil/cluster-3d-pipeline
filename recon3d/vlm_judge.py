#!/usr/bin/env python3
# vlm_judge.py — Juez visual del pipeline de piezas (capa VLM intercambiable).
# Uso: vlm_judge.py <imagen.png> "pregunta"
# Endpoint: VLM_URL si existe; si no, intenta el VLM del cluster en bc250
# (192.168.10.23:8084, requiere modo vlm activo) y hace fallback al VLM local
# de z1 (:8084, Qwen2.5-VL-7B legacy). Modelo descubierto via /v1/models.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.expanduser("~/recon3d"))
from vlm_client import ask, BASE as _B

img_path, question = sys.argv[1], sys.argv[2]

if os.environ.get("VLM_URL"):  # vacio -> auto-deteccion, no usar valor vacio
    print(ask(question, [img_path], max_tokens=200, temperature=0.1))
    sys.exit(0)

import json, urllib.request, vlm_client
for candidate in ("http://192.168.10.23:8084", "http://127.0.0.1:8084"):
    try:
        req = urllib.request.Request(candidate + "/v1/models")
        if vlm_client.KEY:
            req.add_header("Authorization", "Bearer " + vlm_client.KEY)
        with urllib.request.urlopen(req, timeout=4) as r:
            if json.loads(r.read()).get("data"):
                vlm_client.BASE = candidate
                print(ask(question, [img_path], max_tokens=200, temperature=0.1))
                sys.exit(0)
    except Exception:
        continue
sys.exit("VLM_DOWN: no hay VLM disponible en bc250:8084 ni 127.0.0.1:8084")
