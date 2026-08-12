

import csv
import os
import re
from datetime import datetime


def inferir_tipo_coluna(valores):

    nao_nulos = [v for v in valores if v and v.strip()]
    if not nao_nulos:
        return 'TEXT'


    todos_int = True
    for v in nao_nulos:
        try:
            int(v)
        except ValueError:
            todos_int = False
            break
    if todos_int:
        for v in nao_nulos:
            if v[0] == '0' and len(v) > 1:
                return 'TEXT'
        max_len = max(len(v) for v in nao_nulos)
        if max_len > 10:
            return 'TEXT'
        return 'INTEGER'


    todos_float = True
    for v in nao_nulos:
        try:
            float(v)
        except ValueError:
            todos_float = False
            break
    if todos_float:
        return 'NUMERIC'


    todos_date = True
    for v in nao_nulos:
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            todos_date = False
            break
    if todos_date:
        return 'DATE'


    todos_timestamp = True
    for v in nao_nulos:
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            todos_timestamp = False
            break
    if todos_timestamp:
        return 'TIMESTAMP'

    return 'TEXT'


def sanitizar_nome(nome):

    nome = nome.strip().lower()
    nome = re.sub(r'[^a-z0-9]', '_', nome)
    nome = re.sub(r'_+', '_', nome)
    nome = nome.strip('_')
    if not nome or nome[0].isdigit():
        nome = 'col_' + nome
    return nome


def processar_arquivos(data_dir, amostra=None):

    arquivos = [f for f in os.listdir(data_dir) if f.lower().endswith('.csv')]
    sql_statements = []

    for arquivo in arquivos:
        caminho = os.path.join(data_dir, arquivo)
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
                if amostra is not None and i >= amostra:
                    break
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


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    data_dir = os.path.join(root_dir, 'data')
    output_file = os.path.join(script_dir, 'schema.sql')

    if not os.path.isdir(data_dir):
        print(f'Erro: Diretório {data_dir} não encontrado.')
    else:
        sql_final = processar_arquivos(data_dir, amostra=None)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('-- Schema gerado automaticamente\n')
            f.write(f'-- Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write(sql_final)
        print(f'Schema gerado em {output_file}')