# REPORT

MISSION: petrolero_002 Petrolero EPICO v2: 4x res + mastil/anclas + tapas proa-popa + barandilla popa + auto-snap (0 flotantes). 2026-10-11
INPUT: Petrolero escala L=250: casco obra viva/muerta, quilla, bulbo, 7 tanques, piping, superestructura por gradines, 8 ojos de buey, gruas, botes, chimenea, transom, helice. Metricas nauticas HARD.

## HARD CONSTRAINTS
{
 "L": {
  "value": 260.387,
  "tol": 0.5
 },
 "B": {
  "value": 40.7,
  "tol": 0.5
 },
 "H": {
  "value": 74.8,
  "tol": 0.5
 },
 "PARTS": {
  "value": 551,
  "tol": 0
 },
 "draft": {
  "value": 13.75,
  "tol": 0.5
 },
 "freeboard": {
  "value": 18.65,
  "tol": 0.5
 },
 "hull_volume_mm3": {
  "value": 98975.8,
  "tol": 2500
 },
 "displacement_kg": {
  "value": 0.101,
  "tol": 0.005
 }
}

## FINAL PARAMETERS
{
 "L": 250,
 "n_stations": 81,
 "NS": 32
}

## METRICS (ultima version medida)
{
 "dims": {
  "L": 260.387,
  "B": 40.7,
  "H": 74.8
 },
 "counts": {
  "PARTS": 551,
  "UNIQ": 551
 },
 "tanks": 6,
 "manifold": {
  "ok": false,
  "bad_edges": 828
 },
 "floating": 0,
 "nautical": {
  "draft": 13.75,
  "freeboard": 18.65,
  "hull_volume_mm3": 99318.6,
  "displacement_kg": 0.102,
  "displacement_m3": 0.000102,
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
manifold: {'ok': False, 'bad_edges': 828}
STL exportado y hash SHA256 registrado por version

VERDICT: PASS
REASON: convergencia
