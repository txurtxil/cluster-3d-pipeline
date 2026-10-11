# REPORT

MISSION: caja_120x80x40_mm_192107 api-8201
INPUT: Caja 120x80x40 mm, pared 3 mm

## HARD CONSTRAINTS
{
 "L": {
  "value": 120.0,
  "tol": 0.2
 },
 "W": {
  "value": 80.0,
  "tol": 0.2
 },
 "H": {
  "value": 40.0,
  "tol": 0.2
 },
 "WALL": {
  "value": 3.0,
  "tol": 0.15
 }
}

## FINAL PARAMETERS
{
 "L": 120.0,
 "W": 80.0,
 "H": 40.0,
 "WALL": 3.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "L": 120.0,
  "W": 80.0,
  "H": 40.0
 },
 "walls": {
  "-X": 3.0,
  "+X": 3.0,
  "-Y": 3.0,
  "+Y": 3.0
 },
 "wall_min": 3.0,
 "wall_max": 3.0,
 "manifold": {
  "ok": true,
  "bad_edges": 0,
  "components": 1
 },
 "NOT_MEASURED": [
  "holes_count",
  "usbc_dims",
  "normals_orientation"
 ]
}

## ITERATIONS
total: 1
## ROLLBACKS
v0.1: sin rollback multi-version (una version por iteracion, nunca se sobrescribe)

## UNKNOWN / NOT_MEASURED
["holes_count", "usbc_dims", "normals_orientation"]

## WARNINGS
Inyeccion inicial de fallo (test del loop)

## PRINTABILITY
manifold: {'ok': True, 'bad_edges': 0, 'components': 1}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
