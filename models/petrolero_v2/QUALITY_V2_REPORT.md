# PETROLERO_QUALITY_V2 - INFORME

{
 "V1": {
  "objects": 361,
  "manifold": "361/361",
  "stl_bytes": 1594684,
  "vlm": "parece bulk carrier / general cargo"
 },
 "V2": {
  "objects": 458,
  "manifold": "458/458",
  "small_lt_0p4mm": 0
 },
 "cambios": [
  "1. tapas rectangulares tipo bodega fuera; 18 domos de tanque circulares (3x6) con manhole; cubierta al ras",
  "2. gruas de cubierta fuera (son de granelero); derrick de manifold pequeno",
  "3. manifold a media eslora AMBAS BANDAS con 8 ruedas grandes + crossover central (firma petrolero)",
  "4. dos mastiles de ventilacion con brazos, tubos y caps (silueta petrolera)",
  "5. quillas de rolido; manga 42 a 40; sheer de proa mas marcado",
  "6. crossovers transversales de linea de carga en cada limite de tanque"
 ],
 "vlm_v2": {
  "tanker_confidence": 0.95,
  "bulk_carrier_confidence": 0.02,
  "general_cargo_confidence": 0.03
 },
 "metricas_v1_vs_v2": {
  "iou_main": 0.8103,
  "openings_delta_pct": -4.7,
  "nota": "alto IoU = mismo barco; cambio concentrado en cubierta"
 },
 "printability": {
  "partes_menores_0p4mm": 0,
  "manifold": "100%",
  "problemas": "ninguno critico"
 },
 "restante": [
  "hélice/timon poco visibles desde 3/4 (bajo la linea de flotacion) - aceptable a escala",
  "VLM lista 'faltantes' de checklist generico (algunos son rasgos DE granelero: correcto que falten)",
  "domos podrian integrarse mas visualmente en cubierta (menos altura de aro)"
 ],
 "verdict": "READY_FOR_NEXT_ITERATION"
}
