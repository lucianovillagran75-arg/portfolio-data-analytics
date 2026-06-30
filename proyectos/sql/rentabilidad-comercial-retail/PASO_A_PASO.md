# 🛠️ Paso a Paso — Análisis de Rentabilidad en SQL

Documentación del proceso completo, de los datos crudos a las decisiones de negocio.
Cada fase muestra qué problema resuelve, qué se construyó y qué resultado generó.

---

## Fase 1 — Modelado de la base de datos

### El punto de partida

Antes de escribir una sola consulta, el problema era estructural: la información de ventas,
clientes, productos y sucursales vivía dispersa y sin relación entre sí. No se puede analizar
rentabilidad si no podés cruzar, en la misma estructura, el precio al que se vendió, el costo,
el descuento aplicado, quién compró y en qué sucursal.

### Decisiones de diseño

Modelé un **esquema estrella**, el estándar para análisis: una tabla de hechos central rodeada
de dimensiones descriptivas.

```
ventas  (la transacción: qué, cuánto, a qué precio, con qué descuento, a qué costo)
   ├── clientes     (quién compra: segmento, ciudad, región)
   ├── productos    (qué se vende: categoría, costo, precio de lista)
   └── sucursales   (dónde se vende: sucursal, región)
```

En la tabla de hechos precalculé tres columnas que se usan en casi todo el análisis:
`ingreso` (precio × cantidad), `costo` (costo × cantidad) y `margen` (ingreso − costo). Tener el
margen a nivel de línea es lo que después permite sumarlo por producto, por cliente o por sucursal.

### Resultado de la Fase 1

```
✅ 4 tablas en esquema estrella (1 hechos + 3 dimensiones)
✅ 15.700 líneas de venta sobre 24 meses (ene-2024 a dic-2025)
✅ 800 clientes · 37 productos · 5 sucursales
✅ 4 índices creados (fecha, cliente, producto, sucursal) para rendimiento
✅ Dataset reproducible con semilla fija: mismos datos en cualquier máquina
```

---

## Fase 2 — Perfilado y control

### Por qué primero perfilar

Antes de buscar insights, validé el terreno. Una consulta de perfilado responde "¿con qué datos
estoy trabajando?" y entrega los totales de control contra los que después verifico todo. Si más
adelante una suma no cuadra con estos números, sé que algo está mal en la consulta, no en los datos.

### Lo que confirmé

| Métrica | Valor |
|---|---|
| Rango de fechas | 2024-01-01 → 2025-12-31 |
| Líneas de venta | 15.700 |
| Facturación total | $176.646.124 |
| Margen total | $49.807.374 |
| Margen % | 28,2 % |

### Resultado de la Fase 2

```
✅ Totales de control fijados como "verdad" para validar el resto
✅ Margen del 28,2 %: sano en apariencia... pero esconde fugas
✅ Cero fechas fuera de rango, cero huecos en las dimensiones
```

---

## Fase 3 — Las consultas de rentabilidad

### El insight clave

Con el modelo listo, ataqué las cuatro preguntas que valen plata. La regla que me impuse: cada
consulta tiene que terminar en una **decisión**, no en un dato. Un número sin acción no sirve.

### 🩸 Productos vendidos bajo margen

Agrupando el margen por producto, aparecieron **4 productos con margen total negativo**: se vendían
mucho, pero con descuentos del ~17,6 % que los dejaban por debajo del costo. El peor (P020,
Perfumería) acumulaba **-$730.785**. Se estaban vendiendo a pérdida sin que nadie lo notara.

### 🔁 Fuga de clientes

Comparé los clientes activos en 2024 contra los de 2025 con dos CTEs y un `NOT IN`. Resultado:
**156 clientes (21,7 %)** que compraban dejaron de hacerlo. Ese grupo había aportado **$2,45 M
de margen** en 2024.

### 🏬 Brecha entre sucursales

Calculé el ticket promedio por sucursal y lo comparé contra la mediana de la red. La sucursal
**Sur** vendía con un ticket **16 % más bajo** que el resto, con volumen sano: el problema no era
de tráfico sino de tamaño de compra.

### 📦 Baja rotación

Como no había tabla de inventario, medí rotación: unidades de los últimos 6 meses por producto.
**5 productos** casi no se movían (≤ 1–5 unidades/mes), inmovilizando capital improductivo.

### Resultado de la Fase 3

```
✅ 4 productos con margen negativo detectados ($1,82 M acumulado)
✅ 156 clientes en fuga identificados (21,7 %)
✅ Brecha de ticket de la sucursal Sur cuantificada (-16 %)
✅ 5 productos de baja rotación detectados (~$79 k de capital)
✅ Cada hallazgo validado contra las marcas sembradas en los datos
```

---

## Fase 4 — Cuantificación del impacto

### De hallazgo a dinero

Un hallazgo sin un número de negocio es una curiosidad. La última fase fue traducir cada
hallazgo a **$/año**, declarando siempre el supuesto para que sea creíble y defendible.

| Hallazgo | Acción | Impacto $/año |
|---|---|---|
| Productos bajo margen | Repreciar 4 productos | $0,91 M |
| Fuga de clientes | Campaña de recuperación (reactiva 30 %) | $0,74 M |
| Brecha sucursal Sur | Replicar mejores prácticas (cierra 50 %) | $0,39 M |
| Baja rotación | Liquidar 5 productos | $79 k puntual |

### Resultado final

```
✅ Impacto total estimado: ~$2,0 M/año (≈ 8 % del margen anual)
✅ Cada cifra con su supuesto declarado (anualización, tasa, % de captura)
✅ Cero inversión en marketing: solo se deja de perder lo que ya se perdía
```

---

## 📌 Aprendizajes técnicos

1. **Perfilar antes de analizar.** La consulta de control evita horas persiguiendo un número
   que no cuadra: si la suma no da, el problema está en la consulta, no en los datos.

2. **El margen a nivel de línea es la palanca.** Precalcular `margen` por transacción hace que
   todo el análisis posterior (por producto, cliente o sucursal) sea una simple agregación.

3. **CTEs para pensar por pasos.** Encadenar `WITH` (activos_2024 → activos_2025 → fugados) hace
   la lógica legible y auditable, en lugar de una subconsulta anidada imposible de leer.

4. **Comparar siempre contra una línea base.** El ticket de la sucursal Sur no significaba nada
   hasta compararlo con la mediana de la red. Un número solo no es un insight.

5. **El insight termina en una acción con un número.** La diferencia entre "reporte" y "análisis"
   es que el segundo dice qué hacer y cuánto vale hacerlo.

---

*Documentación generada durante el proceso de análisis · Datos simulados del sector retail*
