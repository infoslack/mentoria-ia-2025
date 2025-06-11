import os
from typing import List

import yfinance as yf
from openai import OpenAI
from pydantic import BaseModel, Field

# Inicializa o cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Modelo de dados para saída estruturada
class StockAnalysis(BaseModel):
    ticker: str = Field(description="Símbolo da ação")
    company_name: str = Field(description="Nome da empresa")
    current_price: float = Field(description="Preço atual")
    monthly_change: float = Field(description="Variação mensal em %")
    outlook: str = Field(description="Perspectiva: positiva, neutra ou negativa")
    key_points: List[str] = Field(description="Pontos principais")


def analyze_stock(ticker):
    """Analisa uma ação e retorna dados estruturados."""
    # Obtém dados da ação com Yahoo Finance
    stock = yf.Ticker(ticker)
    info = stock.info
    history = stock.history(period="1mo")

    # Calcula variação mensal
    change_percent = 0
    if not history.empty:
        change_percent = round(
            (
                (history.iloc[-1]["Close"] - history.iloc[0]["Close"])
                / history.iloc[0]["Close"]
            )
            * 100,
            2,
        )

    # Preço atual
    price = info.get(
        "currentPrice", history.iloc[-1]["Close"] if not history.empty else 0
    )

    print(f"Analisando {ticker}: {info.get('shortName', ticker)} a ${price}")

    # Solicita análise estruturada
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=f"""
        Analise a ação {ticker}:
        Nome: {info.get("shortName", ticker)}
        Setor: {info.get("sector", "N/A")}
        Preço: {price} {info.get("currency", "USD")}
        Variação mensal: {change_percent}%
        P/E: {info.get("trailingPE", "N/A")}
        Dividend Yield: {info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0}%
        """,
        instructions="Forneça uma análise financeira estruturada desta ação.",
        text_format=StockAnalysis,
    )

    # Extrai e retorna a análise
    analysis = response.output[0].content[0].parsed

    # Imprime um resumo
    print(f"\n{analysis.company_name} ({analysis.ticker}) - {analysis.outlook.upper()}")
    print(f"Preço: ${analysis.current_price} | Variação: {analysis.monthly_change}%")
    print("\nPontos-chave:")
    for point in analysis.key_points:
        print(f"• {point}")

    return analysis


# Exemplo de uso
result = analyze_stock("AAPL")

# Saída em JSON para uso programático
print("\nJSON:")
print(result.model_dump_json(indent=2))
