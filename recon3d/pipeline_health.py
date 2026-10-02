#!/usr/bin/env python3
# pipeline_health.py — comprobacion UNICA de salud del pipeline (auditoria 2026-10-02).
# Uso: pipeline_health.py [--json out.json]
# Reglas: componente opcional DOWN -> la mision NO finge evaluacion visual
# (VLM_STATUS=DOWN y continua). Componente REQUIRED down -> exit 1. Nada falla
# silenciosamente: cada linea lleva servicio, estado y detalle.
import sys, os, json, socket, time
import paramiko, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg

KEY = cfg.api_key()
ROWS = []


def check(name, required, fn):
    try:
        status, detail = fn()
    except Exception as e:
        status, detail = "FAIL", str(e)[:90]
    if status not in ("OK", "DOWN"):
        status = "FAIL"
    ROWS.append(dict(service=name, status=status, required=required, detail=detail))
    return status


def tcp(host, port, tmo=8):
    s = socket.create_connection((host, port), timeout=tmo)
    s.close()


def http_models(url):
    req = urllib.request.Request(url + "/v1/models")
    req.add_header("Authorization", "Bearer " + KEY)
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())["data"][0]["id"]


def ssh_cmd(host, port, cmd, tmo=25):
    k = paramiko.Ed25519Key.from_private_key_file(os.path.expanduser("~/.ssh/id_ed25519"))
    t = paramiko.Transport((host, port))
    t.start_client(timeout=15)
    t.auth_publickey("txurtxil", k)
    ch = t.open_session(); ch.settimeout(tmo); ch.exec_command(cmd)
    out = b""
    while True:
        if ch.recv_ready():
            out += ch.recv(65536)
        if ch.exit_status_ready() and not ch.recv_ready():
            break
        time.sleep(0.3)
    t.close()
    return out.decode(errors="replace").strip()


Z = ("mundaka.net", cfg.get("blender", "port_external"))
B = ("mundaka.net", cfg.get("coder", "port_external"))

check("SSH_Z1", True, lambda: (tcp(*Z), ("OK", "z1:%d" % Z[1]))[1])
check("SSH_BC250", True, lambda: (tcp(*B), ("OK", "bc250:%d" % B[1]))[1])
check("CONFIG", True, lambda: ("OK", "services.json viva, %d servicios" % len(cfg.load())) if cfg.load() else ("FAIL", "vacía"))


def coder_check():
    m = http_models("http://mundaka.net:%d" % cfg.get("coder", "port_external"))
    return ("OK", m) if m else ("FAIL", "sin modelo")


check("CODER", True, coder_check)


def vlm_check():
    try:
        out = ssh_cmd(*Z, "curl -s -m6 http://127.0.0.1:8084/v1/models 2>/dev/null", tmo=20)
        d = json.loads(out or "{}")
        if d.get("data"):
            return "OK", d["data"][0]["id"]
        return "DOWN", "z1:8084 sin servidor VLM (bajo demanda; start_vlm_z1.sh)"
    except Exception as e:
        return "DOWN", "z1 inaccesible: %s" % str(e)[:60]


check("VLM", False, vlm_check)


def blender_check():
    v = ssh_cmd(*Z, "%s --version | head -1" % cfg.get("blender", "bin"))
    return ("OK", v) if "Blender" in v else ("FAIL", v[:60])


check("BLENDER", True, blender_check)


def sftp_check():
    k = paramiko.Ed25519Key.from_private_key_file(os.path.expanduser("~/.ssh/id_ed25519"))
    t = paramiko.Transport(Z); t.start_client(timeout=15)
    t.auth_publickey("txurtxil", k)
    sftp = paramiko.SFTPClient.from_transport(t)
    sftp.stat("/home/txurtxil/pipeline3d/mision_3d.sh")
    sftp.close(); t.close()
    return "OK", "stat+mision_3d.sh"


check("SFTP", True, sftp_check)


def storage_check():
    d = ssh_cmd(*Z, "df -h / | tail -1 | awk '{print $4}'")
    db = ssh_cmd(*Z, "ssh -o BatchMode=yes -o ConnectTimeout=6 bc250 \"df -h / | tail -1 | awk '{print \\$4}'\" 2>/dev/null")
    return "OK", "z1 libre=%s bc250 libre=%s" % (d, db)


check("STORAGE", True, storage_check)


def rpi5_check():
    out = ssh_cmd(*Z, "ssh -o BatchMode=yes -o ConnectTimeout=5 rpi5 'hostname' 2>&1")
    return ("OK", "lan ok") if out.strip() == "rpi5" else ("FAIL", out[:60])


check("RPI5_LAN", False, rpi5_check)

print("=" * 72)
for r in ROWS:
    print("%-12s %-5s %s" % (r["service"], r["status"], r["detail"]))
print("=" * 72)
vlm = next(r for r in ROWS if r["service"] == "VLM")
print("VLM_STATUS=%s" % vlm["status"])
bad = [r for r in ROWS if r["required"] and r["status"] != "OK"]
print("REQUIRED_DOWN=%d" % len(bad))
if "--json" in sys.argv:
    p = sys.argv[sys.argv.index("--json")+1]
    json.dump(dict(rows=ROWS, vlm_status=vlm["status"], ts=time.strftime("%Y-%m-%dT%H:%M:%S")),
              open(p, "w"), indent=1)
sys.exit(1 if bad else 0)
