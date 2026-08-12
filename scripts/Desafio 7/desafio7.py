import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity   # opcional, mas mais simples

# ============================================================================
# 1. Leitura dos CSVs
# ============================================================================
products = pd.read_csv('products.csv')
variants = pd.read_csv('product_variants.csv')
order_items = pd.read_csv('order_items.csv')
orders = pd.read_csv('orders.csv')

# ============================================================================
# 2. Identificar o produto de referência
# ============================================================================
produto_ref = "Motor de Popa 1949"
produto_ref_id = products[products['name'] == produto_ref]['id'].iloc[0]

# ============================================================================
# 3. Construir a matriz usuário × produto (presença/ausência)
# ============================================================================
# Junta order_items com variants para obter product_id
items_com_produto = pd.merge(order_items, variants[['id', 'product_id']],
                             left_on='product_variant_id', right_on='id')

# Junta com orders para obter customer_id
compras = pd.merge(items_com_produto, orders[['id', 'customer_id']],
                   left_on='order_id', right_on='id')

# Mantém apenas as colunas relevantes e remove duplicatas (um cliente pode comprar o mesmo produto várias vezes)
compras = compras[['customer_id', 'product_id']].drop_duplicates()

# Cria coluna de presença
compras['presenca'] = 1

# Cria a matriz pivot (clientes como índice, produtos como colunas)
matriz = compras.pivot_table(index='customer_id', columns='product_id',
                             values='presenca', fill_value=0)

# ============================================================================
# 4. Calcular similaridade de cosseno entre produtos
# ============================================================================
# Transpor: produtos como linhas, clientes como colunas
produtos_vetores = matriz.T.values

# Usar sklearn para similaridade (mais simples e eficiente)
similaridade = cosine_similarity(produtos_vetores)

# ============================================================================
# 5. Ranking dos 5 produtos mais similares ao "Motor de Popa 1949"
# ============================================================================
# Índice do produto referência na matriz
idx_ref = matriz.columns.get_loc(produto_ref_id)

# Scores de similaridade com todos os outros produtos
scores = similaridade[idx_ref].copy()
scores[idx_ref] = -1   # ignorar ele mesmo

# Obter os 5 produtos com maior similaridade
top_indices = np.argsort(scores)[::-1][:5]
top_product_ids = matriz.columns[top_indices].tolist()
top_nomes = products[products['id'].isin(top_product_ids)]['name'].tolist()
top_scores = scores[top_indices].tolist()

# ============================================================================
# 6. Exibir resultados
# ============================================================================
print(f"Produto de referência: {produto_ref}")
print("\nRanking dos 5 produtos mais similares:")
for i, (nome, score) in enumerate(zip(top_nomes, top_scores), 1):
    print(f"{i}. {nome} (similaridade = {score:.4f})")