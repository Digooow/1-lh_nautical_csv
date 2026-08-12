import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================================
# 1. Leitura dos CSVs
# ============================================================================
products = pd.read_csv('products.csv')
variants = pd.read_csv('product_variants.csv')
order_items = pd.read_csv('order_items.csv')
orders = pd.read_csv('orders.csv')

# ============================================================================
# 2. Filtrar o produto "Bússola de Bordo 702"
# ============================================================================
produto_nome = "Bússola de Bordo 702"
produto_id = products[products['name'] == produto_nome]['id'].iloc[0]

# Variantes desse produto
variants_produto = variants[variants['product_id'] == produto_id]
variant_ids = variants_produto['id'].tolist()

# ============================================================================
# 3. Filtrar itens de pedido e unir com orders
# ============================================================================
items_filtrados = order_items[order_items['product_variant_id'].isin(variant_ids)]

# Agrupa quantity por order_id (pode haver mais de uma variante do mesmo produto no pedido)
items_agg = items_filtrados.groupby('order_id', as_index=False)['quantity'].sum()

# Junta com orders para obter data
orders_filtrados = orders[orders['id'].isin(items_agg['order_id'])]
df_vendas = pd.merge(orders_filtrados[['id', 'created_at']], items_agg, left_on='id', right_on='order_id')
df_vendas = df_vendas[['created_at', 'quantity']]

# ============================================================================
# 4. Converter data e agregar por mês
# ============================================================================
df_vendas['created_at'] = pd.to_datetime(df_vendas['created_at'])
df_vendas['ano_mes'] = df_vendas['created_at'].dt.to_period('M')
vendas_mensais = df_vendas.groupby('ano_mes')['quantity'].sum().reset_index()

# ============================================================================
# 5. Separar treino (até 2025-12) e teste (2026-01 a 2026-03)
# ============================================================================
vendas_mensais['ano'] = vendas_mensais['ano_mes'].dt.year
vendas_mensais['mes'] = vendas_mensais['ano_mes'].dt.month

treino = vendas_mensais[vendas_mensais['ano'] <= 2025].copy()
teste = vendas_mensais[(vendas_mensais['ano'] == 2026) & (vendas_mensais['mes'].isin([1,2,3]))].copy()

# ============================================================================
# 6. Baseline: média móvel dos últimos 3 meses (previsão passo a passo)
# ============================================================================
# Ordenar por data
vendas_mensais = vendas_mensais.sort_values('ano_mes')

# Criar lista com histórico (valores reais do treino)
historico = list(treino['quantity'].values)

previsoes = []
meses = []

for i, row in teste.iterrows():
    if len(historico) >= 3:
        pred = sum(historico[-3:]) / 3
    else:
        pred = np.nan
    previsoes.append(pred)
    meses.append(row['ano_mes'])
    # Adiciona a previsão ao histórico para o próximo passo
    historico.append(pred)

teste['previsao'] = previsoes

# ============================================================================
# 7. Calcular MAE
# ============================================================================
mae = np.mean(np.abs(teste['quantity'] - teste['previsao']))
print(f"MAE (Mean Absolute Error) para o primeiro trimestre de 2026: {mae:.2f} unidades")

# ============================================================================
# 8. Resultados detalhados
# ============================================================================
print("\nPrevisões vs Reais (primeiro trimestre 2026):")
print(teste[['ano_mes', 'quantity', 'previsao']])

# ============================================================================
# 9. Soma total da previsão (arredondada) - Questão 6.2
# ============================================================================
soma_previsao = int(round(sum(previsoes)))
print(f"\nSoma total da previsão para o primeiro trimestre de 2026: {soma_previsao} unidades")