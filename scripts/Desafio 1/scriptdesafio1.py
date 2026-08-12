"""
================================================================================
RESOLUÇÃO DA QUESTÃO 1 – ANÁLISE EXPLORATÓRIA (EDA)
================================================================================

1. OBJETIVO
   Realizar uma análise exploratória inicial na tabela 'orders' para responder
   perguntas críticas sobre volume, distribuição e qualidade dos dados, sem
   realizar qualquer limpeza ou tratamento. O objetivo principal era avaliar
   se os dados são confiáveis para tomada de decisões.

2. ABORDAGEM
   A análise foi implementada em Python 3, utilizando apenas bibliotecas
   padrão (csv, datetime, os), conforme exigido pelo desafio. Não foram
   utilizados pandas, dask ou polars.

   O script percorre o arquivo 'orders.csv', lê cada linha com csv.DictReader
   e extrai as seguintes métricas:
   - Total de linhas e colunas.
   - Intervalo de datas (mínimo e máximo da coluna 'created_at').
   - Estatísticas descritivas da coluna 'total': mínimo, máximo, média.
   - Contagem de valores nulos nessas duas colunas.

   Para garantir a robustez do parsing:
   - Valores ausentes ou não numéricos em 'total' são contabilizados como nulos.
   - Datas com formato inválido são ignoradas para o cálculo do intervalo.

3. RESULTADOS OBTIDOS
   - Total de linhas: 48.998
   - Total de colunas: 13
   - Intervalo de datas: 2020-01-01 01:19:28 a 2026-12-31 23:43:09
   - Valor mínimo de 'total': R$ 32,62
   - Valor máximo de 'total': R$ 127.262,02
   - Valor médio de 'total': R$ 28.704,99
   - Nulos em 'total': 0
   - Nulos em 'created_at': 0

4. DIAGNÓSTICO DE CONFIABILIDADE
   Com base na análise, concluiu-se que o dataset NÃO está pronto para
   análises diretas pelos seguintes motivos:
   - Presença de datas futuras (até 2026) que podem distorcer análises
     temporais e devem ser investigadas.
   - Outlier significativo em 'total' (máximo ~4,4× a média), que pode
     enviesar médias e modelos preditivos.
   - Apesar da boa completude (sem nulos nas colunas chave), recomenda-se
     tratamento de outliers e validação das datas inconsistentes antes de
     qualquer modelagem ou tomada de decisão.

5. VALIDAÇÃO CRUZADA
   Os resultados obtidos nesta análise exploratória foram posteriormente
   reproduzidos via consulta SQL diretamente no PostgreSQL (Questão 1.1),
   confirmando a consistência dos dados e da implementação. Essa validação
   dupla assegura a confiabilidade das métricas apresentadas.

================================================================================
"""




"""
Análise exploratória da tabela orders.
Calcula volume, distribuição e qualidade dos dados.
"""

import csv
from datetime import datetime
import os


def analisar_orders(caminho_csv):
    """
    Retorna métricas da tabela orders:
    - total de linhas e colunas
    - intervalo de datas (created_at)
    - estatísticas de total (min, max, média)
    - contagem de nulos
    """
    with open(caminho_csv, 'r', encoding='utf-8') as f:
        leitor = csv.DictReader(f)
        cabecalho = leitor.fieldnames

        total_linhas = 0
        datas = []
        valores_total = []
        nulos_total = 0
        nulos_created_at = 0

        for linha in leitor:
            total_linhas += 1


            val_total = linha.get('total')
            if val_total is None or val_total.strip() == '':
                nulos_total += 1
            else:
                try:
                    valores_total.append(float(val_total))
                except ValueError:
                    nulos_total += 1


            data_str = linha.get('created_at')
            if data_str is None or data_str.strip() == '':
                nulos_created_at += 1
            else:
                try:
                    datas.append(datetime.fromisoformat(data_str))
                except ValueError:
                    pass

        data_min = min(datas) if datas else None
        data_max = max(datas) if datas else None

        if valores_total:
            total_min = min(valores_total)
            total_max = max(valores_total)
            total_avg = sum(valores_total) / len(valores_total)
        else:
            total_min = total_max = total_avg = None

        num_colunas = len(cabecalho) if cabecalho else 0

        return {
            'linhas': total_linhas,
            'colunas': num_colunas,
            'data_min': data_min,
            'data_max': data_max,
            'total_min': total_min,
            'total_max': total_max,
            'total_avg': total_avg,
            'nulos_total': nulos_total,
            'nulos_created_at': nulos_created_at,
            'total_count': len(valores_total)
        }


if __name__ == '__main__':

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    arquivo = os.path.join(root_dir, 'data', 'orders.csv')

    if not os.path.exists(arquivo):
        print(f"Erro: Arquivo {arquivo} não encontrado.")
    else:
        resultado = analisar_orders(arquivo)

        print("=" * 50)
        print("RELATORIO DE ANALISE EXPLORATORIA - orders")
        print("=" * 50)
        print(f"Total de linhas          : {resultado['linhas']}")
        print(f"Total de colunas         : {resultado['colunas']}")
        print(f"Data minima (created_at) : {resultado['data_min']}")
        print(f"Data maxima (created_at) : {resultado['data_max']}")
        print(f"Valor minimo de total    : {resultado['total_min']:.2f}" if resultado['total_min'] is not None else "Valor minimo: N/A")
        print(f"Valor maximo de total    : {resultado['total_max']:.2f}" if resultado['total_max'] is not None else "Valor maximo: N/A")
        print(f"Valor medio de total     : {resultado['total_avg']:.2f}" if resultado['total_avg'] is not None else "Valor medio: N/A")
        print(f"Registros com total nulo : {resultado['nulos_total']}")
        print(f"Registros com created_at nulo: {resultado['nulos_created_at']}")
        print("=" * 50)