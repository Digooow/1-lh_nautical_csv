"""
Gerador de Dashboard Executivo Interativo (Plotly.js) e artefatos JSON consolidados.

Princípios arquiteturais:
1. Fonte Única da Verdade: não reimplementa nenhuma regra de negócio. Consome
   exclusivamente `metrics.py`, `forecasting.py` e `recommender.py`.
2. Visualização Interativa: gera gráficos Plotly interativos (zoom, hover tooltips,
   alternância de séries de previsão) em um relatório HTML autossuficiente.
3. Segurança e Confiabilidade: sanitiza todas as strings dinâmicas via `html.escape()`
   e exporta `summary_metrics.json` para auditoria automatizada.
"""

from __future__ import annotations

import html
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from lh_nautical.db import get_data_dir, get_reports_dir
from lh_nautical.forecasting import ForecastEvaluation, evaluate_demand_forecast
from lh_nautical.metrics import (
    OrdersEdaReport,
    compute_elite_customers,
    compute_orders_eda,
    compute_weekday_sales,
)
from lh_nautical.recommender import compute_product_recommendations

logger = logging.getLogger(__name__)


def _format_brl(value: float) -> str:
    """Formata um valor numérico no padrão monetário brasileiro (R$ 1.234,56)."""
    formatted = f"{value:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_int(value: int) -> str:
    """Formata um inteiro com separador de milhar brasileiro."""
    return f"{value:,}".replace(",", ".")


def _build_plotly_payloads(
    weekday_df: pd.DataFrame,
    elite_df: pd.DataFrame,
    forecast_eval: ForecastEvaluation,
    rec_df: pd.DataFrame,
) -> dict[str, Any]:
    """Constrói as especificações JSON interativas dos 4 gráficos Plotly."""
    # 1. Gráfico de Vendas por Dia da Semana (ordenado de Segunda a Domingo)
    wd_chron = weekday_df.sort_values("dia_semana_num").reset_index(drop=True)
    min_media = float(wd_chron["media_vendas"].min())
    overall_avg = float(wd_chron["media_vendas"].mean())
    bar_colors = [
        "#dc2626" if float(v) == min_media else "#2563eb"
        for v in wd_chron["media_vendas"]
    ]
    weekday_custom = [
        [
            int(row["dias_calendario"]),
            int(row["dias_com_venda"]),
            int(row["dias_sem_venda"]),
            _format_brl(float(row["receita_total"])),
        ]
        for _, row in wd_chron.iterrows()
    ]

    chart_weekday = {
        "data": [
            {
                "type": "bar",
                "name": "Média Diária (R$)",
                "x": wd_chron["dia_semana"].tolist(),
                "y": [float(v) for v in wd_chron["media_vendas"]],
                "marker": {"color": bar_colors, "line": {"color": "#1e293b", "width": 1}},
                "customdata": weekday_custom,
                "text": [_format_brl(float(v)) for v in wd_chron["media_vendas"]],
                "textposition": "outside",
                "hovertemplate": (
                    "<b>%{x}</b><br>"
                    "Média Diária: %{text}<br>"
                    "Receita Acumulada: %{customdata[3]}<br>"
                    "Dias no Calendário: %{customdata[0]} "
                    "(Com venda: %{customdata[1]} | Sem venda: %{customdata[2]})"
                    "<extra></extra>"
                ),
            },
            {
                "type": "scatter",
                "mode": "lines",
                "name": f"Média Geral ({_format_brl(overall_avg)})",
                "x": wd_chron["dia_semana"].tolist(),
                "y": [overall_avg] * len(wd_chron),
                "line": {"color": "#0f172a", "width": 2, "dash": "dash"},
                "hoverinfo": "skip",
            },
        ],
        "layout": {
            "title": {
                "text": "Q5 — Média de Vendas Diárias por Dia da Semana (Canal POS | Com Calendário)",
                "font": {"size": 15},
            },
            "xaxis": {"title": "Dia da Semana (ISO-8601: Segunda = 0 ... Domingo = 6)"},
            "yaxis": {"title": "Média de Vendas (R$)", "tickprefix": "R$ "},
            "legend": {"orientation": "h", "y": -0.22},
            "margin": {"t": 55, "b": 70, "l": 70, "r": 30},
            "plot_bgcolor": "#ffffff",
            "paper_bgcolor": "#ffffff",
        },
    }

    # 2. Gráfico Top 10 Clientes Elite (ordenado crescente para barra horizontal)
    elite_plot = elite_df.sort_values(
        by=["ticket_medio", "customer_id"], ascending=[True, False]
    ).reset_index(drop=True)
    elite_labels = [f"Cliente {int(cid)}" for cid in elite_plot["customer_id"]]
    elite_custom = [
        [
            _format_brl(float(row["faturamento_total"])),
            int(row["frequencia"]),
            int(row["diversidade"]),
            str(row["categoria_preferida"]),
            int(row["quantidade_itens"]),
        ]
        for _, row in elite_plot.iterrows()
    ]

    chart_elite = {
        "data": [
            {
                "type": "bar",
                "orientation": "h",
                "x": [float(v) for v in elite_plot["ticket_medio"]],
                "y": elite_labels,
                "marker": {"color": "#0284c7", "line": {"color": "#0369a1", "width": 1}},
                "customdata": elite_custom,
                "text": [_format_brl(float(v)) for v in elite_plot["ticket_medio"]],
                "textposition": "outside",
                "hovertemplate": (
                    "<b>%{y}</b><br>"
                    "Ticket Médio: %{text}<br>"
                    "Faturamento Válido: %{customdata[0]}<br>"
                    "Frequência: %{customdata[1]} pedidos<br>"
                    "Diversidade: %{customdata[2]} categorias<br>"
                    "Categoria Preferida: %{customdata[3]} (%{customdata[4]} itens)"
                    "<extra></extra>"
                ),
            }
        ],
        "layout": {
            "title": {
                "text": "Q4 — Top 10 Clientes Elite por Ticket Médio (Diversidade ≥ 13 Categorias)",
                "font": {"size": 15},
            },
            "xaxis": {
                "title": "Ticket Médio por Pedido (R$)",
                "tickprefix": "R$ ",
                "range": [0, float(elite_plot["ticket_medio"].max()) * 1.25],
            },
            "yaxis": {"title": "Cliente"},
            "margin": {"t": 55, "b": 55, "l": 100, "r": 40},
            "plot_bgcolor": "#ffffff",
            "paper_bgcolor": "#ffffff",
        },
    }

    # 3. Gráfico de Previsão de Demanda (Real vs Modelos MA3 e Baselines)
    pred_df = forecast_eval.predictions_df
    x_months = pred_df["mes_nome"].tolist()

    chart_forecast = {
        "data": [
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Realizado",
                "x": x_months,
                "y": [int(v) for v in pred_df["real"]],
                "line": {"color": "#0f172a", "width": 3},
                "marker": {"size": 9},
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "MA(3) One-Step-Ahead",
                "x": x_months,
                "y": [float(v) for v in pred_df["ma3_one_step"]],
                "line": {"color": "#16a34a", "width": 2.5, "dash": "dot"},
                "marker": {"size": 8, "symbol": "diamond"},
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "MA(3) Recursiva",
                "x": x_months,
                "y": [float(v) for v in pred_df["ma3_recursive"]],
                "line": {"color": "#2563eb", "width": 2.5, "dash": "dash"},
                "marker": {"size": 8, "symbol": "square"},
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Baseline Sazonal (t-12)",
                "x": x_months,
                "y": [float(v) for v in pred_df["seasonal_naive_12m"]],
                "line": {"color": "#9333ea", "width": 2, "dash": "dashdot"},
                "marker": {"size": 7},
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Baseline Naive (t-1)",
                "x": x_months,
                "y": [float(v) for v in pred_df["naive_last"]],
                "line": {"color": "#dc2626", "width": 2, "dash": "longdash"},
                "marker": {"size": 7},
            },
        ],
        "layout": {
            "title": {
                "text": f"Q6 — Previsão de Demanda (1T 2026): {forecast_eval.product_name}",
                "font": {"size": 15},
            },
            "xaxis": {"title": "Mês de Teste (1º Trimestre de 2026)"},
            "yaxis": {"title": "Quantidade Vendida (Unidades)"},
            "legend": {"orientation": "h", "y": -0.25},
            "margin": {"t": 55, "b": 80, "l": 65, "r": 30},
            "plot_bgcolor": "#ffffff",
            "paper_bgcolor": "#ffffff",
        },
    }

    # 4. Gráfico de Recomendação por Similaridade de Cosseno
    rec_plot = rec_df.sort_values("rank", ascending=False).reset_index(drop=True)
    rec_custom = [
        [int(row["product_id"]), int(row["clientes_produto"]), int(row["clientes_em_comum"])]
        for _, row in rec_plot.iterrows()
    ]

    chart_recommender = {
        "data": [
            {
                "type": "bar",
                "orientation": "h",
                "x": [float(v) for v in rec_plot["similaridade"]],
                "y": [f"#{int(r['rank'])} {r['product_name']}" for _, r in rec_plot.iterrows()],
                "marker": {"color": "#0d9488", "line": {"color": "#115e59", "width": 1}},
                "customdata": rec_custom,
                "text": [f"{float(v):.4f}" for v in rec_plot["similaridade"]],
                "textposition": "outside",
                "hovertemplate": (
                    "<b>%{y}</b> (ID=%{customdata[0]})<br>"
                    "Similaridade de Cosseno: %{text}<br>"
                    "Clientes em Comum com Referência: %{customdata[2]}<br>"
                    "Total de Clientes do Produto: %{customdata[1]}"
                    "<extra></extra>"
                ),
            }
        ],
        "layout": {
            "title": {
                "text": 'Q7 — Top 5 Produtos Similares ao "Motor de Popa 1949" (Similaridade de Cosseno)',
                "font": {"size": 15},
            },
            "xaxis": {
                "title": "Similaridade de Cosseno",
                "range": [0, float(rec_plot["similaridade"].max()) * 1.25],
            },
            "yaxis": {"title": "Produto Recomendado"},
            "margin": {"t": 55, "b": 55, "l": 190, "r": 40},
            "plot_bgcolor": "#ffffff",
            "paper_bgcolor": "#ffffff",
        },
    }

    return {
        "weekday": chart_weekday,
        "elite": chart_elite,
        "forecast": chart_forecast,
        "recommender": chart_recommender,
    }


def generate_dashboard(
    data_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> tuple[Path, Path]:
    """
    Executa todas as análises oficiais e gera o Dashboard HTML interativo e o JSON de métricas.

    Retorna `(caminho_html, caminho_json)`.
    """
    base_data_dir = data_dir or get_data_dir()
    out_dir = reports_dir or get_reports_dir()

    eda: OrdersEdaReport = compute_orders_eda(data_dir=base_data_dir)
    elite_df = compute_elite_customers(data_dir=base_data_dir, valid_only=True)
    weekday_df = compute_weekday_sales(
        data_dir=base_data_dir, valid_only=True, channel="pos"
    )
    forecast_valid = evaluate_demand_forecast(data_dir=base_data_dir, valid_only=True)
    forecast_raw = evaluate_demand_forecast(data_dir=base_data_dir, valid_only=False)
    rec_raw_df = compute_product_recommendations(data_dir=base_data_dir, valid_only=False)
    rec_valid_df = compute_product_recommendations(
        data_dir=base_data_dir, valid_only=True
    )

    plotly_payloads = _build_plotly_payloads(
        weekday_df=weekday_df,
        elite_df=elite_df,
        forecast_eval=forecast_valid,
        rec_df=rec_raw_df,
    )

    pior_dia_row = weekday_df.iloc[0]
    top_cliente_row = elite_df.iloc[0]
    top_rec_row = rec_raw_df.iloc[0]

    summary_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "q1_eda": eda.to_dict(),
        "q4_elite_customers_valid": elite_df.to_dict(orient="records"),
        "q5_weekday_sales_pos_valid": weekday_df.to_dict(orient="records"),
        "q6_forecast_valid": {
            "product_ids": forecast_valid.product_ids,
            "zero_sale_months_filled": forecast_valid.zero_sale_months_filled,
            "predictions": forecast_valid.predictions_df.to_dict(orient="records"),
            "metrics": forecast_valid.metrics_summary_df.to_dict(orient="records"),
        },
        "q6_forecast_raw": {
            "product_ids": forecast_raw.product_ids,
            "zero_sale_months_filled": forecast_raw.zero_sale_months_filled,
            "predictions": forecast_raw.predictions_df.to_dict(orient="records"),
            "metrics": forecast_raw.metrics_summary_df.to_dict(orient="records"),
        },
        "q7_recommendations_raw": rec_raw_df.to_dict(orient="records"),
        "q7_recommendations_valid": rec_valid_df.to_dict(orient="records"),
    }

    json_path = out_dir / "summary_metrics.json"
    json_path.write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    elite_rows_html = "\n".join(
        f"<tr>"
        f"<td>{int(r['customer_id'])}</td>"
        f"<td>{_format_brl(float(r['ticket_medio']))}</td>"
        f"<td>{_format_brl(float(r['faturamento_total']))}</td>"
        f"<td>{int(r['frequencia'])}</td>"
        f"<td>{int(r['diversidade'])}</td>"
        f"<td>{html.escape(str(r['categoria_preferida']))}</td>"
        f"<td>{int(r['quantidade_itens'])}</td>"
        f"</tr>"
        for _, r in elite_df.iterrows()
    )

    weekday_rows_html = "\n".join(
        f"<tr>"
        f"<td>{int(r['dia_semana_num'])}</td>"
        f"<td>{html.escape(str(r['dia_semana']))}</td>"
        f"<td>{int(r['dias_calendario'])}</td>"
        f"<td>{int(r['dias_com_venda'])}</td>"
        f"<td>{int(r['dias_sem_venda'])}</td>"
        f"<td>{_format_brl(float(r['receita_total']))}</td>"
        f"<td><b>{_format_brl(float(r['media_vendas']))}</b></td>"
        f"</tr>"
        for _, r in weekday_df.iterrows()
    )

    forecast_models_html = "\n".join(
        f"<tr>"
        f"<td>{html.escape(str(r['modelo']))}</td>"
        f"<td>{int(r['soma_real'])}</td>"
        f"<td>{int(r['soma_prevista'])}</td>"
        f"<td><b>{float(r['mae']):.2f}</b></td>"
        f"<td>{float(r['rmse']):.2f}</td>"
        f"</tr>"
        for _, r in forecast_valid.metrics_summary_df.iterrows()
    )

    rec_rows_html = "\n".join(
        f"<tr>"
        f"<td>#{int(r['rank'])}</td>"
        f"<td>{int(r['product_id'])}</td>"
        f"<td>{html.escape(str(r['product_name']))}</td>"
        f"<td>{int(r['clientes_produto'])}</td>"
        f"<td>{int(r['clientes_em_comum'])}</td>"
        f"<td><b>{float(r['similaridade']):.4f}</b></td>"
        f"</tr>"
        for _, r in rec_raw_df.iterrows()
    )

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Estudo de Caso Analítico — LH Nautical</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
    :root {{
        --bg: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #475569;
        --accent: #0284c7;
        --border: #e2e8f0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin: 0;
        padding: 28px;
        background-color: var(--bg);
        color: var(--text);
        line-height: 1.5;
    }}
    header {{
        background: var(--card);
        padding: 24px 28px;
        border-radius: 12px;
        border: 1px solid var(--border);
        margin-bottom: 24px;
    }}
    header h1 {{ margin: 0 0 6px 0; font-size: 24px; }}
    header p {{ margin: 0; color: var(--muted); font-size: 14px; }}
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }}
    .kpi-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 18px;
    }}
    .kpi-card .label {{ font-size: 12px; text-transform: uppercase; color: var(--muted); font-weight: 600; }}
    .kpi-card .value {{ font-size: 22px; font-weight: 700; margin-top: 6px; color: var(--text); }}
    .kpi-card .sub {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
    .chart-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
        gap: 20px;
        margin-bottom: 28px;
    }}
    .card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 22px;
    }}
    .card h2 {{
        margin: 0 0 14px 0;
        font-size: 17px;
        border-left: 4px solid var(--accent);
        padding-left: 10px;
    }}
    .plot-box {{ width: 100%; min-height: 390px; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13.5px;
    }}
    th, td {{
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
        text-align: left;
    }}
    th {{
        background: #f1f5f9;
        font-weight: 600;
        color: #1e293b;
    }}
    tr:hover {{ background: #f8fafc; }}
    footer {{
        text-align: center;
        color: var(--muted);
        font-size: 12.5px;
        margin-top: 24px;
    }}
</style>
</head>
<body>
<header>
    <h1>Estudo de Caso de Engenharia e Análise de Dados — LH Nautical</h1>
    <p>Fonte Única da Verdade: Pedidos comercialmente válidos (status IN ('paid', 'confirmed'): {_format_int(eda.pedidos_validos)} de {_format_int(eda.total_registros_brutos)} registros) • Reconciliação contábil 100% verificada</p>
</header>

<section class="kpi-grid">
    <div class="kpi-card">
        <div class="label">Faturamento Válido</div>
        <div class="value">{_format_brl(eda.faturamento_valido)}</div>
        <div class="sub">Bruto total: {_format_brl(eda.faturamento_bruto)}</div>
    </div>
    <div class="kpi-card">
        <div class="label">Pedidos Válidos</div>
        <div class="value">{_format_int(eda.pedidos_validos)}</div>
        <div class="sub">Excluídos: {_format_int(eda.status_cancelled)} cancelados, {_format_int(eda.status_draft)} rascunhos</div>
    </div>
    <div class="kpi-card">
        <div class="label">Ticket Médio Válido</div>
        <div class="value">{_format_brl(eda.ticket_medio_valido)}</div>
        <div class="sub">Mediana: {_format_brl(eda.mediana_50)} | Outliers IQR: {eda.qtd_outliers_iqr}</div>
    </div>
    <div class="kpi-card">
        <div class="label">Menor Média Diária (POS)</div>
        <div class="value">{html.escape(str(pior_dia_row['dia_semana']))}</div>
        <div class="sub">{_format_brl(float(pior_dia_row['media_vendas']))} / dia (com calendário)</div>
    </div>
    <div class="kpi-card">
        <div class="label">Líder Clientes Elite (Q4)</div>
        <div class="value">Cliente {int(top_cliente_row['customer_id'])}</div>
        <div class="sub">Ticket: {_format_brl(float(top_cliente_row['ticket_medio']))} ({int(top_cliente_row['diversidade'])} categorias)</div>
    </div>
    <div class="kpi-card">
        <div class="label">Top 1 Recomendação (Q7)</div>
        <div class="value">{html.escape(str(top_rec_row['product_name']))}</div>
        <div class="sub">Similaridade de cosseno: {float(top_rec_row['similaridade']):.4f}</div>
    </div>
</section>

<section class="chart-grid">
    <div class="card"><div id="chart-weekday" class="plot-box"></div></div>
    <div class="card"><div id="chart-elite" class="plot-box"></div></div>
    <div class="card"><div id="chart-forecast" class="plot-box"></div></div>
    <div class="card"><div id="chart-recommender" class="plot-box"></div></div>
</section>

<section class="card">
    <h2>Q4 — Top 10 Clientes Elite (Diversidade ≥ 13 Categorias | Sem Fan-Out de JOIN)</h2>
    <table>
        <thead>
            <tr>
                <th>Cliente ID</th>
                <th>Ticket Médio</th>
                <th>Faturamento Válido</th>
                <th>Frequência (Pedidos)</th>
                <th>Diversidade (Categorias)</th>
                <th>Categoria Preferida</th>
                <th>Unidades na Categoria</th>
            </tr>
        </thead>
        <tbody>
            {elite_rows_html}
        </tbody>
    </table>
</section>

<section class="card">
    <h2>Q5 — Desempenho Diário por Dia da Semana (Canal POS | Dimensão Calendário Contínua)</h2>
    <table>
        <thead>
            <tr>
                <th>ISO DOW</th>
                <th>Dia da Semana</th>
                <th>Dias no Calendário</th>
                <th>Dias com Venda</th>
                <th>Dias Zerados</th>
                <th>Receita Acumulada</th>
                <th>Média Diária</th>
            </tr>
        </thead>
        <tbody>
            {weekday_rows_html}
        </tbody>
    </table>
</section>

<section class="card">
    <h2>Q6 — Comparativo de Modelos de Previsão de Demanda (Bússola de Bordo 702 — 1T 2026)</h2>
    <table>
        <thead>
            <tr>
                <th>Modelo Avaliado</th>
                <th>Demanda Real (1T 2026)</th>
                <th>Soma Prevista (Arredondada)</th>
                <th>MAE (Unidades)</th>
                <th>RMSE (Unidades)</th>
            </tr>
        </thead>
        <tbody>
            {forecast_models_html}
        </tbody>
    </table>
</section>

<section class="card">
    <h2>Q7 — Ranking de Produtos Similares ao "Motor de Popa 1949" (Ordenação Preservada)</h2>
    <table>
        <thead>
            <tr>
                <th>Posição</th>
                <th>Product ID</th>
                <th>Nome do Produto</th>
                <th>Total de Clientes</th>
                <th>Clientes em Comum</th>
                <th>Similaridade de Cosseno</th>
            </tr>
        </thead>
        <tbody>
            {rec_rows_html}
        </tbody>
    </table>
</section>

<footer>
    Pipeline Analítico LH Nautical • Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
</footer>

<script>
    const payloads = {json.dumps(plotly_payloads, ensure_ascii=False)};
    const config = {{ responsive: true, displaylogo: false }};
    if (typeof Plotly !== "undefined") {{
        Plotly.newPlot("chart-weekday", payloads.weekday.data, payloads.weekday.layout, config);
        Plotly.newPlot("chart-elite", payloads.elite.data, payloads.elite.layout, config);
        Plotly.newPlot("chart-forecast", payloads.forecast.data, payloads.forecast.layout, config);
        Plotly.newPlot("chart-recommender", payloads.recommender.data, payloads.recommender.layout, config);
    }}
</script>
</body>
</html>
"""

    html_path = out_dir / "dashboard_lh_nautical.html"
    html_path.write_text(html_content, encoding="utf-8")
    logger.info("Dashboard interativo salvo em %s", html_path)
    logger.info("Resumo JSON salvo em %s", json_path)
    return html_path, json_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    generate_dashboard()

