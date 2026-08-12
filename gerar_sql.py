import csv
import os


script_dir = os.path.dirname(os.path.abspath(__file__))



root_dir = os.path.dirname(script_dir) if os.path.basename(script_dir) == 'scripts' else script_dir
data_dir = os.path.join(root_dir, 'data')


if not os.path.isdir(data_dir):
    print(f"Erro: Pasta 'data' não encontrada em {data_dir}")
    exit(1)


arquivos = [f for f in os.listdir(data_dir) if f.lower().endswith('.csv')]
if not arquivos:
    print("Nenhum arquivo CSV encontrado na pasta 'data'.")
    exit(1)

sql = ""

for arquivo in arquivos:
    nome_tabela = os.path.splitext(arquivo)[0].lower()
    caminho = os.path.join(data_dir, arquivo)
    with open(caminho, 'r', encoding='utf-8') as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor)
    colunas = ', '.join([f'"{col}" TEXT' for col in cabecalho])
    sql += f'DROP TABLE IF EXISTS {nome_tabela} CASCADE;\n'
    sql += f'CREATE TABLE {nome_tabela} ({colunas});\n'
    sql += f"\\COPY {nome_tabela} FROM '/tmp/{arquivo}' WITH (FORMAT CSV, HEADER true);\n\n"


output_dir = os.path.join(root_dir, 'sql')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, 'importar.sql')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(sql)

print(f"Arquivo importar.sql gerado com sucesso em {output_file}")