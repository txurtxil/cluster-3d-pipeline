# REPORT

MISSION: caja_roscada_diam_152622 api-8201
INPUT: Caja roscada: DIAM=60, HEIGHT=50, WALL=3, THREAD_PITCH=4, LID_HEIGHT=12, SEAL_GROOVE=0, CHAMFER=0.5

## HARD CONSTRAINTS
{
 "D_body": {
  "value": 60.0,
  "tol": 0.5
 },
 "H": {
  "value": 50.0,
  "tol": 0.5
 },
 "wall": {
  "value": 3.0,
  "tol": 0.5
 },
 "thread_pitch": {
  "value": 4.0,
  "tol": 0.5
 },
 "lid_height": {
  "value": 12.0,
  "tol": 0.5
 }
}

## FINAL PARAMETERS
{
 "DIAM": 60.0,
 "HEIGHT": 50.0,
 "WALL": 3.0,
 "THREAD_PITCH": 4.0,
 "LID_HEIGHT": 12.0,
 "SEAL_GROOVE": 0.0,
 "CHAMFER": 0.5
}

## METRICS (ultima version medida)
{
 "dims": {
  "D_body": 60.0,
  "H": 50.0,
  "wall": 3.0,
  "lid_height": 12.0,
  "thread_pitch": 4.0
 },
 "thread_pitch_lid": 4.0,
 "manifold": {
  "ok": true
 },
 "components": 4,
 "not_measured": [
  "SEAL_GROOVE (reservado v2)",
  "tapa/falda/cresta son solidos solapados: el slicer los une"
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
