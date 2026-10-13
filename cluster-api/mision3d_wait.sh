#!/bin/bash
# mision3d_wait.sh <mission_id> [timeout_s] - espera el VERDICT en UNA llamada
ID="$1"; T=${2:-600}
[ -z "$ID" ] && { echo "uso: mision3d_wait.sh <mission_id> [timeout_s]"; exit 2; }
# Blindaje 12-oct: un numero suelto es casi siempre el timeout pasado como id
# (leccion: OpenClaw llamo 'mision3d_wait.sh 600' y paseo un 404 durante 10 min).
if [[ "$ID" =~ ^[0-9]+$ ]]; then
  echo "ERROR: '$ID' parece un timeout, no un mission_id. Orden correcto: mision3d_wait.sh <mission_id> [timeout_s]"; exit 2
fi
if ! [[ "$ID" =~ ^[A-Za-z0-9_-]{4,64}$ ]]; then
  echo "ERROR: mission_id '$ID' con formato invalido"; exit 2
fi
END=$((SECONDS+T)); LAST=""; N404=0
while [ $SECONDS -lt $END ]; do
  HTTP=$(curl -s -o /tmp/wait_resp.json -w '%{http_code}' --max-time 10 "http://127.0.0.1:8201/mission3d/$ID")
  if [ "$HTTP" = "404" ]; then
    # Leccion 13-oct: la API registra la mision ASINCRONO tras el POST; un 404
    # en el primer segundo es una carrera, no un id inexistente. Solo falla
    # si el 404 persiste (4 intentos seguidos ~ 1 min).
    N404=$((N404+1))
    if [ $N404 -ge 4 ]; then
      echo "ERROR 404: mision '$ID' NO EXISTE tras $N404 intentos. Verifica: ls ~/cluster-3d-pipeline/mission/runs/ en bc250."; exit 3
    fi
    sleep 15
    continue
  fi
  N404=0
  if [ "$HTTP" != "200" ]; then echo "ERROR: API respondio HTTP $HTTP"; exit 3; fi
  RAW=$(python3 -c "import json;print(json.load(open('/tmp/wait_resp.json')).get('raw',''))" 2>/dev/null)
  if echo "$RAW" | grep -q "VERDICT"; then
    echo "$RAW" | grep -E "VERDICT|REASON|iter" | tail -5
    exit 0
  fi
  LAST="$RAW"; sleep 15
done
echo "TIMEOUT tras ${T}s; mision sigue en curso. Ultimo log:"; echo "$LAST" | tail -5; exit 1
