#!/usr/bin/env python3
# vlm_client.py — capa VLM UNICA e intercambiable (auditoria 2026-10-02).
# Endpoint/modelo/key se leen de config/services.json via cfg.py.
# SIN fallback legacy, SIN hardcode. El VLM es asesor: nunca valida geometria.
# Copia unica: recon3d/vlm_client.py (la de pipeline3d fue eliminada).
import sys, os, json, base64, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg

BASE = os.environ.get("VLM_URL") or cfg.url("vlm")
KEY = os.environ.get("VLM_KEY") or cfg.api_key()


def model_name():
    try:
        req = urllib.request.Request(BASE + "/v1/models")
        if KEY:
            req.add_header("Authorization", "Bearer " + KEY)
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            return d["data"][0]["id"]
    except Exception:
        return None


def ask(prompt, image_paths, max_tokens=300, temperature=0.0):
    content = [{"type": "text", "text": prompt}]
    for p in image_paths:
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + b64}})
    payload = {"messages": [{"role": "user", "content": content}],
               "temperature": temperature, "max_tokens": max_tokens}
    m = model_name()
    if m:
        payload["model"] = m
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    if KEY:
        req.add_header("Authorization", "Bearer " + KEY)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()
