-- Pregunta: ¿Qué productos nos hacen perder plata y cuánto recuperamos al corregirlos?
-- Lógica: productos cuyo margen total acumulado es negativo. El margen perdido es lo que
-- se recupera dejando de descontar o repreciando.
WITH por_producto AS (
    SELECT p.id_producto,
           p.nombre_producto,
           p.categoria,
           SUM(v.cantidad)            AS unidades,
           ROUND(SUM(v.ingreso), 2)   AS facturacion,
           ROUND(SUM(v.margen), 2)    AS margen_total,
           ROUND(AVG(v.descuento), 3) AS descuento_promedio
    FROM ventas v
    JOIN productos p USING (id_producto)
    GROUP BY p.id_producto
)
SELECT *,
       ABS(margen_total) AS recuperable_si_se_corrige
FROM por_producto
WHERE margen_total < 0
ORDER BY margen_total ASC;
