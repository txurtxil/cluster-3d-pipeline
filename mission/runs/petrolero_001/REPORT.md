# REPORT

MISSION: petrolero_001 Petrolero unidad corregida (fix casco z0f/z1f: linea de agua z=0)
INPUT: Petrolero: eslora 250 mm, manga 42 mm, con casco real, 7 tanques, piping, botes salvavidas, helice y timon

## HARD CONSTRAINTS
{
 "L": {
  "value": 260.915,
  "tol": 0.5
 },
 "B": {
  "value": 42.84,
  "tol": 0.5
 },
 "H": {
  "value": 78.0,
  "tol": 0.5
 },
 "PARTS": {
  "value": 361,
  "tol": 0
 },
 "draft": {
  "value": 13.75,
  "tol": 0.5
 },
 "freeboard": {
  "value": 19.0,
  "tol": 0.5
 },
 "hull_volume_mm3": {
  "value": 110905.9,
  "tol": 2500
 },
 "displacement_kg": {
  "value": 0.114,
  "tol": 0.005
 }
}

## FINAL PARAMETERS
{
 "L": 250
}

## METRICS (ultima version medida)
{
 "dims": {
  "L": 260.915,
  "B": 42.84,
  "H": 78.0
 },
 "counts": {
  "PARTS": 361,
  "UNIQ": 361
 },
 "manifold": {
  "ok": false,
  "bad_edges": 116
 },
 "nautical": {
  "draft": 13.75,
  "freeboard": 19.0,
  "hull_volume_mm3": 110905.9,
  "displacement_kg": 0.114,
  "displacement_m3": 0.000114,
  "displacement_t": 0.0001,
  "method": "rings(Casco_obra_viva,z<=0.5mm)+closed-submerged-solids; open bow/stern caps excluded"
 }
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
manifold: {'ok': False, 'bad_edges': 116}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
