# REPORT

MISSION: caja_90_x_180608 api-8201
INPUT: Caja 90 x 60 x 25 mm, pared 2 mm

## HARD CONSTRAINTS
{
 "L": {
  "value": 90.0,
  "tol": 0.2
 },
 "W": {
  "value": 60.0,
  "tol": 0.2
 },
 "H": {
  "value": 25.0,
  "tol": 0.2
 },
 "WALL": {
  "value": 2.0,
  "tol": 0.15
 }
}

## FINAL PARAMETERS
{
 "L": 90.0,
 "W": 60.0,
 "H": 25.0,
 "WALL": 2.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "L": 90.0,
  "W": 60.0,
  "H": 25.0
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
Inyeccion inicial de fallo (test del loop)

## PRINTABILITY
manifold: {'ok': True, 'bad_edges': 0, 'components': 1}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
