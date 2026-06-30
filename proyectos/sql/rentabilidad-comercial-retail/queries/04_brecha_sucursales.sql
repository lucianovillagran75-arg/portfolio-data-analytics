-- Pregunta: ¿Qué sucursal/región rinde por debajo del resto y cuánto vale cerrar la brecha?
-- Lógica: comparar el ticket promedio por sucursal. La brecha de la peor sucursal contra la
-- mediana de la red es el potencial de mejora si igualara las prácticas del resto.
WITH por_sucursal AS (
    SELECT s.id_sucursal,
           s.nombre_sucursal,
           s.region,
           COUNT(DISTINCT v.id_cliente)                        AS clientes,
           COUNT(DISTINCT v.id_venta)                          AS tickets,
           ROUND(SUM(v.ingreso))                               AS facturacion,
           ROUND(SUM(v.margen))                                AS margen,
           ROUND(SUM(v.ingreso) / COUNT(DISTINCT v.id_venta), 2) AS ticket_promedio
    FROM ventas v
    JOIN sucursales s USING (id_sucursal)
    GROUP BY s.id_sucursal
)
SELECT *
FROM por_sucursal
ORDER BY ticket_promedio ASC;
