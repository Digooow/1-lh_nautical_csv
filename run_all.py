"""
Orquestrador fim a fim do pipeline analítico LH Nautical.

Executa em um único comando:
1. Ingestão transacional no PostgreSQL (caso o banco esteja acessível e `--skip-db` não seja usado).
2. Suíte de testes automatizados (contratos de dados, anti-fan-out, calendário e recomendação).
3. Análises consolidadas (Q1, Q4, Q5, Q6 e Q7) com saída formatada no terminal.
4. Geração do Dashboard HTML interativo (Plotly.js) e do artefato `reports/summary_metrics.json`.
"""

from __future__ import annotations

import argparse
import logging
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lh_nautical.dashboard import generate_dashboard  # noqa: E402
from lh_nautical.forecasting import evaluate_demand_forecast  # noqa: E402
from lh_nautical.metrics import (  # noqa: E402
    compute_elite_customers,
    compute_orders_eda,
    compute_weekday_sales,
)
from lh_nautical.recommender import compute_product_recommendations  # noqa: E402

logger = logging.getLogger("lh_nautical.pipeline")


def _run_test_suite() -> bool:
    """Descobre e executa a suíte de testes unitários e de contrato."""
    logger.info("Executando suíte de testes automatizados (tests/)...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(PROJECT_ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def _try_database_ingestion(require_db: bool) -> bool:
    """Executa a ingestão transacional no PostgreSQL via SQLAlchemy + psycopg."""
    try:
        from lh_nautical.ingestion import run_ingestion

        counts = run_ingestion()
        logger.info(
            "Banco PostgreSQL sincronizado: %d tabelas (%d registros totais).",
            len(counts),
            sum(counts.values()),
        )
        return True
    except Exception as exc:
        if require_db:
            logger.error("Falha ao executar ingestão no PostgreSQL: %s", exc)
            return False
        logger.warning(
            "PostgreSQL indisponível (%s). Prosseguindo com processamento local validado.",
            exc,
        )
        return True


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal do pipeline LH Nautical."""
    parser = argparse.ArgumentParser(
        description="Executa o pipeline completo de engenharia e análise de dados LH Nautical."
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Pula a etapa de carga no PostgreSQL e executa testes, métricas e dashboard localmente.",
    )
    parser.add_argument(
        "--require-db",
        action="store_true",
        help="Aborta a execução caso a conexão com o PostgreSQL não esteja ativa.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.skip_db:
        if not _try_database_ingestion(require_db=args.require_db):
            return 1

    if not _run_test_suite():
        logger.error("Falha na suíte de testes. Abortando geração de artefatos.")
        return 1

    eda = compute_orders_eda()
    elite_valid = compute_elite_customers(valid_only=True)
    weekday_pos = compute_weekday_sales(valid_only=True, channel="pos")
    forecast_valid = evaluate_demand_forecast(valid_only=True)
    forecast_raw = evaluate_demand_forecast(valid_only=False)
    rec_raw = compute_product_recommendations(valid_only=False)

    print("\n" + "=" * 88)
    print("RESUMO EXECUTIVO — LH NAUTICAL")
    print("=" * 88)
    print(
        f"[Q1] Pedidos Brutos: {eda.total_registros_brutos:,} | "
        f"Pedidos Válidos (paid+confirmed): {eda.pedidos_validos:,} | "
        f"Cancelados: {eda.status_cancelled:,} | Rascunhos: {eda.status_draft:,}"
    )
    print(
        f"[Q1] Faturamento Válido: R$ {eda.faturamento_valido:,.2f} | "
        f"Ticket Médio Válido: R$ {eda.ticket_medio_valido:,.2f} | "
        f"Divergências Contábeis: {eda.divergencias_formula_total + eda.divergencias_soma_itens}"
    )
    print("\n[Q4] Top 10 Clientes Elite (Pedidos Válidos | Diversidade >= 13):")
    print(elite_valid.to_string(index=False))

    print("\n[Q5] Média de Vendas por Dia da Semana (Canal POS | Com Calendário):")
    print(weekday_pos.to_string(index=False))

    print("\n[Q6] Previsão de Demanda — Bússola de Bordo 702 (1T 2026 | Pedidos Válidos):")
    print(forecast_valid.metrics_summary_df.to_string(index=False))

    print("\n[Q6] Previsão de Demanda — Bússola de Bordo 702 (1T 2026 | Base Bruta):")
    print(forecast_raw.metrics_summary_df.to_string(index=False))

    print("\n[Q7] Top 5 Produtos Similares ao 'Motor de Popa 1949' (Ordenação Corrigida):")
    print(rec_raw.to_string(index=False))
    print("=" * 88)

    html_path, json_path = generate_dashboard()
    logger.info("Pipeline concluído. Dashboard: %s | JSON: %s", html_path, json_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

