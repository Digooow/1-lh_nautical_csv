-- =============================================================================
-- Questão 4 — Top 10 Clientes Elite (Diversidade >= 13 Categorias)
-- =============================================================================
-- Correções arquiteturais aplicadas:
--   1. Filtro canônico de pedidos válidos via vw_valid_orders (status IN ('paid', 'confirmed'))
--   2. Prevenção de fan-out de JOIN: faturamento, frequência e ticket médio são
--      agregados estritamente na granularidade de pedido (vw_valid_orders) ANTES
--      do cruzamento com itens e produtos
--   3. Desempate determinístico na categoria preferida:
--      ORDER BY total_quantidade DESC, category_name ASC
-- =============================================================================

WITH receita_por_cliente AS (
    SELECT
        o.customer_id,
        SUM(o.total) AS faturamento_total,
        COUNT(*) AS frequencia,
        SUM(o.total) / COUNT(*) AS ticket_medio
    FROM vw_valid_orders o
    GROUP BY o.customer_id
),
diversidade_por_cliente AS (
    SELECT
        vi.customer_id,
        COUNT(DISTINCT vi.category_id) AS diversidade
    FROM vw_valid_order_items vi
    GROUP BY vi.customer_id
    HAVING COUNT(DISTINCT vi.category_id) >= 13
),
top_clientes AS (
    SELECT
        r.customer_id,
        ROUND(r.ticket_medio, 2) AS ticket_medio,
        d.diversidade,
        ROUND(r.faturamento_total, 2) AS faturamento_total,
        r.frequencia
    FROM receita_por_cliente r
    JOIN diversidade_por_cliente d ON d.customer_id = r.customer_id
    ORDER BY r.ticket_medio DESC, r.customer_id ASC
    LIMIT 10
),
compras_por_categoria AS (
    SELECT
        tc.customer_id,
        vi.category_id,
        vi.category_name,
        SUM(vi.quantity) AS total_quantidade
    FROM top_clientes tc
    JOIN vw_valid_order_items vi ON vi.customer_id = tc.customer_id
    GROUP BY tc.customer_id, vi.category_id, vi.category_name
),
ranking_categoria AS (
    SELECT
        customer_id,
        category_name,
        total_quantidade,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_quantidade DESC, category_name ASC
        ) AS rn
    FROM compras_por_categoria
)
SELECT
    tc.customer_id,
    tc.ticket_medio,
    tc.diversidade,
    tc.faturamento_total,
    tc.frequencia,
    rc.category_name AS categoria_preferida,
    rc.total_quantidade AS quantidade_itens
FROM top_clientes tc
JOIN ranking_categoria rc
  ON rc.customer_id = tc.customer_id
 AND rc.rn = 1
ORDER BY tc.ticket_medio DESC, tc.customer_id ASC;

