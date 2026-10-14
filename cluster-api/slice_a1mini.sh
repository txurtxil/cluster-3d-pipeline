#!/bin/bash
# slice_a1mini.sh <stl> [outdir] - corta para Bambu A1 Mini 0.4 + PETG Bambu Basic
# Requiere: /tmp/squashfs-root (Orca 2.4.2 extraido), xvfb, libwebkit2gtk-4.1
set -e
STL="$1"; OUT="${2:-/tmp/slice}"
R=/tmp/squashfs-root/resources/profiles/BBL
mkdir -p "$OUT"; cd "$OUT"
BASE=$(basename "$STL")
cp "$STL" "$BASE"
xvfb-run -a /tmp/squashfs-root/AppRun \
  --load-settings "$R/machine/Bambu Lab A1 mini 0.4 nozzle.json;$R/process/0.20mm Standard @BBL A1M.json" \
  --load-filaments "$R/filament/Bambu PETG Basic @BBL A1M 0.4 nozzle.json" \
  --slice 0 --outputdir "$OUT" "$BASE"
ls "$OUT"/plate_1.gcode
