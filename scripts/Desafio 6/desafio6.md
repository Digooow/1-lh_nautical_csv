1. Como o baseline foi construído?
O baseline adotado foi a média móvel simples dos últimos 3 meses. O processo de construção seguiu as seguintes etapas:

Agregação mensal: as vendas do produto “Bússola de Bordo 702” foram somadas por mês, gerando uma série temporal mensal.

Separação treino/teste: o treino incluiu todos os meses até 31/12/2025; o teste correspondeu ao primeiro trimestre de 2026 (janeiro, fevereiro e março).

Previsão sequencial (passo a passo): para cada mês do período de teste, a previsão foi calculada como a média dos três meses imediatamente anteriores.

Para janeiro de 2026, foram usados os meses de outubro, novembro e dezembro de 2025 (valores reais).

Para fevereiro de 2026, foram usados novembro e dezembro de 2025, além da previsão de janeiro de 2026 (já que o valor real de janeiro não estava disponível no momento da previsão).

Para março de 2026, foram usados dezembro de 2025 e as previsões de janeiro e fevereiro de 2026.

Essa abordagem simula o que ocorreria na prática: ao prever um mês futuro, só se tem conhecimento dos meses passados (reais ou previstos).

2. Como evitou data leakage?
Data leakage ocorre quando informações futuras (não disponíveis no momento da previsão) são utilizadas inadvertidamente. Para evitá-lo, a seguinte estratégia foi adotada:

O treino foi estritamente limitado a dados com data até 31/12/2025.

Para cada mês previsto (janeiro, fevereiro e março de 2026), a previsão foi calculada exclusivamente com base em dados anteriores àquele mês. Em nenhum momento foram utilizados valores reais do período de teste para compor as previsões. Quando um mês de teste ainda não havia ocorrido (ex.: fevereiro), utilizou-se a previsão do mês anterior (janeiro) como substituto, mantendo a integridade da simulação.

Dessa forma, o modelo nunca “enxerga” o futuro, garantindo que a avaliação do erro (MAE) reflita o desempenho real do baseline em um cenário de produção.

3. Uma limitação do modelo proposto
A principal limitação da média móvel simples é que ela não captura padrões sazonais, tendências ou efeitos de eventos sazonais (como aumento de vendas em determinadas épocas do ano). Para o produto “Bússola de Bordo 702”, que apresenta comportamento sazonal (picos em meses de verão, por exemplo), o modelo subestima consistentemente a demanda em meses de alta, resultando em erros significativos (MAE de 28,02 unidades). Esse baseline é adequado apenas para séries temporais estacionárias, sem sazonalidade ou tendência, o que não é o caso. Para melhorar a precisão, seria necessário adotar modelos mais sofisticados que incorporassem componentes sazonais (como ARIMA, Prophet ou redes neurais).