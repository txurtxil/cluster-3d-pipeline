# ESTADO DEL CLUSTER TXURTXIL — PROMPT DE CONTINUACIÓN (13-oct-2026)
# Pégalo en cualquier chat/agente nuevo. Explica TODO como a un niño de 12 años,
# paso a paso. REGLA DE ORO: nada se afirma sin ejecutar comandos reales.

## 1. INFRAESTRUCTURA
- **bc250-1** (192.168.10.25, TERRAZA): placa AMD BC-250 14GB. Taller: Blender 4.2.23
  headless (~/blender), llama-server :8081 (Qwen3-30B-A3B IQ3_XXS, ctx 16384 real,
  api-key `sk-cluster-72ce643cae6f7db766ded5b32c985611`, -np 1), repo
  ~/cluster-3d-pipeline (push funciona con `git push origin master`), modelos
  ~/models, bandeja ~/incoming/. Ciclo nocturno: apaga 00:00 / enciende 08:00
  (timers systemd de SISTEMA en la rpi5: bc2501-apaga/enciende). Swap 2G.
- **rpi5** (192.168.10.140, CASA, nunca duerme): OpenClaw gateway :18789
  (UI cangrejo.mundaka.net, bot @TxurtxilOpenClaw_bot SOLO charla: adjuntos
  rotos, no prometer archivos), API mission3d :8201 (~/cluster-api/mission3d_api.py,
  snapshot en repo cluster-api/), wrappers pipeline3d.sh/mision3d_wait.sh
  (waiter tolera 4×404 = carrera registro), **OPERADOR bot @txurtxil_operador_bot**
  (~/operador/operador.py, copia en repo operador/; comandos /pide /mision
  MCP server ~/mcp-txurtxil/server.py (stdio, tools estado/temps/mision/entrega,
  probado, sin host conectado aún — candidato: nodo MCP de n8n), n8n :5678
  (workflow briefing 8:05 PENDIENTE clic Publish), docker: n8n/SearXNG/Open
  WebUI/HA/Plex/stack *arr.
- ACCESO agente cloud: helper `/tmp/ap_bc.sh` (echo Temporal01) + `ssh -p 8022
  txurtxil@www.mundaka.net` (WAN intermitente por túnel del móvil: reintentos
  20-30s, comandos cortos). Salto a rpi5: helper `/tmp/ap_rpi.sh` (echo
  Surfing75) + `ssh txurtxil@192.168.10.140` (OJO: helpers mueren si bc250
  reinicia). Multilínea/comillas: base64 por stdin. Ficheros grandes bc250→rpi5:
  `cat f | ssh rpi5 'cat > dest'`.

## 2. FÁBRICA DE PIEZAS (todo verificado PASS, determinista md5)
Familias: **Taza** (gen_taza.py), **Engranaje helicoidal** (gen_gear_helical.py),
**Hélice de barco** (gen_helice.py). Cada una: generador + measure_X.py + ruta
en API. Pedir por Telegram al Operador: `/pide una helice de 120 con 5 palas`
→ traductor local (Qwen3-30B) → completar_brief (defaults) → validar física →
misión → PASS → zip por el MISMO chat. Defaults y validadores viven en
operador.py. Briefs exactos en AGENTS.md (~/.openclaw/workspace/) y en el repo.

## 3. LECCIONES DE METROLOGÍA (costaron iteraciones reales)
- GEN_OK siempre JSON; MEASURE_JSON con dims+manifold{ok}+not_measured.
- Medir por vértices del mesh evaluado + ray-casting, nunca bound_box.
- Blender: EXACT corrompe mallas dentadas (163 vértices imposibles); FAST es
  no-determinista → piezas complejas = sólidos por from_pydata + núcleo liso
  EXACT solapado (slicer une shells).
- FIDUCIALES: si la superficie tiene sesgo irreducible, el generador emite
  puntos del eje teórico (eje/LE/TE) en el .blend, NUNCA en el STL.
- El EJE no codifica el paso (hélice): medir bordes LE→TE.
- Raíz de perfil en t~0 o rake/skew llevan factor (1−t_root) sistemático.
- Contador de dientes FFT 6..60 (36+ se cuenta bien); sesgo helix ±1° en
  ruedas grandes → tol 1.5 en API.
- Taza: el asa se auto-ajusta dentro del cuerpo (superficie del asa > H la
  rompía); H medida = máx(cuerpo, asa).
- API registra misiones asíncrono: 404 en el primer segundo = carrera, no
  "no existe".

## 4. GIT (regla del owner: TODO siempre a GitHub)
Repo github.com/txurtxil/cluster-3d-pipeline, rama master. Contiene: mission/
(generadores+metrologistas), operador/operador.py, cluster-api/mission3d_api.py,
visor (pendiente añadir). Push desde bc250-1: funciona.

## 5. PENDIENTES
1. Clic Publish del workflow n8n (briefing 8:05). 2. Enchufar nodo MCP de n8n
   al server mcp-txurtxil. 3. node2 (encender con botón) → A/B Coder-30B-A3B
   → independencia total de LLM cloud. 4. Visor: añadir proxy host en NPM UI
   de casa; 3MF aún no (solo STL). 5. BIOS bc250-1 (probablemente ya tiene
   Restore on AC Loss — los reinicios tras los cortes lo sugieren).

## 6. NO TOCAR sin supervisión
Config OpenClaw (una clave a la vez, backup, journal 60s; compaction YA
aplicada: keepRecent 4000/memoryFlush/notify). Base de datos n8n (solo UI).
stopO/reboots sin evidencia (curl :8081/health + free -h primero).
