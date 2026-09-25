# Desafio Técnico Indicium Lighthouse — LH Nautical

Este repositório reúne a solução desenvolvida para o desafio técnico da
**Indicium Lighthouse**, usando dados fictícios de uma operação de comércio
náutico. O projeto percorre o ciclo completo de uma análise de dados:
inspeção da qualidade dos dados, modelagem e carga em banco, consultas
analíticas, previsão de demanda, recomendação de produtos e apresentação dos
resultados em um dashboard.

> **Objetivo do projeto:** transformar arquivos CSV operacionais em análises
> reproduzíveis e informações úteis para decisões de vendas, estoque e
> relacionamento com clientes.

## Visão geral do desafio

O conjunto de dados contém tabelas de clientes, pedidos, itens vendidos,
produtos, categorias, fornecedores, compras, estoque, devoluções e outras
entidades de uma operação varejista. As atividades foram organizadas nas
seguintes etapas:

| Etapa     | Entrega                                   | Abordagem utilizada                                             |
| --------- | ----------------------------------------- | --------------------------------------------------------------- |
| 1         | Análise exploratória e consulta inicial | Python com biblioteca padrão e SQL no PostgreSQL               |
| 2         | Geração do schema                       | Inferência de tipos, normalização de nomes e DDL automático |
| 3         | Carga dos dados                           | Docker, PostgreSQL,`docker cp` e `\copy`                    |
| 4         | Clientes elite                            | CTEs, agregações,`HAVING` e função de janela              |
| 5         | Média de vendas por dia da semana        | Dimensão de calendário com`generate_series` e `LEFT JOIN` |
| 6         | Previsão de demanda                      | Baseline de média móvel de três meses                        |
| 7         | Recomendação de produtos                | Matriz cliente–produto e similaridade de cosseno               |
| Dashboard | Comunicação dos resultados              | Python, Matplotlib, Seaborn e HTML                              |

## Estrutura do projeto

```text
.
├── data/                         # 24 arquivos CSV de origem
├── scripts/
│   ├── Desafio 1/
│   │   ├── scriptdesafio1.1.py  # Métricas executadas no PostgreSQL
│   │   └── scriptdesafio1.py    # EDA sem pandas/polars/dask
│   ├── Desafio 2/
│   │   ├── gerar_schema.py      # Geração automática do DDL
│   │   └── schema.sql           # Schema gerado
│   ├── Desafio 3/
│   │   └── carregar_dados.py    # Criação das tabelas e carga dos CSVs
│   ├── Desafio 4/
│   │   ├── analise_clientes.py  # Ranking dos clientes elite
│   │   └── desafio 4.1.md       # Explicação da metodologia
│   ├── Desafio 5/
│   │   ├── consultaSQL.sql      # Calendário e média por dia da semana
│   │   └── consultaSQL.md       # Justificativa da dimensão calendário
│   ├── Desafio 6/
│   │   ├── desafio6.py          # Previsão da Bússola de Bordo 702
│   │   └── desafio6.md          # Metodologia e limitações do baseline
│   └── Desafio 7/
│       ├── desafio7.py          # Recomendação por similaridade
│       └── desafio7.md          # Explicação da matriz e do método
├── dashboard-obrigatorio/
│   ├── dashboard-obrigatorio.py # Orquestração do dashboard
│   ├── utils/                   # Gráficos e gerador de HTML
│   ├── dashboard_graficos.png   # Saída visual estática
│   └── dashboard_alternativo.html # Relatório navegável
└── README.md
```

## Tecnologias

- **Python 3.10+** — scripts de análise e automação. O projeto foi executado
  com Python 3.14.
- **Pandas e NumPy** — manipulação de dados e cálculo numérico.
- **Scikit-learn** — similaridade de cosseno.
- **PostgreSQL** — persistência e consultas analíticas.
- **Docker** — ambiente reprodutível para o banco.
- **Matplotlib e Seaborn** — visualizações.
- **HTML/CSS** — relatório final navegável.

## Como executar

### 1. Pré-requisitos

- Python instalado e disponível no PATH;
- Docker Desktop em execução;
- Git, caso o projeto seja obtido por clone.

Instale as dependências Python:

```powershell
py -m pip install pandas numpy scikit-learn matplotlib seaborn
```

### 2. Criar o banco PostgreSQL

```powershell
docker run --name postgres-challenge `
  -e POSTGRES_PASSWORD=mysecret `
  -e POSTGRES_USER=challenge `
  -e POSTGRES_DB=challenge_db `
  -p 5432:5432 -d postgres
```

Se o container já existir, inicie-o com `docker start postgres-challenge`.

### 3. Executar a análise exploratória

Na raiz do projeto:

```powershell
py ".\scripts\Desafio 1\scriptdesafio1.py"
```

Essa etapa lê `data\orders.csv` diretamente, sem depender de um banco de
dados, e calcula volume, número de colunas, intervalo de datas, estatísticas
de `total` e valores nulos.

### 4. Gerar o schema e carregar os CSVs

```powershell
py ".\scripts\Desafio 2\gerar_schema.py"
py ".\scripts\Desafio 3\carregar_dados.py"
```

O primeiro comando recria `scripts\Desafio 2\schema.sql`. O segundo cria as
tabelas no PostgreSQL e carrega os arquivos encontrados em `data\`.

### 5. Executar consultas e análises

Com o container em execução:

```powershell
py ".\scripts\Desafio 1\scriptdesafio1.1.py"
py ".\scripts\Desafio 4\analise_clientes.py"
docker exec -i postgres-challenge psql -U challenge -d challenge_db `
  -f "/dev/stdin" < ".\scripts\Desafio 5\consultaSQL.sql"
```

As etapas 6 e 7 usam os CSVs diretamente:

```powershell
py ".\scripts\Desafio 6\desafio6.py"
py ".\scripts\Desafio 7\desafio7.py"
```

### 6. Gerar o dashboard

```powershell
py ".\dashboard-obrigatorio\dashboard-obrigatorio.py"
```

Os arquivos `dashboard_graficos.png` e `dashboard_alternativo.html` são
gerados dentro de `dashboard-obrigatorio\`. Abra o HTML em um navegador para
consultar os KPIs, a análise de clientes, a previsão e o ranking de produtos
similares.

## Análise das atividades desenvolvidas

### 1. Qualidade e exploração dos dados

A EDA percorre `orders.csv` com `csv.DictReader`, contabiliza registros e
colunas, converte datas ISO e calcula mínimo, máximo e média de `total`. A
consulta equivalente no PostgreSQL valida os resultados em outro ambiente.

O diagnóstico encontrado foi:

- 48.998 pedidos e 13 colunas em `orders.csv`;
- intervalo de `created_at` entre 2020 e 2026;
- nenhum nulo identificado em `total` ou `created_at`;
- ticket médio aproximado de R$ 28.704,99;
- valor máximo de pedido de aproximadamente R$ 127.262,02.

As datas até 2026 e os valores extremos foram tratados como alertas de
qualidade, não como dados automaticamente válidos. Antes de uma decisão
operacional, seria necessário confirmar a data de referência do dataset e
investigar os outliers.

### 2. Modelagem e ETL

O gerador de schema lê todos os CSVs, sanitiza nomes de tabelas e colunas e
infere tipos básicos (`INTEGER`, `NUMERIC`, `DATE`, `TIMESTAMP` ou `TEXT`).
Depois, o carregador cria as tabelas e usa `\copy`, uma forma eficiente de
importar CSV pelo próprio PostgreSQL.

Essa solução demonstra automação e portabilidade, mas o schema gerado é uma
camada inicial de ingestão: não define chaves primárias, estrangeiras,
índices, `NOT NULL` ou regras de domínio. Em um ambiente produtivo, essas
restrições e validações deveriam ser adicionadas em uma camada de
curadoria.

### 3. Clientes elite

A análise conecta:

```text
orders → order_items → product_variants → products → categories
```

Clientes com pelo menos 13 categorias distintas são filtrados por `HAVING`.
Em seguida, os dez maiores tickets médios são selecionados, e uma função
`ROW_NUMBER()` identifica a categoria preferida de cada cliente pela soma de
quantidades compradas.

Esse desenho mostra domínio de joins, CTEs, agregações e funções de janela,
além da preocupação em restringir o cálculo da categoria aos clientes que
realmente entraram no Top 10.

### 4. Dimensão de calendário

A consulta da Questão 5 gera uma sequência contínua de datas com
`generate_series`, agrega as vendas por dia e faz `LEFT JOIN` com o
calendário. Dias sem venda recebem zero com `COALESCE` antes da média por dia
da semana.

Essa decisão evita uma média artificialmente alta causada pela exclusão dos
dias sem pedidos — um conceito importante para indicadores de operação e
planejamento de abertura da loja.

### 5. Previsão de demanda

Para a **Bússola de Bordo 702**, as vendas são agregadas por mês. O treino vai
até dezembro de 2025 e o teste cobre janeiro, fevereiro e março de 2026. A
previsão é uma média móvel dos três últimos valores disponíveis; depois de
cada previsão, o valor previsto é incorporado ao histórico, simulando uma
previsão recursiva sem vazamento de dados.

Resultado registrado no projeto:

- MAE: aproximadamente 28,02 unidades;
- soma prevista para o trimestre: 72 unidades;
- soma real no período: 156 unidades.

O resultado evidencia a limitação do baseline: uma média móvel simples não
modela sazonalidade, tendência ou eventos. Um próximo passo seria comparar
com um baseline sazonal e modelos como ARIMA, Prophet ou regressão com
variáveis temporais.

### 6. Sistema de recomendação

O recomendador transforma compras em uma matriz binária
**cliente × produto**. Cada produto é representado pelo vetor de clientes
que o compraram, e a similaridade de cosseno compara esses vetores.

Para o produto **Motor de Popa 1949**, o resultado documentado aponta o
**GPS Plotter 6249** como item mais similar, com similaridade aproximada de
0,2566.

O método é simples, explicável e adequado como baseline. Porém, ignora
quantidade, valor, recência e contexto da compra, além de sofrer com
esparsidade e cold start. Recomendações futuras poderiam combinar
similaridade por conteúdo, popularidade, recência e histórico individual.

### 7. Dashboard e comunicação

O dashboard consolida indicadores de faturamento, quantidade de pedidos,
ticket médio, pior dia da semana, clientes elite, previsão versus realizado e
produtos similares. A saída combina gráficos estáticos em PNG com um
relatório HTML leve, que pode ser aberto localmente sem servidor.

Essa etapa transforma análises técnicas em uma narrativa para pessoas
decisoras: cada gráfico responde a uma pergunta de negócio e os resultados
podem ser compartilhados como artefatos.

## Resultados consolidados

| Indicador                          |      Resultado documentado |
| ---------------------------------- | -------------------------: |
| Pedidos analisados                 |                     48.998 |
| Ticket médio                      |               R$ 28.704,99 |
| Maior valor de pedido              |              R$ 127.262,02 |
| Filtro de cliente elite            |   Pelo menos 13 categorias |
| Previsão de demanda               |      MAE de 28,02 unidades |
| Previsão do 1º trimestre de 2026 |                72 unidades |
| Similaridade mais alta documentada | GPS Plotter 6249 — 0,2566 |

Os números acima são resultados registrados nos artefatos do desafio e podem
variar caso os CSVs sejam substituídos ou os scripts sejam executados com
regras de filtro diferentes.

## Pontos de atenção e próximos passos

1. **Unificar filtros de canal:** a consulta SQL da Questão 5 filtra
   `channel = 'pos'`, enquanto o dashboard calcula a média com todos os
   canais. Para comparar os resultados diretamente, a regra de negócio deve
   ser padronizada.
2. **Evitar dupla contagem no faturamento por cliente:** ao juntar pedidos
   com itens, `o.total` pode ser repetido para cada item. O faturamento deve
   ser agregado em uma relação de pedidos antes da junção com itens, ou
   deduplicado por pedido.
3. **Validar o recorte temporal:** datas futuras devem ser confirmadas antes de
   alimentar indicadores ou modelos.
4. **Fortalecer o schema:** adicionar chaves, índices, constraints e uma
   estratégia explícita de staging/curadoria.
5. **Reproduzir dependências:** criar um `requirements.txt` ou `pyproject.toml`
   e fixar versões para facilitar a execução por outras pessoas.
6. **Evoluir os modelos:** comparar a média móvel com baselines sazonais e
   medir o recomendador com métricas offline, como Precision@K ou Recall@K.

## Habilidades adquiridas

### Engenharia e qualidade de dados

- Leitura robusta de CSV e tratamento de datas, nulos e valores inválidos;
- análise de completude, distribuição, outliers e consistência temporal;
- inferência de tipos e sanitização de nomes para geração de DDL;
- automação de carga de múltiplos arquivos em PostgreSQL;
- uso de Docker para criar um ambiente reproduzível.

### SQL e modelagem

- construção de CTEs e consultas analíticas encadeadas;
- joins entre tabelas transacionais e dimensionais;
- `GROUP BY`, `HAVING`, `COUNT(DISTINCT)`, `COALESCE` e `generate_series`;
- funções de janela para ranqueamento;
- compreensão de granularidade e riscos de dupla contagem;
- criação de uma dimensão de calendário para indicadores confiáveis.

### Estatística e machine learning

- agregação e leitura de séries temporais mensais;
- separação temporal de treino e teste;
- prevenção de data leakage;
- avaliação com MAE;
- construção de matriz esparsa cliente–produto;
- aplicação e interpretação de similaridade de cosseno;
- análise crítica das limitações de modelos baseline.

### Comunicação e produto de dados

- definição de KPIs orientados a perguntas de negócio;
- visualização com Matplotlib e Seaborn;
- geração automatizada de relatório HTML;
- documentação de metodologia, resultados, limitações e próximos passos;
- tradução de resultados técnicos em recomendações acionáveis.

## Conclusão

O desafio demonstra uma evolução completa do dado bruto até a informação
apresentável: primeiro foi verificada a qualidade dos dados, depois criada a
estrutura de armazenamento, realizadas consultas para responder perguntas de
negócio e, por fim, construídos modelos simples e um dashboard.

Mais importante que os números isolados, a solução evidencia capacidade de
investigar premissas, escolher métodos adequados ao problema, reconhecer
limitações e comunicar resultados com transparência — competências centrais
para atuação em análise e engenharia de dados.
