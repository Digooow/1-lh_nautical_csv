"""
Previsão de demanda mensal para produtos do catálogo (Questão 6).

Melhorias de engenharia sobre a versão original:
1. Preenchimento explícito de meses sem vendas com zero via `pd.period_range(..., freq='M')`,
   evitando saltos temporais na janela da média móvel.
2. Tratamento explícito e determinístico de homônimos no catálogo (`products.csv` possui
   dois registros com `name = 'Bússola de Bordo 702'`: `id=74` e `id=240`), permitindo
   avaliar tanto o SKU primário (`id=74`, `aggregate_homonyms=False`) quanto a demanda
   consolidada por nome comercial (`id IN (74, 240)`, `aggregate_homonyms=True`).
3. Implementação comparativa de 4 estratégias de avaliação no horizonte de teste (1T 2026):
   - Média Móvel de 3 meses Recursiva (`ma3_recursive`)
   - Média Móvel de 3 meses One-Step-Ahead (`ma3_one_step`)
   - Baseline Ingênuo — Último Mês (`naive_last`)
   - Baseline Sazonal Ingênuo — Homólogo t-12 (`seasonal_naive_12m`)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from lh_nautical.db import get_data_dir
from lh_nautical.metrics import VALID_ORDER_STATUSES, load_orders

TARGET_PRODUCT_DEFAULT = "Bússola de Bordo 702"


@dataclass(frozen=True)
class ForecastEvaluation:
    """Resultado consolidado da previsão de demanda mensal."""

    product_ids: list[int]
    product_name: str
    valid_only: bool
    aggregate_homonyms: bool
    total_months_in_grid: int
    zero_sale_months_filled: int
    train_end_period: str
    test_periods: list[str]
    test_actuals: list[int]
    predictions_df: pd.DataFrame
    metrics_summary_df: pd.DataFrame


def build_monthly_demand_series(
    product_name: str = TARGET_PRODUCT_DEFAULT,
    orders_df: pd.DataFrame | None = None,
    order_items_df: pd.DataFrame | None = None,
    product_variants_df: pd.DataFrame | None = None,
    products_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
    valid_only: bool = True,
    aggregate_homonyms: bool = False,
    start_period: str = "2020-01",
    end_period: str = "2026-03",
) -> tuple[list[int], pd.Series, int]:
    """
    Constrói a série temporal mensal contínua de unidades vendidas para um produto.

    Meses sem nenhuma venda registrada recebem explicitamente o valor `0`.
    Retorna `(product_ids, serie_mensal_continua, qtd_meses_zerados)`.
    """
    base_dir = data_dir or get_data_dir()

    if orders_df is not None:
        orders = orders_df.copy()
        orders["created_at"] = pd.to_datetime(orders["created_at"])
        if valid_only and "status" in orders.columns:
            orders = orders[orders["status"].isin(VALID_ORDER_STATUSES)].copy()
    else:
        orders = load_orders(data_dir=base_dir, valid_only=valid_only)

    order_items = (
        order_items_df.copy()
        if order_items_df is not None
        else pd.read_csv(base_dir / "order_items.csv")
    )
    variants = (
        product_variants_df.copy()
        if product_variants_df is not None
        else pd.read_csv(base_dir / "product_variants.csv")
    )
    products = (
        products_df.copy()
        if products_df is not None
        else pd.read_csv(base_dir / "products.csv")
    )

    matched_products = products[products["name"] == product_name].sort_values("id")
    if matched_products.empty:
        raise ValueError(f"Produto '{product_name}' não encontrado em products.csv.")

    if aggregate_homonyms:
        selected_product_ids = [int(x) for x in matched_products["id"].tolist()]
    else:
        selected_product_ids = [int(matched_products["id"].iloc[0])]

    variant_ids = variants.loc[
        variants["product_id"].isin(selected_product_ids), "id"
    ].tolist()
    if not variant_ids:
        raise ValueError(
            f"Nenhuma variante encontrada para '{product_name}' (ids={selected_product_ids})."
        )

    product_items = order_items[
        order_items["product_variant_id"].isin(variant_ids)
    ].merge(
        orders[["id", "created_at"]],
        left_on="order_id",
        right_on="id",
        how="inner",
    )

    full_grid = pd.period_range(start=start_period, end=end_period, freq="M")

    if product_items.empty:
        empty_series = pd.Series(0, index=full_grid, name="quantity", dtype=int)
        return selected_product_ids, empty_series, len(full_grid)

    product_items["ano_mes"] = product_items["created_at"].dt.to_period("M")
    observed_monthly = product_items.groupby("ano_mes")["quantity"].sum()
    observed_in_window = observed_monthly[
        (observed_monthly.index >= full_grid[0])
        & (observed_monthly.index <= full_grid[-1])
    ]

    continuous_series = (
        observed_in_window.reindex(full_grid, fill_value=0)
        .astype(int)
        .rename("quantity")
    )
    continuous_series.index.name = "ano_mes"
    zero_months = int((continuous_series == 0).sum())

    return selected_product_ids, continuous_series, zero_months


def evaluate_demand_forecast(
    product_name: str = TARGET_PRODUCT_DEFAULT,
    orders_df: pd.DataFrame | None = None,
    order_items_df: pd.DataFrame | None = None,
    product_variants_df: pd.DataFrame | None = None,
    products_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
    valid_only: bool = True,
    aggregate_homonyms: bool = False,
    window: int = 3,
    train_end: str = "2025-12",
    test_start: str = "2026-01",
    test_end: str = "2026-03",
) -> ForecastEvaluation:
    """
    Executa a previsão de demanda mensal (MA recursiva, MA one-step e baselines Naive).
    """
    if window < 1:
        raise ValueError("A janela da média móvel deve ser >= 1.")

    product_ids, series, zero_months = build_monthly_demand_series(
        product_name=product_name,
        orders_df=orders_df,
        order_items_df=order_items_df,
        product_variants_df=product_variants_df,
        products_df=products_df,
        data_dir=data_dir,
        valid_only=valid_only,
        aggregate_homonyms=aggregate_homonyms,
        start_period="2020-01",
        end_period=test_end,
    )

    train_period = pd.Period(train_end, freq="M")
    test_start_period = pd.Period(test_start, freq="M")
    test_end_period = pd.Period(test_end, freq="M")

    train_series = series.loc[:train_period]
    test_series = series.loc[test_start_period:test_end_period]

    if len(train_series) < window:
        raise ValueError(
            f"Histórico de treino ({len(train_series)} meses) menor que a janela ({window})."
        )

    # 1. Média Móvel Recursiva (horizonte fechado em train_end)
    hist_recursive = [float(x) for x in train_series.values]
    preds_recursive: list[float] = []
    for _ in range(len(test_series)):
        pred = float(np.mean(hist_recursive[-window:]))
        preds_recursive.append(pred)
        hist_recursive.append(pred)

    # 2. Média Móvel One-Step-Ahead (atualizada mês a mês com o realizado)
    hist_one_step = [float(x) for x in train_series.values]
    preds_one_step: list[float] = []
    for actual in test_series.values:
        pred = float(np.mean(hist_one_step[-window:]))
        preds_one_step.append(pred)
        hist_one_step.append(float(actual))

    # 3. Baseline Naive (última observação do treino)
    last_train_value = float(train_series.iloc[-1])
    preds_naive = [last_train_value] * len(test_series)

    # 4. Baseline Sazonal Naive (mesmo mês do ano anterior: t - 12)
    preds_seasonal_naive: list[float] = []
    for period in test_series.index:
        lag12_period = period - 12
        preds_seasonal_naive.append(
            float(series.loc[lag12_period])
            if lag12_period in series.index
            else last_train_value
        )

    month_labels_pt = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez",
    }

    predictions_df = pd.DataFrame(
        {
            "ano_mes": [str(p) for p in test_series.index],
            "mes_nome": [
                f"{month_labels_pt[p.month]}/{str(p.year)[2:]}"
                for p in test_series.index
            ],
            "real": [int(x) for x in test_series.values],
            "ma3_recursive": np.round(preds_recursive, 2),
            "ma3_one_step": np.round(preds_one_step, 2),
            "naive_last": np.round(preds_naive, 2),
            "seasonal_naive_12m": np.round(preds_seasonal_naive, 2),
        }
    )

    actual_arr = test_series.values.astype(float)
    model_specs = [
        ("MA(3) Recursiva", preds_recursive),
        ("MA(3) One-Step-Ahead", preds_one_step),
        ("Baseline Naive (t-1)", preds_naive),
        ("Baseline Sazonal (t-12)", preds_seasonal_naive),
    ]

    summary_rows = []
    for label, preds in model_specs:
        preds_arr = np.asarray(preds, dtype=float)
        mae = float(np.mean(np.abs(actual_arr - preds_arr)))
        rmse = float(np.sqrt(np.mean((actual_arr - preds_arr) ** 2)))
        summary_rows.append(
            {
                "modelo": label,
                "soma_real": int(actual_arr.sum()),
                "soma_prevista": int(round(float(preds_arr.sum()))),
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
            }
        )

    metrics_summary_df = pd.DataFrame(summary_rows)

    return ForecastEvaluation(
        product_ids=product_ids,
        product_name=product_name,
        valid_only=valid_only,
        aggregate_homonyms=aggregate_homonyms,
        total_months_in_grid=len(series),
        zero_sale_months_filled=zero_months,
        train_end_period=str(train_period),
        test_periods=[str(p) for p in test_series.index],
        test_actuals=[int(x) for x in test_series.values],
        predictions_df=predictions_df,
        metrics_summary_df=metrics_summary_df,
    )


if __name__ == "__main__":
    for valid_flag, titulo in [
        (True, "Pedidos Válidos (paid + confirmed)"),
        (False, "Base Completa (Gabarito Bruto)"),
    ]:
        ev = evaluate_demand_forecast(valid_only=valid_flag)
        print(
            f"\n=== Q6: Previsão de Demanda — {ev.product_name} "
            f"(IDs={ev.product_ids}) [{titulo}] ==="
        )
        print(
            f"Grade mensal: {ev.total_months_in_grid} meses | "
            f"Meses sem venda preenchidos com 0: {ev.zero_sale_months_filled}"
        )
        print("\nPrevisões Mensais (1T 2026):")
        print(ev.predictions_df.to_string(index=False))
        print("\nComparativo de Erro (MAE / RMSE):")
        print(ev.metrics_summary_df.to_string(index=False))
