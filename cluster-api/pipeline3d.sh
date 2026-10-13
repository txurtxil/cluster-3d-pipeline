#!/bin/bash
# pipeline3d.sh "<brief>" -> lanza mision y espera veredicto. Salida = veredicto.
BRIEF="$1"
[ -z "$BRIEF" ] && { echo "uso: pipeline3d.sh "Caja 100x70x30 mm, pared 2 mm""; exit 2; }
OUT=$(bash /home/txurtxil/cluster-api/tg_mision3d.sh "$BRIEF")
echo "$OUT"
# leccion 13-oct: si la API rechaza el brief (NEEDS_HUMAN_REVIEW), decirlo YA
# y no esperar 10 min a que el waiter muera de 404 (esa mision nunca se registra)
case "$OUT" in
  *'"status": "RUNNING"'*) ;;
  *'"status"'*) REASON=$(printf '%s' "$OUT" | python3 -c "import json,sys
try:
    d=json.loads(sys.stdin.read()); print(d.get('reason','rechazada'))
except Exception:
    print('rechazada')")
    echo "NO_LANZADA: $REASON"; exit 4;;
esac
ID=$(echo "$OUT" | python3 /home/txurtxil/cluster-api/mid.py 2>/dev/null)
[ -z "$ID" ] && { echo "NO_SE_ENCONTRO_MISSION_ID"; exit 1; }
echo "esperando veredicto de $ID ..."
bash /home/txurtxil/cluster-api/mision3d_wait.sh "$ID" 600
