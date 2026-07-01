# PASO A PASO — Optimización de Inventario ABC-XYZ

## Fase A — Diseño del problema y los datos

**El punto de partida:** el equipo de compras de NorteLogix S.A. tomaba decisiones de
reposición basadas en experiencia: "con este proveedor pedimos 200 unidades cada primer
semana del mes". Sin visibilidad sobre variabilidad de demanda ni lead time, la empresa
acumulaba stock en productos lentos y se quedaba sin stock en los de mayor salida.

**Lo que diseñé:**
- Un dataset sintético con 120 SKUs distribuidos en 5 categorías, con 24 meses de historial.
- Patrones deliberados en el inventario actual para que el análisis produzca insights claros:
  - Los SKUs de mayor valor (A-X) con stock por debajo del punto de reorden → riesgo inmediato.
  - Los SKUs de menor valor y demanda errática (C-Z) con inventario excesivo → capital paralizado.
- Semilla fija SEED=42 para reproducibilidad total.

**Outputs de esta fase:**
- `datos/productos.csv` — 120 SKUs con precios, costos, lead times y costos de pedido.
- `datos/demanda_mensual.csv` — 2.880 registros (24 meses × 120 SKUs) con estacionalidad.
- `datos/inventario_actual.csv` — posición de stock actual con los patrones deliberados.

---

## Fase B — Clasificación ABC-XYZ

**Lo que hice:**
1. Calculé el revenue total por SKU sobre los 24 meses (precio × unidades vendidas).
2. Ordené de mayor a menor y calculé el porcentaje acumulado.
3. Asigné clase **A** (≤ 80 % acumulado), **B** (≤ 95 %) y **C** (resto).
4. Calculé el coeficiente de variación (CV = σ / μ) de la demanda mensual por SKU.
5. Asigné clase **X** (CV < 0,30), **Y** (CV < 0,60) y **Z** (CV ≥ 0,60).
6. Combiné ambas clasificaciones: **AX**, **AY**, ..., **CZ** — 9 celdas en la matriz.

**Resultado:** la matriz ABC-XYZ reveló la estructura real del portafolio:
- 21 SKUs tipo A concentran el 80 % del revenue con patrones mayormente estables (X/Y).
- 78 SKUs tipo C representan el 5 % del revenue restante, con alta proporción de demanda errática (Z).

**Por qué importa:** sin la dimensión XYZ, el ABC clásico trataría igual a un ítem AX
(alto valor, predecible → stock fácil de planificar) que a un AZ (alto valor, errático →
requiere más safety stock). Son estrategias de gestión completamente distintas.

---

## Fase C — Política de inventario óptima (SS, ROP, EOQ)

Para cada uno de los 120 SKUs calculé:

**Safety Stock (SS)** — el colchón contra la variabilidad:
```
SS = Z_score × σ_demanda_mensual × √(lead_time_meses)
```
Con Z = 1,645 → nivel de servicio del 95 % (el 95 % de los meses el stock alcanza sin quiebre).

**Reorder Point (ROP)** — cuándo emitir la orden de compra:
```
ROP = μ_mensual × lead_time_meses + SS
```
Cuando el stock baja al ROP, hay que pedir. El lead time del proveedor es el tiempo de espera.

**Economic Order Quantity (EOQ)** — cuántas unidades pedir cada vez:
```
EOQ = √(2 × D_anual × costo_pedido / (costo_unitario × 0,25))
```
Minimiza la suma de costos de pedido (fijos) y costos de holding (proporcionales al stock).

**Identificación de desvíos respecto a la política óptima:**
- Si `stock_actual > ROP + EOQ` → sobrestock: el exceso es capital inmovilizado.
- Si `stock_actual < ROP` → substock: el déficit es ventas en riesgo.

---

## Fase D — Dashboard ejecutivo y cuantificación del impacto

**Lo que construí:** un dashboard de 5 paneles en matplotlib que sintetiza todo el análisis
en una imagen ejecutiva generada automáticamente.

Panel 1 — **Matriz ABC-XYZ** (heatmap): muestra cuántos SKUs y cuánto revenue hay en cada
celda de la matriz. Un gerente de compras puede ver de un vistazo dónde concentrar la atención.

Panel 2 — **Curva Pareto ABC**: la curva de concentración de revenue. Los primeros 21 SKUs
(17,5 % del portafolio) generan el 80 % del ingreso. La estrategia de gestión no puede ser la
misma para los A que para los C.

Panel 3 — **Top 10 sobrestock**: los SKUs con mayor capital inmovilizado. El primero de la
lista tiene casi el doble de stock que su ROP + EOQ combinados. Acción directa: reducir el
próximo lote de compra.

Panel 4 — **Top 10 riesgo de quiebre**: los SKUs con stock por debajo de su ROP. El foco está
en los A-X: son los más urgentes porque combinan alto valor con alta frecuencia de venta.

Panel 5 — **KPI boxes**: los cuatro indicadores de impacto, todos con su supuesto declarado.

**Cuantificación del impacto (con supuestos explícitos):**

| Hallazgo | Impacto | Supuesto clave |
|---|---|---|
| Capital inmovilizado (30 SKUs) | $1,1M liberable | exceso_unidades × costo_unitario |
| Ventas en riesgo (8 SKUs bajo ROP) | $2,2M inmediatos | deficit_unidades × precio_unitario |
| Ahorro costos de pedido (EOQ) | $3,5M/año | política actual = 12 órdenes/año/SKU; EOQ reduce esa frecuencia en items C |
| Automatización (8h/mes → 30s) | $270k/año | 90h/año × $3.000/h analista |
| **Total estimado** | **~$7,0M** | |

---

## Resultado final

El análisis convirtió un proceso de 8 horas manuales en un pipeline de 30 segundos que:
1. Clasifica automáticamente los 120 SKUs según valor y variabilidad.
2. Calcula la política óptima de stock para cada uno.
3. Identifica dónde está el capital mal ubicado y dónde está el riesgo.
4. Genera un dashboard ejecutivo listo para presentar.

El mismo modelo puede correrse mes a mes con datos actualizados — la política de inventario
se vuelve un proceso continuo y basado en evidencia, no en criterio personal.
