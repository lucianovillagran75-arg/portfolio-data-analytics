-- Pregunta: ¿Qué productos tienen baja rotación y cuánto capital improductivo representan?
-- Lógica: no hay tabla de inventario, así que medimos ROTACIÓN. Comparamos las unidades
-- vendidas en los últimos 6 meses contra el ritmo histórico de cada producto. Los de menor
-- rotación son candidatos a descontinuar; el capital inmovilizado se aproxima asumiendo
-- 3 meses de cobertura de stock al ritmo actual (supuesto declarado en el informe).
WITH ventas AS (
    SELECT product_id,
           SUM(quantity) AS unidades_total,
           SUM(CASE WHEN date >= '2025-07-01' THEN quantity ELSE 0 END) AS unidades_6m,
           COUNT(DISTINCT substr(date, 1, 7)) AS meses_con_venta
    FROM fact_sales
    GROUP BY product_id
)
SELECT p.product_id,
       p.product_name,
       p.category,
       p.unit_cost,
       v.unidades_total,
       v.unidades_6m,
       ROUND(v.unidades_6m / 6.0, 1)                       AS unidades_por_mes_reciente,
       ROUND(p.unit_cost * (v.unidades_6m / 6.0) * 3, 0)   AS capital_inmovilizado_aprox
FROM dim_products p
JOIN ventas v USING (product_id)
ORDER BY unidades_6m ASC
LIMIT 8;
