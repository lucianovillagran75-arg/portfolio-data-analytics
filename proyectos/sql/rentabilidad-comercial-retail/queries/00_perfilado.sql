-- Perfilado inicial: antes de analizar, entender el dataset.
-- Rango de fechas, volúmenes y totales de control para validar todo lo que sigue.
SELECT
    (SELECT COUNT(*) FROM fact_sales)                      AS lineas_venta,
    (SELECT MIN(date) FROM fact_sales)                     AS fecha_min,
    (SELECT MAX(date) FROM fact_sales)                     AS fecha_max,
    (SELECT COUNT(*) FROM dim_customers)                   AS clientes,
    (SELECT COUNT(*) FROM dim_products)                    AS productos,
    (SELECT COUNT(*) FROM dim_stores)                      AS sucursales,
    ROUND((SELECT SUM(revenue) FROM fact_sales))           AS facturacion_total,
    ROUND((SELECT SUM(margin)  FROM fact_sales))           AS margen_total,
    ROUND(100.0 * (SELECT SUM(margin) FROM fact_sales)
                / (SELECT SUM(revenue) FROM fact_sales), 1) AS margen_pct;
