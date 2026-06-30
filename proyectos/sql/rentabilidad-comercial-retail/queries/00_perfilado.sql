-- Pregunta: antes de analizar, ¿con qué datos estoy trabajando?
-- Rango de fechas, volúmenes y totales de control para validar todo lo que sigue.
SELECT
    (SELECT COUNT(*) FROM ventas)                          AS lineas_venta,
    (SELECT MIN(fecha) FROM ventas)                        AS fecha_min,
    (SELECT MAX(fecha) FROM ventas)                        AS fecha_max,
    (SELECT COUNT(*) FROM clientes)                        AS clientes,
    (SELECT COUNT(*) FROM productos)                       AS productos,
    (SELECT COUNT(*) FROM sucursales)                      AS sucursales,
    ROUND((SELECT SUM(ingreso) FROM ventas))               AS facturacion_total,
    ROUND((SELECT SUM(margen)  FROM ventas))               AS margen_total,
    ROUND(100.0 * (SELECT SUM(margen) FROM ventas)
                / (SELECT SUM(ingreso) FROM ventas), 1)     AS margen_pct;
