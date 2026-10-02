#!/usr/bin/env python3
# run_iteration.py <project_dir> [--max N]
# Gestor de iteraciones: referencia -> render -> compare -> diagnose -> optimize.
# Cada iteracion queda en iterations/iteration_NNN/ con parameters.json, metrics.json,
# diagnosis.json, renders. Rollback automatico si metrics empeoran.
import sys, json, os, shutil, subprocess

proj = sys.argv[1]
max_iter = int(sys.argv[sys.argv.index("--max")+1]) if "--max" in sys.argv else 10
ref = os.path.join(proj, "reference", "reference.png")
blend = os.path.join(proj, "current.blend")
state_p = os.path.join(proj, "state.json")
R = "~/recon3d"
venv = "~/.venv-recon/bin/python"
blender = "~/blender/blender"
params_p = os.path.join(proj, "parameters.json")

state = json.load(open(state_p)) if os.path.exists(state_p) else dict(iteration=0)
for it in range(state["iteration"]+1, state["iteration"]+max_iter+1):
    it_dir = os.path.join(proj, "iterations", "iteration_%03d" % it)
    os.makedirs(it_dir, exist_ok=True)
    # 1. render del modelo actual (cámara calibrada fija si existe camera.json)
    cam_args = []
    if os.path.exists(os.path.join(proj, "camera.json")):
        cam_args = ["--camera", os.path.join(proj, "camera.json")]
    subprocess.run([os.path.expanduser(blender), "-b", blend, "-P",
                    os.path.expanduser(R+"/render_model.py"), "--",
                    os.path.join(it_dir, "render.png")] + cam_args, check=True)
    # 2. metricas objetivas
    subprocess.run([os.path.expanduser(venv), os.path.expanduser(R+"/compare_images.py"),
                    ref, os.path.join(it_dir, "render.png"), it_dir], check=True)
    m = json.load(open(os.path.join(it_dir, "metrics.json")))
    # ===== PHASE 0 — CAMERA_LOCK (brief 2026-10-02) =====
    # Si la geometria de huecos no coincide (recuento+posicion+area), el bloqueo
    # esta en la CAMARA, no en la geometria: calibrar y NO tocar parametros.
    lock = m["openings"]["geometry"]["combined"]
    locked = lock >= m.get("camera_lock_threshold", 0.60) and not state.get("camera_locked")
    if not locked:
        state["camera_locked"] = False
        print("CAMERA_NOT_LOCKED iter %d (holes_combined=%.2f < %.2f) -> calibrando camara"
              % (it, lock, m.get("camera_lock_threshold", 0.60)))
        subprocess.run([os.path.expanduser(venv), os.path.expanduser(R+"/camera_calibration.py"),
                        ref, blend, os.path.join(proj, "camera.json"), "--budget", "14"],
                       check=True)
        state["prev_metrics"] = state.get("last_metrics")
        state["last_metrics"] = m
        continue
    if not state.get("camera_locked"):
        state["camera_locked"] = True
        print("CAMERA_LOCKED iter %d (holes_combined=%.2f)" % (it, lock))
    # 3. rollback si empeora
    prev = state.get("last_metrics")
    if prev and m["silhouette_iou"] < prev["silhouette_iou"] - 0.01:
        bak = os.path.join(proj, "iterations", "iteration_%03d" % (it-1), "parameters.json")
        if os.path.exists(bak):
            shutil.copy(bak, params_p)
        state["rollback"] = state.get("rollback", 0)+1
        print("ROLLBACK iter %d (iou %.3f < %.3f)" % (it, m["silhouette_iou"], prev["silhouette_iou"]))
        continue
    state["prev_metrics"] = state.get("last_metrics")
    state["last_metrics"] = m
    # 4. diagnostico + correccion parametrica
    subprocess.run([os.path.expanduser(venv), os.path.expanduser(R+"/diagnose_difference.py"),
                    os.path.join(it_dir, "metrics.json"),
                    os.path.join(it_dir, "diagnosis.json")], check=True)
    shutil.copy(params_p, os.path.join(it_dir, "parameters.json"))
    d = json.load(open(os.path.join(it_dir, "diagnosis.json")))
    if d["convergence"]:
        print("CONVERGED iter %d iou=%.3f" % (it, m["silhouette_iou"]))
        break
    subprocess.run([os.path.expanduser(venv), os.path.expanduser(R+"/optimize_parameters.py"),
                    params_p, os.path.join(it_dir, "diagnosis.json"), state_p, it_dir], check=True)
    # 5. REGENERACION PARAMETRICA: gen_tower_v13.py lee parameters.json y
    #    reescribe current.blend SIN reescribir el generador (mision 3)
    subprocess.run([os.path.expanduser(blender), "-b", "--factory-startup", "-P",
                    os.path.expanduser(R+"/gen_tower_v13.py"), "--", blend,
                    "--params", params_p], check=True)
    print("ITER %d done iou=%.3f errors=%d" % (it, m["silhouette_iou"], len(d["errors"])))
state["iteration"] = it
json.dump(state, open(state_p, "w"), indent=1)
print("ITERATION_MANAGER_OK")
