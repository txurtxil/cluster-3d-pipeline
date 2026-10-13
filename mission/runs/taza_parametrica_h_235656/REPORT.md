# REPORT

MISSION: taza_parametrica_h_235656 api-8201
INPUT: Taza parametrica: H=110, D_OUT=85, WALL=2.5, BOTTOM=4, RIM_R=1, HANDLE_D=8, HANDLE_Z_LOW=35, HANDLE_Z_HIGH=80, HANDLE_REACH=26

## HARD CONSTRAINTS
{
 "H": {
  "value": 110.0,
  "tol": 0.5
 },
 "D_body": {
  "value": 85.0,
  "tol": 0.5
 },
 "WALL": {
  "value": 2.5,
  "tol": 0.15
 }
}

## FINAL PARAMETERS
{
 "H": 110.0,
 "D_OUT": 85.0,
 "WALL": 2.5,
 "BOTTOM": 4.0,
 "RIM_R": 1.0,
 "HANDLE_D": 8.0,
 "HANDLE_Z_LOW": 35.0,
 "HANDLE_Z_HIGH": 80.0,
 "HANDLE_REACH": 26.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "H": 110.0,
  "D_body": 85.0,
  "WALL": 2.5
 },
 "D_body": 85.0,
 "D_total_con_asa": 113.5,
 "H": 110.0,
 "wall": 2.5,
 "D_int": 80.0,
 "inner_depth": 106.0,
 "capacity_ml_aprox": 532.8,
 "manifold": {
  "ok": true
 },
 "components": 1,
 "not_measured": [
  "redondeo del filete"
 ]
}

## ITERATIONS
total: 1
## ROLLBACKS
v0.1: sin rollback multi-version (una version por iteracion, nunca se sobrescribe)

## UNKNOWN / NOT_MEASURED
[]

## WARNINGS
Inyeccion inicial de fallo (test del loop)

## PRINTABILITY
manifold: {'ok': True}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
