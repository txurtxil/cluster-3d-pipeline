# BC-250 BASE_SPEC — geometría verificada (2026-10-01)
> Fuente: CAD 2D comunitario + verificación cruzada con dibujo cotado del chasis v3.1.
> Esta hoja es la referencia estable: el generador y cualquier variante deben derivarse
> de estos parámetros, no de la memoria de una sesión.

## PCB (ASRock BC-250, formato propio — no ATX/Mini-ITX)

| Parámetro | Valor | Nota |
|---|---|---|
| board_length | 305 mm | 304,66 en CAD |
| board_width_max | 140 mm | zona del I/O (139,98 CAD) |
| board_width_main | 115 mm | zona principal estrecha |
| step_len | 105 mm | longitud de la zona ancha de PCB (en el extremo I/O) |
| main_len | 200 mm | = 305 − 105 |
| peso c/ disipador | ~400 g | |
| disipador | alto ~32 mm (verificar con calibre) | aire también por cara inferior (memorias) |
| agujeros montaje | spacing 95 mm (comunidad; verificar) | |
| alimentación | 1× PCIe 8-pin 12V, 220W TDP (235–250W con 40 CUs desbloqueadas) | |
| ventilador recomendado | 120×25 mm (Arctic P12 Pro), agujeros 105×105 mm | la placa NO trae mounts |

## Hueco del chasis (clearance = 3 mm perimetral)

| Parámetro | Valor | Derivación |
|---|---|---|
| cavity_length | 311 mm | 305 + 2×3 |
| cavity_width_max | 146 mm | 140 + 2×3 |
| cavity_width_main | 121 mm | 115 + 2×3 |
| **cavity_step_x** | **203 mm** | main_len + 3 (= 305 − 105 + 3) |

```
EXTREMO I/O
        ┌──────────────────────────┐
        │        140 mm            │ 105 mm   ← zona ancha PCB
        └──────────┐               │
                   │   115 mm      │ 200 mm   ← zona estrecha PCB
                   └───────────────┘
        ←──────── 305 mm ────────→
```

**Interpretación canónica (SIN ambigüedad):**
- `step_len = 105` → zona ancha de la **PCB** (en el extremo I/O).
- `cavity_step_x = 203` → posición del escalón del **hueco** = main_len + clearance.
- En `gen_cluster2_bc250.py` esto ya se calcula como `x_step = L − (step_len + clearance)` = 311 − 108 = **203** ✔ (verificado en el archivo, líneas 34–38).

## PSU de referencia (bc250.info)
FlexATX Apevia ITX-PFC500W: 160 × 73,66 × 41,2 mm, cable PCIe 6+2.
Compartimento del chasis: 172 × 85,66 × 49,2 mm internos (margin 6 mm).

## Material de impresión
PETG mínimo en zonas próximas a placa/PSU (el PLA se deforma con el calor residual).


---

## ACTUALIZACION VERIFICADA — 2026-10-11 (modelo comunitario Hrumque, printables 1341336)

Medido del STL de referencia de la placa real ("Accurate 3D model of the AMD
BC-250 board", usado por la comunidad para disenar carcasas que encajan):

| Medida | Valor verificado | Estado |
|--------|------------------|--------|
| Longitud PCB | **341.5 mm** | VERIFICADO (el valor 305 de esta spec queda ANULADO: era 36.5 mm corto) |
| Anchura PCB (con conectores) | **144.3 mm** | VERIFICADO (spec 140 era aproximado) |
| Altura pila completa (PCB->techo) | **32.1 mm** | VERIFICADO (coincide con los 32 mm estimados) |
| Agujeros montaje | (95 mm propia, sin confirmar) | **SIN VERIFICAR — requiere calibre físico** |

FUENTE DEL CONFLICTO: esta spec original (305x140) procedia de mediciones
propias no contrastadas; la documentacion comunitaria (elektricm) publicaba
340/310 x 115 "segun metodo de medicion". El modelo 3D comunitario confirma
341.5 x 144.3. La mision chasis_cluster_006 queda con env 341.5 x 144.3.

Los agujeros de montaje NO estan modelados en el STL de referencia: su
espaciado (95 mm) sigue pendiente de verificacion con calibre fisico, y se
necesitan las posiciones X/Y respecto a esquina de referencia (una distancia
sola no fija 4 taladros en una PCB de forma irregular).
