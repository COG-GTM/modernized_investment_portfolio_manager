# modernized_investment_portfolio_manager
Modernized version of the COBOL Legacy Benchmark Suite (CLBS), a production-grade Investment Portfolio Management System

## Features

### Main Menu Navigation
The application provides a terminal-inspired main menu with three core options:

1. **Portfolio Position Inquiry** - View and analyze investment portfolio holdings and performance
2. **Transaction History** - Review investment transaction history and activity  
3. **Exit** - Return to main menu and reset application state

**Navigation Options:**
- Click menu options with mouse
- Use keyboard shortcuts: Press `1`, `2`, or `3` to select an option
- Use arrow keys (`↑` `↓`) to navigate between options, then press `Enter` to select
- Press `Esc` to reset selection

This design mirrors the original COBOL system's three-option menu structure defined in the legacy CICS/3270 terminal interface.

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
