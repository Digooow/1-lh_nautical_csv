"""
Sistema de recomendação baseado em similaridade de cosseno.
Identifica os 5 produtos mais similares ao 'Motor de Popa 1949'.
"""

import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity


script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))
data_dir = os.path.join(root_dir, 'data')


products = pd.read_csv(os.path.join(data_dir, 'products.csv'))
variants = pd.read_csv(os.path.join(data_dir, 'product_variants.csv'))
order_items = pd.read_csv(os.path.join(data_dir, 'order_items.csv'))
orders = pd.read_csv(os.path.join(data_dir, 'orders.csv'))


produto_ref = "Motor de Popa 1949"
produto_ref_id = products[products['name'] == produto_ref]['id'].iloc[0]



items_com_produto = pd.merge(order_items, variants[['id', 'product_id']],
                             left_on='product_variant_id', right_on='id')


compras = pd.merge(items_com_produto, orders[['id', 'customer_id']],
                   left_on='order_id', right_on='id')


compras = compras[['customer_id', 'product_id']].drop_duplicates()
compras['presenca'] = 1


matriz = compras.pivot_table(index='customer_id', columns='product_id',
                             values='presenca', fill_value=0)


produtos_vetores = matriz.T.values
similaridade = cosine_similarity(produtos_vetores)


idx_ref = matriz.columns.get_loc(produto_ref_id)
scores = similaridade[idx_ref].copy()
scores[idx_ref] = -1   

top_indices = np.argsort(scores)[::-1][:5]
top_product_ids = matriz.columns[top_indices].tolist()
top_nomes = products[products['id'].isin(top_product_ids)]['name'].tolist()
top_scores = scores[top_indices].tolist()


print(f"Produto de referência: {produto_ref}")
print("\nRanking dos 5 produtos mais similares:")
for i, (nome, score) in enumerate(zip(top_nomes, top_scores), 1):
    print(f"{i}. {nome} (similaridade = {score:.4f})")