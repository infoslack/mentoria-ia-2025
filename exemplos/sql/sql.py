"""
CREATE TABLE financial_data (
    id SERIAL PRIMARY KEY,

    -- Identificação
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    period_ending DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL, -- 'annual' ou 'quarterly'
    report_type VARCHAR(20) NOT NULL, -- 'income', 'balance', 'cashflow'

    -- Income Statement
    total_revenue BIGINT,
    gross_profit BIGINT,
    operating_income BIGINT,
    net_income BIGINT,

    -- Balance Sheet
    total_assets BIGINT,
    total_liabilities BIGINT,
    shareholders_equity BIGINT,
    total_debt BIGINT,
    cash_and_equivalents BIGINT,
    current_assets BIGINT,
    current_liabilities BIGINT,

    -- Cash Flow
    operating_cash_flow BIGINT,
    free_cash_flow BIGINT,
    financing_cash_flow BIGINT,
    investing_cash_flow BIGINT,

    -- Metadados
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices únicos
    UNIQUE(symbol, period_ending, period_type, report_type)
);
"""

import os
import yfinance as yf
import psycopg
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configurações do banco
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "dbname": os.getenv("DB_NAME", "data"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", "5432")),
}


def get_company_financials(symbol):
    """Extrai dados financeiros de uma empresa do yfinance"""
    try:
        ticker = yf.Ticker(symbol)

        # Obtém os dados
        annual_income = ticker.financials  # Dados anuais
        quarterly_income = ticker.quarterly_financials  # Dados trimestrais
        annual_balance = ticker.balance_sheet
        quarterly_balance = ticker.quarterly_balance_sheet
        annual_cashflow = ticker.cashflow
        quarterly_cashflow = ticker.quarterly_cashflow

        # Info da empresa
        info = ticker.info
        company_name = info.get("longName", symbol)

        return {
            "company_name": company_name,
            "annual_income": annual_income,
            "quarterly_income": quarterly_income,
            "annual_balance": annual_balance,
            "quarterly_balance": quarterly_balance,
            "annual_cashflow": annual_cashflow,
            "quarterly_cashflow": quarterly_cashflow,
        }
    except Exception as e:
        print(f"Erro ao obter dados para {symbol}: {e}")
        return None


def process_financial_data(symbol, data_dict):
    """Processa os dados financeiros e retorna lista de registros"""
    records = []

    # Mapear os dados para cada tipo de relatório
    report_mappings = {
        "income": {
            "annual": data_dict["annual_income"],
            "quarterly": data_dict["quarterly_income"],
        },
        "balance": {
            "annual": data_dict["annual_balance"],
            "quarterly": data_dict["quarterly_balance"],
        },
        "cashflow": {
            "annual": data_dict["annual_cashflow"],
            "quarterly": data_dict["quarterly_cashflow"],
        },
    }

    for report_type, periods in report_mappings.items():
        for period_type, df in periods.items():
            if df is not None and not df.empty:
                for date, values in df.items():
                    record = {
                        "symbol": symbol,
                        "company_name": data_dict["company_name"],
                        "period_ending": date.date(),
                        "period_type": period_type,
                        "report_type": report_type,
                        "currency": "USD",
                        # Inicializar todos os campos como None
                        "total_revenue": None,
                        "gross_profit": None,
                        "operating_income": None,
                        "net_income": None,
                        "total_assets": None,
                        "total_liabilities": None,
                        "shareholders_equity": None,
                        "total_debt": None,
                        "cash_and_equivalents": None,
                        "current_assets": None,
                        "current_liabilities": None,
                        "operating_cash_flow": None,
                        "free_cash_flow": None,
                        "financing_cash_flow": None,
                        "investing_cash_flow": None,
                    }

                    # Adicionar campos específicos baseado no tipo de relatório
                    if report_type == "income":
                        record.update(
                            {
                                "total_revenue": safe_get_value(
                                    values, "Total Revenue"
                                ),
                                "gross_profit": safe_get_value(values, "Gross Profit"),
                                "operating_income": safe_get_value(
                                    values, "Operating Income"
                                ),
                                "net_income": safe_get_value(values, "Net Income"),
                            }
                        )
                    elif report_type == "balance":
                        record.update(
                            {
                                "total_assets": safe_get_value(values, "Total Assets"),
                                "total_liabilities": safe_get_value(
                                    values, "Total Liab"
                                ),
                                "shareholders_equity": safe_get_value(
                                    values, "Total Stockholder Equity"
                                ),
                                "total_debt": safe_get_value(values, "Total Debt"),
                                "cash_and_equivalents": safe_get_value(
                                    values, "Cash And Cash Equivalents"
                                ),
                                "current_assets": safe_get_value(
                                    values, "Total Current Assets"
                                ),
                                "current_liabilities": safe_get_value(
                                    values, "Total Current Liabilities"
                                ),
                            }
                        )
                    elif report_type == "cashflow":
                        record.update(
                            {
                                "operating_cash_flow": safe_get_value(
                                    values, "Total Cash From Operating Activities"
                                ),
                                "free_cash_flow": safe_get_value(
                                    values, "Free Cash Flow"
                                ),
                                "financing_cash_flow": safe_get_value(
                                    values, "Total Cash From Financing Activities"
                                ),
                                "investing_cash_flow": safe_get_value(
                                    values, "Total Cash From Investing Activities"
                                ),
                            }
                        )

                    records.append(record)

    return records


def safe_get_value(series, key):
    """Obtém valor de forma segura, retornando None se não existir"""
    try:
        value = series.get(key)
        return int(value) if pd.notna(value) else None
    except:  # noqa: E722
        return None


# Exemplo de uso da função debug


def insert_financial_data(records):
    """Insere os dados no PostgreSQL"""
    if not records:
        print("Nenhum dado para inserir")
        return

    insert_query = """
    INSERT INTO financial_data (
        symbol, company_name, period_ending, period_type, report_type,
        total_revenue, gross_profit, operating_income, net_income,
        total_assets, total_liabilities, shareholders_equity, total_debt,
        cash_and_equivalents, current_assets, current_liabilities,
        operating_cash_flow, free_cash_flow, financing_cash_flow,
        investing_cash_flow, currency
    ) VALUES (
        %(symbol)s, %(company_name)s, %(period_ending)s, %(period_type)s, %(report_type)s,
        %(total_revenue)s, %(gross_profit)s, %(operating_income)s, %(net_income)s,
        %(total_assets)s, %(total_liabilities)s, %(shareholders_equity)s, %(total_debt)s,
        %(cash_and_equivalents)s, %(current_assets)s, %(current_liabilities)s,
        %(operating_cash_flow)s, %(free_cash_flow)s, %(financing_cash_flow)s,
        %(investing_cash_flow)s, %(currency)s
    )
    ON CONFLICT (symbol, period_ending, period_type, report_type) 
    DO UPDATE SET
        company_name = EXCLUDED.company_name,
        total_revenue = EXCLUDED.total_revenue,
        gross_profit = EXCLUDED.gross_profit,
        operating_income = EXCLUDED.operating_income,
        net_income = EXCLUDED.net_income,
        total_assets = EXCLUDED.total_assets,
        total_liabilities = EXCLUDED.total_liabilities,
        shareholders_equity = EXCLUDED.shareholders_equity,
        total_debt = EXCLUDED.total_debt,
        cash_and_equivalents = EXCLUDED.cash_and_equivalents,
        current_assets = EXCLUDED.current_assets,
        current_liabilities = EXCLUDED.current_liabilities,
        operating_cash_flow = EXCLUDED.operating_cash_flow,
        free_cash_flow = EXCLUDED.free_cash_flow,
        financing_cash_flow = EXCLUDED.financing_cash_flow,
        investing_cash_flow = EXCLUDED.investing_cash_flow,
        currency = EXCLUDED.currency,
        updated_at = CURRENT_TIMESTAMP
    """

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_query, records)
                conn.commit()
                print(f"Inseridos/atualizados {len(records)} registros")
    except Exception as e:
        print(f"Erro ao inserir dados no banco: {e}")


def main():
    """Função principal"""
    # Lista de símbolos para extrair dados
    symbols = ["NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "META"]

    for symbol in symbols:
        print(f"Processando {symbol}...")

        # Extrai dados do yfinance
        financial_data = get_company_financials(symbol)

        if financial_data:
            # Processa os dados
            records = process_financial_data(symbol, financial_data)

            # Insere no banco
            insert_financial_data(records)

            print(f"Concluído para {symbol}")
        else:
            print(f"Falha ao processar {symbol}")


if __name__ == "__main__":
    main()
