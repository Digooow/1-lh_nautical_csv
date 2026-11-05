"""
Sistema de recomendação Item-Item por Similaridade de Cosseno (Questão 7).

Correção crítica (P0):
- Na implementação original, `products[products['id'].isin(top_product_ids)]['name'].tolist()`
  retornava os nomes na ordem física do arquivo `products.csv` em vez da ordem decrescente
  dos scores de similaridade, atribuindo o score `0.2566` ao `GPS Plotter 6249` (5º lugar)
  em vez do verdadeiro 1º colocado, `Motor de Popa 5331`.
- Esta implementação indexa o catálogo por `product_id` e faz `.reindex(top_product_ids)`,
  preservando a correspondência exata `1:1` entre cada produto ranqueado e seu score.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from lh_nautical.db import get_data_dir
from lh_nautical.metrics import VALID_ORDER_STATUSES, load_orders

REFERENCE_PRODUCT_DEFAULT = "Motor de Popa 1949"


def build_customer_product_matrix(
    orders_df: pd.DataFrame | None = None,
    order_items_df: pd.DataFrame | None = None,
    product_variants_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
    valid_only: bool = False,
) -> pd.DataFrame:
    """
    Constrói a matriz binária de presença `customer_id × product_id`.

    Cada célula `(u, i)` vale `1` se o cliente `u` interagiu/comprou ao menos uma
    unidade de qualquer variante do produto `i`, e `0` caso contrário.
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

    interacoes = (
        order_items[["order_id", "product_variant_id"]]
        .merge(
            variants[["id", "product_id"]].rename(columns={"id": "variant_id_lookup"}),
            left_on="product_variant_id",
            right_on="variant_id_lookup",
            how="inner",
        )
        .merge(
            orders[["id", "customer_id"]].rename(columns={"id": "order_id_lookup"}),
            left_on="order_id",
            right_on="order_id_lookup",
            how="inner",
        )[["customer_id", "product_id"]]
        .drop_duplicates()
    )

    if interacoes.empty:
        raise ValueError("Nenhuma interação cliente-produto encontrada.")

    interacoes["presenca"] = 1
    matriz = interacoes.pivot_table(
        index="customer_id",
        columns="product_id",
        values="presenca",
        fill_value=0,
        aggfunc="max",
    )
    return matriz.astype(np.int8)


def compute_product_recommendations(
    reference_product_name: str = REFERENCE_PRODUCT_DEFAULT,
    top_k: int = 5,
    orders_df: pd.DataFrame | None = None,
    order_items_df: pd.DataFrame | None = None,
    product_variants_df: pd.DataFrame | None = None,
    products_df: pd.DataFrame | None = None,
    data_dir: Path | None = None,
    valid_only: bool = False,
) -> pd.DataFrame:
    """
    Retorna os `top_k` produtos mais similares ao produto de referência via cosseno.

    Garante integridade de ordenação (`similaridade DESC, product_id ASC`) e
    associação exata entre `product_id`, `product_name` e `similaridade`.
    """
    if top_k < 1:
        raise ValueError("O parâmetro top_k deve ser >= 1.")

    base_dir = data_dir or get_data_dir()
    products = (
        products_df.copy()
        if products_df is not None
        else pd.read_csv(base_dir / "products.csv")
    )

    matched = products[products["name"] == reference_product_name]
    if matched.empty:
        raise ValueError(
            f"Produto de referência '{reference_product_name}' não encontrado em products.csv."
        )
    if len(matched) > 1:
        raise ValueError(
            f"Nome de produto de referência ambíguo: '{reference_product_name}'."
        )

    ref_product_id = int(matched["id"].iloc[0])

    matriz = build_customer_product_matrix(
        orders_df=orders_df,
        order_items_df=order_items_df,
        product_variants_df=product_variants_df,
        data_dir=base_dir,
        valid_only=valid_only,
    )

    if ref_product_id not in matriz.columns:
        raise KeyError(
            f"O produto '{reference_product_name}' (id={ref_product_id}) não possui "
            "histórico de compras na matriz cliente-produto."
        )

    product_ids = matriz.columns.to_numpy(dtype=int)
    ref_idx = int(matriz.columns.get_loc(ref_product_id))

    # Cálculo vetorizado apenas contra o vetor do produto de referência: O(N_clientes * N_produtos)
    product_vectors = matriz.T.to_numpy(dtype=float)
    ref_vector = product_vectors[ref_idx : ref_idx + 1]
    scores = cosine_similarity(ref_vector, product_vectors).ravel()

    catalogo_nomes = products.set_index("id")["name"]
    co_buyers = (product_vectors @ ref_vector.ravel()).astype(int)
    total_buyers = product_vectors.sum(axis=1).astype(int)

    ranking_df = pd.DataFrame(
        {
            "product_id": product_ids,
            "product_name": catalogo_nomes.reindex(product_ids).to_numpy(),
            "clientes_produto": total_buyers,
            "clientes_em_comum": co_buyers,
            "similaridade": scores,
        }
    )

    # Remove o próprio produto de referência e ordena com desempate determinístico
    ranking_df = (
        ranking_df[ranking_df["product_id"] != ref_product_id]
        .sort_values(
            by=["similaridade", "product_id"],
            ascending=[False, True],
        )
        .head(top_k)
        .reset_index(drop=True)
    )
    ranking_df["rank"] = np.arange(1, len(ranking_df) + 1)
    ranking_df["similaridade"] = ranking_df["similaridade"].round(4)

    return ranking_df[
        [
            "rank",
            "product_id",
            "product_name",
            "clientes_produto",
            "clientes_em_comum",
            "similaridade",
        ]
    ]


if __name__ == "__main__":
    print("=== Q7: Top 5 Produtos Similares ao 'Motor de Popa 1949' (Base Completa) ===")
    print(compute_product_recommendations(valid_only=False).to_string(index=False))

    print("\n=== Q7: Top 5 Produtos Similares ao 'Motor de Popa 1949' (Pedidos Válidos) ===")
    print(compute_product_recommendations(valid_only=True).to_string(index=False))

