-- Pregunta: ¿Qué productos nos hacen perder plata y cuánto recuperamos al corregirlos?
-- Lógica: productos cuyo margen total acumulado es negativo. El margen perdido es lo que
-- se recupera dejando de descontar o repreciando.
WITH por_producto AS (
    SELECT p.product_id,
           p.product_name,
           p.category,
           SUM(s.quantity)           AS unidades,
           ROUND(SUM(s.revenue), 2)  AS facturacion,
           ROUND(SUM(s.margin), 2)   AS margen_total,
           ROUND(AVG(s.discount), 3) AS descuento_promedio
    FROM fact_sales s
    JOIN dim_products p USING (product_id)
    GROUP BY p.product_id
)
SELECT *,
       ABS(margen_total) AS recuperable_si_se_corrige
FROM por_producto
WHERE margen_total < 0
ORDER BY margen_total ASC;
