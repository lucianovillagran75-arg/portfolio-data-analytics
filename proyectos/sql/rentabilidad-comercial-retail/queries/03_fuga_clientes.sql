-- Pregunta: ¿Cuántos clientes activos en 2024 dejaron de comprar en 2025 y cuánto valen?
-- Lógica: fuga = compró en 2024 y NO compró en 2025. El valor recuperable se aproxima por
-- el margen anual que ese grupo aportaba en 2024.
WITH activos_2024 AS (
    SELECT DISTINCT id_cliente FROM ventas WHERE fecha < '2025-01-01'
),
activos_2025 AS (
    SELECT DISTINCT id_cliente FROM ventas WHERE fecha >= '2025-01-01'
),
fugados AS (
    SELECT id_cliente FROM activos_2024
    WHERE id_cliente NOT IN (SELECT id_cliente FROM activos_2025)
)
SELECT
    (SELECT COUNT(*) FROM fugados)                                 AS clientes_fugados,
    (SELECT COUNT(*) FROM activos_2024)                            AS activos_2024,
    ROUND(100.0 * (SELECT COUNT(*) FROM fugados)
                / (SELECT COUNT(*) FROM activos_2024), 1)          AS tasa_fuga_pct,
    ROUND(SUM(v.margen), 2)                                        AS margen_perdido_2024
FROM ventas v
WHERE v.fecha < '2025-01-01'
  AND v.id_cliente IN (SELECT id_cliente FROM fugados);
