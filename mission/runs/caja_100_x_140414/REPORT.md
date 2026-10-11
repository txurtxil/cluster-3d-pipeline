# REPORT

MISSION: caja_100_x_140414 api-8201
INPUT: Caja 100 x 70 x 30 mm, pared 2 mm

## HARD CONSTRAINTS
{
 "L": {
  "value": 100.0,
  "tol": 0.2
 },
 "W": {
  "value": 70.0,
  "tol": 0.2
 },
 "H": {
  "value": 30.0,
  "tol": 0.2
 },
 "WALL": {
  "value": 2.0,
  "tol": 0.15
 }
}

## FINAL PARAMETERS
{
 "L": 100.0,
 "W": 70.0,
 "H": 30.0,
 "WALL": 2.0,
 "RIM_R": 0.0,
 "HOLE_D": 0.0,
 "HOLE_MARGIN": 0.0,
 "USBC_W": 0.0,
 "USBC_H": 0.0,
 "USBC_Z": 0.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "L": 100.0,
  "W": 70.0,
  "H": 30.0
 },
 "walls": {
  "-X": 2.0,
  "+X": 2.0,
  "-Y": 2.0,
  "+Y": 2.0
 },
 "wall_min": 2.0,
 "wall_max": 2.0,
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
ninguna

## PRINTABILITY
manifold: {'ok': True, 'bad_edges': 0, 'components': 1}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
