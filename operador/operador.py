#!/usr/bin/env python3
"""El Operador v2 — bot de control del cluster Txurtxil.
Anade /pide: el usuario escribe en LENGUAJE SENCILLO y el cerebro LOCAL
(Qwen3-30B en bc250-1) traduce a 'brief' con formato CLAVE=NUM; luego
mision -> veredicto -> zip por Telegram. Kimi cloud NO participa.
"""
import json, os, re, subprocess, sys, time, urllib.request, urllib.parse

HOME = os.path.expanduser("~")
TOKEN_FILE = os.path.join(HOME, ".operador", "token.txt")
ALLOWED_CHAT = 1306877990
API_BASE = "https://api.telegram.org/bot%s/"
LLAMA = "http://192.168.10.25:8081/v1/completions"
LLAMA_KEY = "sk-cluster-72ce643cae6f7db766ded5b32c985611"

TRADUCTOR_PROMPT = (
    'Eres un traductor de peticiones de piezas 3D. Responde SOLO una linea '
    '"BRIEF: <tipo>: CLAVE=NUM, ..." o "NOSE".\n'
    'Tipos y claves:\n'
    '- Taza: H, D_OUT, WALL, BOTTOM, RIM_R, HANDLE_D, HANDLE_Z_LOW, HANDLE_Z_HIGH, HANDLE_REACH\n'
    '- Engranaje helicoidal: MODULE, TEETH, HELIX_ANGLE, FACE_WIDTH, BORE_D, HUB_D, HUB_LEN, KEYWAY, CHAMFER\n'
    '- Helice de barco: DIAM, BLADES, PITCH_RATIO, BAR, HUB_D, HUB_LEN, RAKE, SKEW, SHAFT_D\n'
    '- Caja roscada (tarro con tapa): DIAM, HEIGHT, WALL, THREAD_PITCH, LID_HEIGHT, SEAL_GROOVE, CHAMFER\n'
    'Defaults: Taza H=95,D_OUT=90,WALL=3,BOTTOM=4,RIM_R=1,HANDLE_D=9,HANDLE_Z_LOW=30,HANDLE_Z_HIGH=68,HANDLE_REACH=24 | '
    'Engranaje MODULE=2,TEETH=24,HELIX_ANGLE=19,FACE_WIDTH=15,BORE_D=8,HUB_D=30,HUB_LEN=10,KEYWAY=4,CHAMFER=0.5 | '
    'Helice DIAM=80,BLADES=4,PITCH_RATIO=0.85,BAR=0.52,HUB_D=20,HUB_LEN=15,RAKE=8,SKEW=12,SHAFT_D=8 | '
    'Caja DIAM=60,HEIGHT=50,WALL=3,THREAD_PITCH=4,LID_HEIGHT=12,SEAL_GROOVE=0,CHAMFER=0.5\n'
    'Si piden otra cosa: NOSE.\n'
    'Usuario: "')


def tg(token, method, **kwargs):
    data = urllib.parse.urlencode(kwargs).encode()
    req = urllib.request.Request(API_BASE % token + method, data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def tg_doc(token, chat_id, path, caption):
    boundary = "----txurtxil7"
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        payload = (("--%s\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n%s\r\n"
                    "--%s\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n%s\r\n"
                    "--%s\r\nContent-Disposition: form-data; name=\"document\"; filename=\"%s\"\r\n"
                    "Content-Type: application/octet-stream\r\n\r\n")
                   % (boundary, chat_id, boundary, caption, boundary, fname)).encode() + \
                  f.read() + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(API_BASE % token + "sendDocument", data=payload,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def sh(argv, timeout):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return (p.stdout + p.stderr).strip()


def llama(prompt, max_tokens=150, stop=None):
    payload = {"prompt": prompt, "max_tokens": max_tokens, "temperature": 0}
    if stop:
        payload["stop"] = stop
    body = json.dumps(payload).encode()
    req = urllib.request.Request(LLAMA, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + LLAMA_KEY})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)["choices"][0]["text"]


def traducir(frase):
    """Lenguaje sencillo -> brief CLAVE=NUM, usando el cerebro LOCAL."""
    out = llama(TRADUCTOR_PROMPT + frase.strip() + '"\nBRIEF:',
                max_tokens=100, stop=["\n", " | "]).strip()
    line = out.splitlines()[0].split(" | ")[0].strip()
    for f in FAMILIAS:
        i = line.find(f, len(f))
        if i > 0:
            line = line[:i].strip()
    if line.upper().startswith("BRIEF:"):
        line = line[6:].strip()
    if "NOSE" in line.upper():
        return None
    # el LLM a veces adorna el nombre: "Caja roscada (tarro con tapa):" ->
    # limpiar parentesis antes de validar el nombre de familia
    line = re.sub(r"\s*\([^)]*\)\s*", " ", line)
    m = re.match(r"^(Taza|Engranaje( helicoidal)?|Caja( roscada)?|H[eé]lice( de barco)?)\s*:\s*(.+)$", line)
    if not m:
        return None
    fam, resto = m.group(1), m.group(5)
    if fam[0] in "Hh":
        fam = "Helice de barco"
    elif fam.startswith("Engranaje"):
        fam = "Engranaje helicoidal"
    elif fam.startswith("Caja"):
        fam = "Caja roscada"
    return "%s: %s" % (fam, resto)


FAMILIAS = ("Taza", "Engranaje helicoidal", "Helice de barco")

DEFAULTS = {
    "Taza": dict(H=95, D_OUT=90, WALL=3, BOTTOM=4, RIM_R=1, HANDLE_D=9,
                 HANDLE_Z_LOW=30, HANDLE_Z_HIGH=68, HANDLE_REACH=24),
    "Engranaje helicoidal": dict(MODULE=2, TEETH=24, HELIX_ANGLE=19, FACE_WIDTH=15,
                                 BORE_D=8, HUB_D=30, HUB_LEN=10, KEYWAY=4, CHAMFER=0.5),
    "Helice de barco": dict(DIAM=80, BLADES=4, PITCH_RATIO=0.85, BAR=0.52, HUB_D=20,
                            HUB_LEN=15, RAKE=8, SKEW=12, SHAFT_D=8),
    "Caja roscada": dict(DIAM=60, HEIGHT=50, WALL=3, THREAD_PITCH=4,
                         LID_HEIGHT=12, SEAL_GROOVE=0, CHAMFER=0.5),
}


def completar_brief(brief):
    """El traductor (LLM) a veces omite claves. Rellena con los defaults de
    la familia: el LLM decide familia + valores explicitos; los huecos los
    cubre esta tabla determinista (leccion 13-oct: helice sin HUB_D -> crash)."""
    fam, _, resto = brief.partition(":")
    fam = fam.strip()
    base = DEFAULTS.get(fam)
    if not base:
        return brief
    kv = dict(base)
    for k, v in re.findall(r"([A-Z_]+)\s*=\s*([0-9]+(?:\.[0-9]+)?)", resto):
        kv[k] = float(v)
    partes = []
    for k, v in kv.items():
        partes.append("%s=%s" % (k, int(v) if v == int(v) else v))
    return "%s: %s" % (fam, ", ".join(partes))


def validar_brief(brief):
    """Sentido comun fisico ANTES de fabricar. Devuelve (ok, mensaje)."""
    fam, _, resto = brief.partition(":")
    pares = re.findall(r"([A-Z_]+)\s*=\s*([0-9]+(?:\.[0-9]+)?)", resto)
    kv = dict((k, float(v)) for k, v in pares)
    if not kv:
        return False, "no entendi los numeros del brief."
    if fam.startswith("Taza"):
        h = kv.get("H", 95); d = kv.get("D_OUT", 90); w = kv.get("WALL", 3)
        hd = kv.get("HANDLE_D", 9); bo = kv.get("BOTTOM", 4)
        if h < hd + 2:
            return False, ("una taza de %.0f mm no puede tener un asa de %.0f mm de grueso. "
                           "Dimelo en centimetros o prueba: /pide una taza de 70" % (h, hd))
        if d < 2 * w + 10:
            return False, "el diametro es muy pequeno para el grosor de pared pedido."
        if bo > h - 1:
            return False, "el fondo no cabe en una taza tan bajita."
    elif fam.startswith("Engranaje"):
        m = kv.get("MODULE", 2); z = kv.get("TEETH", 24)
        bore = kv.get("BORE_D", 8); hub = kv.get("HUB_D", 30)
        if z < 8:
            return False, "un engranaje necesita al menos 8 dientes."
        if bore + 4 > hub:
            return False, "el taladro es casi tan grande como el cubo; sube HUB_D."
        if hub + 4 > m * z:
            return False, "el cubo es casi tan grande como el propio engranaje."
    elif fam.startswith("Caja"):
        dd = kv.get("DIAM", 60); hh = kv.get("HEIGHT", 50)
        wp = kv.get("WALL", 3); tp = kv.get("THREAD_PITCH", 4); lh = kv.get("LID_HEIGHT", 12)
        if dd < 30:
            return False, "un tarro de %.0f mm es demasiado pequeno para rosca FDM (min 30)." % dd
        if hh < wp + 12:
            return False, "el tarro es demasiado bajo para esa pared y una rosca util."
        if tp < 2:
            return False, "paso de rosca demasiado fino; minimo 2 mm para FDM."
        if lh < 6:
            return False, "la tapa necesita al menos 6 mm de altura."
    elif fam.startswith("Helice"):
        dd = kv.get("DIAM", 80); bl = kv.get("BLADES", 4)
        shaft = kv.get("SHAFT_D", 8); hub = kv.get("HUB_D", 20)
        if not (2 <= bl <= 6):
            return False, "las helices tienen entre 2 y 6 palas."
        if shaft + 4 > hub:
            return False, "el eje es casi tan grueso como el cubo; sube HUB_D."
        if hub + 6 > dd:
            return False, "el cubo es casi tan grande como la propia helice."
    return True, ""


def cmd_estado():
    api = sh(["curl", "-s", "-m", "10", "http://127.0.0.1:8201/health"], 15)
    brain = sh(["curl", "-s", "-m", "10", "-H",
                "Authorization: Bearer " + LLAMA_KEY,
                "http://192.168.10.25:8081/health"], 15)
    temps = sh(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "bc250",
                "sensors | grep -iE 'edge|Tctl' | tr '\\n' ' '"], 20)
    mem = sh(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "bc250",
              "free -m | awk 'NR==2{print $3\"MB usados / \"$7\"MB libres\"}'"], 20)
    return ("ESTADO DEL CLUSTER\n"
            "· mission3d : %s\n"
            "· cerebro   : %s\n"
            "· temps bc250: %s\n"
            "· memoria   : %s" % (api or "SIN RESPUESTA", brain or "SIN RESPUESTA", temps or "?", mem or "?"))


def cmd_mision(brief):
    if not brief:
        return "uso: /mision <brief con CLAVE=NUM...>"
    out = sh(["bash", os.path.join(HOME, "cluster-api", "pipeline3d.sh"), brief], 660)
    return out[-3500:] if out else "(sin output — revisar logs)"


def cmd_entrega(mid, nombre=None):
    """El run vive en bc250 (la fábrica). Se empaqueta alli y el zip viaja
    a la rpi5 en base64 (scp se cuelga en esta WAN)."""
    import base64 as b64
    if not mid:
        return "ERROR: falta mission_id"
    nombre = ((nombre or mid)[:60].replace("/", "_")) + ".zip"
    base = nombre[:-4]
    remoto = (
        "R=~/cluster-3d-pipeline/mission/runs/%s; "
        "[ -f $R/V001/model.stl ] || { echo NOEXISTE; exit 1; }; "
        "cd /tmp && rm -f %s.zip %s.stl && cp $R/V001/model.stl %s.stl && "
        "zip -q %s.zip %s.stl && md5sum %s.zip | cut -c1-12 && base64 -w0 %s.zip"
        % (mid, base, base, base, base, base, base, base))
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "bc250", remoto], capture_output=True, text=True, timeout=90)
    if "NOEXISTE" in p.stdout or p.returncode != 0:
        return "no existe el run '%s' (o sin STL)" % mid
    lines = p.stdout.strip().splitlines()
    data = b64.b64decode(lines[-1])
    zpath = os.path.join("/tmp/operador_entrega", nombre)
    os.makedirs("/tmp/operador_entrega", exist_ok=True)
    with open(zpath, "wb") as f:
        f.write(data)
    return zpath + " md5:" + (lines[-2] if len(lines) > 1 else "?")


def main():
    token = open(TOKEN_FILE).read().strip()
    offset = 0
    while True:
        try:
            upd = tg(token, "getUpdates", offset=offset + 1, timeout=30)
        except Exception:
            time.sleep(10)
            continue
        for u in upd.get("result", []):
            offset = u["update_id"]
            msg = u.get("message") or {}
            chat = msg.get("chat", {}).get("id")
            text = (msg.get("text") or "").strip()
            if chat != ALLOWED_CHAT or not text.startswith("/"):
                continue
            parts = text.split(None, 1)
            cmd, arg = parts[0].split("@")[0].lower(), (parts[1] if len(parts) > 1 else "")
            try:
                if cmd == "/saluda":
                    r = "Operador en linea. /ayuda para comandos."
                elif cmd == "/ayuda":
                    r = ("/pide <lo que quieras en palabras sencillas> -> fabrico y te mando el zip\n"
                         "/estado -> parte del cluster\n"
                         "/mision <brief CLAVE=NUM> -> fabricar (formato exacto)\n"
                         "/entrega <mission_id> -> mandar el zip de una mision\n"
                         "/saluda -> ping")
                elif cmd == "/estado":
                    r = cmd_estado()
                elif cmd == "/mision":
                    tg(token, "sendMessage", chat_id=chat, text="Mision lanzada, espero veredicto (hasta 10 min)...")
                    r = cmd_mision(arg)
                elif cmd == "/pide":
                    if not arg:
                        r = 'uso: /pide quiero una helice de 80 mm con 4 palas'
                    else:
                        tg(token, "sendMessage", chat_id=chat,
                           text="Entendido, traduciendo y fabricando (2-5 min)...")
                        brief = traducir(arg)
                        if not brief:
                            r = ("No supe traducir eso. Prueba con taza, engranaje helicoidal "
                                 "o helice de barco. O usa /mision con formato CLAVE=NUM.")
                        else:
                            tg(token, "sendMessage", chat_id=chat, text="Brief: " + brief)
                            brief = completar_brief(brief)
                            ok, msg = validar_brief(brief)
                            if not ok:
                                r = "Me detengo: " + msg
                                tg(token, "sendMessage", chat_id=chat, text=r)
                                continue
                            out = cmd_mision(brief)
                            mid = None
                            m = re.search(r'"mission_id":\s*"([^"]+)"', out)
                            if m:
                                mid = m.group(1)
                            if "PASS" in out and mid:
                                z = cmd_entrega(mid).split(" md5:")[0]
                                if z.endswith(".zip"):
                                    tg_doc(token, chat, z, "Pieza lista: %s\nVeredicto: PASS" % brief)
                                    r = out[-600:]
                                else:
                                    r = z + "\n" + out[-600:]
                            else:
                                r = out[-900:]
                elif cmd == "/entrega":
                    a = arg.split()
                    z = cmd_entrega(a[0] if a else "").split(" md5:")[0]
                    if z.endswith(".zip"):
                        tg_doc(token, chat, z, "Entrega %s" % os.path.basename(z))
                        continue
                    r = z
                else:
                    r = "comando desconocido. /ayuda"
            except subprocess.TimeoutExpired:
                r = "TIMEOUT ejecutando %s" % cmd
            except Exception as e:
                r = "ERROR en %s: %s" % (cmd, e)
            try:
                tg(token, "sendMessage", chat_id=chat, text=r[:4000])
            except Exception:
                pass


if __name__ == "__main__":
    main()
