#!/usr/bin/env bash
# tg_mision3d.sh — puente acotado bot -> Mission Manager (API :8201).
# Uso: tg_mision3d.sh "<brief de la pieza>"
# Regla: el brief viaja como campo JSON (jq/python), nunca interpolado en shell.
BRIEF="$1"
[ -z "$BRIEF" ] && { echo "USO: tg_mision3d.sh <descripcion>"; exit 1; }
[ ${#BRIEF} -gt 500 ] && { echo "brief demasiado largo (max 500)"; exit 1; }
RESP=$(python3 - "$BRIEF" <<'EOF'
import json, sys, urllib.request
brief = sys.argv[1]
req = urllib.request.Request("http://127.0.0.1:8201/mission3d",
    data=json.dumps({"brief": brief}).encode(),
    headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=25) as r:
        print(json.dumps(json.load(r), ensure_ascii=False))
except urllib.error.HTTPError as e:
    print(json.dumps({"error": e.code, "detalle": e.read().decode()[:300]}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"error": str(e)[:200]}, ensure_ascii=False))
EOF
)
echo "$RESP"
case "$RESP" in
  *'"status": "RUNNING"'*) exit 0 ;;
  *) exit 1 ;;
esac
