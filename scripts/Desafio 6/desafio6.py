"""
Previsão de demanda para o produto 'Bússola de Bordo 702'.
Modelo baseline: média móvel dos últimos 3 meses.
Treino: até 31/12/2025. Teste: primeiro trimestre de 2026.
"""

import pandas as pd
import numpy as np
import os


script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))
data_dir = os.path.join(root_dir, 'data')


products = pd.read_csv(os.path.join(data_dir, 'products.csv'))
variants = pd.read_csv(os.path.join(data_dir, 'product_variants.csv'))
order_items = pd.read_csv(os.path.join(data_dir, 'order_items.csv'))
orders = pd.read_csv(os.path.join(data_dir, 'orders.csv'))


produto_nome = "Bússola de Bordo 702"
produto_id = products[products['name'] == produto_nome]['id'].iloc[0]
variants_produto = variants[variants['product_id'] == produto_id]
variant_ids = variants_produto['id'].tolist()


items_filtrados = order_items[order_items['product_variant_id'].isin(variant_ids)]
items_agg = items_filtrados.groupby('order_id', as_index=False)['quantity'].sum()
orders_filtrados = orders[orders['id'].isin(items_agg['order_id'])]
df_vendas = pd.merge(orders_filtrados[['id', 'created_at']], items_agg,
                     left_on='id', right_on='order_id')
df_vendas = df_vendas[['created_at', 'quantity']]


df_vendas['created_at'] = pd.to_datetime(df_vendas['created_at'])
df_vendas['ano_mes'] = df_vendas['created_at'].dt.to_period('M')
vendas_mensais = df_vendas.groupby('ano_mes')['quantity'].sum().reset_index()
vendas_mensais['ano'] = vendas_mensais['ano_mes'].dt.year
vendas_mensais['mes'] = vendas_mensais['ano_mes'].dt.month


treino = vendas_mensais[vendas_mensais['ano'] <= 2025].copy()
teste = vendas_mensais[(vendas_mensais['ano'] == 2026) &
                       (vendas_mensais['mes'].isin([1, 2, 3]))].copy()


historico = list(treino['quantity'].values)
previsoes = []
for i in range(len(teste)):
    if len(historico) >= 3:
        pred = sum(historico[-3:]) / 3
    else:
        pred = np.nan
    previsoes.append(pred)
    historico.append(pred)

teste['previsao'] = previsoes


mae = np.mean(np.abs(teste['quantity'] - teste['previsao']))
soma_prev = int(round(sum(previsoes)))

print(f"MAE (Mean Absolute Error): {mae:.2f} unidades")
print(f"Soma da previsão (arredondada): {soma_prev} unidades")
print("\nPrevisões vs Reais (primeiro trimestre 2026):")
print(teste[['ano_mes', 'quantity', 'previsao']])