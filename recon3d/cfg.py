#!/usr/bin/env python3
# cfg.py — cargador UNICO de la configuracion central (config/services.json).
# Todos los clientes del pipeline obtienen endpoints/modelos/keys de aqui.
import json, os

_DIR = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_DIR, "config", "services.json")
_CFG = None


def load():
    global _CFG
    if _CFG is None:
        _CFG = json.load(open(_PATH))
    return _CFG


def get(service, key=None):
    d = load()[service]
    return d if key is None else d[key]


def url(service, external=False):
    s = load()[service]
    h = s.get("host_external") if external else s["host"]
    p = s.get("port_external") if external else s["port"]
    return "http://%s:%s" % (h, p)


def api_key():
    return load()["auth"]["api_key"]


if __name__ == "__main__":
    c = load()
    for svc in ("coder", "vlm", "blender"):
        print(svc.upper().ljust(8), url(svc), c[svc].get("model", c[svc].get("version", "")))
