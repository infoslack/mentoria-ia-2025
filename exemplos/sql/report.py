import os
import psycopg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "dbname": os.getenv("DB_NAME", "data"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", "5432")),
}


def get_financial_data(symbol, report_type, period_type="annual"):
    """Busca dados financeiros do banco"""
    query = """
    SELECT period_ending, total_revenue, net_income
    FROM financial_data
    WHERE symbol = %s AND report_type = %s AND period_type = %s
    ORDER BY period_ending;
    """

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (symbol, report_type, period_type))
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                df = pd.DataFrame(rows, columns=columns)
                return df
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None


def plot_revenue_evolution(symbol="NVDA", period_type="annual"):
    """Gráfico 1: Evolução da Receita Líquida"""
    df = get_financial_data(symbol, "income", period_type)

    if df is None or df.empty:
        print(f"Sem dados de receita para {symbol}")
        return

    # Remove valores nulos e ordena por data
    df = df.dropna(subset=["total_revenue"]).sort_values("period_ending")

    if len(df) < 2:
        print(f"Dados insuficientes para {symbol} - apenas {len(df)} registros")
        return

    # Converte para bilhões
    df["revenue_billions"] = df["total_revenue"] / 1e9

    # Calcula crescimento percentual
    df["growth_rate"] = df["revenue_billions"].pct_change() * 100

    plt.figure(figsize=(14, 8))

    # Plot principal
    plt.plot(
        df["period_ending"],
        df["revenue_billions"],
        marker="o",
        linewidth=3,
        markersize=8,
        color="#1f77b4",
        markerfacecolor="white",
        markeredgewidth=2,
        markeredgecolor="#1f77b4",
    )

    # Área sob a curva para dar mais peso visual
    plt.fill_between(
        df["period_ending"], df["revenue_billions"], alpha=0.2, color="#1f77b4"
    )

    # Adiciona valores nos pontos
    for i, row in df.iterrows():
        plt.annotate(
            f"${row['revenue_billions']:.1f}B",
            (row["period_ending"], row["revenue_billions"]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    # Configurações do gráfico
    plt.title(
        f"Evolução da Receita Líquida - {symbol}",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("Período", fontsize=12, fontweight="bold")
    plt.ylabel("Receita (Bilhões USD)", fontsize=12, fontweight="bold")

    # Grid mais sutil
    plt.grid(True, alpha=0.2, linestyle="-", linewidth=0.5)

    # Ajusta escala do Y para começar próximo ao mínimo
    y_min = df["revenue_billions"].min() * 0.95
    y_max = df["revenue_billions"].max() * 1.05
    plt.ylim(y_min, y_max)

    # Formatação do eixo X
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)

    # Adiciona informações de crescimento
    total_growth = (
        (df["revenue_billions"].iloc[-1] / df["revenue_billions"].iloc[0]) - 1
    ) * 100
    avg_growth = df["growth_rate"].mean()

    # Caixa de texto com estatísticas
    stats_text = f"Crescimento Total: {total_growth:+.1f}%\nCrescimento Médio: {avg_growth:+.1f}%"
    plt.text(
        0.02,
        0.98,
        stats_text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.8),
    )

    dates_numeric = [d.toordinal() for d in df["period_ending"]]
    z = np.polyfit(dates_numeric, df["revenue_billions"], 1)
    p = np.poly1d(z)
    plt.plot(
        df["period_ending"],
        p(dates_numeric),
        linestyle="--",
        alpha=0.7,
        color="red",
        linewidth=2,
        label="Tendência",
    )

    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.show()

    # Mostra dados detalhados
    print(f"\n📊 Resumo - {symbol} ({period_type}):")
    print(f"Períodos analisados: {len(df)}")
    print(f"Receita mais recente: ${df['revenue_billions'].iloc[-1]:.1f}B")
    print(f"Crescimento total: {total_growth:+.1f}%")
    if len(df) > 1:
        print(f"Último crescimento: {df['growth_rate'].iloc[-1]:+.1f}%")


def plot_net_income_comparison(symbols=["AAPL", "MSFT", "GOOGL"], period_type="annual"):
    """Gráfico 2: Comparação do Lucro Líquido - Barras Agrupadas"""
    all_data = {}
    periods = set()

    # Coleta dados de todas as empresas
    for symbol in symbols:
        df = get_financial_data(symbol, "income", period_type)
        if df is not None and not df.empty:
            df = df.dropna(subset=["net_income"]).sort_values("period_ending")
            df["net_income_billions"] = df["net_income"] / 1e9
            all_data[symbol] = df
            periods.update(df["period_ending"].tolist())

    if not all_data:
        print("Sem dados suficientes para comparação")
        return

    # Ordena períodos
    periods = sorted(list(periods))

    # Prepara dados para o gráfico de barras
    period_labels = [p.strftime("%Y") for p in periods]

    # Configurações do gráfico
    fig, ax = plt.subplots(figsize=(16, 10))

    # Cores profissionais para cada empresa
    colors = {
        "AAPL": "#007AFF",  # Azul Apple
        "MSFT": "#00BCF2",  # Azul Microsoft
        "GOOGL": "#4285F4",  # Azul Google
        "AMZN": "#FF9900",  # Laranja Amazon
        "TSLA": "#CC0000",  # Vermelho Tesla
        "META": "#1877F2",  # Azul Meta
        "NVDA": "#76B900",  # Verde NVIDIA
    }

    # Largura das barras e posições
    bar_width = 0.25
    x_positions = np.arange(len(periods))

    # Plot das barras para cada empresa
    for i, symbol in enumerate(symbols):
        if symbol in all_data:
            df = all_data[symbol]
            values = []

            # Para cada período, busca o valor da empresa ou coloca 0
            for period in periods:
                matching_rows = df[df["period_ending"] == period]
                if not matching_rows.empty:
                    values.append(matching_rows["net_income_billions"].iloc[0])
                else:
                    values.append(0)  # Sem dados para este período

            # Posição das barras
            positions = x_positions + (i - len(symbols) / 2 + 0.5) * bar_width

            # Cria as barras
            bars = ax.bar(
                positions,
                values,
                bar_width,
                label=symbol,
                color=colors.get(symbol, f"C{i}"),
                alpha=0.8,
                edgecolor="white",
                linewidth=1,
            )

            # Adiciona valores no topo das barras
            for bar, value in zip(bars, values):
                if value > 0:  # Só mostra se tem valor
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 1,
                        f"${value:.1f}B",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        fontweight="bold",
                    )

    # Configurações do gráfico
    ax.set_title(
        "Comparação do Lucro Líquido por Empresa",
        fontsize=18,
        fontweight="bold",
        pad=25,
    )
    ax.set_xlabel("Ano", fontsize=14, fontweight="bold")
    ax.set_ylabel("Lucro Líquido (Bilhões USD)", fontsize=14, fontweight="bold")

    # Configurações dos eixos
    ax.set_xticks(x_positions)
    ax.set_xticklabels(period_labels, fontsize=12)
    ax.tick_params(axis="y", labelsize=12)

    # Grid sutil
    ax.grid(True, alpha=0.2, linestyle="-", linewidth=0.5, axis="y")
    ax.set_axisbelow(True)

    # Legenda melhorada
    legend = ax.legend(
        loc="upper left", fontsize=12, framealpha=0.9, fancybox=True, shadow=True
    )
    legend.get_frame().set_facecolor("white")

    # Ajusta margem superior para acomodar os valores
    ax.set_ylim(0, ax.get_ylim()[1] * 1.15)

    plt.tight_layout()
    plt.show()

    # Tabela resumo com estatísticas
    print(f"\n📊 Resumo Comparativo - Lucro Líquido ({period_type}):")
    print("=" * 60)

    for symbol in symbols:
        if symbol in all_data:
            df = all_data[symbol]
            if len(df) > 0:
                latest_profit = df["net_income_billions"].iloc[-1]
                avg_profit = df["net_income_billions"].mean()

                if len(df) > 1:
                    growth = (
                        (
                            df["net_income_billions"].iloc[-1]
                            / df["net_income_billions"].iloc[0]
                        )
                        - 1
                    ) * 100
                    print(
                        f"{symbol:6}: Último: ${latest_profit:6.1f}B | Média: ${avg_profit:6.1f}B | Crescimento: {growth:+6.1f}%"
                    )
                else:
                    print(
                        f"{symbol:6}: Último: ${latest_profit:6.1f}B | Média: ${avg_profit:6.1f}B | Crescimento: N/A"
                    )

    # Ranking do período mais recente
    latest_period = max(periods)
    latest_data = []
    for symbol in symbols:
        if symbol in all_data:
            df = all_data[symbol]
            matching = df[df["period_ending"] == latest_period]
            if not matching.empty:
                latest_data.append((symbol, matching["net_income_billions"].iloc[0]))

    if latest_data:
        latest_data.sort(key=lambda x: x[1], reverse=True)
        print(f"\n🏆 Ranking {latest_period.year}:")
        for i, (symbol, profit) in enumerate(latest_data, 1):
            print(f"{i}º {symbol}: ${profit:.1f}B")


def main():
    """Função principal para gerar os gráficos"""
    symbol = "NVDA"  # Altere conforme necessário
    period_type = "annual"  # 'annual' ou 'quarterly'

    print(f"Gerando gráficos para {symbol} ({period_type})...")

    # Gráficos individuais
    plot_revenue_evolution(symbol, period_type)
    plot_net_income_comparison(["AAPL", "NVDA", "TSLA"], period_type)

    print("Gráficos gerados com sucesso!")
    get_financial_data("NVDA", "income", "annual")


if __name__ == "__main__":
    main()
