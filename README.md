# modernized_investment_portfolio_manager
Modernized version of the COBOL Legacy Benchmark Suite (CLBS), a production-grade Investment Portfolio Management System

## Setup Instructions

### Prerequisites
- Node.js and npm
- Python 3.12+ with pip
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/COG-GTM/modernized_investment_portfolio_manager.git
   cd modernized_investment_portfolio_manager
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Setup database (maintain dependencies)**
   ```bash
   cd backend
   ./setup_database.sh
   ```
   This script will:
   - Run Alembic migrations to create the database schema
   - Seed the database with sample portfolio data
   - Verify the setup was successful

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend development server**
   ```bash
   npm run dev
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Database Management

**Quick database commands:**
- Fresh setup: `./setup_database.sh`
- Manual seeding: `python seed_database.py`
- Verify data: `python verify_persistence.py`
