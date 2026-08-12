Questão 5.2 – Explicação
1. Por que é necessário utilizar uma tabela de datas (calendário) em vez de agrupar diretamente a tabela de vendas?
Agrupar diretamente a tabela orders por dia da semana (GROUP BY EXTRACT(DOW FROM created_at)) considera apenas os dias em que houve pelo menos uma venda. Isso faz com que dias sem venda – como domingos em que a loja esteve aberta, mas não houve faturamento – sejam completamente ignorados no cálculo da média.

A tabela de calendário resolve esse problema ao garantir que todos os dias do período estejam representados, independentemente de terem vendas. Com o LEFT JOIN entre o calendário e as vendas diárias, os dias sem venda são incluídos com valor 0 (via COALESCE), permitindo que a média reflita corretamente o desempenho real da loja em todos os dias da semana.

2. O que aconteceria com a média de vendas se um dia da semana tivesse muitos dias sem nenhuma venda registrada?
Se um dia da semana (ex.: domingo) tiver muitos dias sem venda registrada, a média calculada exclusivamente sobre os dias com venda seria inflada artificialmente, porque os dias zerados seriam ignorados. Isso dá uma falsa impressão de que o desempenho é melhor do que realmente é.

Exemplo:

5 domingos no período.

2 domingos com vendas: R
10.000
e
R
10.000eR 5.000.

3 domingos sem vendas (R$ 0).

Método	Cálculo	Média
Sem calendário (apenas dias com venda)	(10.000 + 5.000) / 2 = 7.500	Inflada
Com calendário (todos os dias)	(10.000 + 5.000 + 0 + 0 + 0) / 5 = 3.000	Correta
Com o calendário, a média considera todos os domingos, inclusive os sem venda, resultando em um valor mais baixo e mais realista. Isso evita que a diretoria tome decisões equivocadas baseadas em dados distorcidos, como manter a loja aberta em um dia que, na prática, tem baixo ou nenhum faturamento.

