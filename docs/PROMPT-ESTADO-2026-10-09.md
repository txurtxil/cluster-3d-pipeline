# ESTADO DEL PROYECTO TXURTXIL — AGENTE 3D AUTÓNOMO (RECON3D)
# 2026-10-09 ~21:00 — documento de contexto desde cero para cualquier agente
# REGLA DE ORO: RESULTADO FÍSICO > RESPUESTA DEL MODELO. Verifica todo con
# comandos reales; nunca afirmes nada sin ejecución física.

============================================================
1. CLUSTER — FUENTE DE VERDAD (verificado físicamente hoy)
============================================================

PRODUCCIÓN: bc250-node2 @ 192.168.10.45 (casa)
- Qwen3.8-27B UD-IQ3_XXS (3-bit, ~11 GB) — ÚNICO modelo oficial.
  Honestidad probada (E-003). PROHIBIDO el IQ2_XXS (fabricó resultados 3×).
- llama-server :8082 (servicio llama-node2, ENABLED). n_ctx 53248.
- 40/40 CUs · GTT 14 GB · governor cyan-skillfish → ~19-20 t/s (headless).
- Temperaturas vistas hoy: 38-58 °C en trabajo normal; 90 °C edge cuando
  el planificador razonó en bucle largo. Vigilar: throttle ~95 °C.
- ⚠️ Si hay sesión local/servidor gráfico activo en node2, la GPU comparte
  memoria y la inferencia se desploma (thinking infinito, content vacío).
  Node2 debe quedarse headless para misiones.
- Sin GUI. WoL funciona SOLO desde suspend, no desde poweroff.

REPUESTO: bc250-1 @ 192.168.10.25 (hoy en casa; destino trastero .23)
- Ubuntu 26.04, kernel 7.0.0-38, mismo modelo, llama-node1 :8081 ENABLED.
- APAGADO (decisión del usuario). Sirve en ~3 min si se enciende.

RPI5 @ 192.168.10.140 — ORQUESTADOR (siempre encendido)
- OpenClaw 2026.9.8 gateway :18789. Bot @TxurtxilOpenClaw_bot.
- Token del bot NUEVO (rotado hoy): en ~/.openclaw/credentials/telegram-token.txt
  Canal Telegram configurado (channels.telegram, tokenFile, dmPolicy pairing).
- Corregido HOY: agents.defaults.model.primary apuntaba a un ID inexistente
  (Coder IQ2_XXS prohibido); ahora cluster-qwen/Qwen3.8-27B-UD-IQ3_XXS.gguf
  alias "Qwen3.8-27B IQ3 (Cluster)", reasoning=true (verificado en journal:
  "agent model: cluster-qwen/Qwen3.8-27B-UD-IQ3_XXS.gguf (thinking=medium)").
- bindings: [{agentId: chat, match: {channel: telegram}}] (clave raíz
  "bindings"; "multiAgent" NO existe en esta versión → error en journal).
- Agente chat (perfil minimal) con AGENTS.md de comandos (/mision3d...).
- Proxy LLM 127.0.0.1:18090. cluster_api :8200 (pipeline viejo, app Nexus).
- Otros bots Telegram en rpi5 con tokens DISTINTOS: centinela (redes),
  alfred, wallapop. NO son el bot del cluster.

Z1 @ 192.168.10.12 — TALLER (siempre encendido)
- Blender 4.2.23 LTS en ~/blender/blender (NO está en PATH).
- venv metrología: ~/venvs/metrology (cv2 5.0.0, numpy 2.5.3, scipy 1.18.1).
- VLM Qwen2.5-VL-7B :8084 bajo demanda (start_vlm_z1.sh).
- ~/cluster-3d-pipeline → GitHub txurtxil/cluster-3d-pipeline (rama master).
- Repo cluster-ia-home (docs) también en z1. /tmp es tmpfs (usar ~).
- Disco 92% (limpiar antes de misiones grandes).

RED: casa 192.168.10.x. Trastero por PLC ~14 Mbps (nunca rsync/scp por él).
Acceso remoto del agente: ssh -p 6022 txurtxil@www.mundaka.net (WAN→z1).
⚠️ Password auth activo (Temporal01) — pendiente volver a solo-claves y
desactivar password en WAN. ssh del sandbox usa SSH_ASKPASS trick.

============================================================
2. PIPELINE 3D — QUÉ EXISTE Y DÓNDE (todo en z1:~/cluster-3d-pipeline/mission/)
============================================================

mission_loop.py — Mission Manager v0.1.
- PLAN (Qwen propone params) → build (Blender) → medir → evaluate (HARD
  constraints) → DIAGNOSE (un cambio por iteración) → loop ≤ max_iters.
- Versionado V001.. con parameters/metrics/blend/stl + SHA256SUMS + REPORT.md
  que termina en PASS / FAIL / NEEDS_HUMAN_REVIEW.
- LLM con temperature 0, n_predict 1600, y CLAVE: chat_template_kwargs
  {enable_thinking: false} — sin thinking (JSON determinista; el thinking
  quemaba el presupuesto y devolvía content vacío).
- parser JSON: bloques ```json primero, fallback llaves; raw[:300] al log si
  falla. params_hint por misión (vocabulario del generador).
- manifold solo es HARD si require_manifold=true (celosías tienen aristas
  frontera legítimas: 80 bad_edges = 4 arcos × 2 extremos × 10 lados).

Generadores (leen PARAMETERS.json, escriben blend+stl+GEN_OK):
- gen_box.py + measure_box.py — caja 100×70×30 pared 2 M3 USB-C R5.
  measure_box: dims por bbox + GROSOR DE PARED por ray-casting (4 caras,
  independiente del generador) + manifold.
- gen_tower.py v5 — torre paramétrica. Perfil "resin" = W2 medido
  EMPIRICAMENTE del Eiffel_Resin_09.blend del usuario (dos tramos: bloque
  ancho hasta 0.5H, escalón a torre esbelta; plataformas 0.5H/0.875H; ratio
  H/W 2.4). Perfil "eiffel" = W_KEYS/S_KEYS de la torre real (170 mm).
  Normalización AFÍN a [0,H] exacto (empty raíz TOWER_ROOT). Arcos de
  media-torus (torus completo + borrar mitad x>0 vía bmesh; Blender 4.2 no
  acepta arc=). Zapatas, barandillas (rail+posts), cornisas, chapitel
  (cono+2 anillos+bola tangente a H).
- gen_clone.py + measure_clone.py — RUTA B: clon fiel por KIT. Extrae del
  .blend de referencia 50 piezas únicas + 334 instancias (extract_kit.py),
  filtra la estructura principal (radio 0.35·span_z desde la pieza más
  alta) → 315 piezas/34 únicas, y escala a H exacto. ES la geometría
  original reutilizada: la fidelidad NO se consigue con cilindros
  procedurales, sino reutilizando el kit (lección del día, spec §37).
- kit_eiffel.json — el kit extraído (2.2 MB) en mission/.
- measure_* — metrología por VÉRTICES del mesh evaluado (NO bound_box: la
  bbox del cuadrado circunscrito de un cilindro rotado sobrestima hasta ×√2).
- metrology2d.py + test_metrology.py — metrología 2D validada contra ground
  truth sintético (METROLOGY_PASS): bbox, IoU, contour (validado contra
  implementación de referencia cv2), zonas Z0-Z5 (spec §15), densidad,
  openings. En ~/cluster-3d-pipeline/metrology/ con venv ~/venvs/metrology.

API :8201 (rpi5, systemd user mission3d-api) — mission3d_api.py:
- POST /mission3d {brief} → parser determinista (regex LxWxH + pared, sin
  LLM) → mission.json a z1 → lanza mission_loop (ssh en background local,
  NUNCA 'ssh host "cmd &"' que cuelga el canal).
- GET /mission3d/{id} | /report | /file/model.stl. Sanitización estricta.
- tg_mision3d.sh (rpi5) — puente acotado bot→API para el agente chat.

============================================================
3. MISIONES EJECUTADAS (resultados físicos)
============================================================
- caja_001_validation: PASS — fallo inyectado pared 1.6 detectado por
  ray-cast → diagnose cambió WALL→2.0 → PASS. Nació el loop (spec §25).
- caja_002_autonoma: PASS iter 1 — PLAN de Qwen sin inyección.
- caja_002 por API :8201 (120×80×40 pared 3): PASS — cadena brief→API→z1.
- tower_001 (procedural v1-3): NEEDS_HUMAN_REVIEW — sirvió para curar
  métricas (bound_box vs vértices, z_min, manifold opcional).
- tower_002 (procedural v5, perfil resin): bucle probado (detect→diagnose→
  fix→rebuild en segundos); secundaria tras pivotar a la Ruta B.
- tower_clone: PASS — clon del Eiffel_Resin_09 a 300 mm. H=300.000,
  BASE=122.008, PARTS=315, UNIQ=34, SHA256 02145034…de4bfd. Commit 0218d1b.

============================================================
4. REFERENCIA DE ESTUDIO: Eiffel_Resin_09.blend (del usuario)
============================================================
- En /tmp y en mission/kit_eiffel.json de z1; copia en el sandbox upload.
- 80.12 mm alto · 50 mallas únicas · 334 instancias · 8 paneles DXF de
  relieve (8.176 vértices c/u, frisos de arcos de cornisa).
- Contiene 3 estructuras (torre principal + torre pequeña + ornamento);
  el clon filtra la principal.
- Perfil medido por cortes (usado como W2 en gen_tower): ver gen_tower.py.
- Autoría: kit de piezas 2D (estilo dibujo técnico DXF → instanciado).
- STL del clon: 14.2 MB binario; cabecera de 80 bytes NULOS que algunos
  visores rechazan → reparada (v1 con cabecera ASCII). 116 aristas
  no-manifold HEREDADAS del original. Variante manifold: remesh voxel
  0.3 mm (pendiente de corregir error en remesh_manifold.py).

============================================================
5. PENDIENTES (prioridad)
============================================================
1. Variante manifold del STL (leer /tmp/remesh.log en z1, corregir, entregar).
2. Fase foto-fit (spec §27): silueta/zonas de la foto del usuario vs render
   del clon; optimizer ajusta proporciones. metrology2d ya validado.
3. Extraer panel DXF como asset de cornisa reutilizable en piezas nuevas.
4. Telegram: canal OK tras rotar token; falta pairing (usuario manda /start,
   se aprueba con openclaw pairing approve).
5. Seguridad: quitar password auth del WAN 6022 (dejar solo claves).
6. Soak térmico 15 min/placa (spec pendiente 3.4) — con monitor de temp.
7. Push de docs de estado al repo; node1 al trastero cuando toque.
8. Q3_K_M (Coder-30B 3-bit) A/B opcional en rpi5 (~/modelos-transfer).

============================================================
6. LECCIONES DURAS DEL DÍA (añadir a las del proyecto)
============================================================
- Qwen3 thinking consume n_predict: con 500 → content vacío (finish=length).
  Para trabajo JSON: enable_thinking=false (inmune además a GPU compartida).
- GPU compartida (sesión local en node2) = thinking infinito. Node2 headless.
- bound_box de cilindros rotados = bbox del cuadrado circunscrito (×√2).
  Medir por vértices del mesh evaluado. §36: validar métrica con sintético.
- z_min importa: caps/arcos se cuelan bajo 0 → normalizar afín a [0,H].
- 'ssh host "cmd &"' cuelga el canal pese a setsid/nohup: lanzar el ssh en
  background LOCAL (nohup ssh ... &) o setsid en el lado remoto.
- pkill -f "patrón" se automata (mata la sesión ssh propia): usar [p]atrón.
- Sandbox del agente: se reinicia entre turnos (pierde /tmp y funciones).
  Todo script clave debe re-subirse cada turno o vivir en z1:~/.
- printf con escapes anidados corrompe JSONs: subir ficheros con stdin (cat >).
- STL binario: escribir cabecera ASCII de 80 bytes (algunos visores la exigen).
- Uploads grandes: scp por stdin/wget; verificar con md5sum remoto.
- El planificador no puede arreglar bugs del generador (solo parámetros):
  los bugs de código se arreglan en código, no con diagnose.
- Cuando existe geometría de referencia, el pipeline la REUTILIZA
  (Ruta B). El procedural puro queda para piezas sin referencia.

============================================================
7. ACCESOS RÁPIDOS
============================================================
# ver misión en curso
z1: tail -f ~/cluster-3d-pipeline/mission/runs/<id>/mission.log
# temperatura cerebro
ssh rpi5 → ssh node2 "sensors | grep -i edge"
# lanzar misión (script en z1, con setsid)
z1: bash /tmp/launch_<x>.sh   # pkill [m]isión, rm runs, setsid nohup loop
# API piezas
POST http://192.168.10.140:8201/mission3d {"brief": "Caja 100 x 70 x 30 mm, pared 2"}
# clonar torre a otra altura: cambiar injected_initial H y relanzar tower_clone
