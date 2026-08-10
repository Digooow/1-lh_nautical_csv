import csv
import os

diretorio = r'C:\Users\Rodrigo\Desktop\Projetos\1-lh_nautical_csv'
arquivos = [f for f in os.listdir(diretorio) if f.endswith('.csv')]
sql = ""

for arquivo in arquivos:
    nome_tabela = os.path.splitext(arquivo)[0].lower()
    caminho = os.path.join(diretorio, arquivo)
    with open(caminho, 'r', encoding='utf-8') as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor)
    colunas = ', '.join([f'"{col}" TEXT' for col in cabecalho])
    sql += f'DROP TABLE IF EXISTS {nome_tabela} CASCADE;\n'
    sql += f'CREATE TABLE {nome_tabela} ({colunas});\n'
    sql += f"\\COPY {nome_tabela} FROM '/tmp/{arquivo}' WITH (FORMAT CSV, HEADER true);\n\n"

with open('importar.sql', 'w', encoding='utf-8') as f:
    f.write(sql)

print("Arquivo importar.sql gerado com sucesso!")
