📘 Questão 6.3 – Explicação do modelo baseline
1. Como o baseline foi construído?
O baseline adotado foi a média móvel simples dos últimos 3 meses. A construção seguiu as seguintes etapas:

Agregação mensal: Os dados de vendas do produto "Bússola de Bordo 702" foram agregados por mês, somando a quantidade total vendida em cada mês.

Separação treino/teste: O período de treino incluiu todos os meses até 31/12/2025. O período de teste correspondeu ao primeiro trimestre de 2026 (janeiro, fevereiro e março).

Previsão passo a passo: Para cada mês do período de teste, a previsão foi calculada como a média das vendas dos 3 meses imediatamente anteriores.

Para jan/2026: média de out, nov, dez/2025 (dados reais).

Para fev/2026: média de nov, dez/2025 e a previsão de jan/2026 (já que o valor real de jan não estava disponível no momento da previsão).

Para mar/2026: média de dez/2025, previsão de jan/2026 e previsão de fev/2026.
Isso simula o que aconteceria na prática: ao prever fevereiro, o valor real de janeiro ainda não é conhecido.

Essa abordagem garante que as previsões sejam geradas de forma sequencial, respeitando a ordem cronológica.

2. Como evitou data leakage?
Data leakage ocorre quando informações futuras (que não estariam disponíveis no momento da previsão) são usadas inadvertidamente. Para evitar isso:

O treino utilizou exclusivamente dados até 31/12/2025.

A previsão para cada mês do teste usou apenas dados anteriores àquele mês – ou seja, os 3 meses imediatamente anteriores, que podem ser reais (no caso de janeiro) ou previstos (nos casos de fevereiro e março).

Nunca usamos os valores reais do período de teste para compor as previsões. Quando um mês de teste ainda não tinha ocorrido (ex.: fevereiro), usamos a previsão do mês anterior (janeiro) como se fosse o valor conhecido.

Com isso, o modelo nunca "enxerga" o futuro durante a previsão, mantendo a integridade da avaliação.

3. Uma limitação do modelo proposto.
A principal limitação do baseline de média móvel simples é que ele não captura padrões sazonais, tendências ou efeitos de eventos pontuais (como feriados, promoções ou mudanças de comportamento do consumidor).

Para produtos com sazonalidade marcante – como "Bússola de Bordo 702", cujas vendas podem sofrer picos no verão – esse modelo tende a subestimar ou superestimar a demanda de forma consistente, resultando em erros significativos (como o MAE de ~28 unidades observado). Isso torna o baseline inadequado para decisões de compra e estoque, pois pode gerar rupturas ou excessos.

Modelos mais sofisticados (ARIMA, Prophet, redes neurais) seriam mais adequados para capturar esses padrões, mas exigem maior complexidade e dados históricos mais longos.

✅ Resumo
Pergunta	Resposta
Como foi construído?	Média móvel dos 3 meses anteriores, com previsões passo a passo.
Como evitou data leakage?	Usando apenas dados reais até o passado imediato e previsões anteriores, nunca usando valores reais futuros.
Limitação principal	Não captura sazonalidade nem tendência, gerando erros em produtos com padrões cíclicos.


📘 Explicação detalhada do código Python (Questão 6.1)
O script Python foi construído para atender à Questão 6 – Previsão de demanda. Abaixo, explico cada bloco do código, desde a leitura dos dados até a geração das previsões e cálculo do MAE.

1. Importação das bibliotecas
python
import pandas as pd
import numpy as np
from datetime import datetime
pandas: usada para manipulação de dados (leitura de CSVs, joins, agregações).

numpy: usada para cálculos matemáticos (média, MAE, arredondamento).

datetime: usada para manipulação de datas (embora o pandas já faça isso, é útil para formatação).

2. Leitura dos CSVs
python
products = pd.read_csv('products.csv')
variants = pd.read_csv('product_variants.csv')
order_items = pd.read_csv('order_items.csv')
orders = pd.read_csv('orders.csv')
Cada arquivo é carregado em um DataFrame do pandas. Os caminhos dos arquivos são relativos ao local onde o script é executado (ajuste conforme necessário).

3. Filtragem do produto "Bússola de Bordo 702"
python
produto_nome = "Bússola de Bordo 702"
produto_id = products[products['name'] == produto_nome]['id'].iloc[0]
Localiza o id do produto na tabela products com base no nome.

iloc[0] pega o primeiro (e único) ID encontrado.

python
variants_produto = variants[variants['product_id'] == produto_id]
variant_ids = variants_produto['id'].tolist()
Filtra as variantes do produto na tabela product_variants usando product_id.

Obtém uma lista com todos os id das variantes.

4. Filtrar os itens de pedido e unir com orders
python
items_filtrados = order_items[order_items['product_variant_id'].isin(variant_ids)]
Seleciona apenas as linhas de order_items cujo product_variant_id está na lista de variantes.

python
items_agg = items_filtrados.groupby('order_id', as_index=False)['quantity'].sum()
Como um mesmo pedido pode ter mais de uma variante do mesmo produto, agrupamos por order_id e somamos as quantidades.

python
orders_filtrados = orders[orders['id'].isin(items_agg['order_id'])]
df_vendas = pd.merge(orders_filtrados[['id', 'created_at']], items_agg, left_on='id', right_on='order_id')
df_vendas = df_vendas[['created_at', 'quantity']]
Filtra os pedidos que contêm o produto.

Faz um merge entre os pedidos e os itens agregados, usando order_id como chave.

Mantém apenas as colunas created_at (data do pedido) e quantity (quantidade do produto).

5. Agregação por mês
python
df_vendas['created_at'] = pd.to_datetime(df_vendas['created_at'])
df_vendas['ano_mes'] = df_vendas['created_at'].dt.to_period('M')
vendas_mensais = df_vendas.groupby('ano_mes')['quantity'].sum().reset_index()
Converte a coluna created_at para o tipo datetime.

Cria uma nova coluna ano_mes com o período mensal (ex.: "2025-01").

Agrupa por mês e soma as quantidades.

O resultado é um DataFrame com duas colunas: ano_mes e quantity.

6. Separação em treino e teste
python
vendas_mensais['ano'] = vendas_mensais['ano_mes'].dt.year
vendas_mensais['mes'] = vendas_mensais['ano_mes'].dt.month

treino = vendas_mensais[vendas_mensais['ano'] <= 2025].copy()
teste = vendas_mensais[(vendas_mensais['ano'] == 2026) & (vendas_mensais['mes'].isin([1,2,3]))].copy()
Extrai ano e mês para facilitar a filtragem.

Treino: todas as linhas com ano até 2025.

Teste: linhas do ano 2026 e meses 1, 2 e 3 (janeiro a março).

7. Baseline: média móvel dos últimos 3 meses (passo a passo)
python
historico = list(treino['quantity'].values)
previsoes = []
historico é uma lista com os valores reais do treino (em ordem cronológica).

python
for i, row in teste.iterrows():
    if len(historico) >= 3:
        pred = sum(historico[-3:]) / 3
    else:
        pred = np.nan
    previsoes.append(pred)
    historico.append(pred)   # adiciona a previsão ao histórico
Para cada mês do período de teste, calcula a média dos últimos 3 valores do histórico.

Adiciona essa previsão ao histórico para que o próximo mês use a previsão anterior como dado.

Isso simula o que aconteceria na prática: ao prever fevereiro, o valor real de janeiro ainda não é conhecido, então usamos a previsão de janeiro.

python
teste['previsao'] = previsoes
Adiciona a coluna previsao ao DataFrame de teste.

8. Cálculo do MAE (Mean Absolute Error)
python
mae = np.mean(np.abs(teste['quantity'] - teste['previsao']))
print(f"MAE: {mae:.2f} unidades")
np.abs(teste['quantity'] - teste['previsao']) → erro absoluto de cada mês.

np.mean() → média dos erros absolutos.

O MAE indica, em média, quantas unidades a previsão errou (para mais ou para menos).

9. Exibição dos resultados e soma total
python
print("\nPrevisões vs Reais (primeiro trimestre 2026):")
print(teste[['ano_mes', 'quantity', 'previsao']])
Mostra uma tabela com os meses, valores reais e previstos.

python
soma_previsao = int(round(sum(previsoes)))
print(f"Soma total da previsão: {soma_previsao} unidades")
Soma as três previsões, arredonda para o inteiro mais próximo e exibe.

🔍 Como o código evita data leakage?
Treino restrito a dados até 2025: nenhuma informação do período de teste é usada para ajustar o modelo.

Previsão sequencial: para prever janeiro, usa apenas out/nov/dez 2025 (dados reais). Para prever fevereiro, usa nov/dez 2025 e a previsão de janeiro (não o valor real). Isso garante que, no momento da previsão, o modelo só dispõe de dados anteriores ao mês alvo.

Nunca usamos valores reais futuros em nenhuma etapa do cálculo das previsões.

⚠️ Limitação do modelo (já discutida)
A média móvel simples não captura sazonalidade. Para um produto como a "Bússola de Bordo 702", que pode ter picos no verão, o modelo subestima a demanda, conforme observado (MAE de 28 unidades e previsões bem abaixo dos valores reais). Isso torna o baseline inadequado para decisões de compra e estoque.

📌 Resumo do fluxo do script
Leitura dos CSVs.

Filtragem do produto e obtenção das variantes.

Junção com pedidos e agregação mensal.

Separação treino (até 2025) e teste (jan–mar 2026).

Previsão passo a passo com média móvel dos 3 meses anteriores.

Cálculo do MAE.

Exibição dos resultados e soma total arredondada.

Essa explicação cobre todos os aspectos solicitados na Questão 6.3. 😊