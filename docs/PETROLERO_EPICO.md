# PETROLERO EPICO — bitacora de desarrollo (2026-10-11)

## Que es
Evolucion del petrolero V3 dentro del mission-loop. Tres oleadas de mejora,
todas verificadas con metrologia real (measure_tanker v2) y mission PASS.

## Oleada 1 (v1): velocidad + detalle base
- NS/n_stations parametrizables en gen_petrolero_v3.py (P.get / dict P).
- Resolucion 4x: 81 estaciones, NS=32. Volumen convergido (+0.07% vs 2x).
- Detalles EPIC1: mastil-radar sobre la chimenea (posicion derivada de la
  escena), anillo de radar, luz de mastil, 2 bocinas, 2 anclas con flukes.
- Metrica tanks corregida: Limite_tanque_*/2 = 6 (V3 tiene 6 tanques, no 7).

## Oleada 2 (v2): cerrar y anclar
- Tapas de proa y popa del casco (mallas abiertas cerradas por fan convexo).
- Barandilla de popa (5 postes + 2 rieles a lo largo de Y).
- AUTO-SNAP generico: cualquier pieza con gap 0.05-3 mm a su vecino mas
  cercano se traslada hasta el contacto (0.05 mm). Arreglo bugs heredados
  del V3: Ventanas.003, Plataforma_tecnica.
- Auditoria "floating" en measure_tanker (AABB).

## Oleada 3 (v3): colocacion AUTO-MEDIDA (la leccion importante)
El AABB da falsos negativos: bbox contenido != contacto (curvatura del casco).
Las anclas en media-nave quedaban DENTRO de la cavidad hull (invisibles al
auditoria, visibles para el ojo). Solucion: el generador MIDE su propia
geometria y coloca contra la superficie real:
- Anclas: x = 0.90*L; media-manga medida del casco en esa x (rango z -8..4);
  y = hb - 0.4 (incrustadas 0.4 mm en el flare).
- Bocinas: radio real del cono medido de la malla de la chimenea; apoyadas
  en frad + 0.2.
ESCALA-INVARIANTE: funciona para cualquier L que se pida.

## Estado verificado (mision petrolero_002, 13:49)
L=260.387 B=40.7 H=74.8 PARTS=551 tanks=6 floating=0
draft=13.75 freeboard=18.65 hull_volume~99312 mm3 displacement~0.102 kg

## Reglas que nacen de aqui
1. Toda mejora de geometria se verifica con metrologia, no con el ojo.
2. "No piezas volando" = regla de construccion (auto-snap + auto-medida),
   no de inspeccion posterior.
3. El LLM diseña mal las nauticas concretas: usarlo para ideas, la geometria
   exacta se mide o se calcula. (El 30B propuso "candelabros decorativos".)
4. Todo trabajo se sube a GitHub con su bitacora el mismo dia.
