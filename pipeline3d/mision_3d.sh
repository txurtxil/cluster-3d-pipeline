#!/usr/bin/env bash
# mision_3d.sh — Pipeline completo pieza 3D para OpenClaw (se ejecuta en rpi5)
# Flujo: gen (bpy determinista) -> checkpoint bbox -> render Cycles + STL -> juez VLM -> verificacion fisica
# Uso: mision_3d.sh <gen_script.py> <nombre_run> ["pregunta para el juez VLM"]
set -euo pipefail

GEN="${1:?FALTA: gen_script.py}"
NAME="${2:?FALTA: nombre_run}"
ASK="${3:-Describe la pieza renderizada: forma, color y detalles. Una frase.}"

Z=z1
R=~/pipeline3d/runs/$NAME
ZR=/home/txurtxil/pipeline3d/runs/$NAME
T0=$(date +%s)

mkdir -p "$R"
echo "== MISION_3D $NAME inicio $(date -Is) =="

# 1. Subir generador y ejecutarlo en z1 (Blender headless)
ssh $Z "mkdir -p $ZR"
scp -q "$GEN" $Z:$ZR/gen.py
ssh $Z "~/blender/blender -b --factory-startup -P $ZR/gen.py -- $ZR/pieza.blend" | grep GEN_OK

# 2. Checkpoint dimensional (bbox por objeto)
ssh $Z "~/blender/blender -b $ZR/pieza.blend -P ~/pipeline3d/bbox_check.py" \
    | grep BBOX_REPORT_JSON | sed 's/^BBOX_REPORT_JSON //' > "$R/bbox.json"
echo "BBOX: $(cat $R/bbox.json)"

# 3. Render determinista (Cycles 32, 512x512) + export STL
ssh $Z "~/blender/blender -b $ZR/pieza.blend -P ~/pipeline3d/render_export.py -- $ZR/pieza.png $ZR/pieza.stl" \
    | grep PIPELINE_

# 4. Juez visual VLM
if ssh $Z "python3 ~/pipeline3d/vlm_judge.py $ZR/pieza.png '$ASK'" > "$R/juez.txt" 2>&1; then
  echo "VLM_STATUS=OK (ya activo)" >> "$R/juez.txt"
else
  echo "VLM_STATUS=DOWN -> arranque bajo demanda" >> "$R/juez.txt"
  ssh $Z "bash ~/start_vlm_z1.sh" >> "$R/juez.txt" 2>&1
  ssh $Z "python3 ~/pipeline3d/vlm_judge.py $ZR/pieza.png '$ASK'" > "$R/juez.txt.vlm" 2>&1 \
    && { cat "$R/juez.txt.vlm" >> "$R/juez.txt"; echo "VLM_STATUS=OK (bajo demanda)" >> "$R/juez.txt"; } \
    || echo "JUEZ_FALLA (vlm bajo demanda no respondio)" >> "$R/juez.txt"
  ssh $Z "bash ~/stop_vlm_z1.sh" >> "$R/juez.txt" 2>&1 || true
fi
echo "JUEZ: $(cat $R/juez.txt)"

# 5. Recuperar artefactos y verificacion fisica (timestamps + hash)
scp -q $Z:$ZR/pieza.png $Z:$ZR/pieza.stl $Z:$ZR/pieza.blend "$R/"
T1=$(date +%s)
{
  echo "run: $NAME"
  echo "inicio: $(date -Is -d @$T0)"
  echo "fin: $(date -Is -d @$T1)"
  echo "duracion_s: $((T1-T0))"
  sha256sum "$R/pieza.blend" "$R/pieza.png" "$R/pieza.stl"
} > "$R/verificacion.txt"

echo "== MISION_3D $NAME OK en $((T1-T0))s -> $R =="
ls -lh "$R"
