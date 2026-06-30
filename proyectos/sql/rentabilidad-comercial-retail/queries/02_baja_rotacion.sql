-- Pregunta: ¿Qué productos tienen baja rotación y cuánto capital improductivo representan?
-- Lógica: no hay tabla de inventario, así que medimos ROTACIÓN. Comparamos las unidades
-- vendidas en los últimos 6 meses contra el ritmo histórico de cada producto. Los de menor
-- rotación son candidatos a descontinuar; el capital inmovilizado se aproxima asumiendo
-- 3 meses de cobertura de stock al ritmo actual (supuesto declarado en el informe).
WITH resumen AS (
    SELECT id_producto,
           SUM(cantidad) AS unidades_total,
           SUM(CASE WHEN fecha >= '2025-07-01' THEN cantidad ELSE 0 END) AS unidades_6m,
           COUNT(DISTINCT substr(fecha, 1, 7)) AS meses_con_venta
    FROM ventas
    GROUP BY id_producto
)
SELECT p.id_producto,
       p.nombre_producto,
       p.categoria,
       p.costo_unitario,
       r.unidades_total,
       r.unidades_6m,
       ROUND(r.unidades_6m / 6.0, 1)                            AS unidades_por_mes_reciente,
       ROUND(p.costo_unitario * (r.unidades_6m / 6.0) * 3, 0)   AS capital_inmovilizado_aprox
FROM productos p
JOIN resumen r USING (id_producto)
ORDER BY unidades_6m ASC
LIMIT 8;
