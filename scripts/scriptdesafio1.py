import csv
from datetime import datetime
import os

def analisar_orders(caminho_csv):
    """
    Realiza a análise exploratória da tabela orders.
    Retorna um dicionário com as métricas.
    """
    with open(caminho_csv, 'r', encoding='utf-8') as f:
        leitor = csv.DictReader(f)
        cabecalho = leitor.fieldnames
        
        # Inicialização
        total_linhas = 0
        datas = []
        valores_total = []
        nulos_total = 0
        nulos_created_at = 0
        
        for linha in leitor:
            total_linhas += 1
            
            # Coluna total
            val_total = linha.get('total')
            if val_total is None or val_total.strip() == '':
                nulos_total += 1
            else:
                try:
                    valores_total.append(float(val_total))
                except ValueError:
                    # Caso haja valores não numéricos, contamos como nulos para efeito de análise
                    nulos_total += 1
            
            # Coluna created_at
            data_str = linha.get('created_at')
            if data_str is None or data_str.strip() == '':
                nulos_created_at += 1
            else:
                try:
                    # Assume formato ISO (YYYY-MM-DD HH:MM:SS) ou similar
                    datas.append(datetime.fromisoformat(data_str))
                except ValueError:
                    # Se não conseguir parsear, ignora para min/max (mas conta como inconsistente)
                    pass
        
        # Estatísticas das datas
        if datas:
            data_min = min(datas)
            data_max = max(datas)
        else:
            data_min = data_max = None
        
        # Estatísticas do total
        if valores_total:
            total_min = min(valores_total)
            total_max = max(valores_total)
            total_avg = sum(valores_total) / len(valores_total)
        else:
            total_min = total_max = total_avg = None
        
        # Número de colunas
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
    # Supondo que o arquivo orders.csv está no mesmo diretório
    arquivo = 'orders.csv'
    if not os.path.exists(arquivo):
        print(f"Arquivo {arquivo} não encontrado.")
    else:
        resultado = analisar_orders(arquivo)
        
        print("=" * 50)
        print("RELATÓRIO DE ANÁLISE EXPLORATÓRIA - orders")
        print("=" * 50)
        print(f"Total de linhas          : {resultado['linhas']}")
        print(f"Total de colunas         : {resultado['colunas']}")
        print(f"Data mínima (created_at) : {resultado['data_min']}")
        print(f"Data máxima (created_at) : {resultado['data_max']}")
        print(f"Valor mínimo de total    : {resultado['total_min']}")
        print(f"Valor máximo de total    : {resultado['total_max']}")
        print(f"Valor médio de total     : {resultado['total_avg']:.2f}" if resultado['total_avg'] is not None else "Valor médio: N/A")
        print(f"Registros com total nulo : {resultado['nulos_total']}")
        print(f"Registros com created_at nulo: {resultado['nulos_created_at']}")
        print("=" * 50)