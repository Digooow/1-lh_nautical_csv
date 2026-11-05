-- =============================================================================
-- Questão 1.1 — Diagnóstico Exploratório e Auditoria Contábil da Tabela orders
-- =============================================================================
-- Verifica:
--   1. Volumetria por status (paid, confirmed, cancelled, draft) e por canal
--   2. Cobertura temporal (created_at) e completude de campos obrigatórios
--   3. Reconciliação contábil:
--      a) total = subtotal - discount_amount
--      b) subtotal do pedido = soma de line_total em order_items
--      c) existência de pedidos órfãos (sem itens)
--   4. Distribuição estatística e detecção de outliers pelo critério de Tukey (IQR)
--      sobre os pedidos comercialmente válidos (vw_valid_orders) e base bruta
-- =============================================================================

WITH reconciliacao_itens AS (
    SELECT
        o.id AS order_id,
        o.subtotal,
        COALESCE(SUM(oi.line_total), 0) AS soma_itens,
        COUNT(oi.id) AS qtd_itens
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    GROUP BY o.id, o.subtotal
),
auditoria_base AS (
    SELECT
        COUNT(*) AS total_registros_brutos,
        COUNT(*) FILTER (WHERE o.status IN ('paid', 'confirmed')) AS pedidos_validos,
        COUNT(*) FILTER (WHERE o.status = 'paid') AS status_paid,
        COUNT(*) FILTER (WHERE o.status = 'confirmed') AS status_confirmed,
        COUNT(*) FILTER (WHERE o.status = 'cancelled') AS status_cancelled,
        COUNT(*) FILTER (WHERE o.status = 'draft') AS status_draft,
        COUNT(*) FILTER (WHERE o.channel = 'ecommerce') AS canal_ecommerce,
        COUNT(*) FILTER (WHERE o.channel = 'pos') AS canal_pos,
        MIN(o.created_at) AS data_minima,
        MAX(o.created_at) AS data_maxima,
        COUNT(*) FILTER (WHERE o.total IS NULL) AS nulos_total,
        COUNT(*) FILTER (WHERE o.created_at IS NULL) AS nulos_created_at,
        COUNT(*) FILTER (WHERE ABS((o.subtotal - o.discount_amount) - o.total) > 0.01) AS divergencias_formula_total,
        COUNT(*) FILTER (WHERE ABS(ri.soma_itens - o.subtotal) > 0.01) AS divergencias_soma_itens,
        COUNT(*) FILTER (WHERE ri.qtd_itens = 0) AS pedidos_sem_itens,
        ROUND(AVG(o.total), 2) AS ticket_medio_bruto,
        ROUND(SUM(o.total), 2) AS faturamento_bruto
    FROM orders o
    JOIN reconciliacao_itens ri ON ri.order_id = o.id
),
quartis_validos AS (
    SELECT
        MIN(total) AS valor_minimo,
        MAX(total) AS valor_maximo,
        ROUND(AVG(total), 2) AS ticket_medio_valido,
        ROUND(SUM(total), 2) AS faturamento_valido,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total) AS q1,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total) AS mediana,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total) AS q3
    FROM vw_valid_orders
),
outliers_validos AS (
    SELECT
        q.*,
        ROUND((q.q3 - q.q1)::NUMERIC, 2) AS iqr,
        ROUND((q.q3 + 1.5 * (q.q3 - q.q1))::NUMERIC, 2) AS limite_superior_iqr,
        (
            SELECT COUNT(*)
            FROM vw_valid_orders v
            WHERE v.total > (q.q3 + 1.5 * (q.q3 - q.q1))
        ) AS qtd_outliers_iqr
    FROM quartis_validos q
)
SELECT
    a.total_registros_brutos,
    a.pedidos_validos,
    a.status_paid,
    a.status_confirmed,
    a.status_cancelled,
    a.status_draft,
    a.canal_ecommerce,
    a.canal_pos,
    a.data_minima,
    a.data_maxima,
    a.nulos_total,
    a.nulos_created_at,
    a.divergencias_formula_total,
    a.divergencias_soma_itens,
    a.pedidos_sem_itens,
    a.faturamento_bruto,
    a.ticket_medio_bruto,
    o.faturamento_valido,
    o.ticket_medio_valido,
    o.valor_minimo,
    ROUND(o.q1::NUMERIC, 2) AS q1_25,
    ROUND(o.mediana::NUMERIC, 2) AS mediana_50,
    ROUND(o.q3::NUMERIC, 2) AS q3_75,
    o.valor_maximo,
    o.iqr,
    o.limite_superior_iqr,
    o.qtd_outliers_iqr
FROM auditoria_base a
CROSS JOIN outliers_validos o;

