"""Ingestão transacional dos 24 arquivos CSV no PostgreSQL via SQLAlchemy + psycopg."""

from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy import Engine, text

from lh_nautical.db import PROJECT_ROOT, get_data_dir, get_engine

logger = logging.getLogger(__name__)

# Ordem estritamente topológica respeitando todas as 37 chaves estrangeiras.
TOPOLOGICAL_TABLES: tuple[str, ...] = (
    "locations",
    "attributes",
    "brands",
    "categories",
    "customers",
    "suppliers",
    "employees",
    "addresses",
    "products",
    "product_variants",
    "variant_attribute_values",
    "product_suppliers",
    "orders",
    "order_items",
    "payments",
    "fiscal_invoices",
    "purchase_orders",
    "purchase_order_items",
    "goods_receipts",
    "goods_receipt_items",
    "returns",
    "return_items",
    "stock_levels",
    "stock_movements",
)


def _count_csv_data_rows(csv_path: Path) -> int:
    """Conta o número de linhas de dados de um CSV (excluindo o cabeçalho)."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def run_ingestion(
    engine: Engine | None = None,
    schema_path: Path | None = None,
    data_dir: Path | None = None,
) -> dict[str, int]:
    """
    Executa o DDL e carrega todos os 24 CSVs em uma única transação atômica.

    Se qualquer arquivo falhar na validação de tipos, restrições de chave ou
    contagem de linhas, toda a operação sofre rollback automático.
    """
    engine = engine or get_engine()
    schema_path = schema_path or (PROJECT_ROOT / "sql" / "schema.sql")
    data_dir = data_dir or get_data_dir()

    if not schema_path.is_file():
        raise FileNotFoundError(f"Arquivo de schema não encontrado: {schema_path}")
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Diretório de dados não encontrado: {data_dir}")

    missing_files = [
        table for table in TOPOLOGICAL_TABLES if not (data_dir / f"{table}.csv").is_file()
    ]
    if missing_files:
        raise FileNotFoundError(
            f"Arquivos CSV obrigatórios ausentes em {data_dir}: {', '.join(missing_files)}"
        )

    ddl_sql = schema_path.read_text(encoding="utf-8")
    loaded_counts: dict[str, int] = {}

    with engine.begin() as conn:
        raw_conn = conn.connection.driver_connection
        if raw_conn is None:
            raise RuntimeError("Conexão psycopg subjacente indisponível.")

        with raw_conn.cursor() as cur:
            logger.info("Aplicando DDL relacional a partir de %s", schema_path.name)
            cur.execute(ddl_sql)

            for table in TOPOLOGICAL_TABLES:
                csv_path = data_dir / f"{table}.csv"
                expected_rows = _count_csv_data_rows(csv_path)

                copy_sql = (
                    f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')"
                )
                with csv_path.open("r", encoding="utf-8-sig") as csv_file:
                    with cur.copy(copy_sql) as copy_ctx:
                        while chunk := csv_file.read(65536):
                            copy_ctx.write(chunk)

                db_rows = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar_one()

                if db_rows != expected_rows:
                    raise RuntimeError(
                        f"Divergência de contagem na tabela '{table}': "
                        f"CSV={expected_rows}, DB={db_rows}"
                    )

                loaded_counts[table] = int(db_rows)
                logger.info("Tabela %-26s carregada (%6d registros)", table, db_rows)

    return loaded_counts


def main() -> int:
    """Ponto de entrada CLI para ingestão transacional do banco."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    try:
        counts = run_ingestion()
        total_rows = sum(counts.values())
        logger.info(
            "Ingestão concluída com sucesso: %d tabelas, %d registros totais.",
            len(counts),
            total_rows,
        )
        return 0
    except Exception as exc:
        logger.error("Falha crítica na ingestão (rollback executado): %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

