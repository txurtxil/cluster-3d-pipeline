# ESTADO PROYECTO TXURTXIL — AGENTE 3D AUTONOMO (RECON3D)
# 2026-10-10 10:45 — contexto desde cero para cualquier agente
# REGLA DE ORO: RESULTADO FISICO > RESPUESTA DEL MODELO.

## 1. CLUSTER (verificado)
- node2 .45: CEREBRO. Qwen3.8-27B IQ3_XXS :8082 (llama-node2, n_ctx 53248,
  40CU, governor cyan-skillfish, ~19-20 t/s SOLO headless; si hay sesion
  local en node2 la GPU comparte y el thinking se dispara a infinito).
  Temperaturas vistas: 38-58 C normal, 90 C en bucles largos (throttle ~95).
  WoL solo desde suspend.
- node1 .25: replica del modelo, APAGADO (repuesto, trastero luego).
- rpi5 .140: OpenClaw :18789 + bot @TxurtxilOpenClaw_bot (token NUEVO rotado
  9-oct, en ~/.openclaw/credentials/telegram-token.txt; canal configurado,
  polling limpio; FALTA pairing: usuario /start -> approve). Modelo del agente
  CORREGIDO: cluster-qwen/Qwen3.8-27B-UD-IQ3_XXS.gguf. bindings raiz:
  [{agentId: chat, match:{channel: telegram}}] ("multiAgent" NO existe).
  API mission3d :8201 + wrapper tg_mision3d.sh. Otros bots en rpi5
  (centinela/alfred/wallapop) usan tokens distintos.
- z1 .12: PUERTA (ssh -p 6022 txurtxil@www.mundaka.net -> z1) + MANOS:
  Blender 4.2.23 en ~/blender/blender, venv ~/venvs/metrology
  (cv2/numpy/scipy/trimesh), VLM :8084 bajo demanda. En z1 NO hay LLM.
  ~/cluster-3d-pipeline -> GitHub txurtxil/cluster-3d-pipeline (rama master).
  /tmp=tmpfs. Disco 92%.
- Password auth (Temporal01) activo en WAN 6022: pendiente solo-claves.
  El sandbox del agente se REINICIA entre turnos: re-subir scripts o
  guardarlos en z1. WAN intermitente (caidas nocturnas; verificar md5 de
  uploads criticos).

## 2. PIPELINE 3D (z1:~/cluster-3d-pipeline/mission/)
mission_loop.py v0.1: PLAN->build->medir->evaluate->DIAGNOSE->loop. LLM con
temperature 0, n_predict 1600 y CRITICO: chat_template_kwargs
{"enable_thinking": false} (el thinking quemaba el presupuesto -> content
vacio). Parser ```json + fallback; raw[:300] al log en fallo. params_hint por
mision. manifold HARD solo si require_manifold (celosias legitiman bordes).
Versionado SHA256 + REPORT.md terminado en PASS/FAIL/NEEDS_HUMAN_REVIEW.
Generadores (PARAMETERS.json -> blend+stl+GEN_OK):
- gen_box/measure_box: caja; pared medida por ray-cast independiente.
- gen_tower.py v5: torre procedural. Perfil "resin" = W2 medido del
  Eiffel_Resin_09.blend (dos tramos, plataformas 0.5H/0.875H, ratio 2.4);
  "eiffel" = curva real (W_KEYS/S_KEYS). Normalizacion afil [0,H] exacta
  (TOWER_ROOT). Arcos media-torus (borrado de mitad via bmesh; 4.2 no acepta
  arc=).
- gen_clone.py + measure_clone.py: RUTA B — clon fiel por KIT
  (extract_kit.py: 50 piezas unicas/334 instancias -> filtro radio 0.35*
  span_z desde la pieza mas alta -> 315/34, torre unica). ES la geometria
  original escalada: con referencia, el pipeline la REUTILIZA; el procedural
  solo para piezas sin referencia.
- gen_tanker.py + measure_tanker.py: rescate del gen_petrolero_stress.py del
  usuario (343 lineas, casco real, tanques, piping, botes, helice toro,
  audit) adaptado al mission-loop. UNIDAD: {"L":250} -> L=260.915 (helice),
  B=42.84, H=109.672, 361 PARTS, audit limpio.
- metrology2d.py (METROLOGY_PASS): bbox/IoU/contorno/zonas Z0-Z5/densidad.
- Medir por VERTICES, nunca bound_box (cilindros rotados: xsqrt2).
- API :8201 (rpi5): POST /mission3d {brief} -> parser regex LxWxH -> z1.
  Lanzamiento: nohup ssh local o setsid remoto; NUNCA 'ssh host "cmd &"'.

## 3. MISIONES PASS
caja_001 (fallo inyectado detectado/corregido) - caja_002 autonoma -
caja API 120x80x40 - tower_clone: H=300.000 BASE=122.008 315p/34u
SHA256 02145034...de4bfd. ENTREGADA: STL v1 (cabecera reparada) + 3MF
(watertight:false por 116 aristas heredadas; slicers la reparan). Usuario
CONFIRMO: "es la torre perfecta".

## 4. REFERENCIA Eiffel_Resin_09.blend
80.12 mm - 50 mallas unicas/334 instancias - 8 paneles DXF relieve 8176 v
(frisos de arcos) - 3 estructuras en el archivo (filtrar) - kit en
mission/kit_eiffel.json (2.2 MB).

## 5. PENDIENTES
1. petrolero_001 -> entregar STL/3MF.
2. Variante manifold torre (remesh voxel; remesh_manifold.py fallo, leer log).
3. Foto-fit (silueta/zonas vs foto). 4. Panel DXF como asset.
5. Telegram pairing. 6. Quitar password WAN. 7. Soak termico.
8. node1 al trastero. Q3_K_M A/B opcional.

## 6. LECCIONES (9-oct + 10-oct)
thinking tokens / enable_thinking=false / GPU compartida / bound_box xsqrt2 /
normalizacion afil / ssh '&' cuelga / pkill se automata con [p]atron /
sandbox resets / printf corrompe JSON -> stdin / STL cabecera 80B ASCII /
planificador no arregla bugs de codigo / Ruta B > procedural con referencia /
verificar md5 tras upload critico.
