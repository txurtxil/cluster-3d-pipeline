#!/usr/bin/env python3
# optimize_parameters.py <parameters.json> <diagnosis.json> <state.json> <out_dir>
# Correccion PARAMETRICA con historial, rollback y estrategia coarse->fine.
# Escribe PARAMETER_CORRECTION.json por correccion y parameters.json actualizado.
import sys, json, os

params_p, diag_p, state_p, out_dir = sys.argv[1:5]
os.makedirs(out_dir, exist_ok=True)
params = json.load(open(params_p))
diag = json.load(open(diag_p))
state = json.load(open(state_p)) if os.path.exists(state_p) else dict(
    iteration=0, history=[], param_history={}, last_metrics=None)
state["iteration"] += 1

STEP_COARSE, STEP_FINE = 0.10, 0.03
PLATEAU_EPS = 0.003


def snap(m):
    """Snapshot reducido de metricas para el bloque gain."""
    if not m:
        return None
    return dict(
        iou=m.get("silhouette_iou"),
        holes=(m.get("openings", {}).get("geometry", {}) or {}).get("combined"),
        bbox_err=m.get("bbox_width_err"))


def step_for(param):
    return STEP_FINE if len(state["param_history"].get(param, [])) >= 2 else STEP_COARSE


def mark_inactive(param, reason):
    if param not in state.setdefault("inactive_params", []):
        state["inactive_params"].append(param)
        print("PARAM_INACTIVE %s: %s" % (param, reason))

corrections = []
inactive = set(state.get("inactive_params", []))
for err in diag.get("errors", []):
    p = err["estimated_correction"]["parameter"]
    if p == "CAMERA_TARGET_X" or p in ("SILHOUETTE", "CONTOUR"):
        corrections.append(dict(parameter=p, action="deferred_to_camera_phase",
                                reason=err["type"]))
        continue
    if p in inactive:
        # mark_parameter_as_inactive (brief): sin causalidad demostrada -> no
        # gastar iteraciones en el; se reactiva solo si otra metrica lo pide
        corrections.append(dict(parameter=p, action="skipped_inactive", reason=err["type"]))
        continue
    if p not in params:
        params[p] = 1.0
    old = params[p]
    st = step_for(p)
    if err["estimated_correction"]["direction"] == "increase":
        new = old*(1+st)
    elif err["estimated_correction"]["direction"] == "decrease":
        new = old*(1-st)
    else:
        continue
    params[p] = round(new, 4)
    # bloque GAIN completo: metric_before/after, gain por metrica, effective, plateau
    m_before = snap(state.get("prev_metrics"))
    m_after = snap(state.get("last_metrics"))
    gain = {}
    if m_before and m_after:
        for k in ("iou", "holes"):
            if m_before.get(k) is not None and m_after.get(k) is not None:
                gain[k] = round(m_after[k]-m_before[k], 4)
        if m_before.get("bbox_err") is not None and m_after.get("bbox_err") is not None:
            gain["bbox"] = round(-(m_after["bbox_err"]-m_before["bbox_err"]), 4)
    effective = round(0.7*gain.get("iou", 0.0)+0.3*gain.get("holes", 0.0), 4)
    plateau = abs(effective) < PLATEAU_EPS
    rec = dict(parameter=p, old_value=old, new_value=params[p],
               reason=err["type"], source="image_metrics", region=err["region"],
               severity=err["severity"],
               metric_before=m_before, metric_after=m_after,
               gain=gain, effective_gain=effective, plateau=plateau)
    corrections.append(rec)
    hist = state["param_history"].setdefault(p, [])
    hist.append(dict(iter=state["iteration"], old=old, new=params[p], effective_gain=effective))
    if len(hist) >= 2 and all(abs(h.get("effective_gain", 0)) < PLATEAU_EPS for h in hist[-2:]):
        mark_inactive(p, "2 correcciones con |effective_gain| < %g" % PLATEAU_EPS)

json.dump(params, open(params_p, "w"), indent=1)
json.dump(corrections, open(os.path.join(out_dir, "PARAMETER_CORRECTION.json"), "w"), indent=1)
state["history"].append(dict(iteration=state["iteration"], corrections=len(corrections),
                             errors=len(diag.get("errors", []))))
json.dump(state, open(state_p, "w"), indent=1)
print("OPTIMIZE_OK iter=%d corrections=%d" % (state["iteration"], len(corrections)))
