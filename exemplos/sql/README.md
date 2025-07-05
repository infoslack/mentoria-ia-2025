# Financial Agent Demo

Demonstração de um agent financeiro usando tools parametrizadas em vez de geração dinâmica de SQL.

## Arquivos

### `sql.py`
- Criação da tabela `financial_data` no PostgreSQL
- Ingestão de dados financeiros do yfinance (NVDA, AAPL, MSFT, TSLA, GOOGL, META)

### `report.py` 
- Tools parametrizadas para consulta e visualização de dados
- Funções: `get_financial_data()`, `plot_revenue_evolution()`, `plot_net_income_comparison()`

### `agent.py`
- Exemplo de agent usando OpenAI com routing pattern
- Consome as tools do `report.py` via structured output

## Setup

1. Configure o arquivo `.env`:
```
DB_HOST=localhost
DB_NAME=data
DB_USER=postgres
DB_PASSWORD=sua-senha
DB_PORT=5432
OPENAI_API_KEY=sua-chave-openai
```

2. Execute na ordem:
```bash
python sql.py      # Cria tabela e ingere dados
python report.py   # Testa as tools
python agent.py    # Testa o agent
```

## Conceito

Agent usa **routing pattern** para classificar queries e direcionar para tools específicas, evitando geração dinâmica de SQL.