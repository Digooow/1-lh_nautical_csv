"""
================================================================================
RESOLUÇÃO DA QUESTÃO 1.1 – SQL
================================================================================

Esta solução foi desenvolvida para atender aos requisitos do desafio técnico,
utilizando apenas ferramentas padrão e garantindo a reprodutibilidade dos
resultados.

1. ESCOLHA DO AMBIENTE
   Optou-se pelo uso de Docker para criar um container PostgreSQL isolado.
   Essa decisão eliminou a necessidade de instalação local do banco de dados,
   garantindo que o ambiente seja consistente e portável entre diferentes
   sistemas operacionais (Windows, Linux, macOS). O container foi criado com
   o comando:
       docker run --name postgres-challenge -e POSTGRES_PASSWORD=mysecret \\
           -e POSTGRES_USER=challenge -e POSTGRES_DB=challenge_db \\
           -p 5432:5432 -d postgres

2. CARGA DOS DADOS
   Todos os arquivos CSV foram importados para o PostgreSQL utilizando a
   ferramenta nativa \copy, que é eficiente e lida automaticamente com a
   formatação dos dados. Para evitar erros de conversão de tipos (já que
   os CSVs contêm dados diversos), todas as colunas foram criadas como
   TEXT. Posteriormente, as conversões necessárias são feitas diretamente
   nas consultas (ex.: total::numeric). O processo de carga foi automatizado
   por um script Python que:
   - Lê o cabeçalho de cada CSV para definir as colunas da tabela.
   - Gera um arquivo SQL com comandos DROP/CREATE TABLE e \copy.
   - Copia os CSVs para o container e executa o script SQL via stdin.

3. CONSULTA SQL (QUESTÃO 1.1)
   A consulta que retorna as métricas solicitadas (total de linhas,
   intervalo de datas, mínimo, máximo e média do campo "total") é executada
   diretamente no banco PostgreSQL. O script Python apresentado a seguir
   utiliza o comando 'docker exec' para invocar o psql dentro do container,
   garantindo que a consulta seja processada pelo banco sem a necessidade
   de instalar clientes PostgreSQL localmente.

4. VALIDAÇÃO
   Após a carga, a consulta foi executada tanto manualmente no terminal
   quanto via script Python, confirmando que os resultados obtidos batem
   com a análise exploratória realizada anteriormente (script EDA).
   Essa dupla verificação assegura a confiabilidade dos dados e a correta
   implementação da solução.

Observação: Caso a coluna 'total' seja convertida para NUMERIC no futuro,
as conversões explícitas (total::numeric) podem ser removidas da consulta.

================================================================================
"""





import subprocess
import csv
import io

class PostgresExecutor:
    def __init__(self, container_name='postgres-challenge', user='challenge', dbname='challenge_db'):
        self.container_name = container_name
        self.user = user
        self.dbname = dbname

    def execute_query(self, sql):
        # Mantém --tuples-only para não ter cabeçalho, mas não usa --csv,
        # apenas saída delimitada por vírgula e sem alinhamento.
        cmd = [
            'docker', 'exec', '-i', self.container_name,
            'psql', '-U', self.user, '-d', self.dbname,
            '--no-psqlrc', '--tuples-only', '-A', '-F', ',',
            '-c', sql
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Erro: {stderr}")
        if not stdout.strip():
            return None
        # Lê a primeira linha como dados (sem cabeçalho)
        reader = csv.reader(io.StringIO(stdout))
        rows = list(reader)
        if not rows:
            return None
        # Os campos estão na ordem: total_linhas, data_minima, data_maxima, valor_minimo, valor_maximo, valor_medio
        fields = ['total_linhas', 'data_minima', 'data_maxima', 'valor_minimo', 'valor_maximo', 'valor_medio']
        values = rows[0]
        return dict(zip(fields, values))

def main():
    sql = """
    SELECT 
        COUNT(*) AS total_linhas,
        MIN(created_at) AS data_minima,
        MAX(created_at) AS data_maxima,
        MIN(total::numeric) AS valor_minimo,
        MAX(total::numeric) AS valor_maximo,
        AVG(total::numeric) AS valor_medio
    FROM orders;
    """
    executor = PostgresExecutor()
    try:
        resultado = executor.execute_query(sql)
        if resultado is None:
            print("Nenhum resultado retornado.")
            return
        print("=" * 60)
        print("RESULTADO DA CONSULTA SQL (Questão 1.1)")
        print("=" * 60)
        print(f"Total de linhas      : {resultado['total_linhas']}")
        print(f"Data mínima          : {resultado['data_minima']}")
        print(f"Data máxima          : {resultado['data_maxima']}")
        print(f"Valor mínimo (total) : {resultado['valor_minimo']}")
        print(f"Valor máximo (total) : {resultado['valor_maximo']}")
        print(f"Valor médio (total)  : {resultado['valor_medio']}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    main()