# 📈 Informe de hallazgos — Rentabilidad Comercial (TiendaNova)

> Análisis sobre `datos/retail.db` · 24 meses (ene-2024 a dic-2025).
> Facturación total: **$176,6 M** · Margen total: **$49,8 M (28,2 %)**.
> Cada cifra sale de las consultas en [`queries/`](./queries/) y es reproducible.
> Los supuestos de anualización y tasas están declarados en cada hallazgo.

---

## 1. Productos vendidos bajo margen → *dinero recuperado*

**Hallazgo:** 4 productos acumulan **margen negativo** por descuentos agresivos (descuento
promedio ~17,6 %): se venden mucho, pero a pérdida.

**Evidencia** ([`01_margen_negativo.sql`](./queries/01_margen_negativo.sql)):

| Producto | Categoría | Unidades | Facturación | Margen total |
|----------|-----------|---------:|------------:|-------------:|
| P020 | Perfumería | 2.601 | $5.815.932 | **-$730.785** |
| P017 | Limpieza   | 2.815 | $4.046.601 | **-$491.179** |
| P005 | Bebidas    | 2.627 | $2.728.636 | **-$365.970** |
| P009 | Almacén    | 2.856 | $1.829.663 | **-$235.225** |

**Acción:** quitar el descuento o repreciar estos 4 SKU hasta margen ≥ 0.
**Impacto estimado:** **~$0,91 M/año** _(margen negativo acumulado $1,82 M / 24 meses; supone
mantener volumen — aun si baja algo al subir precio, sigue siendo mejor que vender a pérdida)._

---

## 2. Productos de baja rotación → *capital liberado*

**Hallazgo:** 5 productos casi no rotan (≤ 1–5 unidades/mes en los últimos 6 meses) e inmovilizan
surtido improductivo.

**Evidencia** ([`02_baja_rotacion.sql`](./queries/02_baja_rotacion.sql)): P036, P029, P023, P021,
P003. Capital inmovilizado aproximado (asumiendo 3 meses de cobertura al ritmo actual): **~$79.000**.

**Acción:** liquidar/descontinuar y redirigir espacio y capital a SKUs de alta rotación.
**Impacto estimado:** **~$79.000 de capital liberado** (one-time) + ~$6.300/año de costo de
oportunidad recuperado _(tasa 8 % anual)._

---

## 3. Churn de clientes → *ingreso recuperable*

**Hallazgo:** **156 clientes (21,7 %)** que compraron en 2024 **no volvieron** en 2025.

**Evidencia** ([`03_churn_clientes.sql`](./queries/03_churn_clientes.sql)): ese grupo aportó
**$2,45 M de margen en 2024**, hoy perdido.

**Acción:** campaña de win-back priorizada (cupón dirigido, contacto comercial) sobre ese listado.
**Impacto estimado:** **~$0,74 M/año** _(recuperando el 30 % del grupo; supuesto conservador)._

---

## 4. Brecha entre sucursales → *ingreso incremental*

**Hallazgo:** la sucursal **Sur (Bariloche)** tiene el **ticket promedio más bajo**: $9.499 vs.
mediana de la red $11.267 (−16 %), pese a un volumen de tickets sano (3.128).

**Evidencia** ([`04_brecha_sucursales.sql`](./queries/04_brecha_sucursales.sql)):

| Sucursal | Región | Tickets | Ticket promedio |
|----------|--------|--------:|----------------:|
| **Sur** | Sur | 3.128 | **$9.499** |
| Cuyo | Cuyo | 3.467 | $10.882 |
| Centro | Centro | 743 | $11.267 |
| Litoral | Centro | 5.562 | $11.730 |
| Norte | Norte | 2.800 | $12.713 |

**Acción:** replicar en Sur las prácticas comerciales de las sucursales líderes (cross-sell,
surtido, tamaño de compra).
**Impacto estimado:** **~$0,39 M/año** _(cerrar el 50 % de la brecha de ticket × 3.128 tickets ×
margen 28,2 %; el cierre total valdría ~$0,78 M/año)._

---

## ✅ Resumen ejecutivo

| Hallazgo | Acción | Impacto $/año | Esfuerzo | Supuesto clave |
|----------|--------|--------------:|----------|----------------|
| Productos bajo margen | Repreciar 4 SKU | **$0,91 M** | Bajo | Mantiene volumen |
| Churn de clientes | Campaña win-back | **$0,74 M** | Medio | Reactiva 30 % |
| Brecha sucursal Sur | Replicar mejores prácticas | **$0,39 M** | Medio | Cierra 50 % de la brecha |
| Baja rotación | Liquidar 5 SKU | $0,006 M + **$79 k** one-time | Bajo | Cobertura 3 meses, tasa 8 % |

### 💰 Impacto total estimado del análisis: **~$2,0 M/año** (+ ~$79 k de capital liberado)

Sobre un margen anual de ~$24,9 M, representa **~8 % de mejora de margen** identificada con cinco
consultas SQL, sin invertir en nuevos clientes ni publicidad — solo dejando de perder plata donde
ya se estaba perdiendo.
