# REPORT

MISSION: tower_002 Replica torre Eiffel de referencia (barandillas, cornisas, arcos, chapitel)
INPUT: Torre Eiffel identica a la referencia: altura 300 mm, base 150x150 mm, patas gruesas curvas con zapatas, 4 arcos redondeados, celosia X densa con anillos, 3 plataformas con barandilla y cornisa, corona y chapitel con anillos

## HARD CONSTRAINTS
{
 "H": {
  "value": 300.0,
  "tol": 1.0
 },
 "BASE": {
  "value": 181.5,
  "tol": 2.0
 },
 "LEGS": {
  "value": 4,
  "tol": 0
 },
 "PADS": {
  "value": 4,
  "tol": 0
 },
 "PLATFORMS": {
  "value": 2,
  "tol": 0
 },
 "CROWN": {
  "value": 1,
  "tol": 0
 },
 "SPIRE": {
  "value": 1,
  "tol": 0
 },
 "SPRINGS": {
  "value": 2,
  "tol": 0
 },
 "ARCHES": {
  "value": 4,
  "tol": 0
 },
 "BARS": {
  "value": 96,
  "tol": 0
 },
 "RINGS": {
  "value": 16,
  "tol": 0
 },
 "RAILS": {
  "value": 12,
  "tol": 0
 },
 "CORNICES": {
  "value": 12,
  "tol": 0
 }
}

## FINAL PARAMETERS
{
 "H": 300.0,
 "BASE": 181.5,
 "PROFILE": "eiffel",
 "N_BAYS": 4,
 "LEG_R": 8.0,
 "BAR_R": 1.2,
 "RING_R": 1.5,
 "ARCH_SPRING": 2,
 "ARCH_TUBE": 2.5,
 "PAD": true,
 "PAD_SIZE": 25.0,
 "PAD_T": 3.0,
 "CAP": true,
 "SPIRE_R": 1.0,
 "PLATFORM_T": 2.0,
 "OVERHANG": 10.0,
 "RAILING": true,
 "RAIL_H": 4.0,
 "RAIL_R": 0.8,
 "POST_SPACING": 15.0,
 "CORNICE_T": 0.4
}

## METRICS (ultima version medida)
{
 "dims": {
  "H": 300.0,
  "BASE": 175.941
 },
 "counts": {
  "LEGS": 4,
  "PADS": 4,
  "PLATFORMS": 3,
  "BARS": 48,
  "RINGS": 20,
  "ARCHES": 4,
  "CROWN": 1,
  "SPIRE": 1,
  "SPRINGS": 2,
  "RAILS": 16,
  "RAILPOSTS": 76,
  "CORNICES": 16
 },
 "manifold": {
  "ok": false,
  "bad_edges": 80,
  "worst_object": "ARCH0",
  "components": 236
 },
 "NOT_MEASURED": [
  "footprint_incl_pads",
  "lattice_spacing",
  "leg_wall",
  "arch_opening_dims",
  "zone_density_2d"
 ]
}

## ITERATIONS
total: 8
## ROLLBACKS
v0.1: sin rollback multi-version (una version por iteracion, nunca se sobrescribe)

## UNKNOWN / NOT_MEASURED
["footprint_incl_pads", "lattice_spacing", "leg_wall", "arch_opening_dims", "zone_density_2d"]

## WARNINGS
ninguna

## PRINTABILITY
manifold: {'ok': False, 'bad_edges': 80, 'worst_object': 'ARCH0', 'components': 236}
STL exportado y hash SHA256 registrado por version

VERDICT: FAIL
REASON: max_iter 8
