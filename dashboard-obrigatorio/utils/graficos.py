import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
import os

def gerar_graficos(media_dia, top10, teste, top_nomes, top_scores, produto_nome, prod_ref, script_dir):
    """
    Gera 4 gráficos com formatação profissional, evitando sobreposição de rótulos.
    """
    # Configurar estilo e tamanho das fontes
    plt.style.use('ggplot')  # Estilo limpo e compatível
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['xtick.labelsize'] = 11
    plt.rcParams['ytick.labelsize'] = 11
    plt.rcParams['legend.fontsize'] = 11

    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle('📊 Dashboard de Análise – LH Nautical', fontsize=20, fontweight='bold', y=0.98)

    # Função para formatar valores em R$ (usada nos eixos)
    def real_format(x, pos):
        if x >= 1e6:
            return f'R$ {x/1e6:.1f}M'
        elif x >= 1e3:
            return f'R$ {x/1e3:.0f}k'
        else:
            return f'R$ {x:,.0f}'

    # ---------- GRÁFICO 1: Média de vendas por dia da semana ----------
    ax = axes[0, 0]
    cores_dias = sns.color_palette("coolwarm", n_colors=len(media_dia))
    bars = sns.barplot(data=media_dia, x='dia_semana', y='total_dia', ax=ax, palette='coolwarm', edgecolor='black', linewidth=0.5)
    ax.set_title('Média de Vendas por Dia da Semana (com calendário)', fontweight='bold')
    ax.set_xlabel('Dia da semana', fontweight='bold')
    ax.set_ylabel('Média de Vendas (R$)', fontweight='bold')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(real_format))
    ax.axhline(y=media_dia['total_dia'].mean(), color='red', linestyle='--', linewidth=2, label=f'Média geral: R$ {media_dia["total_dia"].mean():,.2f}')
    ax.legend()

    # Adicionar rótulos nas barras com offset vertical para evitar sobreposição
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        # Posiciona o texto acima da barra com um pequeno offset
        ax.annotate(f'R$ {height:,.0f}',
                    (p.get_x() + p.get_width() / 2., height),
                    ha='center', va='bottom',
                    fontsize=10, fontweight='bold',
                    xytext=(0, 5), textcoords='offset points')  # 5 pixels para cima
    ax.tick_params(axis='x', rotation=45)

        # ---------- GRÁFICO 2: Top 10 clientes (ticket médio) ----------
    ax = axes[0, 1]
    top10_sorted = top10.sort_values('ticket_medio', ascending=True)
    
    # Criar rótulos para o eixo Y com o ID do cliente
    clientes_labels = [f'Cliente {cid}' for cid in top10_sorted['customer_id']]
    
    bars = sns.barplot(
        data=top10_sorted, 
        x='ticket_medio', 
        y=clientes_labels, 
        ax=ax, 
        palette='rocket_r', 
        edgecolor='black', 
        linewidth=0.5
    )
    ax.set_title('Top 10 Clientes – Ticket Médio', fontweight='bold')
    ax.set_xlabel('Ticket Médio (R$)', fontweight='bold')
    ax.set_ylabel('Cliente', fontweight='bold')
    
    # Formatação do eixo X com valores completos (sem abreviação)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
    
    # Adicionar rótulos com valor exato à direita das barras
    for i, p in enumerate(ax.patches):
        width = p.get_width()
        if width > 0:
            ax.annotate(f'R$ {width:,.0f}',
                        (width, p.get_y() + p.get_height() / 2.),
                        ha='left', va='center',
                        fontsize=10, fontweight='bold',
                        xytext=(5, 0), textcoords='offset points')
    
    # Ajustar limite do eixo X para dar espaço aos rótulos
    max_width = top10_sorted['ticket_medio'].max()
    ax.set_xlim(0, max_width * 1.25)
    
    ax.tick_params(axis='y', labelsize=11)

    # ---------- GRÁFICO 3: Previsão vs Real ----------
    ax = axes[1, 0]
    x = ['Jan', 'Fev', 'Mar']
    ax.plot(x, teste['quantity'], marker='o', markersize=10, linewidth=3, label='Real', color='#2E86C1')
    ax.plot(x, teste['previsao'], marker='s', markersize=10, linewidth=3, label='Previsão', color='#E74C3C', linestyle='--')
    ax.set_title(f'Previsão vs Real – {produto_nome}', fontweight='bold')
    ax.set_xlabel('Mês', fontweight='bold')
    ax.set_ylabel('Quantidade (unidades)', fontweight='bold')
    ax.legend(loc='upper left', frameon=True, shadow=True)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Anotar valores com deslocamento para evitar sobreposição
    for i, txt in enumerate(teste['quantity']):
        ax.annotate(f'{txt}', (x[i], teste['quantity'].iloc[i]),
                    textcoords="offset points", xytext=(0, 10), ha='center', fontweight='bold', fontsize=11)
    for i, txt in enumerate(teste['previsao']):
        ax.annotate(f'{txt:.1f}', (x[i], teste['previsao'].iloc[i]),
                    textcoords="offset points", xytext=(0, -15), ha='center', fontweight='bold', fontsize=11, color='#E74C3C')

    # Ajustar limites do eixo Y para dar espaço aos rótulos
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min, y_max * 1.1)

    # ---------- GRÁFICO 4: Produtos similares ----------
    ax = axes[1, 1]
    nomes_curtos = [nome[:25] + '...' if len(nome) > 25 else nome for nome in top_nomes]
    bars = sns.barplot(x=top_scores, y=nomes_curtos, ax=ax, palette='magma', edgecolor='black', linewidth=0.5)
    ax.set_title(f'Top 5 similares ao "{prod_ref}"', fontweight='bold')
    ax.set_xlabel('Similaridade de cosseno', fontweight='bold')
    ax.set_ylabel('Produto', fontweight='bold')
    ax.set_xlim(0, max(top_scores) * 1.15)

    # Rótulos dentro das barras, alinhados à direita
    for i, p in enumerate(ax.patches):
        width = p.get_width()
        ax.annotate(f'{top_scores[i]:.4f}',
                    (width - 0.01, p.get_y() + p.get_height() / 2.),
                    ha='right', va='center',
                    fontsize=10, fontweight='bold', color='white',
                    xytext=(-3, 0), textcoords='offset points')  # pequeno deslocamento para dentro
    ax.tick_params(axis='y', labelsize=11)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    img_path = os.path.join(script_dir, 'dashboard_graficos.png')
    plt.savefig(img_path, dpi=200, bbox_inches='tight')
    plt.close()
    return img_path