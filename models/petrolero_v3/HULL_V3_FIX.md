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
