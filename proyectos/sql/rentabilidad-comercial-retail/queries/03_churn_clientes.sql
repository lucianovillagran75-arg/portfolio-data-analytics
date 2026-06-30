-- Pregunta: ¿Cuántos clientes activos en 2024 dejaron de comprar en 2025 y cuánto valen?
-- Lógica: churn = compró en 2024 y NO compró en 2025. El valor recuperable se aproxima por
-- el margen anual que ese grupo aportaba en 2024.
WITH activos_2024 AS (
    SELECT DISTINCT customer_id FROM fact_sales WHERE date < '2025-01-01'
),
activos_2025 AS (
    SELECT DISTINCT customer_id FROM fact_sales WHERE date >= '2025-01-01'
),
churn AS (
    SELECT customer_id FROM activos_2024
    WHERE customer_id NOT IN (SELECT customer_id FROM activos_2025)
)
SELECT
    (SELECT COUNT(*) FROM churn)                                   AS clientes_churn,
    (SELECT COUNT(*) FROM activos_2024)                            AS activos_2024,
    ROUND(100.0 * (SELECT COUNT(*) FROM churn)
                / (SELECT COUNT(*) FROM activos_2024), 1)          AS tasa_churn_pct,
    ROUND(SUM(s.margin), 2)                                        AS margen_perdido_2024
FROM fact_sales s
WHERE s.date < '2025-01-01'
  AND s.customer_id IN (SELECT customer_id FROM churn);
