# REPORT

MISSION: helice_de_barco_144928 api-8201
INPUT: Helice de barco: DIAM=60, BLADES=3, PITCH_RATIO=0.85, BAR=0.52, HUB_D=20, HUB_LEN=15, RAKE=8, SKEW=12, SHAFT_D=8

## HARD CONSTRAINTS
{
 "D": {
  "value": 60.0,
  "tol": 0.5
 },
 "blades": {
  "value": 3.0,
  "tol": 0.5
 },
 "pitch_ratio": {
  "value": 0.85,
  "tol": 0.5
 },
 "rake": {
  "value": 8.0,
  "tol": 0.5
 },
 "skew": {
  "value": 12.0,
  "tol": 0.5
 },
 "shaft_d": {
  "value": 8.0,
  "tol": 0.5
 }
}

## FINAL PARAMETERS
{
 "DIAM": 60.0,
 "BLADES": 3.0,
 "PITCH_RATIO": 0.85,
 "BAR": 0.52,
 "HUB_D": 20.0,
 "HUB_LEN": 15.0,
 "RAKE": 8.0,
 "SKEW": 12.0,
 "SHAFT_D": 8.0
}

## METRICS (ultima version medida)
{
 "dims": {
  "D": 60.0,
  "blades": 3.0,
  "pitch_ratio": 0.803,
  "rake": 7.88,
  "skew": 11.8,
  "hub_d": 22.0,
  "shaft_d": 7.99
 },
 "manifold": {
  "ok": true
 },
 "components": 2,
 "not_measured": [
  "BAR (area de palas): estimado por construccion, no por vertices"
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
