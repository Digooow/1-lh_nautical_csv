"""
Suíte de testes automatizados para validação das regras de negócio e contratos de dados.

Cobre:
1. Prevenção de fan-out de JOIN no cálculo de faturamento e ticket médio (Q4).
2. Exclusão canônica de pedidos `cancelled` e `draft` e desempate determinístico de categoria.
3. Mapeamento correto de `dt.dayofweek` (0 = Segunda-feira ... 6 = Domingo) e preenchimento
   de dias sem venda na dimensão calendário (Q5).
4. Preenchimento de meses sem venda (`reindex` mensal com zero) e cálculo exato das médias
   móveis recursiva e one-step-ahead (Q6).
5. Preservação estrita da ordenação por score na recomendação por similaridade de cosseno,
   independentemente da ordem física de `products.csv` (Q7).
6. Testes de contrato e gabarito sobre os dados reais do projeto (`data/*.csv`).
"""

from __future__ import annotations

import unittest

import pandas as pd

from lh_nautical.forecasting import (
    build_monthly_demand_series,
    evaluate_demand_forecast,
)
from lh_nautical.metrics import (
    compute_elite_customers,
    compute_orders_eda,
    compute_weekday_sales,
)
from lh_nautical.recommender import compute_product_recommendations


class TestLhNauticalMetrics(unittest.TestCase):
    """Testes unitários com fixtures sintéticas controladas e testes de integração na base real."""

    def test_elite_customers_prevents_join_fan_out_and_breaks_ties(self) -> None:
        """
        Um pedido com múltiplos itens deve ter seu `total` contabilizado uma única vez.
        """
        orders = pd.DataFrame(
            [
                # Cliente 10: 1 pedido válido de R$ 1.000,00 com 3 itens + 1 pedido cancelado de R$ 9.000,00
                {
                    "id": 1,
                    "customer_id": 10,
                    "status": "paid",
                    "channel": "pos",
                    "subtotal": 1000.0,
                    "discount_amount": 0.0,
                    "total": 1000.0,
                    "created_at": "2025-01-10 10:00:00",
                },
                {
                    "id": 2,
                    "customer_id": 10,
                    "status": "cancelled",
                    "channel": "pos",
                    "subtotal": 9000.0,
                    "discount_amount": 0.0,
                    "total": 9000.0,
                    "created_at": "2025-01-11 10:00:00",
                },
            ]
        )
        # 3 itens no mesmo pedido (id=1), com empate de quantidade (5 vs 5) entre Zebra e Ancoragem
        order_items = pd.DataFrame(
            [
                {"id": 101, "order_id": 1, "product_variant_id": 1, "quantity": 5, "line_total": 400.0},
                {"id": 102, "order_id": 1, "product_variant_id": 2, "quantity": 5, "line_total": 400.0},
                {"id": 103, "order_id": 1, "product_variant_id": 3, "quantity": 2, "line_total": 200.0},
            ]
        )
        variants = pd.DataFrame(
            [
                {"id": 1, "product_id": 1},
                {"id": 2, "product_id": 2},
                {"id": 3, "product_id": 3},
            ]
        )
        products = pd.DataFrame(
            [
                {"id": 1, "category_id": 1, "name": "Prod A"},
                {"id": 2, "category_id": 2, "name": "Prod B"},
                {"id": 3, "category_id": 3, "name": "Prod C"},
            ]
        )
        categories = pd.DataFrame(
            [
                {"id": 1, "name": "Zebra Náutica"},
                {"id": 2, "name": "Ancoragem"},
                {"id": 3, "name": "Cabos"},
            ]
        )

        res = compute_elite_customers(
            orders_df=orders,
            order_items_df=order_items,
            product_variants_df=variants,
            products_df=products,
            categories_df=categories,
            valid_only=True,
            min_categories=3,
            top_n=10,
        )

        self.assertEqual(len(res), 1)
        row = res.iloc[0]
        # Sem fan-out: R$ 1.000,00 (e não 3 * 1.000 = R$ 3.000,00) e sem o pedido cancelado
        self.assertAlmostEqual(float(row["faturamento_total"]), 1000.00, places=2)
        self.assertAlmostEqual(float(row["ticket_medio"]), 1000.00, places=2)
        self.assertEqual(int(row["frequencia"]), 1)
        self.assertEqual(int(row["diversidade"]), 3)
        # Desempate alfabético entre 'Ancoragem' (5) e 'Zebra Náutica' (5) -> 'Ancoragem'
        self.assertEqual(str(row["categoria_preferida"]), "Ancoragem")
        self.assertEqual(int(row["quantidade_itens"]), 5)

    def test_weekday_sales_iso_mapping_and_zero_day_padding(self) -> None:
        """
        2024-01-01 e 2024-01-15 são Segundas-feiras (dayofweek=0).
        A segunda-feira intermediária (2024-01-08) não tem vendas e deve entrar com R$ 0,00.
        """
        orders = pd.DataFrame(
            [
                {
                    "id": 1,
                    "status": "paid",
                    "channel": "pos",
                    "total": 300.0,
                    "created_at": "2024-01-01 09:00:00",  # Segunda-feira
                },
                {
                    "id": 2,
                    "status": "confirmed",
                    "channel": "pos",
                    "total": 600.0,
                    "created_at": "2024-01-15 14:00:00",  # Segunda-feira (2024-01-08 ficou sem venda)
                },
            ]
        )

        df = compute_weekday_sales(orders_df=orders, valid_only=True, channel="pos")
        self.assertEqual(len(df), 7)

        monday_row = df[df["dia_semana_num"] == 0].iloc[0]
        self.assertEqual(monday_row["dia_semana"], "Segunda-feira")
        self.assertEqual(int(monday_row["dias_calendario"]), 3)
        self.assertEqual(int(monday_row["dias_com_venda"]), 2)
        self.assertEqual(int(monday_row["dias_sem_venda"]), 1)
        # Média correta com calendário: (300 + 0 + 600) / 3 = 300.00 (sem calendário seria 450.00)
        self.assertAlmostEqual(float(monday_row["media_vendas"]), 300.00, places=2)

    def test_forecasting_fills_missing_months_with_zero(self) -> None:
        """
        Verifica que meses sem vendas dentro da janela recebem 0 antes do cálculo da MA(3).
        """
        orders = pd.DataFrame(
            [
                {"id": 1, "status": "paid", "created_at": "2025-10-10 10:00:00"},
                # 2025-11 ausente -> deve ser preenchido com 0
                {"id": 2, "status": "paid", "created_at": "2025-12-10 10:00:00"},
                {"id": 3, "status": "paid", "created_at": "2026-01-10 10:00:00"},
                {"id": 4, "status": "paid", "created_at": "2026-02-10 10:00:00"},
                {"id": 5, "status": "paid", "created_at": "2026-03-10 10:00:00"},
            ]
        )
        order_items = pd.DataFrame(
            [
                {"order_id": 1, "product_variant_id": 10, "quantity": 30},
                {"order_id": 2, "product_variant_id": 10, "quantity": 30},
                {"order_id": 3, "product_variant_id": 10, "quantity": 50},
                {"order_id": 4, "product_variant_id": 10, "quantity": 40},
                {"order_id": 5, "product_variant_id": 10, "quantity": 60},
            ]
        )
        variants = pd.DataFrame([{"id": 10, "product_id": 74}])
        products = pd.DataFrame([{"id": 74, "name": "Bússola de Bordo 702"}])

        _, series, _ = build_monthly_demand_series(
            product_name="Bússola de Bordo 702",
            orders_df=orders,
            order_items_df=order_items,
            product_variants_df=variants,
            products_df=products,
            start_period="2025-10",
            end_period="2026-03",
        )
        self.assertEqual(int(series.loc[pd.Period("2025-11", freq="M")]), 0)

        ev = evaluate_demand_forecast(
            product_name="Bússola de Bordo 702",
            orders_df=orders,
            order_items_df=order_items,
            product_variants_df=variants,
            products_df=products,
            window=3,
        )
        # Previsão para 2026-01 = média(30, 0, 30) = 20.0
        jan_pred = float(ev.predictions_df.loc[0, "ma3_recursive"])
        self.assertAlmostEqual(jan_pred, 20.00, places=2)

    def test_recommender_preserves_similarity_order_regardless_of_catalog_order(self) -> None:
        """
        Garante que a ordem física de `products.csv` não embaralha os nomes do ranking.
        """
        # No catálogo físico, ID 10 aparece antes do ID 99, mas ID 99 tem similaridade 1.0 com ID 1
        products = pd.DataFrame(
            [
                {"id": 1, "name": "Motor de Popa 1949"},
                {"id": 10, "name": "Produto Baixa Similaridade"},
                {"id": 99, "name": "Produto Alta Similaridade"},
            ]
        )
        variants = pd.DataFrame(
            [
                {"id": 1, "product_id": 1},
                {"id": 10, "product_id": 10},
                {"id": 99, "product_id": 99},
            ]
        )
        # Clientes 1, 2 e 3 compraram Produto 1 e Produto 99 juntos; apenas Cliente 1 comprou Produto 10 (+ Clientes 4, 5)
        orders = pd.DataFrame(
            [
                {"id": 1, "customer_id": 1, "status": "paid"},
                {"id": 2, "customer_id": 2, "status": "paid"},
                {"id": 3, "customer_id": 3, "status": "paid"},
                {"id": 4, "customer_id": 4, "status": "paid"},
                {"id": 5, "customer_id": 5, "status": "paid"},
            ]
        )
        order_items = pd.DataFrame(
            [
                {"order_id": 1, "product_variant_id": 1},
                {"order_id": 1, "product_variant_id": 99},
                {"order_id": 1, "product_variant_id": 10},
                {"order_id": 2, "product_variant_id": 1},
                {"order_id": 2, "product_variant_id": 99},
                {"order_id": 3, "product_variant_id": 1},
                {"order_id": 3, "product_variant_id": 99},
                {"order_id": 4, "product_variant_id": 10},
                {"order_id": 5, "product_variant_id": 10},
            ]
        )

        rec = compute_product_recommendations(
            reference_product_name="Motor de Popa 1949",
            top_k=2,
            orders_df=orders,
            order_items_df=order_items,
            product_variants_df=variants,
            products_df=products,
        )

        self.assertEqual(int(rec.loc[0, "product_id"]), 99)
        self.assertEqual(str(rec.loc[0, "product_name"]), "Produto Alta Similaridade")
        self.assertAlmostEqual(float(rec.loc[0, "similaridade"]), 1.0000, places=4)

        self.assertEqual(int(rec.loc[1, "product_id"]), 10)
        self.assertEqual(str(rec.loc[1, "product_name"]), "Produto Baixa Similaridade")
        self.assertAlmostEqual(float(rec.loc[1, "similaridade"]), 0.3333, places=4)

    def test_real_dataset_contracts_and_gabarito(self) -> None:
        """
        Valida os números de gabarito diretamente sobre os CSVs reais do projeto.
        """
        eda = compute_orders_eda()
        self.assertEqual(eda.total_registros_brutos, 48998)
        self.assertEqual(eda.pedidos_validos, 41700)
        self.assertEqual(eda.divergencias_formula_total, 0)
        self.assertEqual(eda.divergencias_soma_itens, 0)
        self.assertEqual(eda.pedidos_sem_itens, 0)

        # Q4: Verifica ausência de fan-out tanto na visão válida quanto na base completa
        elite_valid = compute_elite_customers(valid_only=True)
        self.assertEqual(int(elite_valid.loc[0, "customer_id"]), 300)
        self.assertAlmostEqual(float(elite_valid.loc[0, "ticket_medio"]), 45525.24, places=2)
        self.assertLessEqual(float(elite_valid["faturamento_total"].sum()), eda.faturamento_valido)

        elite_all = compute_elite_customers(valid_only=False)
        self.assertEqual(int(elite_all.loc[0, "customer_id"]), 22)
        self.assertAlmostEqual(float(elite_all.loc[0, "ticket_medio"]), 41839.94, places=2)

        # Q5: Menor média diária no POS
        weekday_pos = compute_weekday_sales(valid_only=True, channel="pos")
        self.assertEqual(str(weekday_pos.loc[0, "dia_semana"]), "Quinta-feira")
        self.assertAlmostEqual(float(weekday_pos.loc[0, "media_vendas"]), 134118.35, places=2)

        # Q6: Série mensal contínua de 75 meses
        fc_raw = evaluate_demand_forecast(valid_only=False)
        self.assertEqual(fc_raw.total_months_in_grid, 75)
        self.assertEqual(fc_raw.zero_sale_months_filled, 7)
        ma3_rec_row = fc_raw.metrics_summary_df.iloc[0]
        self.assertEqual(int(ma3_rec_row["soma_prevista"]), 72)
        self.assertAlmostEqual(float(ma3_rec_row["mae"]), 28.02, places=2)

        # Q7: Motor de Popa 5331 deve liderar o ranking com 0.2566 (e GPS Plotter 6249 em 5º com 0.2377)
        rec_raw = compute_product_recommendations(valid_only=False, top_k=5)
        self.assertEqual(str(rec_raw.loc[0, "product_name"]), "Motor de Popa 5331")
        self.assertAlmostEqual(float(rec_raw.loc[0, "similaridade"]), 0.2566, places=4)
        self.assertEqual(str(rec_raw.loc[4, "product_name"]), "GPS Plotter 6249")
        self.assertAlmostEqual(float(rec_raw.loc[4, "similaridade"]), 0.2377, places=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)

