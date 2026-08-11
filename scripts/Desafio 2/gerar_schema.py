import csv
import os
import re
from datetime import datetime

# Configurações
DIRETORIO_CSV = r'C:\Users\Rodrigo\Desktop\Projetos\1-lh_nautical_csv'
ARQUIVO_SAIDA = 'schema.sql'
AMOSTRA_LINHAS = None  # None = lê todas as linhas para inferência precisa

def inferir_tipo_coluna(valores):
    """Infere o tipo PostgreSQL mais adequado para uma coluna."""
    nao_nulos = [v for v in valores if v and v.strip()]
    if not nao_nulos:
        return 'TEXT'

    # Tenta INTEGER
    todos_int = True
    for v in nao_nulos:
        try:
            int(v)
        except ValueError:
            todos_int = False
            break
    if todos_int:
        # Verifica se algum valor começa com zero (ex: CPF, telefone)
        for v in nao_nulos:
            if v[0] == '0' and len(v) > 1:
                return 'TEXT'
        # Se o número for muito grande (> 10 dígitos), usa TEXT
        max_len = max(len(v) for v in nao_nulos)
        if max_len > 10:
            return 'TEXT'
        return 'INTEGER'

    # Tenta NUMERIC (decimal)
    todos_float = True
    for v in nao_nulos:
        try:
            float(v)
        except ValueError:
            todos_float = False
            break
    if todos_float:
        return 'NUMERIC'

    # Tenta DATE (YYYY-MM-DD)
    todos_date = True
    for v in nao_nulos:
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            todos_date = False
            break
    if todos_date:
        return 'DATE'

    # Tenta TIMESTAMP (YYYY-MM-DD HH:MM:SS)
    todos_timestamp = True
    for v in nao_nulos:
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            todos_timestamp = False
            break
    if todos_timestamp:
        return 'TIMESTAMP'

    # Se não encaixou em nenhum dos acima, é TEXT
    return 'TEXT'

def sanitizar_nome(nome):
    """Converte nome para formato seguro (minúsculo, underscores)."""
    nome = nome.strip().lower()
    nome = re.sub(r'[^a-z0-9]', '_', nome)
    nome = re.sub(r'_+', '_', nome)
    nome = nome.strip('_')
    if not nome or nome[0].isdigit():
        nome = 'col_' + nome
    return nome

def processar_arquivos(diretorio):
    arquivos = [f for f in os.listdir(diretorio) if f.lower().endswith('.csv')]
    sql_statements = []

    for arquivo in arquivos:
        caminho = os.path.join(diretorio, arquivo)
        nome_tabela = sanitizar_nome(os.path.splitext(arquivo)[0])
        print(f'Processando {arquivo} -> {nome_tabela}')

        with open(caminho, 'r', encoding='utf-8-sig') as f:
            leitor = csv.reader(f)
            try:
                cabecalho = next(leitor)
            except StopIteration:
                print(f'  Aviso: {arquivo} vazio. Pulando.')
                continue

            colunas = [sanitizar_nome(col) for col in cabecalho]
            valores_por_coluna = {i: [] for i in range(len(colunas))}

            for i, linha in enumerate(leitor):
                if AMOSTRA_LINHAS is not None and i >= AMOSTRA_LINHAS:
                    break
                # Normaliza número de colunas
                if len(linha) < len(colunas):
                    linha += [''] * (len(colunas) - len(linha))
                elif len(linha) > len(colunas):
                    linha = linha[:len(colunas)]
                for idx, val in enumerate(linha):
                    valores_por_coluna[idx].append(val)

        tipos = [inferir_tipo_coluna(valores_por_coluna[i]) for i in range(len(colunas))]

        colunas_sql = [f'    "{col}" {tipo}' for col, tipo in zip(colunas, tipos)]
        create_sql = f'DROP TABLE IF EXISTS {nome_tabela} CASCADE;\n'
        create_sql += f'CREATE TABLE {nome_tabela} (\n' + ',\n'.join(colunas_sql) + '\n);'
        sql_statements.append(create_sql)

    return '\n\n'.join(sql_statements)

def main():
    if not os.path.isdir(DIRETORIO_CSV):
        print(f'Diretório {DIRETORIO_CSV} não encontrado.')
        return

    sql_final = processar_arquivos(DIRETORIO_CSV)
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        f.write('-- Schema gerado automaticamente\n')
        f.write(f'-- Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        f.write(sql_final)

    print(f'\n✅ Schema gerado em {ARQUIVO_SAIDA}')

if __name__ == '__main__':
    main()