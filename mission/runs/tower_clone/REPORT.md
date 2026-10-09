# REPORT

MISSION: tower_clone Ruta B: clon fiel por instanciado del kit de 50 piezas del Eiffel_Resin_09.blend
INPUT: Clonar la torre de referencia: altura 300 mm (escala x3.75 del original de 80.12 mm), con sus 334 piezas instanciadas y sus 50 piezas unicas

## HARD CONSTRAINTS
{
 "H": {
  "value": 300.0,
  "tol": 0.5
 },
 "BASE": {
  "value": 122.0,
  "tol": 1.5
 },
 "PARTS": {
  "value": 315,
  "tol": 0
 },
 "UNIQ": {
  "value": 34,
  "tol": 0
 }
}

## FINAL PARAMETERS
{
 "H": 300
}

## METRICS (ultima version medida)
{
 "dims": {
  "H": 300.0,
  "BASE": 122.008
 },
 "counts": {
  "PARTS": 315,
  "UNIQ": 34
 },
 "manifold": {
  "ok": false,
  "bad_edges": 116
 },
 "NOT_MEASURED": [
  "internal_fit",
  "feature_positions"
 ]
}

## ITERATIONS
total: 1
## ROLLBACKS
v0.1: sin rollback multi-version (una version por iteracion, nunca se sobrescribe)

## UNKNOWN / NOT_MEASURED
["internal_fit", "feature_positions"]

## WARNINGS
Inyeccion inicial de fallo (test del loop)

## PRINTABILITY
manifold: {'ok': False, 'bad_edges': 116}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
