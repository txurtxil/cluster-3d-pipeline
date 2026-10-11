# REPORT

MISSION: chasis_cluster_004 Chasis rack 2x BC250 v4: migrado a mission-loop, unidad medida 2026-10-11
INPUT: Chasis inteligente 2x BC-250: 2 canales aire aislados, torre ventilacion trasera 120mm (hueco 122x80, taladros 105), tapa trasera rejilla escape, 2 compartimentos FlexATX con admision suelo, cuña frontal 6 ranuras, apoyos placa 95mm, canal cables, skin, patas.

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
 "env_w": 140
}

## METRICS (ultima version medida)
{
 "dims": {
  "X": 510.5,
  "Y": 308.0,
  "Z": 193.2
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
