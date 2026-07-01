# Informe de Hallazgos — Optimización de Inventario ABC-XYZ
## NorteLogix S.A. | Enero 2023 – Diciembre 2024

---

## Contexto del análisis

NorteLogix S.A. distribuye 120 SKUs de consumo masivo en 5 categorías (Bebidas, Lácteos, Snacks,
Limpieza y Granos) a 300 puntos de venta en 3 provincias. El criterio de reposición era artesanal:
el área de compras pedía "cuando parecía que había poco", sin calcular variabilidad de demanda,
lead time de proveedor ni costo de mantener stock.

**Datos utilizados:** 3 archivos CSV generados con SEED=42 (reproducibles). 120 SKUs, 2.880
registros de demanda mensual (24 meses) y posiciones de stock al cierre de enero 2025.

---

## Hallazgo 1 — La empresa tiene $1,1M en capital inmovilizado en sobrestock

**Qué encontré:** 30 SKUs tienen un stock actual superior a ROP + EOQ (es decir, más de un ciclo
completo de reposición acumulado). La mayor parte son productos C-Z y C-Y: bajo valor, demanda
errática, pero con órdenes mensuales que se acumularon sin consumirse.

**Evidencia:**

| SKU | Clase | Stock actual | Stock óptimo | Exceso (unidades) | Capital inmovilizado |
|---|---|---|---|---|---|
| Top 1 | CZ | 3.8× stock óptimo | 124 u. | 349 u. | $145k |
| Top 2 | CZ | 4.1× stock óptimo | 89 u. | 281 u. | $118k |
| Top 3 | CY | 3.2× stock óptimo | 201 u. | 441 u. | $97k |
| ... (27 más) | CZ/CY | | | | |
| **TOTAL** | | | | | **$1,10M** |

**Acción recomendada:** reducir el lote de compra en los próximos ciclos para los 30 SKUs
identificados. No necesariamente dejar de comprar — sino comprar en lotes más pequeños y con
la frecuencia óptima (EOQ).

**Impacto estimado:** **$1,1M liberados**
*(Supuesto: capital liberado = exceso_unidades × costo_unitario al momento del análisis.)*

---

## Hallazgo 2 — 8 SKUs están por debajo de su punto de reorden: $2,2M en ventas en riesgo

**Qué encontré:** 8 SKUs tienen stock actual por debajo de su ROP. Cinco de ellos son ítems A-X
(alto valor, demanda estable) — los que más impactan en la facturación si se agotan. El cálculo
del ROP tuvo en cuenta el lead time real de cada proveedor (entre 8 y 20 días según el caso).

**Evidencia:**

| SKU | Clase | Stock actual | ROP | Déficit (unidades) | Valor en riesgo |
|---|---|---|---|---|---|
| SKU-001 | AX | 18 u. | 124 u. | 106 u. | $928k |
| SKU-002 | AX | 25 u. | 108 u. | 83 u. | $714k |
| SKU-003 | AX | 9 u. | 97 u. | 88 u. | $602k |
| SKU-004 | AY | 31 u. | 82 u. | 51 u. | — |
| ... (4 más) | AX/AY | | | | |
| **TOTAL** | | | | | **$2,18M** |

**Acción recomendada:** emitir órdenes de compra urgentes para los 8 SKUs identificados. El
foco está en SKU-001 a SKU-003: son los de mayor valor y están más lejos de su ROP.

**Impacto estimado:** **$2,2M de ventas recuperadas** (evitando el quiebre de stock)
*(Supuesto: valor en riesgo = deficit_unidades × precio_unitario. No anualizado: es el riesgo
inmediato al momento del análisis. Si la política no se corrige, la situación se repite.)*

---

## Hallazgo 3 — El modelo EOQ identifica $3,5M/año de ahorro en costos de pedido

**Qué encontré:** comparando la frecuencia de compra implícita en la política EOQ óptima vs. la
frecuencia actual estimada (12 órdenes/año por SKU, una mensual), hay un exceso significativo
de órdenes en los ítems de baja rotación. Para ítems C-Z con demanda de 2-5 unidades/mes, el
EOQ indica comprar una o dos veces al año — no mensualmente.

**Lógica del cálculo:**
- EOQ para CZ con demanda=60 u/año, costo_pedido=$2.500, holding=$200/u/año → EOQ=38 u → 1,6 órdenes/año.
- Diferencia vs. 12 órdenes/año: 10,4 órdenes menos × $2.500 = $26.000/año por SKU.
- Para los 45 SKUs C-Z: ~$1,17M/año; sumando BY y BZ adds up a los $3,46M totales.

**Acción recomendada:** adoptar el EOQ como lote estándar de compra. Para ítems C-Z, pasar a
compras trimestrales o semestrales. Para ítems A-X con alta demanda, el EOQ puede implicar
comprar más seguido — el modelo indica la frecuencia óptima en cada caso.

**Impacto estimado:** **$3,5M/año en costos operativos de pedido**
*(Supuesto: cada orden de compra tiene un costo fijo de procesamiento de $1.500-$10.000 según
el SKU. Política actual: 12 órdenes/año por SKU. EOQ reduce esta frecuencia en los ítems C.)*

---

## Hallazgo 4 — La automatización del cálculo mensual libera 90 horas/año de trabajo analítico

**Qué encontré:** el proceso de actualización mensual del inventario (reordenar data, aplicar
fórmulas, revisar por excepción) llevaba ~8 horas de trabajo manual por mes. Con el pipeline
Python, el mismo cálculo se ejecuta en menos de 30 segundos.

**Impacto estimado:** **$270k/año en horas de analista recuperadas**
*(Supuesto: 7,5 horas ahorradas/mes × 12 = 90 horas/año × $3.000/hora analista.)*
*Equivalente alternativo: 90 horas/año que pueden redirigirse a análisis de mayor valor.*

---

## Tabla resumen de impacto

| Hallazgo | Acción | Impacto | Esfuerzo | Supuesto clave |
|---|---|---|---|---|
| 30 SKUs C-Z/C-Y con sobrestock | Reducir lotes de compra | $1,1M liberable | Bajo | exceso × costo_unitario |
| 8 SKUs bajo ROP (A-X/A-Y) | Reposición urgente | $2,2M en ventas recuperadas | Bajo | deficit × precio_unitario |
| Frecuencia de pedido no óptima | Adoptar política EOQ | $3,5M/año ahorro operativo | Medio | 12 órdenes/año actual vs EOQ |
| Cálculo manual mensual (8h/mes) | Ejecutar pipeline automático | $270k/año en tiempo | Bajo | 90h/año × $3.000/h |
| **TOTAL** | | **~$7,0M** | | |

**Impacto total estimado del análisis: ~$7,0M**

---

## Próximos pasos recomendados

1. **Inmediato (semana 1):** emitir órdenes de compra urgentes para los 8 SKUs bajo ROP
   (especialmente SKU-001 a SKU-005). Riesgo de quiebre en los próximos ciclos.

2. **Corto plazo (mes 1-2):** implementar el lote EOQ para las compras de los próximos 30
   SKUs en sobrestock — no comprar hasta que el stock baje al nivel ROP.

3. **Proceso continuo:** integrar `analisis_abcxyz.py` al cierre mensual de inventario.
   El modelo tarda 30 segundos y entrega la política actualizada para los 120 SKUs.

---

*Datos sintéticos generados con distribuciones realistas del sector distribución · SEED=42*
*Supuestos sujetos a validación con datos reales del negocio*
