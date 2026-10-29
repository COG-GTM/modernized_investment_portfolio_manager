# Portfolio Management Backend API

A FastAPI backend service for investment portfolio management that serves as the data service for the modernized investment portfolio management frontend application.

## Features

- **Portfolio Management**: Get portfolio summary and holdings for account numbers
- **Account Validation**: Validate 9-digit numeric account numbers (no zeros allowed)
- **Transaction History**: Placeholder endpoint for future transaction data
- **Mock Data**: Returns realistic mock portfolio data matching frontend structure
- **SQLite Database**: Basic database setup with SQLAlchemy models for future data persistence

## API Endpoints

### Portfolio Endpoints
- `GET /api/portfolio/{account_number}` - Returns portfolio summary and holdings
- `GET /api/transactions/{account_number}` - Returns transaction history (placeholder)

### Account Endpoints  
- `GET /api/accounts/{account_number}/validate` - Validates account number format

### Health Check
- `GET /healthz` - Health check endpoint

## Project Structure

```
backend/
├── app/
│   └── main.py              # FastAPI app entry point
├── models/
│   ├── __init__.py
│   ├── portfolio.py         # Pydantic models
│   └── database.py          # SQLAlchemy models
├── routers/
│   ├── __init__.py
│   ├── portfolio.py         # Portfolio endpoints
│   └── accounts.py          # Account endpoints
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Poetry configuration
└── README.md               # This file
```

## ESG emissions feed loader

The monthly ESG emissions file lands in the inbound bucket (locally `backend/inbound/`, override with `ESG_INBOUND_DIR`) as `esg/<YYYY-MM>/esg_emissions_<YYYY-MM>.csv` with the header `as_of_month,investment_id,scope1_tco2e,scope2_tco2e,revenue_musd`. Run from `backend/`:

```bash
python -m esg.load_esg_feed --file inbound/esg/2026-10/esg_emissions_2026-10.csv
python -m esg.load_esg_feed --all   # every file not yet loaded
```

- Each file gets an `esg_load_batches` row (status `C` complete or `F` failed, with `BAD_HEADER`, `EMPTY_FILE` or `ALL_ROWS_REJECTED`).
- Accepted rows replace the month's snapshot in `stg_esg_emissions` (keyed by month and investment, tagged with the batch id).
- Malformed rows go to `esg_load_rejects` with a reason code (`INVALID_AS_OF_MONTH`, `MISSING_INVESTMENT_ID`, `INVALID_SCOPE1`, `INVALID_SCOPE2`, `INVALID_REVENUE`, `DUPLICATE_INVESTMENT_ID`, `WRONG_COLUMN_COUNT`).
- Re-running a file that is already loaded writes nothing. Exit code is 0 on success and 1 when a file fails.

## Data Models

### PortfolioSummary
- `accountNumber`: 9-digit account identifier
- `totalValue`: Total portfolio market value
- `totalGainLoss`: Total gain/loss amount
- `totalGainLossPercent`: Total gain/loss percentage
- `holdings`: Array of portfolio holdings
- `lastUpdated`: Last update timestamp

### PortfolioHolding
- `symbol`: Stock ticker symbol
- `name`: Company name
- `shares`: Number of shares owned
- `currentPrice`: Current share price
- `marketValue`: Total market value of holding
- `gainLoss`: Gain/loss amount for holding
- `gainLossPercent`: Gain/loss percentage for holding

## Account Validation Rules

Account numbers must:
- Be exactly 9 digits long
- Contain only numeric characters
- Not contain any zero digits

## Getting Started

### Prerequisites
- Python 3.12+
- Poetry (for dependency management)

### Installation

1. Navigate to the project directory:
```bash
cd portfolio_backend
```

2. Install dependencies using Poetry:
```bash
poetry install
```

### Running the Service

Start the development server:
```bash
poetry run fastapi dev app/main.py
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Testing the API

Test the health check endpoint:
```bash
curl -X GET "http://localhost:8000/healthz"
```

Test account validation:
```bash
curl -X GET "http://localhost:8000/api/accounts/123456789/validate"
```

Test portfolio data:
```bash
curl -X GET "http://localhost:8000/api/portfolio/123456789"
```

Test transactions endpoint:
```bash
curl -X GET "http://localhost:8000/api/transactions/123456789"
```

## Development Notes

- The service currently returns mock data identical to the frontend's mock data generator
- SQLite database models are set up but not yet used for data persistence
- CORS is enabled for all origins to support frontend development
- The service uses Poetry for dependency management and virtual environment handling

## Future Enhancements

- Replace mock data with actual database queries
- Implement user authentication and authorization
- Add Redis caching for improved performance
- Add Docker containerization for deployment
- Implement comprehensive logging and monitoring
