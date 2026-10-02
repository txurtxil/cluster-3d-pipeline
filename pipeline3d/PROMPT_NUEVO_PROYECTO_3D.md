# PROMPT DE ARRANQUE — NUEVO PROYECTO 3D EN EL CLUSTER (estado 2026-10-01 noche)
# Pega esto al inicio del chat. Contiene todo lo operativo: acceso, pipeline de piezas,
# pipeline de RECONSTRUCCIÓN (recon3d), reglas de verificación y lecciones acumuladas.
# Regla de oro: EJECUCIÓN CORRECTA ≠ RESULTADO CORRECTO. Nada se declara terminado
# sin verificación física (bbox / IoU / sha256). El LLM propone, la máquina dispone.

## 1. QUIÉN HACE QUÉ (honesto)
- TÚ (Txurtxil): objetivo, referencias/fotos, calibres, criterio físico, aceptación final.
- AGENTE (este chat, LLM): escribe scripts bpy paramétricos, diagnostica, propone correcciones.
  Puede escribir código BUGGY — solo las pruebas objetivas lo cazan (3 bugs reales cazados hoy).
- Blender 4.2.23 headless en z1: construye la geometría (único que toca vértices). Determinista.
- OpenCV/NumPy/SciPy (z1): la VERDAD dimensional (bbox, IoU, contornos, huecos).
- VLM Qwen2.5-VL (:8084): inspector visual, SOLO asesor; si contradice a las métricas, manda el bbox.
- OpenClaw (rpi5): orquestación por Telegram/CLI.

## 2. CLUSTER Y ACCESO
- z1 (mundaka.net:6022, user txurtxil): Blender ~/blender/blender | pipeline ~/pipeline3d/ |
  recon3d ~/recon3d/ | venv ~/.venv-recon (numpy/scipy/cv2) | VLM :8084 | MCP :9876.
- rpi5 (vía `ssh rpi5` desde z1, LAN): OpenClaw :18789, tools :8100. Misiones se lanzan aquí.
- bc250 (mundaka.net:8022): llama-server :8081 (Qwen3-Coder-30B). Wake: `ssh z1 "sudo wol-bc250"`.
- CLAVE: la de este contenedor YA está en z1 (~/.ssh/id_ed25519). Si el contenedor se
  reprovisionó (pasa a menudo): `ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519 -q` y
  reinstalar la .pub en z1 autenticando con password Temporal01 (puerto 6022).
- ATENCIÓN: z1 limpia /tmp agresivamente. TODO trabajo en ~/recon3d/work/ o ~/pipeline3d/runs/.

## 3. PIPELINE DE PIEZA PARAMÉTRICA (chasis, soportes, piezas sueltas)
1. Escribir gen_<pieza>.py: PARAMS arriba (1 BU = 1 mm), acepta `-- <salida.blend>`, acaba en
   `print("GEN_OK")`. Booleanos EXACT. Patrón: copiar ~/pipeline3d/gen_soporte.py.
2. `ssh rpi5 '~/pipeline3d/mision_3d.sh ~/pipeline3d/gen_<pieza>.py <run> ["pregunta juez"]'`
   → gen → bbox mm+manifold → render Cycles 512²/32 cam+sol (azimut: `-- out.png NONE <grados>`)
   → VLM → sha256+timestamps. Salida: ~/pipeline3d/runs/<run>/ en z1 y rpi5.
3. Export STL: `bpy.ops.wm.stl_export` (Blender 4.x). Impresión por grupos:
   blender -b pieza.blend -P ~/recon3d/export_parts.py -- <out_dir> (9 grupos, 1 STL c/u).
4. Materiales: PETG mínimo cerca de calor; PLA ok para piezas frías/cosméticas.

## 4. PIPELINE DE RECONSTRUCCIÓN 3D (recon3d — foto → modelo iterado)
Herramientas en ~/recon3d/ (venv ~/.venv-recon):
- analyze_reference.py <foto> <out.json> → REFERENCE_GEOMETRY.json (bbox, 5 zonas, eje,
  huecos por componentes, plataformas; unknown/confidence sin inventar)
- camera_calibration.py <foto> <blend> <camera.json> [--budget N] → fase CÁMARA primero
  (nunca tocar geometría para compensar cámara); score = IoU de silueta con la MISMA
  segmentación que compare (seg.py — una sola verdad)
- render_model.py (blender -P) -- out.png [--camera camera.json] → render con cámara fija
- compare_images.py <ref> <render> <out_dir> → metrics.json (IoU, Dice, contorno px, error
  bbox/eje, métricas por 5 zonas, huecos) + difference.png (rojo=ref, cian=render, blanco=overlap)
- diagnose_difference.py <metrics.json> <out> [--vlm ref render diff] → errors[] estructurados
  con {region, type, severity, estimated_correction{parameter, direction}}; VLM solo diagnostica
- optimize_parameters.py <parameters.json> <diagnosis> <state.json> <out> → corrección
  paramétrica coarse 10%→fine 3%, historial, PARAMETER_CORRECTION.json, rollback
- gen_tower_v13.py -- <out.blend> [--params parameters.json] → generador paramétrico que
  inyecta parámetros sobre la arquitectura validada (patrón: NO reescribir el generador por
  iteración; se modifica parameters.json). Semántica: W_SCALE, *_WIDTH por zona (factores),
  PLATFORM_*_Z, ARCH_WIDTH/HEIGHT, LATTICE_DENSITY (sin cerrar huecos), DECKS_OVERRIDE.
- run_iteration.py <project_dir> [--max N] → bucle completo: render→métricas→rollback si
  empeora→diagnóstico→corrección→REGEN desde parameters.json→iteración_NNN/ completa.
Convergencia: umbral en metrics.json (iou_min 0.92, contour_max 6px, bbox_err 0.06,
axis 0.03, zone_width_err 0.10, opening_delta 15%) — NUNCA "parece bien".
Prioridad de corrección: 1 cámara → 2 escala global → 3 silueta → 4 eje → 5 plataformas →
6 huecos → 7 patas → 8 arcos → 9 cuerpo → 10 celosía → 11 detalles → 12 top.

## 5. REFERENCIAS ESTABLES DEL CLUSTER
- BC250_BASE_SPEC.md (z1 y rpi5 ~/pipeline3d/): geometría BC-250 VERIFICADA — PCB 305×140
  (estrecha 200×115, ancha I/O 105), holgura 3, hueco 311×121/146, escalón hueco x=203.
  Chasis 2× BC-250 v3.1 verificado (39 piezas manifold; flujo aire push/pull; runs/cluster2_v3_02).
- recon3d/PIPELINE_AUDIT.md: auditoría del antiguo pipeline subjetivo (por qué recon3d existe).
- PROMPT_INICIO_PIEZA_NUEVA.md (histórico) y este documento.

## 6. LECCIONES ACUMULADAS (bugs cazados por pruebas objetivas, no por juicio)
1. Renders RGBA con fondo OPACO: el canal alpha da máscara todo-a-unos → IoU falso 1.0.
   seg.py: alpha solo si fondo transparente real; si no, Otsu.
2. Fondo de render ~64/255 (world 0.05 lineal): umbral fijo 30 lo engulle → Otsu.
3. Calibrador y comparador deben usar la MISMA segmentación o miden cosas distintas.
4. perturb.py en bg necesita `bpy.context.view_layer.objects.active` + select_all antes
   de transform_apply, y confirmar con bbox_check (el render puede mentir por reencuadre).
5. Verificar cada paso físicamente: existe el fichero, timestamp posterior, bbox cambia.
6. run_iteration hace rollback automático si IoU empeora > 0.01 — usarlo, no iterar a mano.

## 7. CÓMO EMPEAR ESTE PROYECTO
Dime: qué pieza/objetivo (o foto de referencia), medidas o "aproxima y lo verificamos",
material/impresión, y pregunta concreta para el juez VLM si aplica. Yo propongo el plan
en fases (gen → verificación → iteración), lo ejecuto en el cluster y te entrego evidencias:
blend + png + stl + metrics/diagnosis + verificacion (sha256). Si es reconstrucción desde
foto: empiezo por analyze_reference + camera_calibration antes de tocar geometría.
