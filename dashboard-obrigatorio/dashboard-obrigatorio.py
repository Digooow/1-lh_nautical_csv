import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from graficos import gerar_graficos
from html_generator import gerar_html

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir) if os.path.basename(script_dir) == 'dashboard-obrigatorio' else script_dir
os.makedirs(script_dir, exist_ok=True)

orders = pd.read_csv(os.path.join(root_dir, 'data', 'orders.csv'))
order_items = pd.read_csv(os.path.join(root_dir, 'data', 'order_items.csv'))
products = pd.read_csv(os.path.join(root_dir, 'data', 'products.csv'))
categories = pd.read_csv(os.path.join(root_dir, 'data', 'categories.csv'))
customers = pd.read_csv(os.path.join(root_dir, 'data', 'customers.csv'))
product_variants = pd.read_csv(os.path.join(root_dir, 'data', 'product_variants.csv'))

orders['created_at'] = pd.to_datetime(orders['created_at'])

total_vendas = orders['total'].sum()
num_pedidos = len(orders)
ticket_medio = total_vendas / num_pedidos

print(f"Total de Vendas: R$ {total_vendas:,.2f}")
print(f"Número de Pedidos: {num_pedidos}")
print(f"Ticket Médio: R$ {ticket_medio:,.2f}")

data_min = orders['created_at'].min().normalize()
data_max = orders['created_at'].max().normalize()
calendario = pd.date_range(start=data_min, end=data_max, freq='D')
df_cal = pd.DataFrame({'data': calendario})

vendas_dia = orders.groupby(orders['created_at'].dt.floor('D'))['total'].sum().reset_index()
vendas_dia.columns = ['data', 'total_dia']
df_cal = df_cal.merge(vendas_dia, on='data', how='left')
df_cal['total_dia'] = df_cal['total_dia'].fillna(0)

dias_semana = {0: 'Domingo', 1: 'Segunda', 2: 'Terça', 3: 'Quarta',
               4: 'Quinta', 5: 'Sexta', 6: 'Sábado'}
df_cal['dia_semana_num'] = df_cal['data'].dt.dayofweek
df_cal['dia_semana'] = df_cal['dia_semana_num'].map(dias_semana)

media_dia = df_cal.groupby('dia_semana_num')['total_dia'].mean().reset_index()
media_dia['dia_semana'] = media_dia['dia_semana_num'].map(dias_semana)
media_dia = media_dia.sort_values('total_dia')
pior_dia = media_dia.iloc[0]['dia_semana']
print(f"Pior dia da semana: {pior_dia} (média = R$ {media_dia.iloc[0]['total_dia']:,.2f})")

compras_cliente = (
    orders[['id', 'customer_id', 'total']]
    .merge(order_items[['order_id', 'product_variant_id', 'quantity']], left_on='id', right_on='order_id')
    .merge(product_variants[['id', 'product_id']], left_on='product_variant_id', right_on='id')
    .merge(products[['id', 'category_id']], left_on='product_id', right_on='id')
)

cliente_stats = compras_cliente.groupby('customer_id').agg(
    faturamento=('total', 'sum'),
    frequencia=('order_id', 'nunique'),
    diversidade=('category_id', 'nunique')
).reset_index()
cliente_stats['ticket_medio'] = cliente_stats['faturamento'] / cliente_stats['frequencia']
cliente_stats = cliente_stats[cliente_stats['diversidade'] >= 13]
cliente_stats = cliente_stats.sort_values(['ticket_medio', 'customer_id'], ascending=[False, True])
top10 = cliente_stats.head(10)

top_categorias = []
for cid in top10['customer_id']:
    compras_cli = compras_cliente[compras_cliente['customer_id'] == cid]
    cat_counts = compras_cli.groupby('category_id')['quantity'].sum().reset_index()
    cat_counts = cat_counts.merge(categories[['id', 'name']], left_on='category_id', right_on='id')
    top_cat = cat_counts.loc[cat_counts['quantity'].idxmax(), 'name'] if not cat_counts.empty else 'N/A'
    top_categorias.append(top_cat)
top10['categoria_preferida'] = top_categorias

produto_nome = "Bússola de Bordo 702"
produto_id = products[products['name'] == produto_nome]['id'].iloc[0]
variants_prod = product_variants[product_variants['product_id'] == produto_id]
variant_ids = variants_prod['id'].tolist()

items_prod = order_items[order_items['product_variant_id'].isin(variant_ids)]
items_prod = items_prod.merge(orders[['id', 'created_at']], left_on='order_id', right_on='id')
items_prod['mes_ano'] = items_prod['created_at'].dt.to_period('M')
vendas_mensais = items_prod.groupby('mes_ano')['quantity'].sum().reset_index()
vendas_mensais['ano'] = vendas_mensais['mes_ano'].dt.year
vendas_mensais['mes'] = vendas_mensais['mes_ano'].dt.month

treino = vendas_mensais[vendas_mensais['ano'] <= 2025]
teste = vendas_mensais[(vendas_mensais['ano'] == 2026) & (vendas_mensais['mes'].isin([1, 2, 3]))]

historico = list(treino['quantity'].values)
previsoes = []
for _ in range(len(teste)):
    pred = sum(historico[-3:]) / 3 if len(historico) >= 3 else np.nan
    previsoes.append(pred)
    historico.append(pred)

teste['previsao'] = previsoes
teste['mes_nome'] = ['Jan', 'Fev', 'Mar']
mae = np.mean(np.abs(teste['quantity'] - teste['previsao']))
soma_prev = int(round(sum(previsoes)))

prod_ref = "Motor de Popa 1949"
ref_id = products[products['name'] == prod_ref]['id'].iloc[0]

compras_presenca = compras_cliente[['customer_id', 'product_id']].drop_duplicates()
compras_presenca['presenca'] = 1
matriz = compras_presenca.pivot_table(index='customer_id', columns='product_id', values='presenca', fill_value=0)
sim = cosine_similarity(matriz.T)
idx_ref = matriz.columns.get_loc(ref_id)
scores = sim[idx_ref].copy()
scores[idx_ref] = -1
top_indices = np.argsort(scores)[::-1][:5]
top_ids = matriz.columns[top_indices].tolist()
top_nomes = products[products['id'].isin(top_ids)]['name'].tolist()
top_scores = scores[top_indices]

img_path = gerar_graficos(media_dia, top10, teste, top_nomes, top_scores, produto_nome, prod_ref, script_dir)
print(f"Imagem salva em: {img_path}")

html_path = gerar_html(total_vendas, num_pedidos, ticket_medio, pior_dia, media_dia,
                       top10, teste, soma_prev, mae, top_nomes, top_scores, produto_nome, script_dir)
print(f"Relatório gerado em: {html_path}")