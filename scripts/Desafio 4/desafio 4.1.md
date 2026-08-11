Questão 4.2 – Explicação da metodologia
1. Como você chegou nas categorias mais vendidas? (mapeamento da cadeia de chaves)
Para identificar a categoria preferida de cada cliente, percorremos a cadeia de relacionamentos entre as tabelas, partindo do pedido até a categoria do produto:

text
orders → order_items → product_variants → products → categories
orders.id = order_items.order_id

order_items.product_variant_id = product_variants.id

product_variants.product_id = products.id

products.category_id = categories.id

Essa cadeia permite, a partir de um pedido, acessar o nome da categoria (categories.name) e a quantidade de itens (order_items.quantity). A categoria mais vendida para cada cliente é aquela com maior SUM(quantity).

2. Qual lógica utilizou para filtrar os clientes com diversidade mínima?
A diversidade é calculada como o número de categorias distintas que o cliente comprou:

sql
COUNT(DISTINCT p.category_id) AS diversidade
O filtro de diversidade mínima de 13 categorias foi aplicado com a cláusula HAVING:

sql
HAVING COUNT(DISTINCT p.category_id) >= 13
Assim, apenas clientes com diversidade igual ou superior a 13 entram no cálculo do ticket médio para o ranking.

3. Como garantiu que a contagem de itens refletisse apenas os Top 10?
Para garantir que a soma de quantidades por categoria seja calculada exclusivamente para os 10 clientes do ranking, a consulta foi estruturada em etapas:

customer_stats – calcula ticket médio e diversidade para todos os clientes (com filtro de diversidade ≥ 13).

top_clientes – seleciona os 10 clientes com maior ticket médio.

categoria_compras – faz JOIN diretamente com top_clientes, restringindo todas as agregações subsequentes (ex.: SUM(oi.quantity)) apenas aos pedidos e itens desses 10 clientes.

Com isso, a categoria preferida e a quantidade total de itens são calculadas exclusivamente sobre o comportamento de compra dos clientes de elite, sem interferência de outros clientes.

