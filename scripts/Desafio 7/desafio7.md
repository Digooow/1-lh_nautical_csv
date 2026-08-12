📌 Questão 7.2 – Produto com MAIOR similaridade
Ao executar o script, o primeiro item do ranking é o produto com a maior similaridade de cosseno em relação ao "Motor de Popa 1949".

Exemplo de saída (simulado):

text
Produto de referência: Motor de Popa 1949

Ranking dos 5 produtos mais similares:
1. Motor de Popa 1950 (similaridade = 0.8734)   ← MAIOR similaridade
2. Caixa de Direção 2000 (similaridade = 0.7652)
3. Hélice Náutica 4 pás (similaridade = 0.7421)
4. Sistema de Injeção Eletrônica (similaridade = 0.6897)
5. Tanque de Combustível 100L (similaridade = 0.6543)
Resposta: O produto com maior similaridade é "Motor de Popa 1950" (no exemplo). Para obter o valor real, execute o script com seus dados.

📘 Questão 7.3 – Explicação
a) Como a matriz foi construída?
A matriz de interação usuário × produto foi construída seguindo estas etapas:

Junção das tabelas: orders (com customer_id) → order_items → product_variants → products (com product_id).

Filtragem: Mantivemos apenas as colunas customer_id e product_id, removendo duplicatas (um cliente pode comprar o mesmo produto várias vezes, mas queremos apenas presença).

Criação da coluna de presença: atribuímos valor 1 para cada par (cliente, produto) que aparece na lista de compras.

Pivotamento: Usamos pivot_table com fill_value=0 para criar uma tabela onde as linhas são customer_id, as colunas são product_id e os valores são 1 ou 0.

O resultado é uma matriz esparsa (muitos zeros) que representa, para cada cliente, quais produtos ele já comprou.

b) O que significa a similaridade de cosseno nesse contexto?
A similaridade de cosseno entre dois produtos A e B mede o quão parecidos são os padrões de compra dos clientes que adquiriram cada um.

Cada produto é representado por um vetor binário onde cada posição corresponde a um cliente e o valor é 1 se aquele cliente comprou o produto, 0 caso contrário.

O cosseno do ângulo entre esses dois vetores é calculado como:

cos_sim
(
A
,
B
)
=
A
⋅
B
∥
A
∥
∥
B
∥
cos_sim(A,B)= 
∥A∥∥B∥
A⋅B
​
 
O numerador é o número de clientes que compraram ambos os produtos.

O denominador é a raiz quadrada do produto das quantidades de clientes que compraram cada um (normalização).

Quanto maior o valor (próximo de 1), mais clientes compraram os dois produtos juntos, indicando maior similaridade. Produtos com baixa similaridade têm padrões de compra diferentes.

c) Uma limitação desse método de recomendação.
Limitação principal: O método baseado em similaridade de cosseno com dados binários (presença/ausência) ignora a quantidade comprada e o valor monetário das compras. Um cliente que comprou 100 unidades de um produto e outro que comprou apenas 1 têm o mesmo peso na matriz. Isso pode distorcer a recomendação, pois produtos de alto valor ou alta frequência podem ser subestimados.

Além disso, o método sofre com o problema de cold start: produtos novos ou com poucas compras têm vetores esparsos, dificultando o cálculo de similaridade com outros itens. Também não considera a ordem temporal das compras ou preferências explícitas (como avaliações).

✅ Resumo das respostas
Item	Resposta
7.1	Código Python fornecido acima.
7.2	O nome do produto com maior similaridade é o primeiro da lista gerada pelo script. Execute para obter o valor real.
7.3	Explicação detalhada sobre construção da matriz, significado da similaridade de cosseno e limitação do método.