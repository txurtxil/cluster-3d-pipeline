# REPORT

MISSION: taza_h_7_112546 api-8201
INPUT: Taza: H=7, D_OUT=90, WALL=3, BOTTOM=4, RIM_R=1, HANDLE_D=9, HANDLE_Z_LOW=30, HANDLE_Z_HIGH=68, HANDLE_REACH=24

## HARD CONSTRAINTS
{
 "H": {
  "value": 7.0,
  "tol": 0.5
 },
 "D_body": {
  "value": 90.0,
  "tol": 0.5
 },
 "WALL": {
  "value": 3.0,
  "tol": 0.15
 }
}

## FINAL PARAMETERS
{
 "H": 7.0,
 "D_OUT": 90.0,
 "WALL": 3.0,
 "BOTTOM": 4.0,
 "RIM_R": 1.0,
 "HANDLE_D": 9.0,
 "HANDLE_Z_LOW": 30.0,
 "HANDLE_Z_HIGH": 68.0,
 "HANDLE_REACH": 24.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "H": 36.338,
  "D_body": null,
  "WALL": null
 },
 "D_body": null,
 "D_total_con_asa": 117.0,
 "H": 36.338,
 "wall": null,
 "D_int": null,
 "inner_depth": 29.919,
 "capacity_ml_aprox": null,
 "manifold": {
  "ok": false
 },
 "components": 1,
 "not_measured": [
  "redondeo del filete"
 ]
}

## ITERATIONS
total: 2
## ROLLBACKS
v0.1: sin rollback multi-version (una version por iteracion, nunca se sobrescribe)

## UNKNOWN / NOT_MEASURED
[]

## WARNINGS
Inyeccion inicial de fallo (test del loop)

## PRINTABILITY
manifold: {'ok': False}
STL exportado y hash SHA256 registrado por version

VERDICT: FAIL
REASON: PLATEAU parametro-repetido iter 2
