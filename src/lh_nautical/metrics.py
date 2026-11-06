"""
Módulo central de regras de negócio e métricas analíticas (Q1, Q4 e Q5).

Fonte Única da Verdade (Single Source of Truth):
- Define o filtro canônico de pedidos válidos: status IN ('paid', 'confirmed').
- Garante paridade exata entre as consultas SQL no PostgreSQL, o processamento
  em Python/pandas e as visualizações do Dashboard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd

from lh_nautical.db import get_data_dir

VALID_ORDER_STATUSES: tuple[str, str] = ("paid", "confirmed")

WEEKDAY_NAMES_PT: dict[int, str] = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


class OrdersEdaReportDict(TypedDict):
    total_registros_brutos: int
    pedidos_validos: int
    status_paid: int
    status_confirmed: int
    status_cancelled: int
    status_draft: int
    canal_ecommerce: int
    canal_pos: int
    data_minima: str
    data_maxima: str
    nulos_total: int
    nulos_created_at: int
    duplicatas_id: int
    duplicatas_order_number: int
    divergencias_formula_total: int
    divergencias_soma_itens: int
    pedidos_sem_itens: int
    faturamento_bruto: float
    ticket_medio_bruto: float
    faturamento_valido: float
    ticket_medio_valido: float
    valor_minimo: float
    q1_25: float
    mediana_50: float
    q3_75: float
    valor_maximo: float
    iqr: float
    limite_superior_iqr: float
    qtd_outliers_iqr: int


@dataclass(frozen=True)
class OrdersEdaReport:
    """Estrutura consolidada de diagnóstico exploratório e auditoria contábil (Q1)."""

    total_registros_brutos: int
    pedidos_validos: int
    status_paid: int
    status_confirmed: int
    status_cancelled: int
    status_draft: int
    canal_ecommerce: int
    canal_pos: int
    data_minima: str
    data_maxima: str
    nulos_total: int
    nulos_created_at: int
    duplicatas_id: int
    duplicatas_order_number: int
    divergencias_formula_total: int
    divergencias_soma_itens: int
    pedidos_sem_itens: int
    faturamento_bruto: float
    ticket_medio_bruto: float
    faturamento_valido: float
    ticket_medio_valido: float
    valor_minimo: float
    q1_25: float
    mediana_50: float
    q3_75: float
    valor_maximo: float
    iqr: float
    limite_superior_iqr: float
    qtd_outliers_iqr: int

    def to_dict(self) -> OrdersEdaReportDict:
        """Converte o relatório em dicionário serializável estritamente tipado."""
        return asdict(self)  # type: ignore[return-value]


def load_orders(
    data_dir: Path | None = None,
    valid_only: bool = True,
) -> pd.DataFrame:
    """
    Carrega a tabela `orders.csv` com parsing temporal e filtro canônico opcional.

    Quando `valid_only=True` (padrão), exclui pedidos com status `cancelled` e `draft`,
    reproduzindo exatamente a view `vw_valid_orders` do PostgreSQL.
    """
    base_dir = data_dir or get_data_dir()
    orders = pd.read_csv(base_dir / "orders.csv")
    orders["created_at"] = pd.to_datetime(orders["created_at"])
    orders["placed_at"] = pd.to_datetime(orders["placed_at"])
    orders["updated_at"] = pd.to_datetime(orders["updated_at"])

    if valid_only:
        orders = orders[orders["status"].isin(VALID_ORDER_STATUSES)].copy()

    return orders


def compute_orders_eda(
    orders_df: pd.DataFrame | None = None,
    order_items_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
) -> OrdersEdaReport:
    """
    Executa a auditoria de qualidade, integridade contábil e distribuição (IQR) de `orders`.

    Validações de contrato de dados executadas:
    1. Unicidade de `id` e `order_number`.
    2. Identidade contábil no cabeçalho: `total == subtotal - discount_amount`.
    3. Reconciliação entre cabeçalho e itens: `orders.subtotal == SUM(order_items.line_total)`.
    4. Detecção de pedidos órfãos (sem registros em `order_items`).
    5. Identificação estatística de outliers pelo critério de Tukey (Q3 + 1.5 * IQR).
    """
    base_dir = data_dir or get_data_dir()
    raw_orders = (
        orders_df.copy()
        if orders_df is not None
        else pd.read_csv(base_dir / "orders.csv")
    )
    items = (
        order_items_df.copy()
        if order_items_df is not None
        else pd.read_csv(base_dir / "order_items.csv")
    )

    nulos_total = int(raw_orders["total"].isna().sum())
    nulos_created_at = int(raw_orders["created_at"].isna().sum())

    raw_orders["created_at"] = pd.to_datetime(raw_orders["created_at"])

    status_counts = raw_orders["status"].value_counts()
    channel_counts = raw_orders["channel"].value_counts()

    duplicatas_id = int(raw_orders["id"].duplicated().sum())
    duplicatas_order_number = int(raw_orders["order_number"].duplicated().sum())

    formula_diff = (
        raw_orders["subtotal"] - raw_orders["discount_amount"] - raw_orders["total"]
    ).abs()
    divergencias_formula_total = int((formula_diff > 0.01).sum())

    items_grouped = items.groupby("order_id", as_index=False).agg(
        soma_itens=("line_total", "sum"),
        qtd_itens=("id", "count"),
    )
    reconciled = raw_orders[["id", "subtotal"]].merge(
        items_grouped, left_on="id", right_on="order_id", how="left"
    )
    reconciled["soma_itens"] = reconciled["soma_itens"].fillna(0.0)
    reconciled["qtd_itens"] = reconciled["qtd_itens"].fillna(0).astype(int)

    divergencias_soma_itens = int(
        ((reconciled["subtotal"] - reconciled["soma_itens"]).abs() > 0.01).sum()
    )
    pedidos_sem_itens = int((reconciled["qtd_itens"] == 0).sum())

    valid_orders = raw_orders[raw_orders["status"].isin(VALID_ORDER_STATUSES)]
    if valid_orders.empty:
        raise ValueError("Nenhum pedido válido encontrado para cálculo de quartis.")

    q1 = float(np.percentile(valid_orders["total"], 25))
    mediana = float(np.percentile(valid_orders["total"], 50))
    q3 = float(np.percentile(valid_orders["total"], 75))
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    qtd_outliers = int((valid_orders["total"] > upper_fence).sum())

    return OrdersEdaReport(
        total_registros_brutos=len(raw_orders),
        pedidos_validos=len(valid_orders),
        status_paid=int(status_counts.get("paid", 0)),
        status_confirmed=int(status_counts.get("confirmed", 0)),
        status_cancelled=int(status_counts.get("cancelled", 0)),
        status_draft=int(status_counts.get("draft", 0)),
        canal_ecommerce=int(channel_counts.get("ecommerce", 0)),
        canal_pos=int(channel_counts.get("pos", 0)),
        data_minima=str(raw_orders["created_at"].min()),
        data_maxima=str(raw_orders["created_at"].max()),
        nulos_total=nulos_total,
        nulos_created_at=nulos_created_at,
        duplicatas_id=duplicatas_id,
        duplicatas_order_number=duplicatas_order_number,
        divergencias_formula_total=divergencias_formula_total,
        divergencias_soma_itens=divergencias_soma_itens,
        pedidos_sem_itens=pedidos_sem_itens,
        faturamento_bruto=round(float(raw_orders["total"].sum()), 2),
        ticket_medio_bruto=round(float(raw_orders["total"].mean()), 2),
        faturamento_valido=round(float(valid_orders["total"].sum()), 2),
        ticket_medio_valido=round(float(valid_orders["total"].mean()), 2),
        valor_minimo=round(float(valid_orders["total"].min()), 2),
        q1_25=round(q1, 2),
        mediana_50=round(mediana, 2),
        q3_75=round(q3, 2),
        valor_maximo=round(float(valid_orders["total"].max()), 2),
        iqr=round(iqr, 2),
        limite_superior_iqr=round(upper_fence, 2),
        qtd_outliers_iqr=qtd_outliers,
    )


def compute_elite_customers(
    orders_df: pd.DataFrame | None = None,
    order_items_df: pd.DataFrame | None = None,
    product_variants_df: pd.DataFrame | None = None,
    products_df: pd.DataFrame | None = None,
    categories_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
    valid_only: bool = True,
    min_categories: int = 13,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Calcula o ranking dos Top N Clientes Elite com diversidade mínima de categorias (Q4).

    Prevenção contra Fan-Out de JOIN:
    - O faturamento (`SUM(total)`), a frequência (`COUNT(id)`) e o ticket médio são
      agregados estritamente na granularidade de `orders` antes de qualquer junção
      com `order_items`.
    - O desempate da categoria preferida por volume de itens é determinístico:
      `quantidade_itens DESC, categoria_preferida ASC`.
    """
    base_dir = data_dir or get_data_dir()

    if orders_df is not None:
        orders = orders_df.copy()
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
    categories = (
        categories_df.copy()
        if categories_df is not None
        else pd.read_csv(base_dir / "categories.csv")
    )

    # 1. Agregação na granularidade de PEDIDO (sem fan-out)
    receita_cliente = orders.groupby("customer_id", as_index=False).agg(
        faturamento_total=("total", "sum"),
        frequencia=("id", "count"),
    )
    receita_cliente["ticket_medio"] = (
        receita_cliente["faturamento_total"] / receita_cliente["frequencia"]
    )

    # Guardrail de reconciliação contábil: soma por cliente jamais pode exceder soma de orders
    total_orders_revenue = float(orders["total"].sum())
    if float(receita_cliente["faturamento_total"].sum()) > total_orders_revenue + 1e-4:
        raise AssertionError("Fan-out detectado no cálculo de faturamento por cliente.")

    # 2. Cadeia de itens para cálculo de diversidade e volume por categoria
    itens_enriquecidos = (
        orders[["id", "customer_id"]]
        .merge(
            order_items[["order_id", "product_variant_id", "quantity"]],
            left_on="id",
            right_on="order_id",
            how="inner",
        )
        .merge(
            variants[["id", "product_id"]].rename(columns={"id": "variant_id_ lookup"}),
            left_on="product_variant_id",
            right_on="variant_id_ lookup",
            how="inner",
        )
        .merge(
            products[["id", "category_id"]].rename(columns={"id": "product_id_lookup"}),
            left_on="product_id",
            right_on="product_id_lookup",
            how="inner",
        )
        .merge(
            categories[["id", "name"]].rename(
                columns={"id": "cat_id_lookup", "name": "category_name"}
            ),
            left_on="category_id",
            right_on="cat_id_lookup",
            how="inner",
        )
    )

    diversidade_cliente = itens_enriquecidos.groupby("customer_id", as_index=False).agg(
        diversidade=("category_id", "nunique")
    )
    diversidade_filtrada = diversidade_cliente[
        diversidade_cliente["diversidade"] >= min_categories
    ]

    top_clientes = (
        receita_cliente.merge(diversidade_filtrada, on="customer_id", how="inner")
        .sort_values(
            by=["ticket_medio", "customer_id"],
            ascending=[False, True],
        )
        .head(top_n)
        .copy()
    )

    if top_clientes.empty:
        return pd.DataFrame(
            columns=[
                "customer_id",
                "ticket_medio",
                "diversidade",
                "faturamento_total",
                "frequencia",
                "categoria_preferida",
                "quantidade_itens",
            ]
        )

    # 3. Categoria preferida restrita aos Top N clientes com desempate alfabético
    compras_cat = (
        itens_enriquecidos[
            itens_enriquecidos["customer_id"].isin(top_clientes["customer_id"])
        ]
        .groupby(["customer_id", "category_id", "category_name"], as_index=False)[
            "quantity"
        ]
        .sum()
        .rename(columns={"quantity": "quantidade_itens"})
        .sort_values(
            by=["customer_id", "quantidade_itens", "category_name"],
            ascending=[True, False, True],
        )
    )
    preferida_por_cliente = compras_cat.drop_duplicates(
        subset=["customer_id"], keep="first"
    ).rename(columns={"category_name": "categoria_preferida"})

    resultado = (
        top_clientes.merge(
            preferida_por_cliente[
                ["customer_id", "categoria_preferida", "quantidade_itens"]
            ],
            on="customer_id",
            how="left",
        )
        .sort_values(by=["ticket_medio", "customer_id"], ascending=[False, True])
        .reset_index(drop=True)
    )

    resultado["ticket_medio"] = resultado["ticket_medio"].round(2)
    resultado["faturamento_total"] = resultado["faturamento_total"].round(2)
    resultado["diversidade"] = resultado["diversidade"].astype(int)
    resultado["frequencia"] = resultado["frequencia"].astype(int)
    resultado["quantidade_itens"] = resultado["quantidade_itens"].astype(int)

    return resultado[
        [
            "customer_id",
            "ticket_medio",
            "diversidade",
            "faturamento_total",
            "frequencia",
            "categoria_preferida",
            "quantidade_itens",
        ]
    ]


def compute_weekday_sales(
    orders_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
    valid_only: bool = True,
    channel: str | None = "pos",
) -> pd.DataFrame:
    """
    Calcula a média de vendas diárias por dia da semana usando dimensão calendário (Q5).

    Regras aplicadas:
    - Padroniza o filtro de pedidos válidos (`valid_only=True`) e o canal (`channel='pos'`).
    - Constrói um calendário diário contínuo (`pd.date_range`) entre a menor e a maior
      data do recorte e preenche dias sem faturamento com `0.0`.
    - Mapeia `dt.dayofweek` segundo o padrão ISO-8601 (`0 = Segunda-feira ... 6 = Domingo`).
    """
    base_dir = data_dir or get_data_dir()

    if orders_df is not None:
        orders = orders_df.copy()
        orders["created_at"] = pd.to_datetime(orders["created_at"])
        if valid_only and "status" in orders.columns:
            orders = orders[orders["status"].isin(VALID_ORDER_STATUSES)].copy()
    else:
        orders = load_orders(data_dir=base_dir, valid_only=valid_only)

    if channel is not None:
        orders = orders[orders["channel"] == channel].copy()

    if orders.empty:
        raise ValueError("Nenhum pedido encontrado para o filtro selecionado.")

    orders["data"] = orders["created_at"].dt.floor("D")
    data_inicio = orders["data"].min()
    data_fim = orders["data"].max()

    calendario = pd.DataFrame(
        {"data": pd.date_range(start=data_inicio, end=data_fim, freq="D")}
    )
    vendas_diarias = orders.groupby("data", as_index=False).agg(
        total_dia=("total", "sum")
    )

    calendario_vendas = calendario.merge(vendas_diarias, on="data", how="left")
    calendario_vendas["teve_venda"] = calendario_vendas["total_dia"].notna().astype(int)
    calendario_vendas["total_dia"] = calendario_vendas["total_dia"].fillna(0.0)
    calendario_vendas["dia_semana_num"] = calendario_vendas["data"].dt.dayofweek
    calendario_vendas["dia_semana"] = calendario_vendas["dia_semana_num"].map(
        WEEKDAY_NAMES_PT
    )

    resumo = (
        calendario_vendas.groupby(["dia_semana_num", "dia_semana"], as_index=False)
        .agg(
            dias_calendario=("data", "count"),
            dias_com_venda=("teve_venda", "sum"),
            receita_total=("total_dia", "sum"),
            media_vendas=("total_dia", "mean"),
        )
        .assign(
            dias_sem_venda=lambda d: d["dias_calendario"] - d["dias_com_venda"],
            receita_total=lambda d: d["receita_total"].round(2),
            media_vendas=lambda d: d["media_vendas"].round(2),
        )
        .sort_values(by=["media_vendas", "dia_semana_num"], ascending=[True, True])
        .reset_index(drop=True)
    )

    return resumo[
        [
            "dia_semana_num",
            "dia_semana",
            "dias_calendario",
            "dias_com_venda",
            "dias_sem_venda",
            "receita_total",
            "media_vendas",
        ]
    ]


if __name__ == "__main__":
    eda = compute_orders_eda()
    print("=== Q1: Auditoria e EDA (orders) ===")
    for k, v in eda.to_dict().items():
        print(f"  {k:<28}: {v}")

    print("\n=== Q4: Top 10 Clientes Elite (Pedidos Válidos) ===")
    print(compute_elite_customers(valid_only=True).to_string(index=False))

    print("\n=== Q5: Média Diária por Dia da Semana (Canal POS | Pedidos Válidos) ===")
    print(compute_weekday_sales(valid_only=True, channel="pos").to_string(index=False))

