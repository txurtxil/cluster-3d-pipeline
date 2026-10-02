# cluster-3d-pipeline
Pipeline 3D del cluster Txurtxil: generacion parametrica bpy (z1, Blender 4.2.23),
metricas objetivas OpenCV (recon3d), VLM bajo demanda (Qwen3-VL-8B @ z1:8084),
Coder (Qwen3-Coder-30B @ bc250:8081), orquestacion OpenClaw (rpi5).

## Contenido
- pipeline3d/ — generadores (bracket, soporte, chasis BC-250, torre, petrolero V1/V2),
  mision_3d.sh, render/bbox/STL/export_parts, specs y prompts de arranque.
- recon3d/ — vision: analyze/compare/diagnose/optimize/run_iteration,
  camera_calibration (CAMERA_LOCK), GAIN con mark_inactive, config/services.json,
  vlm_client unico, sftp_transfer sin paramiko, pipeline_health.
- iterations/ — PETROLERO_STRESS_TEST_FINAL (run1/run2): infraestructura verificada
  (pipeline GREEN; geometria reproducible bit-a-bit, orden de serializacion documentado).
- models/petrolero_v2/ — PETROLERO_QUALITY_V2: 458 objetos, manifold 100%,
  tanker_confidence 0.95 (Qwen3-VL-8B). V1 en models/petrolero_v1.

Regla de oro: el LLM propone, Blender construye, las metricas deciden.
