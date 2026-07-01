# Optimización de Inventario — Clasificación ABC-XYZ y Política de Stock

> **Herramienta:** Python (pandas, numpy, matplotlib)
> **Sector:** Logística y Cadena de Suministro
> **Contexto:** Distribuidora "NorteLogix S.A." — 120 SKUs · 5 categorías · 24 meses de historial
> **Período:** Enero 2023 – Diciembre 2024

---

## El problema

NorteLogix S.A. gestiona 120 SKUs de consumo masivo distribuidos en Bebidas, Lácteos, Snacks,
Limpieza y Granos. La política de compras la definía el criterio del comprador: pedir más o menos
cuando "parecía que había poco". Sin un modelo detrás, el resultado era el clásico contrasentido
de la cadena de suministro:

> *"Tenemos depósitos llenos de productos que casi nadie pide, y nos quedamos sin stock justo
> de los que más vendemos."*

**El problema tenía dos caras:**
- **Sobrestock en ítems C-Z** (bajo valor, demanda errática): capital inmovilizado sin trabajar.
- **Substock en ítems A-X** (alto valor, demanda estable): quiebres justo en los productos que
  más impacto tienen en el negocio.

El análisis mensual de inventario se hacía en 8 horas de trabajo manual; cualquier error de
criterio quedaba invisible hasta que el cliente se quejaba o el balance cerraba mal.

---

## La solución

Construí un modelo de optimización de inventario en Python que reemplaza el criterio "a ojo" por
una **política estadística y reproducible**, ejecutable en segundos con un solo comando.

```
cargar → abc → xyz → safety_stock → rop → eoq → identificar sobrestock/substock → dashboard → impacto
```

El modelo hace cuatro cosas que el analista promedio no hace:

| El analista promedio | Este modelo |
|---|---|
| Solo ABC (ranking por ventas) | **ABC + XYZ**: valor de facturación × variabilidad de demanda |
| Stock mínimo "a ojo" | **Safety stock estadístico** (95 % de nivel de servicio, Z = 1,645) |
| "Pedimos cuando hay poco" | **Punto de reorden** exacto = μ × lead_time + SS |
| Lote fijo por costumbre | **EOQ** = √(2DS/H) — minimiza el costo total de inventario |

### Qué calcula el modelo para cada SKU

- **Safety stock**: unidades de colchón contra variabilidad de demanda y lead time.
- **ROP (reorder point)**: nivel exacto al que hay que emitir la orden de compra.
- **EOQ (economic order quantity)**: lote óptimo que minimiza la suma de costos de pedido y holding.
- **Sobrestock**: unidades por encima de ROP + EOQ → capital inmovilizado en $.
- **Substock**: unidades por debajo del ROP → ventas en riesgo en $.

---

## Resultados

### Distribución de la matriz ABC-XYZ (120 SKUs)

| | X (estable) | Y (variable) | Z (errático) |
|---|---|---|---|
| **A (alto valor)** | 10 SKUs — prioridad máxima | 8 SKUs | 3 SKUs |
| **B (medio)** | 10 SKUs | 9 SKUs | 2 SKUs |
| **C (bajo valor)** | 6 SKUs | 34 SKUs | 38 SKUs |

> Los **AX** son los productos estrella: alta facturación, demanda predecible — los que más duele
> quedarse sin stock. Los **CZ** son la "cola larga": bajo valor y demanda errática — donde se
> acumula el sobrestock.

### Impacto económico identificado

| Hallazgo | Magnitud | Acción | Impacto |
|---|---|---|---|
| Capital inmovilizado en sobrestock (30 SKUs C-Z/C-Y) | 30 SKUs con exceso | Reducir lotes de compra en items C | **$1,1M liberable** |
| Ventas en riesgo por quiebres (8 SKUs bajo ROP) | 8 SKUs críticos | Reposición urgente A-X/A-Y | **$2,2M en riesgo** |
| Ahorro en costos de pedido con política EOQ | 120 SKUs | Adoptar lote EOQ vs frecuencia fija mensual | **$3,5M/año** |
| Automatización del cálculo mensual de stock | 8 h/mes → 30 s | Ejecutar `analisis_abcxyz.py` mensualmente | **$270k/año** |

### 💰 Impacto total estimado: **~$7,0M**

- $3,3M en capital y ventas recuperables (sobrestock + substock)
- $3,7M en ahorros recurrentes (EOQ + automatización)

El detalle con supuestos declarados está en [`informe.md`](./informe.md).

---

## Dashboard generado

**Panel de Inventario — 5 visualizaciones en un solo comando**

![Dashboard ABC-XYZ de Inventario](./output/dashboard_inventario.png)

El dashboard muestra:
1. **Matriz ABC-XYZ** — dónde está cada SKU y cuánto vale cada celda
2. **Curva Pareto ABC** — concentración del revenue en los primeros 21 SKUs
3. **Top 10 sobrestock** — SKUs con más capital inmovilizado
4. **Top 10 riesgo de quiebre** — SKUs bajo su punto de reorden
5. **KPI boxes** — los 4 impactos económicos en una vista

---

## Técnicas utilizadas

- **Clasificación ABC** por revenue acumulado (pandas `groupby` + `cumsum`).
- **Clasificación XYZ** por coeficiente de variación (CV = σ / μ) de la demanda mensual.
- **Safety stock estadístico**: `SS = Z × σ × √LT` con nivel de servicio del 95 %.
- **Reorder point**: `ROP = μ × LT + SS`.
- **Economic Order Quantity**: `EOQ = √(2DS/H)` donde D = demanda anual, S = costo de pedido,
  H = costo de holding (25 % del costo unitario).
- **Identificación de excesos y déficits**: comparación de stock actual vs ROP y ROP + EOQ.
- **Dashboard de 5 paneles** con matplotlib — colores por clase ABC-XYZ, semáforo rojo/naranja
  para los SKUs críticos.
- **Pipeline reproducible**: dos scripts ejecutables de punta a punta, sin pasos manuales.

---

## Archivos

| Archivo | Descripción |
|---|---|
| [`datos/generar_datos.py`](./datos/generar_datos.py) | Generador reproducible (SEED=42) — 3 CSVs |
| [`src/analisis_abcxyz.py`](./src/analisis_abcxyz.py) | Análisis completo + dashboard + impacto |
| [`output/clasificacion_abcxyz.csv`](./output/clasificacion_abcxyz.csv) | 120 SKUs con clase ABC-XYZ, CV y revenue |
| [`output/politica_inventario.csv`](./output/politica_inventario.csv) | SS, ROP, EOQ, sobrestock y déficit por SKU |
| [`output/dashboard_inventario.png`](./output/dashboard_inventario.png) | Dashboard ejecutivo de 5 paneles |
| [`informe.md`](./informe.md) | Hallazgos con supuestos y tabla de impacto |
| [`PASO_A_PASO.md`](./PASO_A_PASO.md) | Proceso de construcción fase a fase |

---

## Cómo reproducirlo

```bash
cd proyectos/python/optimizacion-inventario-abcxyz
python datos/generar_datos.py     # genera los 3 CSVs (semilla fija)
python src/analisis_abcxyz.py     # genera dashboard, CSVs de output e impacto
```

Requiere: `pandas`, `numpy`, `matplotlib` (incluidos en `requirements.txt`).

---

## Qué demuestra este proyecto

Que la gestión de inventario no es una cuestión de intuición — es estadística aplicada. El mismo
dataset que el comprador "conocía de memoria" ocultaba $7,0M de oportunidad: capital mal ubicado
en productos lentos y ventas en riesgo en los productos estrella. El modelo lo detecta en 30
segundos, genera una política óptima por SKU y la actualiza automáticamente cada mes.

La metodología (ABC-XYZ + safety stock + EOQ) es estándar en supply chain profesional; lo que
marca la diferencia es implementarla de forma reproducible, automatizada y con impacto cuantificado.

---

*Datos simulados con distribuciones realistas del sector distribución · Portfolio de Datos y Analítica*
