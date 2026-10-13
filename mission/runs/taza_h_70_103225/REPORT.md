# REPORT

MISSION: taza_h_70_103225 api-8201
INPUT: Taza: H=70, D_OUT=70, WALL=3, BOTTOM=4, RIM_R=1, HANDLE_D=9, HANDLE_Z_LOW=30, HANDLE_Z_HIGH=68, HANDLE_REACH=24

## HARD CONSTRAINTS
{
 "H": {
  "value": 70.0,
  "tol": 0.5
 },
 "D_body": {
  "value": 70.0,
  "tol": 0.5
 },
 "WALL": {
  "value": 3.0,
  "tol": 0.15
 }
}

## FINAL PARAMETERS
{
 "H": 67.0,
 "D_OUT": 70.0,
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
  "H": 72.964,
  "D_body": 70.0,
  "WALL": 3.0
 },
 "D_body": 70.0,
 "D_total_con_asa": 97.0,
 "H": 72.964,
 "wall": 3.0,
 "D_int": 64.0,
 "inner_depth": 68.964,
 "capacity_ml_aprox": 221.9,
 "manifold": {
  "ok": false
 },
 "components": 1,
 "not_measured": [
  "redondeo del filete"
 ]
}

## ITERATIONS
total: 5
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
REASON: PLATEAU parametro-repetido iter 5
