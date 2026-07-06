# 🛠️ Paso a Paso — Construcción del Sistema de Inventario

Documentación del proceso completo de diseño y construcción del sistema.
Cada fase muestra qué problema resuelve, qué se construyó y qué resultado generó.

---

## Fase 1 — Base de datos de inventario

### El punto de partida

Antes de escribir una sola fórmula, el primer problema era estructural: **no existía una fuente única de datos**. La información de stock estaba en una planilla, las ventas en otra, y los proveedores en correos. El primer paso fue diseñar una base de datos que centralizara todo.

### Decisiones de diseño

Se definieron 75 SKUs distribuidos en 3 categorías reales de consumo masivo:
- **Alimentos Secos** (25 SKUs): arroz, fideos, harina, aceites, yerba, café
- **Limpieza del Hogar** (25 SKUs): lavandina, detergentes, jabones en polvo, papel higiénico
- **Higiene Personal** (25 SKUs): shampoo, pasta dental, desodorantes, cremas

Cada SKU tiene 19 columnas de información: identificación, proveedor, precio de costo, stock actual, stock mínimo, ventas de los últimos 6 meses, fecha de último movimiento y capital inmovilizado.

### Convención de colores aplicada

Desde el inicio se aplicó la convención profesional de Excel:
- **Texto azul** → datos de entrada editables por el usuario
- **Texto negro** → fórmulas calculadas automáticamente
- **Texto verde** → referencias a otras hojas del mismo archivo

### Resultado de la Fase 1

```
✅ 75 SKUs registrados con historial de 6 meses
✅ 19 columnas · 309 fórmulas · 0 errores
✅ Filtros automáticos activados en todos los encabezados
✅ Panel congelado en fila 4 para navegación sin perder headers
✅ Capital total inmovilizado visible: $64,8 M ARS (64.825 miles de $)
```

---

## Fase 2 — Motor de análisis y KPIs

### El insight clave

Con los datos centralizados, el siguiente problema era la **interpretación**. Un número de stock no dice nada por sí solo. 200 unidades puede ser mucho o poco dependiendo de si el producto vende 10 o 500 por mes. Necesitábamos contexto.

### Los 9 KPIs calculados automáticamente

| KPI | Fórmula base | Por qué importa |
|---|---|---|
| Días de cobertura | `stock / (vprom / 30)` | Cuántos días dura el stock al ritmo actual |
| Índice de rotación | `ventas_6m / stock_actual` | Qué tan rápido "da vuelta" el inventario |
| Capital inmovilizado | `stock × precio_costo` | Cuánto dinero está "dormido" en ese SKU |
| Estado (semáforo) | IF anidado con 5 estados | Diagnóstico inmediato visual |
| Clasificación ABC | PERCENTILE dinámico | Priorización por volumen de ventas |
| % sobre total ventas | `ventas_sku / ventas_total` | Peso del SKU en la operación |
| Alerta quiebre | `SI(cobertura < 7, "⚠ SÍ", "—")` | Flag binario para filtrado rápido |
| Días sin movimiento | `fecha_hoy - fecha_ult_movimiento` | Detectar productos estancados |
| Acción recomendada | IF compuesto | Instrucción directa para el operador |

### El semáforo de 5 estados

```
🔴 QUIEBRE        → cobertura < 7 días     → acción: REPOSICIÓN URGENTE
🟡 CRÍTICO        → cobertura 7-14 días    → acción: Revisar orden de compra
🟢 NORMAL         → cobertura 14-90 días   → acción: Stock en niveles óptimos
🟡 SOBRESTOCK     → cobertura 90-180 días  → acción: Reducir próxima compra
🔴 STOCK MUERTO   → cobertura > 180 días   → acción: LIQUIDAR / DEVOLVER
```

### Formato condicional inteligente

Se aplicaron 10 reglas de formato condicional:
- Escala de colores en días de cobertura (rojo → amarillo → verde)
- Escala de colores en índice de rotación
- Resaltado automático por estado (🔴/🟡/🟢)
- Clasificación ABC con fondo azul oscuro/medio/claro

### Resultado de la Fase 2

```
✅ 4.517 fórmulas · 0 errores
✅ 7 SKUs en quiebre detectados (cobertura < 7 días)
✅ 12 SKUs con stock muerto identificados
✅ $22,5 M ARS en capital inmovilizado sin rotación
✅ 49 SKUs en niveles óptimos (normal)
✅ Clasificación ABC: 15 tipo A · 23 tipo B · 37 tipo C
```

---

## Fase 3 — Panel de alertas operativas

### El problema de la acción

Tener los KPIs calculados no era suficiente. El operador necesitaba saber **exactamente qué hacer hoy**, sin tener que revisar 75 filas buscando los problemas. Se construyó una hoja de alertas con 4 secciones de extracción automática.

### Las 4 categorías de alerta

**🔴 Quiebre inminente** — los 7 SKUs que se quedan sin stock en menos de 7 días:
- Harina 000 1kg → 2 días de cobertura, vende 375 unidades/mes
- Sal Fina 1kg → 6 días de cobertura, vende 407 unidades/mes
- Mayonesa 500g → 2 días de cobertura, vende 407 unidades/mes
- *(+ 4 más)*

**🔴 Stock muerto** — 12 SKUs sin movimiento significativo hace más de 60 días:
- Jabón en Polvo 3kg → $6.912 inmovilizado
- Yerba Mate 1kg → $3.888 inmovilizado
- *(+ 10 más)*

**🟡 Sobrestock** — 6 SKUs con cobertura entre 90 y 180 días

**🟡 Crítico** — 1 SKU con cobertura entre 7 y 14 días

### El impacto en tiempo operativo

| Tarea | Método anterior | Con el sistema |
|---|---|---|
| Identificar quiebres | Revisar 75 filas manualmente | Panel automático, 0 búsqueda |
| Calcular días de cobertura | Fórmula manual por SKU | Calculado para los 75 simultáneamente |
| Detectar stock muerto | Cruzar planillas distintas | Hoja de Alertas actualizada en tiempo real |
| Preparar reporte mensual | 4,5 horas | 20 minutos |

---

## Fase 4 — Dashboard ejecutivo

### La pieza central del portfolio

El dashboard es la hoja que un gerente, cliente o reclutador ve primero. Tiene que contar la historia completa en una sola pantalla, sin necesidad de navegar otras hojas.

### Estructura del dashboard

**Header:** Título, período y nota de actualización automática.

**3 KPI Cards:**
- Capital total inmovilizado: **$64,8 M ARS** (64.825 miles de $)
- Capital en stock muerto: **$22,5 M ARS** (34,7% del total)
- SKUs en nivel normal: **49 de 75**

**4 Gráficos embebidos:**
1. **Distribución de estados** (pie chart) — proporción visual de los 5 estados
2. **Capital por categoría** (bar chart) — Alimentos $13.815 / Limpieza $25.493 / Higiene $25.517
3. **Evolución de ventas mensuales** (line chart) — tendencia Ene–Jun 2025
4. **Clasificación ABC** (column chart) — 15A / 23B / 37C

**Top 10 capital inmovilizado** — tabla con los productos que más dinero tienen dormido

**Comparativa antes/después** — la historia de impacto en 6 métricas

**Tabla de quiebre urgente** — los 7 SKUs que necesitan reposición inmediata

### Resultado final del archivo completo

```
✅ 4 hojas operativas interconectadas
✅ 4.617 fórmulas totales · 0 errores en todo el archivo
✅ 4 gráficos embebidos con datos dinámicos
✅ Dashboard de una sola pantalla lista para presentar
✅ Tiempo de actualización al cambiar datos: < 1 segundo
```

---

## 📌 Aprendizajes técnicos

1. **Arquitectura primero, datos después.** Diseñar la estructura de las 4 hojas antes de escribir una fórmula evita refactorizar a mitad del proyecto.

2. **Protección contra errores en las fórmulas.** Usar `IFERROR()` en todas las divisiones evita que un solo SKU sin ventas rompa toda la hoja de análisis.

3. **PERCENTILE dinámico para la clasificación ABC.** En lugar de hardcodear umbrales fijos (ej: "clase A = más de 100 unidades"), usar `PERCENTILE($rango, 0.8)` hace que la clasificación se ajuste automáticamente al mix del negocio.

4. **Referencias cruzadas entre hojas como arquitectura.** Toda la información fluye en una sola dirección: `Base_Datos` → `Análisis` → `Alertas` y `Dashboard`. Nunca en sentido inverso. Esto evita referencias circulares y hace el modelo auditable.

5. **El dashboard es para personas, no para datos.** La hoja de Análisis tiene 16 columnas técnicas. El Dashboard muestra 3 números, 4 gráficos y 2 tablas de acción. Son audiencias distintas y necesitan formatos distintos.

---

*Documentación generada durante el proceso de construcción · Junio 2025*