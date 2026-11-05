-- =============================================================================
-- Questão 5 — Média de Vendas Diárias por Dia da Semana (Dimensão Calendário)
-- =============================================================================
-- Regras aplicadas:
--   1. SQL puro e autoexecutável (sem comandos de shell embutidos)
--   2. Fonte única da verdade: vw_valid_orders (status IN ('paid', 'confirmed'))
--      filtrada pelo canal de loja física (channel = 'pos')
--   3. Geração explícita de série contínua de datas (generate_series) e LEFT JOIN
--      com COALESCE(..., 0) para incluir dias sem faturamento no denominador
--   4. Padronização ISO-8601 do dia da semana (0 = Segunda-feira ... 6 = Domingo),
--      compatível com pandas.Series.dt.dayofweek
-- =============================================================================

WITH limites_calendario AS (
    SELECT
        MIN(created_at::DATE) AS data_inicio,
        MAX(created_at::DATE) AS data_fim
    FROM vw_valid_orders
    WHERE channel = 'pos'
),
calendario AS (
    SELECT
        generate_series(
            (SELECT data_inicio FROM limites_calendario),
            (SELECT data_fim FROM limites_calendario),
            INTERVAL '1 day'
        )::DATE AS data
),
vendas_diarias AS (
    SELECT
        created_at::DATE AS data,
        SUM(total) AS total_dia
    FROM vw_valid_orders
    WHERE channel = 'pos'
    GROUP BY created_at::DATE
),
calendario_vendas AS (
    SELECT
        c.data,
        (EXTRACT(ISODOW FROM c.data)::INTEGER - 1) AS dia_semana_num,
        COALESCE(vd.total_dia, 0.00) AS total_dia,
        CASE WHEN vd.total_dia IS NULL THEN 0 ELSE 1 END AS teve_venda
    FROM calendario c
    LEFT JOIN vendas_diarias vd ON vd.data = c.data
)
SELECT
    dia_semana_num,
    CASE dia_semana_num
        WHEN 0 THEN 'Segunda-feira'
        WHEN 1 THEN 'Terça-feira'
        WHEN 2 THEN 'Quarta-feira'
        WHEN 3 THEN 'Quinta-feira'
        WHEN 4 THEN 'Sexta-feira'
        WHEN 5 THEN 'Sábado'
        WHEN 6 THEN 'Domingo'
    END AS dia_semana,
    COUNT(*) AS dias_calendario,
    SUM(teve_venda) AS dias_com_venda,
    COUNT(*) - SUM(teve_venda) AS dias_sem_venda,
    ROUND(SUM(total_dia), 2) AS receita_total,
    ROUND(AVG(total_dia), 2) AS media_vendas
FROM calendario_vendas
GROUP BY dia_semana_num
ORDER BY media_vendas ASC, dia_semana_num ASC;

