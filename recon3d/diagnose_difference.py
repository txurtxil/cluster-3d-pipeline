#!/usr/bin/env python3
# diagnose_difference.py <metrics.json> <salida.json> [--vlm ref.png render.png diff.png]
# Motor de reglas sobre metricas OBJETIVAS -> diagnosis.json estructurado.
# VLM opcional: SOLO diagnostico (identifica diferencias), nunca valida solo.
import sys, json

m = json.load(open(sys.argv[1])); out_path = sys.argv[2]
th = m["convergence_thresholds"]
errors = []

def add(region, etype, severity, param, direction, evidence):
    errors.append(dict(region=region, type=etype, severity=round(min(severity, 1.0), 2),
                       estimated_correction=dict(parameter=param, direction=direction),
                       evidence=evidence))

if m["bbox_width_err"] > th["bbox_err_max"]:
    add("global", "object_too_wide" if m["zones"]["zone_1"]["width_render"] > m["zones"]["zone_1"]["width_ref"] else "object_too_narrow",
        m["bbox_width_err"]/0.20, "W_SCALE", "decrease" if m["zones"]["zone_1"]["width_render"] > m["zones"]["zone_1"]["width_ref"] else "increase",
        "bbox_width_err=%.3f" % m["bbox_width_err"])

for i in range(1, 6):
    z = m["zones"]["zone_%d" % i]
    if z["width_err"] is not None and z["width_err"] > th["zone_width_err_max"]:
        region = {1: "base", 2: "lower_body", 3: "middle", 4: "upper_platform", 5: "top"}[i]
        param = {1: "BASE_WIDTH", 2: "P2_WIDTH", 3: "MID_WIDTH", 4: "UPPER_SHAFT_WIDTH", 5: "TOP_WIDTH"}[i]
        direction = "decrease" if z["width_render"] > z["width_ref"] else "increase"
        add(region, "zone_width_mismatch", z["width_err"]/0.25, param, direction,
            "zone_%d width_ref=%d width_render=%d" % (i, z["width_ref"], z["width_render"]))

if m["silhouette_iou"] < th["iou_min"]:
    add("global", "silhouette_mismatch", (th["iou_min"]-m["silhouette_iou"])/0.25, "SILHOUETTE", "fit",
        "iou=%.3f" % m["silhouette_iou"])
if m["contour_error_px"] > th["contour_px_max"]:
    add("global", "contour_deviation", m["contour_error_px"]/20.0, "CONTOUR", "fit",
        "contour_error_px=%.1f" % m["contour_error_px"])
if m["center_axis_error"] > th["axis_err_max"]:
    add("global", "axis_or_camera_offset", m["center_axis_error"]/0.10, "CAMERA_TARGET_X", "fit_first",
        "center_axis_error=%.3f" % m["center_axis_error"])
od = m["openings"]["area_delta_pct"]
if abs(od) > th["opening_area_delta_max"]:
    # LEY DEL PLATEAU (detectado en run autonomo 2026-10-02): si el render tiene
    # MENOS huecos que la referencia, la causa es la CELOSIA que los rellena ->
    # palanca LATTICE_DENSITY. ARCH_WIDTH solo si el recuento de huecos coincide
    # (el arco en si es demasiado pequeno).
    if m["openings"]["count_render"] < m["openings"]["count_ref"]:
        add("openings", "openings_filled_by_lattice",
            abs(od)/60.0, "LATTICE_DENSITY", "decrease" if od < 0 else "increase",
            "opening area delta=%+.1f%% counts %d vs %d" % (od, m["openings"]["count_render"], m["openings"]["count_ref"]))
    else:
        add("openings", "openings_too_small" if od < 0 else "openings_too_large",
            abs(od)/60.0, "ARCH_WIDTH", "increase" if od < 0 else "decrease",
            "opening area delta=%+.1f%% counts %d vs %d" % (od, m["openings"]["count_render"], m["openings"]["count_ref"]))
if m["openings"]["count_render"] > m["openings"]["count_ref"]:
    add("lattice", "excess_lattice_or_filled_openings",
        min(1.0, 0.3*(m["openings"]["count_render"]-m["openings"]["count_ref"])),
        "LATTICE_DENSITY", "decrease",
        "openings render=%d ref=%d" % (m["openings"]["count_render"], m["openings"]["count_ref"]))

vlm_out = None
if "--vlm" in sys.argv:
    i = sys.argv.index("--vlm")
    from vlm_client import ask
    prompt = ("Compara A (referencia) y B (render). Lista SOLO diferencias geométricas "
              "observables (silueta, anchuras, plataformas, huecos, eje). Responde JSON: "
              '{"errors":[{"region":"...","type":"...","severity":0-1}]}')
    try:
        raw = ask(prompt, sys.argv[i+1:i+4], max_tokens=300)
        vlm_out = json.loads(raw.strip().strip("`").replace("json\n", "", 1))
    except Exception as e:
        vlm_out = dict(error=str(e)[:200])

out = dict(source="image_metrics" if not vlm_out else "metrics+vlm",
           errors=errors, vlm=vlm_out,
           convergence=not errors)
json.dump(out, open(out_path, "w"), indent=1)
print("DIAGNOSE_OK errors=%d converged=%s" % (len(errors), not errors))
