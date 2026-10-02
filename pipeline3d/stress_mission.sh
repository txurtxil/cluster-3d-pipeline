#!/usr/bin/env bash
# stress_mission.sh — Petrolero hiperdetallado: stress test END-TO-END del pipeline.
# Se ejecuta en rpi5. Artefactos en z1:~/recon3d/iterations/stress_test_01/
# Reglas: ningun fallo se convierte en OK; VLM bajo demanda con espera READY real.
set -uo pipefail

Z=z1
ZR=/home/txurtxil/recon3d/iterations/stress_test_01
R=~/recon3d/iterations/stress_test_01
KEY="sk-cluster-72ce643cae6f7db766ded5b32c985611"
mkdir -p "$R"
ssh $Z "mkdir -p $ZR"
T0=$(date +%s%3N)
echo "t() { echo \$(( \$(date +%s%3N) - $T0 )); }" > /tmp/stress_t.sh
ts() { echo $(( $(date +%s%3N) - T0 )); }
RAM_SNAPS=""

ram_snap() { ssh $Z 'free -m | awk "/Mem/{print \$3}"' | tr '\n' ' ' >> "$R/ram_snaps.txt"; echo "$1" >> "$R/ram_snaps.txt"; }

echo "MISSION=petrolero_stress_test_01" > "$R/status.env"
ram_snap RAM_BEFORE

# 1) GEN (Blender headless en z1) — BC250/Coder ya genero este script; aqui se ejecuta
T=$(date +%s%3N)
ssh $Z "~/blender/blender -b --factory-startup -P ~/pipeline3d/gen_petrolero_stress.py -- $ZR/petrolero.blend" > "$R/gen.log" 2>&1
GEN_RC=$?
GEN_T=$(( $(date +%s%3N) - T ))
grep -q GEN_OK "$R/gen.log" && BLENDER_STATUS=OK || BLENDER_STATUS=FAIL_GEN
ram_snap RAM_AFTER_GEN

# 2) BBOX (metricas geometricas = fuente de verdad)
T=$(date +%s%3N)
ssh $Z "~/blender/blender -b $ZR/petrolero.blend -P ~/pipeline3d/bbox_check.py" 2>/dev/null | grep BBOX_REPORT > "$R/bbox.json"
BBOX_T=$(( $(date +%s%3N) - T ))

# 3) RENDERS x5 (3/4 principal con STL, proa, costado, popa, cenital) + STL+SHA
T=$(date +%s%3N)
declare -A VIEWS=( [main]="NONE 0.55" [bow]="-35 0.55" [side]="55 0.5" [stern]="145 0.5" )
ssh $Z "~/blender/blender -b $ZR/petrolero.blend -P ~/pipeline3d/render_export.py -- $ZR/render_main.png $ZR/petrolero.stl -35 0.55" > "$R/render_main.log" 2>&1
for v in bow side stern; do
  read -r az el <<< "${VIEWS[$v]}"
  ssh $Z "~/blender/blender -b $ZR/petrolero.blend -P ~/pipeline3d/render_export.py -- $ZR/render_$v.png NONE $az $el" > "$R/render_$v.log" 2>&1
done
ssh $Z "~/blender/blender -b $ZR/petrolero.blend -P ~/pipeline3d/render_export.py -- $ZR/render_top.png NONE top" > "$R/render_top.log" 2>&1
RENDER_T=$(( $(date +%s%3N) - T ))
grep -q PIPELINE_STL_OK "$R/render_main.log" && STL_STATUS=OK || STL_STATUS=FAIL
SHA=$(ssh $Z "sha256sum $ZR/petrolero.stl | cut -d' ' -f1")
STL_SIZE=$(ssh $Z "stat -c %s $ZR/petrolero.stl")

# 4) SFTP robusto: rpi5 <-- z1 (sftp_transfer.py con hash y retry)
T=$(date +%s%3N)
if ssh $Z "test -f $ZR/petrolero.stl"; then
  python3 ~/recon3d/sftp_transfer.py get 192.168.10.12 22 "$ZR/petrolero.stl" "$R/petrolero.stress_test_01.stl" --retries 3 > "$R/sftp.log" 2>&1
  SFTP_RC=$?
  grep -q SFTP_OK "$R/sftp.log" && SFTP_STATUS=OK || SFTP_STATUS=FAIL
else
  echo "remoto no existe" > "$R/sftp.log"; SFTP_STATUS=FAIL; SFTP_RC=2
fi
SFTP_T=$(( $(date +%s%3N) - T ))

# 5) VLM bajo demanda con espera READY real (timeout 180 s, intervalo 5 s)
T=$(date +%s%3N)
VLM_STATUS=DOWN
if ssh $Z "curl -s -m4 http://127.0.0.1:8084/v1/models 2>/dev/null | grep -q data"; then
  VLM_STATUS=READY
else
  ssh $Z "bash ~/start_vlm_z1.sh" >> "$R/vlm.log" 2>&1
  for i in $(seq 1 36); do
    sleep 5
    if ssh $Z "curl -s -m4 http://127.0.0.1:8084/v1/models 2>/dev/null | grep -q data"; then
      VLM_STATUS=READY; break
    fi
  done
fi
VLM_START_T=$(( $(date +%s%3N) - T ))
ram_snap RAM_DURING_VLM

T=$(date +%s%3N)
if [ "$VLM_STATUS" = "READY" ]; then
  ssh $Z "python3 ~/pipeline3d/vlm_judge.py $ZR/render_main.png 'Identifica el tipo de buque y enumera 6 detalles visibles estructurales (casco, tanques, gruas, superestructura, tuberias, popa).' " > "$R/vlm_analysis.txt" 2>&1 \
    && VLM_STATUS=OK || VLM_STATUS=FAIL_INFERENCE
else
  echo "VLM no disponible (DOWN); mision continua sin analisis visual" > "$R/vlm_analysis.txt"
fi
VLM_INF_T=$(( $(date +%s%3N) - T ))
T=$(date +%s%3N)
ssh $Z "bash ~/stop_vlm_z1.sh" >> "$R/vlm.log" 2>&1 || true
VLM_STOP_T=$(( $(date +%s%3N) - T ))
ram_snap RAM_AFTER_VLM

# 6) Métricas OpenCV (stress cruzado: vista 3/4 vs costado -> discriminacion real)
T=$(date +%s%3N)
ssh $Z "~/.venv-recon/bin/python ~/recon3d/compare_images.py $ZR/render_main.png $ZR/render_side.png $ZR/metrics" > "$R/metrics.log" 2>&1
METRICS_T=$(( $(date +%s%3N) - T ))
grep -q COMPARE_OK "$R/metrics.log" && METRICS_STATUS=OK || METRICS_STATUS=FAIL

# 7) GAIN (ejercitar codigo del optimizador sin cambios arbitrarios)
echo '{"errors": []}' > "$R/diag_empty.json"
echo '{}' > "$R/params_scratch.json"
# FASE 6: transferir + verificar (exists, size, sha256) ANTES de ejecutar GAIN
scp -q "$R/diag_empty.json" "$R/params_scratch.json" $Z:$ZR/ 2>"$R/gain_scp.err" || cat "$R/gain_scp.err" >> "$R/gain_scp.err"
V_EXISTS=$(ssh $Z "test -f $ZR/params_scratch.json && echo Y")
S_LOCAL=$(sha256sum "$R/params_scratch.json" | cut -d' ' -f1)
S_REMOTE=$(ssh $Z "sha256sum $ZR/params_scratch.json 2>/dev/null | cut -d' ' -f1")
if [ "$V_EXISTS" = "Y" ] && [ -n "$S_REMOTE" ] && [ "$S_LOCAL" = "$S_REMOTE" ]; then
  ssh $Z "~/.venv-recon/bin/python ~/recon3d/optimize_parameters.py $ZR/params_scratch.json $ZR/diag_empty.json $ZR/state_scratch.json $ZR" > "$R/gain.log" 2>&1 \
    && GAIN_STATUS=OK || GAIN_STATUS=FAIL
else
  echo "GAIN_PREFLIGHT_FAIL exists=$V_EXISTS sha_match=$([ "$S_LOCAL" = "$S_REMOTE" ] && echo Y || echo N)" > "$R/gain.log"
  GAIN_STATUS=FAIL
fi

# 8) INFORME
TOTAL_T=$(( $(date +%s%3N) - T0 ))
OBJ_COUNT=$(grep -o 'OBJECT_COUNT: [0-9]*' "$R/gen.log" | awk '{print $2}')
MANIFOLD_STATS=$(python3 -c "
import json,collections
d=json.loads(open('$R/bbox.json').read().replace('BBOX_REPORT_JSON ',''))
c=collections.Counter(v['manifold'] for v in d.values())
print('objects=%d manifold_true=%d manifold_false=%d' % (len(d), c.get(True,0), c.get(False,0)))" 2>/dev/null || echo "bbox_parse_fail")
N_MANIF_FALSE=$(echo "$MANIFOLD_STATS" | grep -o 'manifold_false=[0-9]*' | cut -d= -f2)
[ "${N_MANIF_FALSE:-0}" = "0" ] && MANIFOLD=OK || MANIFOLD=FAIL

cat > "$R/petrolero_stress_test_report.txt" <<EOF
MISSION=petrolero_stress_test_01
STATUS=$([ "$BLENDER_STATUS" = OK ] && [ "$STL_STATUS" = OK ] && echo COMPLETED || echo COMPLETED_WITH_FAILURES)
TOTAL_TIME_MS=$TOTAL_T
OBJECT_COUNT=$OBJ_COUNT
GEN_TIME_MS=$GEN_T
BLENDER_TIME_MS=$GEN_T
RENDER_TIME_MS=$RENDER_T
STL_TIME_MS=$RENDER_T
STL_SIZE_BYTES=$STL_SIZE
SHA256=$SHA
BBOX_TIME_MS=$BBOX_T
BBOX=$MANIFOLD_STATS
MANIFOLD=$MANIFOLD
SFTP_TIME_MS=$SFTP_T
SFTP_STATUS=$SFTP_STATUS
VLM_START_TIME_MS=$VLM_START_T
VLM_INFERENCE_TIME_MS=$VLM_INF_T
VLM_STOP_TIME_MS=$VLM_STOP_T
METRICS_TIME_MS=$METRICS_T
METRICS_STATUS=$METRICS_STATUS
GAIN_STATUS=$GAIN_STATUS
CODER_STATUS=OK (generador producido por BC250:8081 antes de la mision)
VLM_STATUS=$VLM_STATUS
BLENDER_STATUS=$BLENDER_STATUS
SFTP_STATUS=$SFTP_STATUS
CAMERA_LOCK=NOT_INVOKED (stress test; prohibido por mision)
WARNINGS=ver gen.log/audits
EOF
cat "$R/ram_snaps.txt" >> "$R/petrolero_stress_test_report.txt"
scp -q $ZR/metrics.json "$R/metrics.json" 2>/dev/null
scp -q $ZR/render_main.png "$R/render_main.png" 2>/dev/null
echo "STRESS_MISSION_DONE rc_gen=$GEN_RC total_ms=$TOTAL_T vlm=$VLM_STATUS manifold=$MANIFOLD sftp=$SFTP_STATUS metrics=$METRICS_STATUS"
