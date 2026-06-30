# 📂 Datos — TiendaNova (Python)

Mismo negocio que el proyecto SQL, generado de forma **reproducible** (semilla fija). Así Python y
SQL trabajan sobre el mismo caso y los resultados se pueden cruzar.

## Generar

```bash
python generar_datos.py
```

Produce `raw/clientes.csv`, `raw/productos.csv`, `raw/sucursales.csv`, `raw/ventas.csv`.

## Tablas

| Archivo | Descripción | Columnas |
|---|---|---|
| `ventas.csv` | Líneas de venta | id_venta, fecha, id_cliente, id_producto, id_sucursal, cantidad, precio_unitario, descuento, costo_unitario, ingreso, costo, margen |
| `clientes.csv` | Clientes | id_cliente, nombre_cliente, segmento, ciudad, region, fecha_alta, es_fuga |
| `productos.csv` | Productos | id_producto, nombre_producto, categoria, costo_unitario, precio_lista, es_margen_fino, es_baja_rotacion |
| `sucursales.csv` | Sucursales | id_sucursal, nombre_sucursal, ciudad, region |
