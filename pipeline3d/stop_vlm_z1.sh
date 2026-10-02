#!/bin/bash
# stop_vlm_z1.sh — detiene SOLO el VLM (PID exacto vía PIDFILE; FASE 4: nada de pkill generico).
PIDFILE=~/recon3d/work/vlm_8084.pid
if [ -f "$PIDFILE" ]; then
    kill "$(cat $PIDFILE)" 2>/dev/null
    rm -f "$PIDFILE"
else
    # ultimo recurso acotado al patron del VLM (nunca pkill generico)
    pkill -f 'llama-server.*8084' 2>/dev/null
fi
for i in $(seq 1 15); do
    sleep 1
    pgrep -f 'llama-server.*8084' >/dev/null || break
done
if pgrep -f 'llama-server.*8084' >/dev/null; then
    echo "VLM_STILL_RUNNING"; exit 1
fi
PORTFREE=$(ss -tln 2>/dev/null | grep -c ':8084' || echo 0)
MEM=$(free -m | awk '/Mem/{print $7}')
echo "VLM_STOPPED port_8084_listeners=$PORTFREE mem_avail=${MEM}MB"
