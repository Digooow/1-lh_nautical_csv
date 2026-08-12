"""
Carregamento de todos os CSVs para o PostgreSQL.
Utiliza o schema.sql gerado na Questão 2 e a estrutura de pastas:
- data/ : arquivos CSV
- scripts/desafio_2/schema.sql (ou scripts/Desafio 2/schema.sql)
"""

import os
import subprocess
import re


CONTAINER = 'postgres-challenge'
DB_USER = 'challenge'
DB_NAME = 'challenge_db'


def sanitizar_nome(nome):

    nome = nome.strip().lower()
    nome = re.sub(r'[^a-z0-9]', '_', nome)
    nome = re.sub(r'_+', '_', nome)
    nome = nome.strip('_')
    if not nome or nome[0].isdigit():
        nome = 'col_' + nome
    return nome


def executar_schema(schema_path):

    if not os.path.exists(schema_path):
        print(f"Erro: Arquivo {schema_path} não encontrado.")
        return False

    with open(schema_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    for comando in sql.split(';'):
        comando = comando.strip()
        if comando:
            cmd_escaped = comando.replace("'", "''")
            resultado = subprocess.run(
                ['docker', 'exec', '-i', CONTAINER,
                 'psql', '-U', DB_USER, '-d', DB_NAME,
                 '-c', cmd_escaped],
                text=True,
                capture_output=True
            )
            if resultado.returncode != 0:
                print(f"Erro ao executar comando: {comando[:50]}...")
                print(resultado.stderr)
                return False

    print("Schema executado com sucesso.")
    return True


def carregar_csv(caminho_csv):

    nome_arquivo = os.path.basename(caminho_csv)
    nome_tabela = sanitizar_nome(os.path.splitext(nome_arquivo)[0])
    print(f"Carregando {nome_arquivo} -> {nome_tabela}")


    subprocess.run(
        ['docker', 'cp', caminho_csv, f'{CONTAINER}:/tmp/{nome_arquivo}'],
        check=True,
        text=True,
        capture_output=True
    )


    comando_copy = f"\\copy {nome_tabela} FROM '/tmp/{nome_arquivo}' WITH CSV HEADER"
    resultado = subprocess.run(
        ['docker', 'exec', '-i', CONTAINER,
         'psql', '-U', DB_USER, '-d', DB_NAME,
         '-c', comando_copy],
        text=True,
        capture_output=True
    )

    if resultado.returncode != 0:
        print(f"Erro ao carregar {nome_arquivo}: {resultado.stderr}")
        raise subprocess.CalledProcessError(resultado.returncode, resultado.args, resultado.stderr)

    print(f"  {nome_arquivo} carregado com sucesso.")


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    data_dir = os.path.join(root_dir, 'data')


    possiveis_caminhos = [
        os.path.join(root_dir, 'scripts', 'desafio_2', 'schema.sql'),
        os.path.join(root_dir, 'scripts', 'Desafio 2', 'schema.sql'),
        os.path.join(root_dir, 'schema.sql'),  
    ]
    schema_path = None
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            schema_path = caminho
            break

    if schema_path is None:
        print("Erro: schema.sql não encontrado. Execute a Questão 2 primeiro.")
        return

    if not os.path.isdir(data_dir):
        print(f"Erro: Pasta de dados '{data_dir}' não encontrada.")
        return


    if not executar_schema(schema_path):
        return


    arquivos = list(set([f for f in os.listdir(data_dir) if f.lower().endswith('.csv')]))
    if not arquivos:
        print("Nenhum arquivo CSV encontrado.")
        return

    print(f"Encontrados {len(arquivos)} arquivos CSV.")


    sucessos = 0
    for arquivo in arquivos:
        caminho = os.path.join(data_dir, arquivo)
        try:
            carregar_csv(caminho)
            sucessos += 1
        except subprocess.CalledProcessError:
            continue

    print(f"Processo concluido. {sucessos} de {len(arquivos)} arquivos carregados com sucesso.")


if __name__ == '__main__':
    main()