import os
from datetime import datetime

def gerar_html(total_vendas, num_pedidos, ticket_medio, pior_dia, media_dia, top10, teste, soma_prev, mae, top_nomes, top_scores, produto_nome, script_dir):
    """
    Gera um relatório HTML com os resultados e gráficos.
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>Dashboard - LH Nautical</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f8f9fa; color: #333; }}
    h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
    h2 {{ color: #34495e; margin-top: 30px; border-left: 5px solid #3498db; padding-left: 15px; }}
    .kpi {{ display: flex; flex-wrap: wrap; gap: 20px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
    .kpi-item {{ flex: 1; min-width: 150px; text-align: center; padding: 10px; background: #f1f9ff; border-radius: 8px; }}
    .kpi-item .label {{ font-size: 14px; color: #7f8c8d; font-weight: bold; }}
    .kpi-item .value {{ font-size: 24px; font-weight: bold; color: #2c3e50; margin-top: 5px; }}
    .kpi-item .value.real {{ color: #27ae60; }}
    .grafico {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
    .grafico img {{ width: 100%; height: auto; border-radius: 5px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 20px 0; }}
    th {{ background-color: #3498db; color: white; font-weight: bold; padding: 12px 8px; text-align: center; }}
    td {{ padding: 10px 8px; text-align: center; border-bottom: 1px solid #ecf0f1; }}
    tr:hover {{ background-color: #f1f9ff; }}
    .footer {{ text-align: center; color: #95a5a6; font-size: 14px; margin-top: 30px; border-top: 1px solid #ecf0f1; padding-top: 20px; }}
</style>
</head>
<body>
<h1>📊 Dashboard de Análise – LH Nautical</h1>

<div class="kpi">
    <div class="kpi-item">
        <div class="label">Faturamento Total</div>
        <div class="value real">R$ {total_vendas:,.2f}</div>
    </div>
    <div class="kpi-item">
        <div class="label">Número de Pedidos</div>
        <div class="value">{num_pedidos:,}</div>
    </div>
    <div class="kpi-item">
        <div class="label">Ticket Médio</div>
        <div class="value real">R$ {ticket_medio:,.2f}</div>
    </div>
    <div class="kpi-item">
        <div class="label">Pior Dia da Semana</div>
        <div class="value">{pior_dia}</div>
        <div style="font-size:14px;color:#e74c3c;">R$ {media_dia.iloc[0]['total_dia']:,.2f} em média</div>
    </div>
</div>

<div class="grafico">
    <h2>📈 Gráficos Analíticos</h2>
    <img src='dashboard_graficos.png' alt='Gráficos' style='max-width:100%;'>
</div>

<h2>🏆 Top 10 Clientes Elite (Diversidade ≥ 13)</h2>
<table>
    <tr><th>Cliente</th><th>Faturamento</th><th>Frequência</th><th>Ticket Médio</th><th>Diversidade</th><th>Categoria Preferida</th></tr>
"""
    for _, row in top10.iterrows():
        html += f"<tr><td>{row['customer_id']}</td><td>R$ {row['faturamento']:,.2f}</td><td>{row['frequencia']}</td><td>R$ {row['ticket_medio']:,.2f}</td><td>{row['diversidade']}</td><td>{row['categoria_preferida']}</td></tr>"

    html += f"""
</table>

<h2>📦 Previsão vs Real – {produto_nome}</h2>
<table>
    <tr><th>Mês</th><th>Real</th><th>Previsão</th></tr>
"""
    for _, row in teste.iterrows():
        html += f"<tr><td>{row['mes_nome']}</td><td>{row['quantity']}</td><td>{row['previsao']:.2f}</td></tr>"

    html += f"""
</table>
<p><b>Soma da previsão (arredondada):</b> {soma_prev} unidades</p>
<p><b>MAE (Mean Absolute Error):</b> {mae:.2f} unidades</p>

<h2>🛍️ Produtos similares ao "Motor de Popa 1949"</h2>
<ol>
"""
    for nome, score in zip(top_nomes, top_scores):
        html += f"<li>{nome} (similaridade = {score:.4f})</li>"

    html += f"""
</ol>

<div class="footer">
    Dashboard gerado automaticamente com Python • LH Nautical • {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
</body>
</html>
"""
    html_path = os.path.join(script_dir, 'dashboard_alternativo.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_path