📌 Passo a passo para construir a consulta e chegar ao resultado correto
Abaixo, o raciocínio completo para construir a consulta SQL que calcula a média de vendas por dia da semana usando um calendário, corrigindo o erro do estagiário.

🎯 Objetivo final
Descobrir qual dia da semana tem a menor média de vendas nas lojas físicas, considerando todos os dias do período (inclusive aqueles sem venda).

🧩 Passo 1 – Definir o período de análise
Primeiro, precisamos saber quando começa e termina o período que vamos analisar.

sql
WITH datas_limites AS (
  SELECT
    MIN(created_at::DATE) AS data_inicio,
    MAX(created_at::DATE) AS data_fim
  FROM orders
  WHERE channel = 'pos'
)
MIN(created_at) → primeira venda.

MAX(created_at) → última venda.

Filtramos apenas lojas físicas (channel = 'pos').

🧩 Passo 2 – Construir o calendário completo
Agora, geramos uma lista com todos os dias entre essas duas datas.

sql
calendario AS (
  SELECT
    generate_series(
      (SELECT data_inicio FROM datas_limites),
      (SELECT data_fim FROM datas_limites),
      '1 day'::INTERVAL
    )::DATE AS data
)
generate_series cria uma linha para cada dia.

Isso garante que nenhum dia seja omitido, mesmo os sem vendas.

🧩 Passo 3 – Agregar as vendas por dia (apenas lojas físicas)
Na tabela orders, somamos o total por dia.

sql
vendas_diarias AS (
  SELECT
    created_at::DATE AS data,
    SUM(total) AS total_dia
  FROM orders
  WHERE channel = 'pos'
  GROUP BY created_at::DATE
)
SUM(total) → faturamento total daquele dia.

Dias sem venda não aparecem nesse resultado.

🧩 Passo 4 – Cruzar calendário com vendas diárias (LEFT JOIN)
Unimos o calendário com as vendas diárias.

sql
SELECT
  c.data,
  vd.total_dia
FROM calendario c
LEFT JOIN vendas_diarias vd ON c.data = vd.data
LEFT JOIN mantém todos os dias do calendário.

Para dias sem venda, vd.total_dia é NULL.

🧩 Passo 5 – Substituir NULL por 0 (dias sem venda)
Usamos COALESCE para transformar NULL em 0.

sql
COALESCE(vd.total_dia, 0) AS total_dia
Agora, todos os dias têm um valor (0 se não houve venda).

🧩 Passo 6 – Agrupar por dia da semana e calcular a média
Agrupamos pelo número do dia da semana (EXTRACT(DOW FROM data)) e calculamos a média dos total_dia.

sql
GROUP BY EXTRACT(DOW FROM data)
AVG(total_dia) → soma os valores de todos os dias daquele dia da semana e divide pelo número total de dias daquele dia da semana no período.

🧩 Passo 7 – Traduzir o dia da semana para português
Usamos um CASE para converter o número (0 = domingo, 1 = segunda, ...) no nome em português.

sql
CASE EXTRACT(DOW FROM data)
  WHEN 0 THEN 'Domingo'
  WHEN 1 THEN 'Segunda-feira'
  ...
END AS dia_semana
🧩 Passo 8 – Ordenar e identificar o pior dia
Ordenamos pela média em ordem crescente (ASC) – o primeiro da lista é o dia com a pior média.

sql
ORDER BY media_vendas ASC
Se quisermos apenas o pior, adicionamos LIMIT 1.