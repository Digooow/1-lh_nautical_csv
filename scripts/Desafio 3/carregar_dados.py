"""
Questão 3 – Carregamento de dados
---------------------------------
Este script carrega todos os arquivos CSV do diretório para o PostgreSQL,
utilizando o schema definido na Questão 2 (schema.sql). A carga é feita via
docker exec, utilizando o comando \copy do psql, que é eficiente e mantém
os dados brutos, sem qualquer transformação.
"""

import os
import subprocess
import re

# ============================================================================
# CONFIGURAÇÕES (ajuste conforme seu ambiente)
# ============================================================================

DIRETORIO_CSV = r'C:\Users\Rodrigo\Desktop\Projetos\1-lh_nautical_csv'
CONTAINER = 'postgres-challenge'
DB_USER = 'challenge'
DB_NAME = 'challenge_db'

# Caminho do schema.sql (gerado na Questão 2) – assume que está na raiz do projeto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_SQL = os.path.join(SCRIPT_DIR, '..', '..', 'schema.sql')

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def sanitizar_nome(nome):
    """
    Sanitiza o nome da tabela para corresponder ao nome gerado no schema.
    Deve ser a mesma função usada na Questão 2.
    """
    nome = nome.strip().lower()
    nome = re.sub(r'[^a-z0-9]', '_', nome)
    nome = re.sub(r'_+', '_', nome)
    nome = nome.strip('_')
    if not nome or nome[0].isdigit():
        nome = 'col_' + nome
    return nome

def executar_schema():
    """
    Executa o arquivo schema.sql no banco de dados.
    Isso cria (ou recria) todas as tabelas com os tipos inferidos.
    """
    if not os.path.exists(SCHEMA_SQL):
        print(f'❌ Arquivo {SCHEMA_SQL} não encontrado. Execute a Questão 2 primeiro.')
        return False

    with open(SCHEMA_SQL, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Divide os comandos SQL individuais (separados por ;)
    for comando in sql.split(';'):
        comando = comando.strip()
        if comando:
            # Escapa aspas simples para evitar problemas no shell
            cmd_escaped = comando.replace("'", "''")
            resultado = subprocess.run(
                ['docker', 'exec', '-i', CONTAINER,
                 'psql', '-U', DB_USER, '-d', DB_NAME,
                 '-c', cmd_escaped],
                text=True,
                capture_output=True
            )
            if resultado.returncode != 0:
                print(f'⚠️ Erro ao executar comando: {comando[:50]}...')
                print(f'   {resultado.stderr}')
                return False

    print('✅ Schema executado com sucesso.')
    return True

def carregar_csv(caminho_csv):
    """
    Carrega um único arquivo CSV para sua tabela correspondente.
    A tabela deve já existir no banco (criada pelo schema).
    """
    nome_arquivo = os.path.basename(caminho_csv)
    nome_tabela = sanitizar_nome(os.path.splitext(nome_arquivo)[0])
    print(f'📤 Carregando {nome_arquivo} -> tabela {nome_tabela}')

    # 1. Copia o arquivo CSV para dentro do container (pasta /tmp)
    subprocess.run(
        ['docker', 'cp', caminho_csv, f'{CONTAINER}:/tmp/{nome_arquivo}'],
        check=True,
        text=True,
        capture_output=True
    )

    # 2. Executa o comando \copy dentro do container
    #    O HEADER true indica que a primeira linha é o cabeçalho (ignorada)
    comando_copy = f"\\copy {nome_tabela} FROM '/tmp/{nome_arquivo}' WITH CSV HEADER"
    resultado = subprocess.run(
        ['docker', 'exec', '-i', CONTAINER,
         'psql', '-U', DB_USER, '-d', DB_NAME,
         '-c', comando_copy],
        text=True,
        capture_output=True
    )

    if resultado.returncode != 0:
        print(f'❌ Erro ao carregar {nome_arquivo}: {resultado.stderr}')
        raise subprocess.CalledProcessError(resultado.returncode, resultado.args, resultado.stderr)

    print(f'   ✅ {nome_arquivo} carregado com sucesso.')

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Orquestra o processo completo:
    1. Executa o schema (cria as tabelas).
    2. Lista todos os arquivos CSV (sem duplicatas).
    3. Carrega cada um, continuando mesmo se algum falhar.
    """
    print('🚀 Iniciando carregamento dos dados...')

    # 1. Executa o schema
    if not executar_schema():
        print('❌ Falha ao executar o schema. Abortando.')
        return

    # 2. Lista os CSVs (usando set para eliminar duplicatas)
    arquivos = list(set([
        f for f in os.listdir(DIRETORIO_CSV)
        if f.lower().endswith('.csv')
    ]))

    if not arquivos:
        print('❌ Nenhum arquivo CSV encontrado no diretório.')
        return

    print(f'📂 Encontrados {len(arquivos)} arquivos CSV.')

    # 3. Carrega cada arquivo
    sucessos = 0
    for arquivo in arquivos:
        caminho = os.path.join(DIRETORIO_CSV, arquivo)
        try:
            carregar_csv(caminho)
            sucessos += 1
        except subprocess.CalledProcessError:
            # O erro já foi exibido pela função carregar_csv
            continue

    print(f'🎉 Processo concluído. {sucessos} de {len(arquivos)} arquivos carregados com sucesso.')

if __name__ == '__main__':
    main()