# REPORT

MISSION: caja_usb_length_183346 api-8201
INPUT: Caja usb: LENGTH=120, WIDTH=80, HEIGHT=35, WALL=2.5, COMP_X=3, COMP_Y=2, DIVIDER_W=2, DEPTH=20, TAB_W=8, TAB_T=1.2, CHAMFER=0.5

## HARD CONSTRAINTS
{
 "H_body": {
  "value": 35.0,
  "tol": 0.5
 },
 "wall": {
  "value": 2.5,
  "tol": 0.5
 },
 "compartments_x": {
  "value": 3.0,
  "tol": 0.5
 },
 "compartments_y": {
  "value": 2.0,
  "tol": 0.5
 }
}

## FINAL PARAMETERS
{
 "LENGTH": 120.0,
 "WIDTH": 80.0,
 "HEIGHT": 35.0,
 "WALL": 2.5,
 "COMP_X": 3.0,
 "COMP_Y": 2.0,
 "DIVIDER_W": 2.0,
 "DEPTH": 20.0,
 "TAB_W": 8.0,
 "TAB_T": 1.2,
 "CHAMFER": 0.5
}

## METRICS (ultima version medida)
{
 "dims": {
  "L_body": 120.0,
  "W": 82.7,
  "H_body": 35.0,
  "H_total": 39.5,
  "wall": 2.5,
  "compartments_x": 3.0,
  "compartments_y": 2.0,
  "compartments": 6.0
 },
 "manifold": {
  "ok": true
 },
 "components": 21,
 "not_measured": [
  "fuerza del snap (verificacion fisica al imprimir)",
  "W incluye pestanas de la tapa; L_body es el cuerpo",
  "compartimentos por autoridad de diseno (objetos div_*)"
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
