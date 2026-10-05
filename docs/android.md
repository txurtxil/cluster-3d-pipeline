# Android — Herramienta de mando del cluster 3D (Nexus)

Fecha: 2026-10-05 · Estado: FASE 1 verificada (API), FASE 2 en diseño (Nexus).

## Arquitectura

```
[Nexus Android] --HTTPS/api-key--> [cluster-api :8200 rpi5] --ssh--> [z1: Blender 4.2.23 / recon3d / VLM]
                                            |
                                            +--ssh--> [bc250: Qwen3-Coder-30B :8081]
```

- **cluster-api** (`cluster-api/cluster_api.py`, FastAPI): wrapper FINO sobre lo probado.
  No reinventa nada: lanza `mision_3d.sh` con setsid, retransmite `pipeline_health.py`,
  delega la vision en `recon3d/analyze_reference.py` (venv-recon en z1).
- **Auth**: header `X-Api-Key` == `recon3d/config/services.json auth.api_key`
  (config unica; cluster-api la sincroniza de z1 al arrancar).
- OpenClaw :18789 queda como canal de chat/operaciones (WS), NO como backend de la app.

## API (todas verificadas con tests de punta a punta el 2026-10-05)

| Endpoint | Descripcion |
|---|---|
| `GET /health` | Salud del pipeline (9 filas: SSH_Z1, SSH_BC250, CONFIG, CODER, VLM, BLENDER, SFTP, STORAGE, RPI5_LAN). VLM/RPI5 opcionales. |
| `GET /gens` | Lista generadores disponibles (`gen_*.py` en `~/pipeline3d`). |
| `POST /mission` | `{name, gen, ask?}` -> `run_id`. Whitelist `gen_[A-Za-z0-9_]+.py`, basename-only anti-path. setsid + state.json + api.log + exitcode. |
| `GET /missions` | Lista de runs. |
| `GET /mission/{run_id}` | RUNNING/DONE/FAILED real (exitcode) + bbox + verificacion + juez + log_tail. |
| `GET /artifacts/{run_id}` | Lista con sha256 de cada fichero. |
| `GET /artifacts/{run_id}/{file}` | Descarga (anti path-traversal). sha256 extremo a extremo verificado. |
| `POST /reference` | Foto (multipart) -> z1 -> `analyze_reference.py` -> `REFERENCE_GEOMETRY.json` (bbox, silueta, openings, platforms, keypoints...). |

## Reglas del cluster (aplicadas y verificadas)

1. recon3d/vision en z1 -> **venv `~/.venv-recon/bin/python`** (OpenCV 5.0, NumPy 2.5, SciPy 1.18, paramiko).
   Todo lo que toca bpy -> **Blender headless** (python interno). Nunca mezclar.
2. Copias LAN: sha256 extremo a extremo siempre (leccion 6).
3. Descargas: tamaño + magica GGUF; marcadores `*.done` sin verificacion NO valen
   (incidente 2026-10-05: `dl.done` falso, `~/models/vlm/` vacio -> VLM legacy vivo 3 dias).
4. ssh en background: setsid + redireccion completa; ojo `pkill -f <patron>`: el patron
   casa con el propio shell remoto (autokill). Comillas anidadas: todo script por base64.
5. `pipeline_health.py` funciona dentro y fuera de la LAN (deteccion por TCP al coder).
   Requiere clave SSH del ejecutor autorizada en z1 **y** bc250.
6. VLM bajo demanda: `start_vlm_z1.sh` / `stop_vlm_z1.sh` en z1. Modelo vigente:
   Qwen3VL-8B-Instruct-Q4_K_M.gguf (en `~/models/vlm/`, verificado 2026-10-05).

## FASE 2 — Cliente Android: Nexus

Base: https://github.com/txurtxil/Nexus (adaptar/simplificar/unir, no reescribir).
Decision: PWA instalable (sin Play Store) con envoltura TWA opcional; Tasker+HTTP como
arranque cero-dev. Notificaciones: Telegram (bot ya operativo) o Web Push.
Visor: GLB (`wm.gltf_export`) + `<model-viewer>`; fallback Fast STL Viewer.


## Endpoints VLM (FASE 2-A, verificados 2026-10-05)

| Endpoint | Descripcion |
|---|---|
| `GET /vlm/status` | VLM UP/DOWN + modelo cargado vs esperado (services.json). |
| `POST /vlm/ask` | `{image_b64, prompt}` -> wake bajo demanda (~40s si DOWN) + respuesta Qwen3-VL-8B. El movil nunca habla con z1:8084 directo (escucha en 127.0.0.1 y es secuencial con Blender). |

Verificacion: status OK (modelo correcto), ask con imagen sintetica (descripcion exacta),
wake-on-demand de punta a punta (VLM parado -> ask -> woken:true -> respuesta correcta en 43s).
