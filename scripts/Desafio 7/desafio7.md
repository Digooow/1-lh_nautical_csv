1. Como a matriz foi construída?
A matriz usuário × produto foi construída a partir dos dados de pedidos e itens, seguindo os seguintes passos:

Junção das tabelas:

orders (contém customer_id) foi unida a order_items via order_id.

order_items foi unida a product_variants via product_variant_id.

product_variants foi unida a products via product_id.
Essa cadeia permitiu mapear cada compra de um cliente a um produto específico.

Remoção de duplicatas:
Para cada par (cliente, produto), manteve‑se apenas uma ocorrência, independentemente da quantidade comprada. Isso garante que a matriz reflita apenas a presença (se o cliente comprou ou não o produto), e não a frequência ou volume.

Pivotamento:
Os dados foram transformados em uma tabela onde:

Linhas: clientes (customer_id)

Colunas: produtos (product_id)

Valores: 1 se o cliente comprou o produto pelo menos uma vez; 0 caso contrário.
Essa operação gerou uma matriz esparsa (com muitos zeros), que é a base para o cálculo de similaridade.

2. O que significa a similaridade de cosseno nesse contexto?
A similaridade de cosseno mede o quão parecidos são os padrões de compra de dois produtos, com base nos clientes que os adquiriram.

Cada produto é representado por um vetor binário de dimensão igual ao número de clientes. Cada posição do vetor indica se aquele cliente comprou o produto (1) ou não (0).

A similaridade de cosseno entre dois produtos A e B é calculada como:

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
 
O numerador (A · B) é o número de clientes que compraram ambos os produtos.

O denominador normaliza o resultado, dividindo pelo produto das normas (tamanhos) dos vetores, evitando que produtos muito populares sejam favorecidos apenas por terem mais compras.

O resultado é um valor entre 0 e 1 (neste caso, todos positivos, pois não há vetores negativos). Quanto maior o valor, mais clientes compraram os dois produtos juntos, indicando maior similaridade. No exemplo, a similaridade de 0,2566 entre o motor de popa e o GPS Plotter 6249 indica uma sobreposição moderada de clientes, mas ainda assim a maior entre todos os pares.

3. Uma limitação desse método de recomendação
A principal limitação é que a similaridade de cosseno com dados binários (presença/ausência) ignora a quantidade comprada e o valor monetário das transações. Um cliente que comprou 100 unidades de um produto e outro que comprou apenas 1 têm o mesmo peso na matriz. Isso pode distorcer a recomendação, pois produtos de alto valor ou alta recorrência podem ser subestimados em relação a produtos mais baratos ou comprados esporadicamente.

Além disso, o método sofre com o problema de cold start: produtos novos ou com poucas compras têm vetores esparsos (poucos clientes), dificultando o cálculo de similaridade com outros itens. Também não considera a ordem temporal das compras, nem preferências explícitas (como avaliações ou notas), o que limita a capacidade de personalização da recomendação.