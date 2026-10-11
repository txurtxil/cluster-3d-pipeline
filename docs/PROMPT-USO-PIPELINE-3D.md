# PROMPT DE USO — PIPELINE 3D TXURTXIL (RECON3D)
# 2026-10-10 — contexto operativo para cualquier agente
# REGLA DE ORO: RESULTADO FÍSICO > RESPUESTA. Verifica con ejecución real.

## 1. DÓNDE VIVE EL PIPELINE (después de la migración)
TODO en bc250-1 (192.168.10.25, "la terraza"):
- Blender 4.2.23 LTS: ~/blender/blender (headless, -b)
- Repo: ~/cluster-3d-pipeline → github.com/txurtxil/cluster-3d-pipeline (rama master)
- venv metrología: ~/venvs/metrology (numpy 2.5.3, scipy 1.18.1, cv2 5.0.0, trimesh 5.1.1)
- LLM local: llama-server :8081 (Qwen3.8-27B-UD-IQ3_XXS, --api-key en mission/.apikey)
- z1 está JUBILADA (apagada). No depender de ella. node2 apagado (repuesto).
- Ciclo diario: bc250-1 se APAGA a las 00:00 y ENCIENDE a las 08:00 (timers
  systemd bc2501-* en rpi5). De noche NO hay modelo ni Blender. Excepción:
  desde rpi5 `sudo systemctl start bc2501-enciende` despierta en ~30 s.

## 2. ACCESOS (secretos NUNCA en el repo: ver ACCESOS_LOCAL.md en rpi5 o preguntar al owner)
- WAN: ssh -p 8022 txurtxil@www.mundaka.net (bc250-1). WAN intermitente:
  reintentar; para ficheros usar base64 por trozos de 200k, no scp (stall PLC).
- rpi5: ssh -p 7022 txurtxil@www.mundaka.net (forward EFÍMERO, app del owner).
- LAN interna: desde rpi5 a bc250-1 por clave ssh (alias bc250 en ~/.ssh/config).
- GitHub: token en rpi5 ~/.git-credentials. API key llama: mission/.apikey.
- Si el 8022 cae (WAN flaky por momentos), trabajar vía salto: sandbox→rpi5
  (7022)→bc250-1 (ssh -o BatchMode=yes bc250 '...'). Comandos CORTOS por
  celda; no pkill -f anidado entre comillas dobles (usar [p]atrón).

## 3. CÓMO LANZAR MISIONES (tres vías)
1) BOT Telegram → @TxurtxilOpenClaw_bot:
   `/mision3d Caja 100x70x30 mm, pared 2 mm`  (parser regex LxWxH+pared)
2) API rpi5:  POST http://192.168.10.140:8201/mission3d {"brief": "..."}
   → GET /mission3d/{id} y /mission3d/{id}/report
3) DIRECTO (misiones con json propio, ej. petrolero):
   bc250-1: cd ~/cluster-3d-pipeline/mission && python3 mission_loop.py <mision>.json
   (lanzar con setsid/nohup; NUNCA 'ssh host "cmd &"')

## 4. FORMATO DE MISIÓN (mission/*.json)
{"mission_id", "brief", "generator": "gen_X.py" (opcional, default gen_box),
 "measurer": "measure_X.py" (¡OBLIGATORIO si no es caja! el loop defaultea
 a measure_box.py y medirá el modelo EQUIVOCADO: wall_min=0.768, PARTS=0.768),
 "hard": {"CLAVE": {"value": X, "tol": Y}, ...},
 "max_iters": N, "injected_initial": {...} (ancla la unidad: evita que el
 LLM proponga params que gatillen auto-scale del generador → modelo de 2 mm)}
CLAVEs válidas: L, B, H, WALL, PARTS, UNIQ + náuticas (ver §6).
manifold: require_manifold=true solo si se exige STL cerrado; los modelos
actuales heredan 116-140 bad_edges de estilo → require_manifold=false.

## 5. GENERADORES (mission/gen_*.py; invocación idéntica)
blender -b --factory-startup -P gen_X.py -- params.json out.blend out.stl
- gen_box/measure_box: caja LxWxH pared WALL (ray-cast 4 caras, manifold).
- gen_tower v5: torre procedural; perfiles "resin"/"eiffel"; normalización
  afín a [0,H] (TOWER_ROOT).
- gen_clone/measure_clone: RUTA B — clon por KIT (kit_eiffel.json, 2.2 MB;
  315 piezas/34 únicas del Eiffel_Resin). Cuando hay referencia, REUTILIZAR.
- gen_tanker/measure_tanker v2: PETROLERO línea V1 (legacy; unidad corregida).
- gen_petrolero_v3/measure_tanker: PETROLERO LÍNEA ACTUAL (V3). Linaje en
  models/petrolero_v2 y models/petrolero_v3 (HULL_V3_FIX.md: wl por estación,
  sección manga-en-flotación V3.1, gradines V3.2, ojos de buey V3.3, 533
  piezas, watertight por objeto). ¡NO usar entregables/petrolero_250mm.*: es
  la línea V1 vieja (generada antes del fix del casco)!

## 6. CONVENCIONES DEL PETROLERO (línea V3 = actual; unidad PASS 2026-10-10)
- Línea V1 (legacy): L=260.915, B=42.84, H=78.0, PARTS=361, draft=13.75,
  freeboard=19.0, hull_volume_mm3=110905.9, displacement_kg=0.114.
- Línea V3 (actual): L=260.387, B=40.7, H=66.6, PARTS=533, draft=13.75,
  freeboard=18.65, hull_volume_mm3=98975.8, displacement_kg=0.101.
  bad_edges global=140 (aristas compartidas entre piezas vecinas; los
  462/462 watertight del informe V3 son POR OBJETO, métricas distintas).
- measure_tanker v2 sirve para ambas líneas (draft=−z_min global;
  freeboard=z_min de "Cubierta"; volumen=anillos de estación z≤0.5mm +
  sólidos watertight sumergidos). Casco V3: wl por estación, convexo.
- measure_tanker v2: draft=−z_min global; freeboard=z_min de "Cubierta";
  volumen=anillos de estación de Casco_obra_viva (z≤0.5mm) por shoelace
  convexo + sólidos watertight sumergidos; tapas proa/pop abiertas excluidas.
- mission_loop evaluate lee constraints de dims, counts Y nautical (fix
  commit 474c866; antes daba UNKNOWN a draft/freeboard/volumen/displacement).

## 7. LECCIONES CRÍTICAS (no releerlas por las malas)
- LLM del loop: temperature 0, n_predict 1600 y OBLIGATORIO
  chat_template_kwargs {"enable_thinking": false}. El thinking quema el
  presupuesto → content vacío (finish=length).
- Medir por VÉRTICES del mesh evaluado, nunca bound_box (cilindro rotado:
  bbox=×√2). Validar cada métrica nueva contra sintético conocido.
- El planificador NO arregla bugs del generador: bug de código → fix en
  código; la unidad se recalibra DESPUÉS del fix.
- STL binario: cabecera ASCII de 80 bytes (algunos visores rechazan NULOS).
- pkill -f "patrón" se automata (mata la sesión ssh propia): usar [p]atrón.
- Subir/editar código remoto: base64 por stdin; printf con escapes anidados
  corrompe JSON.
- El sandbox del agente se REINICIA entre turnos: re-crear helpers ssh
  (SSH_ASKPASS trick) cada turno.
- GitHub: token en rpi5 ~/.git-credentials (usuario txurtxil).

## 8. RUTINA ÚTIL
bc250-1:
  tail -f ~/cluster-3d-pipeline/mission/runs/<id>/mission.log
  ~/venvs/metrology/bin/python ~/cluster-3d-pipeline/metrology/test_metrology.py → METROLOGY_PASS
rpi5: curl -s http://127.0.0.1:8201/health  → {"bc250-1":["UP","LOOP_OK"]}
## 9. EMERGENCIA MEMORIA
- La placa tiene 14 GB unificados; el cerebro (30B-A3B IQ3_XXS, 12.9 GB)
  deja ~2 GB. SI se bloquea por memoria: tras reboot, UN comando: stopO
  (/usr/local/sbin/stopO: para+deshabilita llama-node1). Volver: startO.
- Config sana del servicio: -c 16384 (16k ctx). Maximo probado: 32768.
  49152 NO cabe (fallo radv "Failed to allocate a buffer" en bucle).
