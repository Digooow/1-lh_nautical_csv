# ⚓ Desafio Técnico – Indicium Academy

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-24.0-2496ED.svg)](https://www.docker.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0-150458.svg)](https://pandas.pydata.org/)


Este repositório contém a solução completa para um desafio de análise de dados proposto pela **Indicium Academy**. O objetivo foi explorar, modelar e extrair insights de um banco de dados de vendas do setor náutico, utilizando ferramentas modernas de engenharia e análise de dados.

---

## 📋 Contexto do Desafio

A empresa fictícia **LH Nautical** enfrentava problemas de gestão de estoque e falta de visibilidade sobre o comportamento dos clientes. A partir de um conjunto de arquivos CSV, foram propostas as seguintes tarefas:

- Realizar uma **análise exploratória** dos dados.
- Construir um **schema otimizado** para o banco de dados.
- **Carregar os dados** em um PostgreSQL via Docker.
- Identificar **clientes fiéis (elite)** com base em ticket médio e diversidade de categorias.
- Criar uma **dimensão de calendário** para corrigir a média de vendas por dia da semana.
- Construir um **modelo baseline de previsão de demanda**.
- Desenvolver um **sistema de recomendação** de produtos usando similaridade de cosseno.
- Entregar um **dashboard interativo** com os principais indicadores.

---

## 🛠️ Tecnologias Utilizadas

| Ferramenta | Descrição |
|------------|-----------|
| **Python 3.14** | Processamento de dados, scripts ETL, modelos de previsão e recomendação. |
| **Pandas / NumPy** | Manipulação e análise de dados. |
| **Scikit-learn** | Cálculo de similaridade de cosseno. |
| **PostgreSQL** | Banco de dados relacional (em container Docker). |
| **Docker** | Ambiente isolado e reproduzível para o banco de dados. |
| **Matplotlib / Seaborn** | Geração de gráficos estáticos. |
| **HTML + CSS** | Dashboard interativo gerado automaticamente. |
| **Git** | Versionamento do código. |

---

## 📁 Estrutura do Projeto

```

├── data/ # Arquivos CSV originais
│ ├── orders.csv
│ ├── order_items.csv
│ ├── products.csv
│ ├── customers.csv
│ └── ...
├── scripts/ # Scripts por desafio
│ ├── desafio 1/ # Análise Exploratória (EDA)
│ ├── desafio 2/ # Geração de Schema com inferência de tipos
│ ├── desafio 3/ # Carga dos dados no PostgreSQL
│ ├── desafio 4/ # Análise de clientes (ranking elite)
│ ├── desafio 5/ # Dimensão de calendário
│ ├── desafio 6/ # Previsão de demanda
│ └── desafio 7/ # Sistema de recomendação
├── dashboard-obrigatorio/ # Dashboard principal
│ ├── dashboard_obrigatorio.py
│ └── utils/
│ ├── graficos.py
│ └── html_generator.py
├── dashboard_alternativo.html # Dashboard gerado (abrir no navegador)
├── dashboard_graficos.png # Imagem dos gráficos
└── README.md

```

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos

- **Docker** instalado e em execução.
- **Python 3.14** (ou superior) com `pip`.
- **Git** (para clonar o repositório).

---

### 2. Clonar o Repositório


git clone https://github.com/seu-usuario/indicium-academy-challenge.git
cd indicium-academy-challenge

---


3. Configurar o Banco de Dados (PostgreSQL com Docker)


bash
docker run --name postgres-challenge \
  -e POSTGRES_PASSWORD=mysecret \
  -e POSTGRES_USER=challenge \
  -e POSTGRES_DB=challenge_db \
  -p 5432:5432 -d postgres

---
  
4. Carregar os Dados
Navegue até scripts/desafio_3/ e execute:

bash
python carregar_dados.py
Isso criará as tabelas e importará todos os CSVs da pasta data/.

---

5. Executar o Dashboard
Na raiz do projeto:

bash
python dashboard-obrigatorio/dashboard_obrigatorio.py
Serão gerados dois arquivos:

dashboard_graficos.png – imagem com os gráficos.

dashboard_alternativo.html – relatório interativo (abra no navegador).

---

6. (Opcional) Exportar para Power BI / Looker Studio
Caso prefira utilizar ferramentas de BI, exporte as tabelas principais via \copy ou utilize os CSVs já disponíveis em data/.

---

📊 Principais Resultados
Análise Exploratória (Questão 1)
Total de linhas: 48.998 pedidos.

Período: de 2020-01-01 a 2026-12-31.

Ticket médio: R$ 28.704,99.

Diagnóstico: dados com outliers significativos e datas futuras inconsistentes – exigem tratamento para análises robustas.

Clientes Elite (Questão 4)
Top 10 clientes com diversidade ≥ 13 categorias e maior ticket médio.

Categoria preferida predominante: Hélices e Equipamentos.

Média de Vendas por Dia da Semana (Questão 5)
Pior dia: Quarta-feira (média de R$ 540.432,34), corrigindo a distorção causada por dias sem venda.

Previsão de Demanda (Questão 6)
Produto: Bússola de Bordo 702.

MAE: 28,02 unidades.

Soma prevista (arredondada): 72 unidades para o 1º trimestre de 2026 (real = 156).

Recomendação de Produtos (Questão 7)
Produto mais similar ao "Motor de Popa 1949": GPS Plotter 6249 (similaridade = 0,2566).

📈 Dashboard
O dashboard gerado contém:

Visão Geral: Faturamento total, número de pedidos, ticket médio, pior dia da semana.

Gráfico de Média por Dia da Semana.

Top 10 Clientes Elite com faturamento, frequência, ticket médio e categoria preferida.

Previsão vs Real para a Bússola de Bordo 702.

Ranking de Produtos Similares ao Motor de Popa 1949.

Preview do Dashboard
https://dashboard-obrigatorio/dashboard_graficos.png

O arquivo dashboard_alternativo.html pode ser aberto diretamente no navegador para visualização interativa.

🧠 Competências Demonstradas
Análise exploratória de dados (EDA) com bibliotecas padrão.

Modelagem de dados e inferência de tipos para PostgreSQL.

ETL com Python e integração com Docker/PostgreSQL.

SQL avançado – CTEs, janelas de agregação, dimensão de datas.

Previsão de demanda com baseline de média móvel.

Sistema de recomendação baseado em similaridade de cosseno.

Criação de dashboard automatizado com Python, matplotlib e HTML.

Organização de projeto com estrutura modular e documentação clara.

📌 Conclusão
Este projeto demonstra a capacidade de extrair valor de dados brutos, transformando-os em informações acionáveis para a tomada de decisão. A abordagem combinou técnicas estatísticas, machine learning (simples) e engenharia de dados, tudo em um ambiente reproduzível e documentado.

