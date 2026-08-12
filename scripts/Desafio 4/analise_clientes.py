"""
Analise de clientes - Ranking dos 10 clientes com maior ticket medio
e diversidade >= 13 categorias. Identifica a categoria preferida de cada um.
"""

import subprocess
import csv
import io

CONTAINER = 'postgres-challenge'
DB_USER = 'challenge'
DB_NAME = 'challenge_db'


def executar_consulta(sql):

    cmd = [
        'docker', 'exec', '-i', CONTAINER,
        'psql', '-U', DB_USER, '-d', DB_NAME,
        '--csv',
        '-c', sql
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Erro ao executar SQL: {stderr}")
    if not stdout.strip():
        return []
    reader = csv.DictReader(io.StringIO(stdout))
    return list(reader)


def main():
    sql = """
    WITH customer_stats AS (
      SELECT
        o.customer_id,
        SUM(o.total) AS faturamento_total,
        COUNT(DISTINCT o.id) AS frequencia,
        SUM(o.total) / COUNT(DISTINCT o.id) AS ticket_medio,
        COUNT(DISTINCT p.category_id) AS diversidade
      FROM orders o
      JOIN order_items oi ON o.id = oi.order_id
      JOIN product_variants pv ON oi.product_variant_id = pv.id
      JOIN products p ON pv.product_id = p.id
      GROUP BY o.customer_id
      HAVING COUNT(DISTINCT p.category_id) >= 13
    ),
    top_clientes AS (
      SELECT
        customer_id,
        ticket_medio,
        diversidade,
        faturamento_total,
        frequencia
      FROM customer_stats
      ORDER BY ticket_medio DESC, customer_id ASC
      LIMIT 10
    ),
    categoria_compras AS (
      SELECT
        tc.customer_id,
        p.category_id,
        c.name AS category_name,
        SUM(oi.quantity) AS total_quantidade
      FROM top_clientes tc
      JOIN orders o ON tc.customer_id = o.customer_id
      JOIN order_items oi ON o.id = oi.order_id
      JOIN product_variants pv ON oi.product_variant_id = pv.id
      JOIN products p ON pv.product_id = p.id
      JOIN categories c ON p.category_id = c.id
      GROUP BY tc.customer_id, p.category_id, c.name
    ),
    ranking_categoria AS (
      SELECT
        customer_id,
        category_name,
        total_quantidade,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_quantidade DESC) AS rn
      FROM categoria_compras
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
    LEFT JOIN ranking_categoria rc ON tc.customer_id = rc.customer_id AND rc.rn = 1
    ORDER BY tc.ticket_medio DESC, tc.customer_id ASC;
    """

    try:
        resultados = executar_consulta(sql)
        if not resultados:
            print("Nenhum cliente encontrado com diversidade >= 13.")
            return

        print("=" * 90)
        print("TOP 10 CLIENTES ELITE (Ticket Medio + Diversidade >= 13)")
        print("=" * 90)
        print(f"{'Cliente':<10} {'Ticket Medio':>15} {'Diversidade':>12} "
              f"{'Faturamento':>15} {'Frequencia':>10} {'Categoria Preferida':<30} {'Qtd Itens':>10}")
        print("-" * 90)

        for linha in resultados:
            print(f"{linha['customer_id']:<10} "
                  f"{float(linha['ticket_medio']):>15.2f} "
                  f"{int(linha['diversidade']):>12} "
                  f"{float(linha['faturamento_total']):>15.2f} "
                  f"{int(linha['frequencia']):>10} "
                  f"{linha['categoria_preferida']:<30} "
                  f"{int(linha['quantidade_itens']):>10}")

    except Exception as e:
        print(f"Erro: {e}")


if __name__ == '__main__':
    main()