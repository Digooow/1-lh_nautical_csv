# Estudo de Caso de Engenharia e Análise de Dados — LH Nautical

Pipeline de engenharia e análise de dados desenvolvido sobre o conjunto transacional de varejo e suprimentos náuticos **LH Nautical** (24 tabelas relacionais, ~422 mil registros combinados).

O projeto estrutura o ciclo completo desde a modelagem relacional estrita e carga transacional em **PostgreSQL 16** até a reconciliação contábil, consultas analíticas avançadas, previsão de séries temporais, filtragem colaborativa item-item e visualização interativa em **Plotly**.

---

## 1. Arquitetura e Fonte Única da Verdade

A solução elimina duplicação de regras de negócio entre SQL, Python e camada de visualização por meio de três decisões arquiteturais:

1. **Filtro Canônico de Pedidos Válidos (`status IN ('paid', 'confirmed')`):**
   A tabela bruta `orders` contém **48.998 registros**, dos quais **4.847 (9,89%)** possuem status `cancelled` e **2.451 (5,00%)** possuem status `draft`. Tanto no banco de dados (via views `vw_valid_orders` e `vw_valid_order_items` em [`sql/schema.sql`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/sql/schema.sql)) quanto no pacote Python ([`src/lh_nautical/metrics.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/metrics.py)), pedidos cancelados e rascunhos são isolados das métricas comerciais. Todos os módulos aceitam o parâmetro explícito `valid_only: bool` para permitir auditoria cruzada contra a base bruta sem filtro.
2. **Ingestão Transacional via `psycopg` v3 `COPY`:**
   O módulo [`src/lh_nautical/ingestion.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/ingestion.py) aplica o DDL e carrega as 24 tabelas em ordem estritamente topológica (respeitando todas as 37 chaves estrangeiras) dentro de uma única transação atômica (`with engine.begin():`), validando a paridade exata de contagem de linhas entre CSV e tabela após cada `COPY`.
3. **Preservação de Granularidade (Anti-Fan-Out):**
   Métricas na granularidade de pedido (`SUM(orders.total)`, `COUNT(orders.id)`) são agregadas em CTE/DataFrame próprio antes de qualquer junção `1:N` com `order_items` (média de 3,01 itens por pedido), impedindo a multiplicação artificial de receita.

```text
lh-nautical-case-study/
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── docker-compose.yml
├── requirements.txt
├── run_all.py                   # Orquestrador em 1 comando (ingestão, testes, métricas e dashboard)
├── data/                        # 24 arquivos CSV de origem
├── reports/                     # Artefatos gerados (dashboard_lh_nautical.html, summary_metrics.json)
├── sql/
│   ├── schema.sql               # DDL tipado (PKs, 37 FKs, BOOLEAN, NUMERIC, CHAR(8), views)
│   ├── q1_eda_orders.sql        # Questão 1.1: Auditoria contábil e quartis/IQR de orders
│   ├── q4_elite_customers.sql   # Questão 4: Top 10 clientes elite sem fan-out de JOIN
│   └── q5_weekday_sales.sql     # Questão 5: Média diária por dia da semana com generate_series
├── src/
│   └── lh_nautical/
│       ├── __init__.py
│       ├── db.py                # Engine SQLAlchemy + psycopg v3 + variáveis de ambiente
│       ├── ingestion.py         # Carga transacional atômica em ordem topológica
│       ├── metrics.py           # Fonte única da verdade (Q1, Q4 e Q5)
│       ├── forecasting.py       # Questão 6: Série mensal contínua, MA(3) recursivo/one-step e Naive
│       ├── recommender.py       # Questão 7: Matriz cliente-produto e similaridade de cosseno ordenada
│       └── dashboard.py         # Gerador de relatório HTML interativo (Plotly.js) e JSON
└── tests/
    └── test_metrics.py          # Suíte de testes unitários e de contrato de dados
```

---

## 2. Como Executar em 1 Comando

### Pré-requisitos

- **Python 3.11+**
- **Docker** e **Docker Compose** (opcional para execução local apenas sobre CSVs via `--skip-db`)

### Execução Completa (Banco PostgreSQL + Testes + Dashboard)

```bash
# 1. Instalar dependências
python -m pip install -r requirements.txt

# 2. Subir o PostgreSQL 16 (com healthcheck e provisionamento automático do schema)
docker compose up -d --wait

# 3. Executar ingestão transacional, suíte de testes e geração do dashboard
python run_all.py
```

Para executar todo o pipeline analítico, suíte de testes e geração do dashboard localmente sem depender de instância Docker ativa:

```bash
python run_all.py --skip-db
```

Os artefatos finais são gravados em:
- `reports/dashboard_lh_nautical.html` (Dashboard interativo com gráficos Plotly.js)
- `reports/summary_metrics.json` (Métricas estruturadas para inspeção programática)

---

## 3. Síntese dos Resultados Verificados

A tabela abaixo consolida os indicadores auditados tanto na **Visão Comercial Canônica** (`status IN ('paid', 'confirmed')`) quanto na **Visão de Gabarito Bruto** (todos os registros de `orders.csv`).

| Questão / Indicador | Visão Comercial Canônica (`paid` + `confirmed`) | Visão Base Bruta (Todos os `status`) |
| :--- | :--- | :--- |
| **Q1 — Volumetria de `orders`** | **41.700** pedidos válidos (`34.365` pagos, `7.335` confirmados) | **48.998** registros (`4.847` cancelados, `2.451` rascunhos) |
| **Q1 — Faturamento Acumulado** | **R\$ 1.199.367.079,54** | **R\$ 1.406.487.201,80** |
| **Q1 — Ticket Médio / Mediana** | **R\$ 28.761,80** / **R\$ 26.004,60** | **R\$ 28.704,99** / **R\$ 25.917,84** |
| **Q1 — Limite Superior IQR e Outliers** | **R\$ 82.697,79** (**377** pedidos acima de $Q_3 + 1{,}5 \times \text{IQR}$) | **R\$ 82.597,85** (**452** pedidos acima de $Q_3 + 1{,}5 \times \text{IQR}$) |
| **Q1 — Divergências Contábeis** | **0** (`total = subtotal - discount_amount` e `subtotal = SUM(line_total)` em 100% da base) | **0** divergências e **0** pedidos sem itens |
| **Q4 — Top 1 Cliente Elite (Diversidade $\ge 13$)** | **Cliente 300** — Ticket: **R\$ 45.525,24** (13 pedidos, categoria: *Pesca*) | **Cliente 22** — Ticket: **R\$ 41.839,94** (26 pedidos, categoria: *Hélices*) |
| **Q5 — Menor Média Diária (Canal POS, com calendário)** | **Quinta-feira** — **R\$ 134.118,35 / dia** (366 dias, 26 zerados) | **Quinta-feira** — **R\$ 157.154,32 / dia** |
| **Q5 — Maior Média Diária (Canal POS, com calendário)** | **Quarta-feira** — **R\$ 147.948,93 / dia** (366 dias, 14 zerados) | **Quarta-feira** — **R\$ 173.605,44 / dia** |
| **Q6 — Demanda Real 1T 2026 (`Bússola de Bordo 702`, ID 74)** | **140 unidades** (Jan: 66, Fev: 32, Mar: 42) \| 9 meses zerados no histórico | **156 unidades** (Jan: 69, Fev: 42, Mar: 45) \| 7 meses zerados no histórico |
| **Q6 — Previsão MA(3) Recursiva (Soma / MAE)** | **62 unidades** \| **MAE = 25,84** (RMSE = 29,66) | **72 unidades** \| **MAE = 28,02** (RMSE = 30,25) |
| **Q6 — Previsão MA(3) One-Step-Ahead (Soma / MAE)** | **95 unidades** \| **MAE = 18,67** (RMSE = 26,20) | **107 unidades** \| **MAE = 16,44** (RMSE = 25,32) |
| **Q6 — Baseline Naive $t-1$ / Sazonal $t-12$ (MAE)** | Naive: **35,67** \| Sazonal: **23,00** | Naive: **38,00** \| Sazonal: **30,00** |
| **Q7 — Top 1 Similar ao `Motor de Popa 1949`** | **Vela Mestra 1913** (ID 75) — Similaridade: **0,2452** | **Motor de Popa 5331** (ID 389) — Similaridade: **0,2566** |

---

## 4. Detalhamento Técnico por Etapa

### Q1 — Auditoria Exploratória e Contratos de Dados ([`sql/q1_eda_orders.sql`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/sql/q1_eda_orders.sql) | [`metrics.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/metrics.py))

- **Integridade Contábil:** 100% dos 48.998 pedidos satisfazem a identidade de cabeçalho `total = subtotal - discount_amount` e a reconciliação com as 147.320 linhas de `order_items` (`orders.subtotal = SUM(order_items.line_total)`), sem nenhum pedido órfão.
- **Horizonte Temporal:** O intervalo `2020-01-01` a `2026-12-31` corresponde à janela sintética completa do dataset (onde o 1º trimestre de 2026 é utilizado como conjunto de teste na Questão 6).
- **Qualidade de Catálogo (`products.csv`):** A auditoria identificou 4 pares de nomes duplicados entre os 500 produtos cadastrados (`Bússola de Bordo 702` nos IDs `74` e `240`; `Defensa Náutica 3153` nos IDs `29` e `317`; `Sonar Transducer 7193` nos IDs `408` e `422`; e registros de teste `asdf` nos IDs `187` e `342`).

### Q2 e Q3 — Modelagem DDL e Ingestão Transacional ([`sql/schema.sql`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/sql/schema.sql) | [`ingestion.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/ingestion.py))

- Todas as 24 tabelas possuem chaves primárias (incluindo chaves compostas em `product_suppliers`, `stock_levels` e `variant_attribute_values`) e 37 chaves estrangeiras validadas.
- Campos booleanos utilizam `BOOLEAN NOT NULL`, valores monetários utilizam `NUMERIC(12,2)`, quantidades físicas fracionárias (`weight_kg`, `quantity_received`, `quantity_on_hand`) utilizam `NUMERIC(12,3)` e códigos fiscais/documentos de tamanho fixo utilizam `CHAR(8)` (NCM), `CHAR(11)` (CPF), `CHAR(13)` (EAN) e `CHAR(44)` (Chave NFe).

### Q4 — Top 10 Clientes Elite sem Fan-Out de JOIN ([`sql/q4_elite_customers.sql`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/sql/q4_elite_customers.sql) | [`metrics.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/metrics.py))

- Agregar `SUM(orders.total)` após o `JOIN` com `order_items` multiplicaria o valor de cada pedido pelo número de linhas do pedido (~3,01 itens/pedido), inflando o ticket médio em ~4x.
- A solução isola o cálculo de `faturamento_total`, `frequencia` e `ticket_medio` na CTE `receita_por_cliente` (granularidade `orders`) e cruza o resultado com a CTE `diversidade_por_cliente` (`HAVING COUNT(DISTINCT category_id) >= 13`).

#### Top 10 Clientes Elite — Visão Comercial Canônica (`status IN ('paid', 'confirmed')`)

| Posição | `customer_id` | Ticket Médio | Diversidade | Faturamento Válido | Frequência | Categoria Preferida | Qtd. Itens |
| :---: | :---: | ---: | :---: | ---: | :---: | :--- | ---: |
| 1 | **300** | R\$ 45.525,24 | 13 | R\$ 591.828,11 | 13 | Pesca | 86 |
| 2 | **22** | R\$ 43.856,63 | 14 | R\$ 877.132,67 | 20 | Hélices | 50 |
| 3 | **1477** | R\$ 41.992,32 | 13 | R\$ 713.869,41 | 17 | Hélices | 53 |
| 4 | **1527** | R\$ 41.821,96 | 14 | R\$ 794.617,18 | 19 | Pesca | 56 |
| 5 | **1470** | R\$ 41.451,10 | 14 | R\$ 911.924,14 | 22 | Equipamentos | 81 |
| 6 | **1691** | R\$ 41.345,85 | 14 | R\$ 661.533,66 | 16 | SEGURANÇA | 42 |
| 7 | **1784** | R\$ 41.215,68 | 14 | R\$ 618.235,16 | 15 | Pintura Marítima | 58 |
| 8 | **1722** | R\$ 41.085,39 | 14 | R\$ 1.068.220,16 | 26 | Pesca | 55 |
| 9 | **965** | R\$ 40.966,92 | 13 | R\$ 409.669,17 | 10 | Iluminação | 35 |
| 10 | **21** | R\$ 40.475,73 | 13 | R\$ 607.135,92 | 15 | Coletes Salva-Vidas | 49 |

### Q5 — Média Diária de Vendas por Dia da Semana ([`sql/q5_weekday_sales.sql`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/sql/q5_weekday_sales.sql) | [`metrics.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/metrics.py))

- A consulta gera uma dimensão calendário contínua (`generate_series` no PostgreSQL / `pd.date_range(freq='D')` no pandas) entre a menor e a maior data do canal de loja física (`channel = 'pos'`), preenchendo dias sem vendas com `R$ 0,00` antes do cálculo da média.
- A indexação do dia da semana segue o padrão ISO-8601 (`0 = Segunda-feira ... 6 = Domingo`), eliminando divergências entre `EXTRACT(ISODOW)` no SQL e `dt.dayofweek` no pandas.

| ISO DOW | Dia da Semana | Dias no Calendário | Dias com Venda | Dias sem Venda | Receita Acumulada (POS) | Média Diária (POS) |
| :---: | :--- | :---: | :---: | :---: | ---: | ---: |
| 3 | **Quinta-feira** | 366 | 340 | 26 | R\$ 49.087.316,06 | **R\$ 134.118,35** |
| 6 | **Domingo** | 365 | 351 | 14 | R\$ 49.293.410,25 | **R\$ 135.050,44** |
| 0 | **Segunda-feira** | 365 | 351 | 14 | R\$ 49.974.472,13 | **R\$ 136.916,36** |
| 5 | **Sábado** | 365 | 347 | 18 | R\$ 51.159.941,53 | **R\$ 140.164,22** |
| 4 | **Sexta-feira** | 365 | 351 | 14 | R\$ 52.290.861,97 | **R\$ 143.262,64** |
| 1 | **Terça-feira** | 365 | 353 | 12 | R\$ 52.965.536,05 | **R\$ 145.111,06** |
| 2 | **Quarta-feira** | 366 | 352 | 14 | R\$ 54.149.307,19 | **R\$ 147.948,93** |

### Q6 — Previsão de Demanda Mensal ([`forecasting.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/forecasting.py))

- A série mensal da **Bússola de Bordo 702** (`product_id = 74`) é reindexada sobre a grade contínua `pd.period_range('2020-01', '2026-03', freq='M')` com `fill_value=0` (preenchendo os meses sem vendas antes da janela móvel).
- O módulo compara a **Média Móvel de 3 Meses Recursiva** (horizonte fechado em `2025-12`) e a **Média Móvel One-Step-Ahead** (atualizada mês a mês) contra os baselines **Naive ($t-1$)** e **Sazonal Naive ($t-12$)**:

| Modelo | Soma Real (Válidos / Bruto) | Soma Prevista (Válidos / Bruto) | MAE Válidos | MAE Base Bruta |
| :--- | :---: | :---: | ---: | ---: |
| **MA(3) One-Step-Ahead** | 140 / 156 | 95 / 107 | **18,67** | **16,44** |
| **Baseline Sazonal ($t-12$)** | 140 / 156 | 97 / 116 | **23,00** | **30,00** |
| **MA(3) Recursiva** | 140 / 156 | 62 / 72 | **25,84** | **28,02** |
| **Baseline Naive ($t-1$)** | 140 / 156 | 33 / 42 | **35,67** | **38,00** |

### Q7 — Sistema de Recomendação Item-Item ([`recommender.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/src/lh_nautical/recommender.py))

- Constrói a matriz binária de interação `customer_id × product_id` e calcula a similaridade de cosseno entre o vetor do produto de referência (**Motor de Popa 1949**, `id = 116`) e os demais itens do catálogo.
- O mapeamento de nomes utiliza indexação direta (`products.set_index("id")["name"].reindex(product_ids)`), preservando a ordem exata de pontuação:

| Rank | `product_id` | Produto Recomendado (Base Completa) | Clientes do Produto | Clientes em Comum | Similaridade de Cosseno |
| :---: | :---: | :--- | :---: | :---: | ---: |
| **1** | **389** | **Motor de Popa 5331** | 430 | 106 | **0,2566** |
| **2** | **295** | **Cabo Náutico 2105** | 407 | 103 | **0,2562** |
| **3** | **75** | **Vela Mestra 1913** | 385 | 100 | **0,2558** |
| **4** | **337** | **Cabo Náutico 9048** | 431 | 99 | **0,2393** |
| **5** | **55** | **GPS Plotter 6249** | 428 | 98 | **0,2377** |

---

## 5. Testes Automatizados

A suíte em [`tests/test_metrics.py`](file:///c:/Users/Rodrigo/Desktop/Projetos/1-lh_nautical_csv/tests/test_metrics.py) valida tanto fixtures sintéticas controladas (cálculo manual exato) quanto contratos de integridade sobre os CSVs reais:

```bash
PYTHONPATH=src pytest -v
# ou usando apenas a biblioteca padrão:
PYTHONPATH=src python -m unittest discover -s tests -v
```
