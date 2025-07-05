"""
Agent Financeiro com Tools Parametrizadas

Requer arquivo .env na raiz do projeto com:
OPENAI_API_KEY=sua-chave-openai-aqui
"""

import openai
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import report

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class FinancialRequest(BaseModel):
    """Routing para análise financeira"""

    tool_name: Literal[
        "get_financial_data", "plot_revenue_evolution", "plot_net_income_comparison"
    ] = Field(description="Tool a ser executada")
    symbol: Optional[str] = Field(description="Símbolo da empresa (para uma empresa)")
    symbols: Optional[List[str]] = Field(
        description="Lista de símbolos (para comparação)"
    )
    report_type: Literal["income", "balance", "cash_flow"] = Field(
        description="Tipo de relatório", default="income"
    )
    period_type: Literal["annual", "quarterly"] = Field(
        description="Período", default="annual"
    )


def analyze_financial_query(user_input: str) -> Optional[str]:
    """Analisa query e executa tool apropriada"""

    # Routing com structured output
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Analise a consulta financeira e determine:
                - get_financial_data: para dados brutos
                - plot_revenue_evolution: para evolução de receita de UMA empresa  
                - plot_net_income_comparison: para comparar MÚLTIPLAS empresas
                
                Símbolos: AAPL, MSFT, GOOGL, NVDA, TSLA, META, AMZN""",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=FinancialRequest,
    )

    request = completion.choices[0].message.parsed

    # Executa a tool correspondente
    try:
        if request.tool_name == "get_financial_data":
            result = report.get_financial_data(
                symbol=request.symbol,
                report_type=request.report_type,
                period_type=request.period_type,
            )
            return f"Dados obtidos para {request.symbol}: {len(result) if result is not None else 0} registros"

        elif request.tool_name == "plot_revenue_evolution":
            report.plot_revenue_evolution(
                symbol=request.symbol, period_type=request.period_type
            )
            return f"Gráfico de evolução gerado para {request.symbol}"

        elif request.tool_name == "plot_net_income_comparison":
            report.plot_net_income_comparison(
                symbols=request.symbols, period_type=request.period_type
            )
            return f"Gráfico comparativo gerado para {', '.join(request.symbols)}"

    except Exception as e:
        return f"Erro: {str(e)}"


def main():
    queries = [
        "Evolução da receita da NVIDIA",
        "Compare Apple Nvidia e Tesla",
        "Dados trimestrais da Tesla",
    ]

    for query in queries:
        print(f"\nPergunta: {query}")
        result = analyze_financial_query(query)
        print(f"Resultado: {result}")
        print("-" * 50)


if __name__ == "__main__":
    main()
