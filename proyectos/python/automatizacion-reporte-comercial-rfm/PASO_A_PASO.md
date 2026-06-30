# 🛠️ Paso a Paso — Reporte Comercial Automático + RFM

Documentación del proceso completo, organizado en las cuatro fases del trabajo: **recopilación,
planificación, ejecución y control**. Cada fase muestra qué problema resuelve, qué construí y qué
resultado generó.

---

## Fase 1 — Recopilación

### El punto de partida

El primer paso fue **conseguir y entender los datos**. El negocio tiene cuatro fuentes (ventas,
clientes, productos y sucursales). En el mundo real esto llega como exportaciones sueltas; acá las
unifiqué en un mismo punto de carga para que el resto del proceso no dependa de dónde estén.

### Qué hice

- Cargué `ventas`, `clientes`, `productos` y `sucursales` desde los CSV, parseando las fechas.
- Definí una **única función de carga** (`cargar()`): si mañana cambia el origen, se toca un solo lugar.

### Resultado de la Fase 1

```
✅ 4 fuentes unificadas en un punto de carga
✅ 15.700 líneas de venta · 776 clientes con actividad · 5 sucursales
✅ Fechas tipadas correctamente (no como texto)
```

---

## Fase 2 — Planificación

### El insight clave

Antes de programar, decidí **qué tenía que entregar el reporte y cómo medir el RFM**. Sin esta
definición, el código termina siendo un montón de cálculos sueltos sin una historia.

### Decisiones de diseño

- **KPIs**: facturación, margen $, margen %, ticket promedio, clientes activos y variación mes a mes.
- **Cortes**: mensual (tendencia), por sucursal y por categoría.
- **RFM**: Recencia (días desde la última compra), Frecuencia (cantidad de compras) y Monto
  (facturación), cada uno en quintiles 1–5. Combiné F y M en un score `FM` y segmenté por reglas
  R × FM en 6 grupos, cada uno con su **acción recomendada**.
- **Arquitectura del pipeline**: funciones chicas y encadenadas
  `cargar → validar → transformar → kpis → rfm → exportar → medir_impacto`.

### Resultado de la Fase 2

```
✅ 6 KPIs definidos + 3 cortes de análisis
✅ Método RFM definido (quintiles + segmentación por reglas)
✅ 6 segmentos con acción comercial asignada
✅ Pipeline diseñado como funciones reutilizables y testeables
```

---

## Fase 3 — Ejecución

### Lo que construí

Implementé el pipeline y lo dejé corriendo de punta a punta con un solo comando. Tres detalles que
cuidé:

1. **RFM robusto**: usé `qcut` sobre el `rank` de cada métrica para evitar el error de "bordes de
   bin duplicados" cuando hay muchos clientes con la misma frecuencia.
2. **Salidas listas para usar**: un Excel formateado de 5 hojas, cuatro gráficos `.png` y un CSV
   con la lista de clientes y su acción — el entregable que el equipo comercial realmente usa.
3. **Reproducible e idempotente**: correrlo dos veces da exactamente lo mismo, sin duplicar nada.

### La segmentación que apareció

| Segmento | Clientes | % | Qué hacer |
|---|---:|---:|---|
| 🟦 Campeones | 214 | 28 % | Fidelizar (VIP) |
| 🟦 Leales | 135 | 17 % | Upsell y recompensas |
| 🟦 Potenciales | 59 | 8 % | Incentivar 2ª compra |
| 🟦 Necesitan atención | 58 | 8 % | Ofertas reactivadoras |
| 🟥 **En riesgo** | **85** | **11 %** | **Recuperación urgente** |
| 🟥 Hibernando / Perdidos | 225 | 29 % | Recuperación de bajo costo |

### Resultado de la Fase 3

```
✅ Reporte Excel (5 hojas) + 4 figuras + CSV de segmentos generados en segundos
✅ 776 clientes clasificados en 6 segmentos con acción recomendada
✅ 85 clientes "En riesgo" identificados (valiosos que se están enfriando)
✅ Proceso de un comando: python src/pipeline.py
```

---

## Fase 4 — Control

### De salida a confianza

Un reporte automático **solo sirve si confiás en él**. La última fase fue blindar el proceso y
traducir el resultado a un número de negocio.

- **Validación de datos**: chequeo nulos, duplicados, integridad referencial (que toda venta tenga
  un cliente válido) y **recálculo de totales** (que `ingreso` = precio × cantidad). Si algo no
  cuadra, el pipeline lo avisa antes de exportar.
- **Medición de impacto** (`medir_impacto`): el proceso imprime cuánto vale, con supuestos
  declarados (costo hora, tasa de recuperación, anualización).

### Resultado de la Fase 4

```
✅ Validación automática de datos en cada corrida (totales cuadran, sin duplicados)
✅ Impacto cuantificado: ~$1,0 M/año ($0,27 M horas + $0,73 M retención)
✅ Cada cifra con su supuesto declarado
```

---

## 📌 Aprendizajes técnicos

1. **El cuello de botella no era técnico, era humano.** El valor no estuvo en una fórmula compleja
   sino en **sacar el proceso de las manos de una persona** y volverlo reproducible.

2. **`rank` antes de `qcut`.** Con muchos clientes de igual frecuencia, `qcut` falla por bordes
   duplicados; rankear primero reparte los empates y deja quintiles parejos.

3. **Validar antes de exportar.** Recalcular los totales contra la fuente evita publicar un reporte
   con un error de cálculo — el problema que justamente queríamos eliminar.

4. **Funciones chicas y encadenadas.** Partir el pipeline en pasos (`cargar`, `validar`, …) hace que
   cada parte se pueda probar y reutilizar sola.

5. **Todo termina en un número de negocio.** `medir_impacto` no es opcional: convierte el script en
   una decisión con plata atrás.

---

*Documentación generada durante el proceso de construcción · Datos simulados del sector retail*
