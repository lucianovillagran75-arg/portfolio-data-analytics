-- Pregunta: ¿Qué sucursal/región rinde por debajo del resto y cuánto vale cerrar la brecha?
-- Lógica: comparar el ticket promedio por sucursal. La brecha de la peor sucursal contra la
-- mediana de la red es el potencial de mejora si igualara las prácticas del resto.
WITH por_sucursal AS (
    SELECT st.store_id,
           st.store_name,
           st.region,
           COUNT(DISTINCT s.customer_id)                        AS clientes,
           COUNT(DISTINCT s.sale_id)                            AS tickets,
           ROUND(SUM(s.revenue))                                AS facturacion,
           ROUND(SUM(s.margin))                                 AS margen,
           ROUND(SUM(s.revenue) / COUNT(DISTINCT s.sale_id), 2) AS ticket_promedio
    FROM fact_sales s
    JOIN dim_stores st USING (store_id)
    GROUP BY st.store_id
)
SELECT *
FROM por_sucursal
ORDER BY ticket_promedio ASC;
