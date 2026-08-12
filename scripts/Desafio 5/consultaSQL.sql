-- ========================================================================
-- Questão 5 – Média de vendas por dia da semana (com calendário)
-- ========================================================================

WITH
-- 1. Datas limite do período (apenas lojas físicas)
datas_limites AS (
  SELECT
    MIN(created_at::DATE) AS data_inicio,
    MAX(created_at::DATE) AS data_fim
  FROM orders
  WHERE channel = 'pos'
),

-- 2. Calendário completo (todos os dias do período)
calendario AS (
  SELECT
    generate_series(
      (SELECT data_inicio FROM datas_limites),
      (SELECT data_fim FROM datas_limites),
      '1 day'::INTERVAL
    )::DATE AS data
),

-- 3. Vendas diárias (soma do total por dia, apenas lojas físicas)
vendas_diarias AS (
  SELECT
    created_at::DATE AS data,
    SUM(total) AS total_dia
  FROM orders
  WHERE channel = 'pos'
  GROUP BY created_at::DATE
),

-- 4. Cruzamento calendário × vendas (com zeros para dias sem venda)
vendas_por_dia AS (
  SELECT
    c.data,
    COALESCE(vd.total_dia, 0) AS total_dia
  FROM calendario c
  LEFT JOIN vendas_diarias vd ON c.data = vd.data
)

-- 5. Média por dia da semana
SELECT
  CASE EXTRACT(DOW FROM data)
    WHEN 0 THEN 'Domingo'
    WHEN 1 THEN 'Segunda-feira'
    WHEN 2 THEN 'Terça-feira'
    WHEN 3 THEN 'Quarta-feira'
    WHEN 4 THEN 'Quinta-feira'
    WHEN 5 THEN 'Sexta-feira'
    WHEN 6 THEN 'Sábado'
  END AS dia_semana,
  AVG(total_dia) AS media_vendas
FROM vendas_por_dia
GROUP BY EXTRACT(DOW FROM data)
ORDER BY media_vendas ASC
LIMIT 1;   -- o primeiro é o dia com a pior média