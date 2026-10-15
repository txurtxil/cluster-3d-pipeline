# REPORT

MISSION: avion_span_150_003319 api-8201
INPUT: Avion: SPAN=150, LENGTH=180, ENGINES=4, SWEEP=30, FUSE_R=12, THICK_W=4, WING_POS=0.45, TAIL=1, WINGLETS=1, CHAMFER=1

## HARD CONSTRAINTS
{
 "W": {
  "value": 150.0,
  "tol": 0.5
 },
 "L": {
  "value": 180.0,
  "tol": 0.5
 }
}

## FINAL PARAMETERS
{
 "SPAN": 147.0,
 "LENGTH": 181.15,
 "ENGINES": 4.0,
 "SWEEP": 30.0,
 "FUSE_R": 12.0,
 "THICK_W": 4.0,
 "WING_POS": 0.45,
 "TAIL": 1.0,
 "WINGLETS": 1.0,
 "CHAMFER": 1.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "L": 180.0,
  "W": 150.0,
  "H": 34.44
 },
 "manifold": {
  "ok": true
 },
 "components": 12,
 "not_measured": [
  "metrologia especifica: la pieza aun no es familia registrada"
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
manifold: {'ok': True}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
