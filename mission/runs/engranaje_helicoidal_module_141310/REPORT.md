# REPORT

MISSION: engranaje_helicoidal_module_141310 api-8201
INPUT: Engranaje helicoidal: MODULE=2.5, TEETH=36, HELIX_ANGLE=19, FACE_WIDTH=15, BORE_D=8, HUB_D=30, HUB_LEN=10, KEYWAY=4, CHAMFER=0.5

## HARD CONSTRAINTS
{
 "teeth": {
  "value": 36.0,
  "tol": 0.5
 },
 "helix_angle": {
  "value": 19.0,
  "tol": 1.5
 },
 "bore_d": {
  "value": 8.0,
  "tol": 0.5
 }
}

## FINAL PARAMETERS
{
 "MODULE": 2.5,
 "TEETH": 36.0,
 "HELIX_ANGLE": 19.0,
 "FACE_WIDTH": 15.0,
 "BORE_D": 8.0,
 "HUB_D": 30.0,
 "HUB_LEN": 10.0,
 "KEYWAY": 4.0,
 "CHAMFER": 0.5
}

## METRICS (ultima version medida)
{
 "dims": {
  "pitch_d": 90.0,
  "teeth": 36.0,
  "helix_angle": 20.0,
  "bore_d": 8.0
 },
 "tip_d": 95.0,
 "root_d": 83.75,
 "manifold": {
  "ok": true
 },
 "components": 2,
 "not_measured": [
  "pitch_d DERIVADO (RA y modulo estimados; no medible directo por ray-casting)",
  "raiz corregida por EMBED=0.25 (convencion compartida con el generador)",
  "helix por pendiente de fase en 4 anillos (requiere twist/tramo < medio-paso)"
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
