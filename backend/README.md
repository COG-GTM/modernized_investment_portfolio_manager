# Portfolio Management Backend API

A FastAPI backend service for investment portfolio management that serves as the data service for the modernized investment portfolio management frontend application.

## Features

- **Portfolio Management**: Get portfolio summary and holdings for account numbers
- **Account Validation**: Endpoint for the 10-digit account number check (currently bypassed: always valid)
- **Transaction History**: Placeholder endpoint for future transaction data
- **Mock Data**: Portfolio endpoint returns the same mock holdings for every account
- **SQLite Database**: SQLAlchemy models, Alembic migrations and a seed script; not yet read by the API

See [../docs/architecture.md](../docs/architecture.md) for the full architecture.

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
│   ├── portfolio.py         # Pydantic response models
│   ├── database.py          # SQLAlchemy Portfolio, Position + engine
│   ├── transactions.py      # SQLAlchemy Transaction
│   └── history.py           # SQLAlchemy History (audit trail)
├── routers/
│   ├── portfolio.py         # Portfolio and transactions endpoints
│   └── accounts.py          # Account endpoints
├── validation/portfolio.py  # Field validation ported from COBOL
├── services/portfolio_service.py  # Transaction processing
├── migrations/              # Alembic migrations
├── tests/validation/        # pytest tests
├── setup_database.sh        # migrate + seed + verify
├── seed_database.py, verify_persistence.py, test_models.py
├── requirements.txt         # Outdated pins (fail on Python 3.12)
├── pyproject.toml           # Poetry configuration
└── README.md                # This file
```

## Data Models

### PortfolioSummary
- `accountNumber`: account identifier (10 digits in the frontend form)
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

The frontend form (zod, `src/types/account.ts`) requires exactly 10 numeric digits. On the backend, `validate_account_number` in `validation/portfolio.py` is disabled and returns `True` for any input, and the portfolio and transactions endpoints do not call it (intentional IDOR demo).

## Getting Started

### Prerequisites
- Python 3.12+
- Poetry (for dependency management)

### Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using Poetry:
```bash
poetry install --no-root
```

### Running the Service

Start the development server:
```bash
poetry run uvicorn app.main:app --reload --port 8000
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
curl -X GET "http://localhost:8000/api/accounts/1234567890/validate"
```

Test portfolio data:
```bash
curl -X GET "http://localhost:8000/api/portfolio/1234567890"
```

Test transactions endpoint:
```bash
curl -X GET "http://localhost:8000/api/transactions/1234567890"
```

## Development Notes

- The portfolio endpoint returns hard-coded mock data (`generate_mock_portfolio`)
- The SQLite schema is created by Alembic and seeded by `setup_database.sh`, but no endpoint queries it yet
- CORS is enabled for all origins to support frontend development
- The service uses Poetry for dependency management and virtual environment handling

## Future Enhancements

- Replace mock data with actual database queries
- Implement user authentication and authorization
- Add Redis caching for improved performance
- Add Docker containerization for deployment
- Implement comprehensive logging and monitoring
