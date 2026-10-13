# REPORT

MISSION: taza_parametrica_h_184611 api-8201
INPUT: Taza parametrica: H=95, D_OUT=90, WALL=3, BOTTOM=4, RIM_R=1, HANDLE_D=9, HANDLE_Z_LOW=30, HANDLE_Z_HIGH=68, HANDLE_REACH=24

## HARD CONSTRAINTS
{
 "H": {
  "value": 95.0,
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
 "H": 95.0,
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
  "H": 95.0,
  "D_body": 90.0,
  "WALL": 3.0
 },
 "D_body": 90.0,
 "D_total_con_asa": 117.0,
 "H": 95.0,
 "wall": 3.0,
 "D_int": 84.0,
 "inner_depth": 91.0,
 "capacity_ml_aprox": 504.3,
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
