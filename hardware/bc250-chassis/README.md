# Cluster definitivo 2x BC-250 — LAB RAX (rack modular impreso)

**Fecha:** 2026-10-11 · **Estado:** DEFINITIVO (reemplaza los disenos generados)

## Que es

`cluster-definitivo.3mf` — proyecto de impresion completo (Bambu/Creality) del
sistema **Lab Rax** (Assembling Lab, MakerWorld): rack modular de 10" con
bandejas adaptadas a **2 placas AMD BC-250**, extraido de la coleccion
comunitaria BC-250 de MakerWorld. 26 piezas de modelo en 14 platos de
impresion, con fotos de montaje, guia de inserts de laton y perfiles de
impresion para Creality.

Por que es el definitivo: es un diseno de comunidad con cientos de montajes
reales (verificacion de facto), incluye la adaptacion de bandejas a la huella
BC-250, y el usuario lo valido funcionalmente ("este ya esta funcionando").
Los disenos generados por pipeline (gen_chasis_cluster.py, gen_cluster2 v3.1)
quedan **eliminados del repo**: quedaban cortos en longitud de PCB (la spec
vieja 305 mm era erronea; la real verificada es 341.5 mm) y un chasis
comunitario probado supera a uno generado sin mediciones fisicas.

## Contenido

| Fichero | Que es |
|---|---|
| `cluster-definitivo.3mf` | Proyecto 3MF completo (17 MB): 26 piezas, 14 platos, perfiles Creality |
| `BC250_BASE_SPEC.md` | Cotas de la PCB VERIFICADAS (341.5 x 144.3 x 32.1, modelo Hrumque) |
| `img/` | Fotos del sistema: rack completo, bandejas pobladas, ventilador 120mm, inserts de laton |
| `docs/petrolero...` | (en ../docs) bitacoras del pipeline 3D |

## Requisitos de montaje (del propio 3MF)

- **Inserts de laton** (M3 tipico) en las piezas de union — foto en img/
- Ventilador de 120 mm (ranura dedicada en el rack)
- PETG recomendado para piezas estructurales/cercanas a placa (PLA se
  deforma con el calor de la BC-250)
- FlexATX estandar 150 x 81.5 x 40.5 mm (confirmado documentalmente)

## Verificacion pendiente (antes de imprimir bandejas de placa)

Los agujeros de montaje de la BC-250 (95 mm de spec propia) NO estan
verificados: medir con calibre posiciones X/Y respecto a esquina de
referencia. La PCB es 341.5 x 144.3 (ver BC250_BASE_SPEC.md).

## Procedencia

- Rack: "Lab Rax" de Assembling Lab (MakerWorld), adaptacion BC-250 de la
  coleccion comunitaria BC-250 (mothenjoyer69/NeHoMaR ecosystem).
- 3MF exportado de Creality Print 07.01.01.4472.
