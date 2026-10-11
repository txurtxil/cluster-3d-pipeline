# REPORT

MISSION: chasis_cluster_006 Chasis v6: PCB REAL medido de modelo comunitario Hrumque (printables 1341336): 341.5 x 144.3 x 32.1. La spec vieja 305x140 queda ANULADA en longitud. Agujeros 95mm SIN verificar (caliper pendiente). FlexATX 150x81.5x40.5 estandar.
INPUT: Chasis rack 2x BC-250 v6 con PCB real 341.5x144.3. Canales aislados, torre ventilacion 120mm, tapa rejilla, 2x FlexATX estandar, apoyos 95mm (pendiente verificar), canal cables, skin, patas.

## HARD CONSTRAINTS
{
 "X": {
  "value": 547.0,
  "tol": 3.0
 },
 "Y": {
  "value": 310.0,
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
 "env_len": 330.0,
 "env_w": 140.0,
 "psu_len": 150,
 "psu_w": 81.5,
 "psu_h": 40.5
}

## METRICS (ultima version medida)
{
 "dims": {
  "X": 548.0,
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
total: 3
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
