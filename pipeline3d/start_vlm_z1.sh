#!/bin/bash
# start_vlm_z1.sh — Qwen3-VL-8B en z1:8084, BAJO DEMANDA, con espera READY REAL.
# FASE 3: prohibido sleep fijo como readiness. Poll del endpoint cada 2 s, timeout 120 s.
PIDFILE=~/recon3d/work/vlm_8084.pid
mkdir -p ~/recon3d/work
if curl -s -m3 http://127.0.0.1:8084/v1/models 2>/dev/null | grep -q data; then
    pgrep -f 'llama-server.*8084' > "$PIDFILE" 2>/dev/null || true
    echo "VLM_ALREADY_READY"; exit 0
fi
nohup ~/llama.cpp/build/bin/llama-server \
  -m ~/models/vlm/Qwen3VL-8B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/vlm/mmproj-Qwen3VL-8B-Instruct-F16.gguf \
  -ngl 0 -c 8192 --host 127.0.0.1 --port 8084 --jinja \
  > ~/recon3d/work/vlm_8084.log 2>&1 &
PID=$!
echo $PID > "$PIDFILE"
echo "VLM_STARTING pid $PID"
for i in $(seq 1 200); do
    sleep 2
    if curl -s -m3 http://127.0.0.1:8084/v1/models 2>/dev/null | grep -q data; then
        echo "VLM_READY after ~$((i*2))s"
        exit 0
    fi
    kill -0 $PID 2>/dev/null || { echo "VLM_DIED (ver ~/recon3d/work/vlm_8084.log)"; exit 2; }
done
echo "VLM_TIMEOUT_400S"; exit 3
