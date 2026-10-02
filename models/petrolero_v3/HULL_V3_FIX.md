# PETROLERO V3 — RECONSTRUCCION DEL CASCO

Diagnostico (audit_hull.py sobre V2): la banda de obra viva se interpolaba
con fracciones z0f=-1,z1f=0 -> quedaba colgando de z=-45.7 a -1.56 mm bajo la
quilla (calado visual 3.5x, obra viva real sin pintar, bulbo enterrado).

Fix en gen_petrolero_v3.py: wl=(0-zlo)/(zhi-zlo) por estacion;
banda roja g=fz*wl (quilla->flotacion), negra g=wl+fz*(1-wl);
secciones 7 pares (rizado redondo); cubierta en loft propio;
bulbo integrado (punta 1.012L).

Validado: obra viva z[-13,0] exacta | simetria 0.0 | 0 caras invertidas
| voladizo cubierta 0.35 mm | 458/458 manifold.

## V3.1 — FIX de la seccion invertida (reporte del usuario)
La foto de popa mostraba la base invertida: la seccion transversal tenia la
manga maxima en la QUILLA y la minima en la flotacion (desde V1).
Causa: mapeo fz->altura dentro de hull_band. Fix: prof_rel describe la seccion
completa cubierta->quilla con g=1-fz; banda negra fz en [0, 1-wl], roja
[1-wl, 1] (comparten punto de flotacion -> casco continuo); espejo de
estribor en orden inverso (normales exteriores).
Verificado: seccion media wl=18.98mm / quilla=15.48mm (PASS), obra viva
z[-13,0], popa renderizada correcta (render_stern_v31.png).

## V3.2 — Superstructura por gradines + flotantes eliminados
Problemas (foto usuario): castillo era una losa unica irreconLista; botes/davits
fuera de la huella del bloque (flotando); bocinas separadas del casco; railing
superior fuera de la losa; ala de puente volada sin soporte.
Fix: N1/N2/deckhouse/puente con retranqueos progresivos; alas con soporte
diagonal; cubierta superior a huella de N2; botes sobre boat-deck (techo N2)
en y=+-B*0.24; bocinas en y=+-B*0.24 (casco popa); escalera apoyada en cara
de proa de N1. 455 obj, 455/455 manifold.

## V3.3 — Chimenea asentada + transom a medida (reporte usuario, 2 fotos)
Foto 1: chimenea volando -> la reescritura V3.2 movio el puente pero la chimenea
quedo en x=ssx-0.055L (popa del puente, 8.5 mm sobre N1). Fix: chimenea sobre
el techo de N2 (eje N2, base F+17.45); mastil de popa reubicado al techo del
puente (su x quedo dentro de la chimenea nueva).
Foto 2: placa gigante en popa -> Espejo_popa media 39.6 mm pero la seccion de
popa del casco solo 20 mm (voladizo + popa hueca bajo z=-0.4, visible sobre la
helice). Fix: transom calculado de la geometria real (2*half_breadth(0),
de quilla-0.25 a cubierta+0.35).
455 obj, 455/455 manifold. Renders verificados desde ambos angulos del usuario.
