# 📂 Datos — TiendaNova

Dataset sintético y **reproducible** de una cadena retail ficticia. Se genera con semilla fija,
así que cualquier persona obtiene exactamente los mismos datos.

## Generar

```bash
python generar_datos.py
```

Produce:
- `raw/*.csv` — las 4 tablas en CSV (versionadas).
- `retail.db` — base SQLite con las 4 tablas e índices (se regenera, no se versiona).

## Modelo (esquema estrella)

| Tabla | Descripción | Columnas clave |
|---|---|---|
| `fact_sales` | Líneas de venta | date, customer_id, product_id, store_id, quantity, unit_price, discount, unit_cost, revenue, cost, margin |
| `dim_customers` | Clientes | segment, city, region, signup_date, churn_flag |
| `dim_products` | Productos | category, unit_cost, list_price, thin_margin_flag, dead_stock_flag |
| `dim_stores` | Sucursales | store_name, city, region |

## Problemas deliberados (para descubrir con SQL)

Los datos esconden a propósito cuatro situaciones reales. Los campos `*_flag` son la "verdad"
sembrada: sirven para **validar** que el análisis los encuentra, no para reemplazarlo.

1. **Margen negativo** — 4 productos con descuentos que dejan margen por debajo del costo.
2. **Baja rotación** — 5 productos que casi no venden en los últimos meses.
3. **Churn** — ~18 % de clientes que dejan de comprar pasado el primer año.
4. **Brecha de sucursal** — la región Sur opera con tickets más chicos que el resto.
