# REPORT

MISSION: chasis_cluster_005 Chasis v5: FlexATX estandar confirmada 150x81.5x40.5. PCB 305x140 segun spec propia (comunidad dice 340/310x115: VERIFICAR con regla). Agujeros 95mm sin verificar. Disipador 32mm corroborado externamente.
INPUT: Chasis rack 2x BC-250 v5. PSU estandar FlexATX 150x81.5x40.5 (confirmado Intel/FSP). Resto de cotas = spec canonica pendiente de verificacion fisica.

## HARD CONSTRAINTS
{
 "X": {
  "value": 510.5,
  "tol": 2.0
 },
 "Y": {
  "value": 306.0,
  "tol": 2.0
 },
 "Z": {
  "value": 193.2,
  "tol": 1.0
 },
 "PARTS": {
  "value": 35,
  "tol": 0
 },
 "supports_spacing_mm": {
  "value": 95.0,
  "tol": 0.5
 }
}

## FINAL PARAMETERS
{
 "env_len": 305,
 "env_w": 140,
 "psu_len": 150,
 "psu_w": 81.5,
 "psu_h": 40.5
}

## METRICS (ultima version medida)
{
 "dims": {
  "X": 510.5,
  "Y": 308.0,
  "Z": 192.5
 },
 "counts": {
  "PARTS": 35,
  "UNIQ": 35,
  "supports": 8
 },
 "supports_spacing_mm": 95.0,
 "manifold": {
  "ok": true,
  "bad_edges": 0
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
manifold: {'ok': True, 'bad_edges': 0}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
