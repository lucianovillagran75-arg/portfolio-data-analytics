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
| `ventas` | Líneas de venta | fecha, id_cliente, id_producto, id_sucursal, cantidad, precio_unitario, descuento, costo_unitario, ingreso, costo, margen |
| `clientes` | Clientes | segmento, ciudad, region, fecha_alta, es_fuga |
| `productos` | Productos | categoria, costo_unitario, precio_lista, es_margen_fino, es_baja_rotacion |
| `sucursales` | Sucursales | nombre_sucursal, ciudad, region |

## Problemas deliberados (para descubrir con SQL)

Los datos esconden a propósito cuatro situaciones reales. Las columnas `es_*` son la "verdad"
sembrada: sirven para **validar** que el análisis los encuentra, no para reemplazarlo.

1. **Margen negativo** — 4 productos con descuentos que dejan margen por debajo del costo.
2. **Baja rotación** — 5 productos que casi no venden en los últimos meses.
3. **Fuga de clientes** — ~18 % de clientes que dejan de comprar pasado el primer año.
4. **Brecha de sucursal** — la región Sur opera con tickets más chicos que el resto.
