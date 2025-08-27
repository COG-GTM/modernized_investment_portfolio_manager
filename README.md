# Modernized Investment Portfolio Manager

A modern web-based investment portfolio management system that enables financial professionals and investors to view, analyze, and manage investment portfolios through an intuitive interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Modernized Investment Portfolio Manager is a production-grade web application that represents a modernized version of the COBOL Legacy Benchmark Suite (CLBS). This project transitions from legacy COBOL infrastructure to a contemporary full-stack web technology stack, providing financial professionals with modern tools for portfolio management.

**Target Users:**
- Financial advisors
- Portfolio managers
- Individual investors
- Investment analysts

## Features

- **Portfolio Inquiry**: Search and view detailed portfolio information by account number
- **Real-time Data**: Live portfolio performance with gain/loss calculations and percentage changes
- **Transaction History**: Comprehensive transaction records and activity tracking
- **Accessibility First**: Full keyboard navigation support and screen reader compatibility
- **Responsive Design**: Optimized for desktop and mobile devices
- **Modern UI**: Clean, professional interface built with Tailwind CSS

## Quick Start

### Prerequisites

- **Node.js**: 18.x or higher
- **Python**: 3.9 or higher
- **PostgreSQL**: 12.x or higher
- **npm** or **yarn**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/COG-GTM/modernized_investment_portfolio_manager.git
   cd modernized_investment_portfolio_manager
   ```

2. **Install frontend dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   ```bash
   # Create PostgreSQL database
   createdb portfolio_manager
   
   # Run migrations
   cd backend
   alembic upgrade head
   ```

### Running the Application

**Start the backend server:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start the frontend development server:**
```bash
npm run dev
# or
yarn dev
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
├── src/                          # Frontend React application
│   ├── components/               # Reusable UI components
│   │   ├── ui/                  # Basic UI building blocks
│   │   └── dialogs/             # Modal and dialog components
│   ├── pages/                   # Top-level page components
│   ├── hooks/                   # Custom React hooks
│   ├── types/                   # TypeScript type definitions
│   ├── utils/                   # Utility functions
│   └── services/                # API service layer
├── backend/                     # FastAPI backend application
│   ├── app/                     # Application core
│   ├── models/                  # Database models
│   ├── routers/                 # API route handlers
│   ├── migrations/              # Database migrations
│   └── requirements.txt         # Python dependencies
├── public/                      # Static assets
└── dist/                        # Production build output
```

## Technology Stack

### Frontend
- **React 19** - Modern UI library with hooks and concurrent features
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router DOM** - Client-side routing
- **Zod** - Schema validation and type inference

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **PostgreSQL** - Relational database

### Development Tools
- **ESLint** - Code linting and formatting
- **PostCSS** - CSS processing
- **shadcn/ui** - Component library integration

## Development

### Available Scripts

**Frontend:**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

**Backend:**
```bash
uvicorn app.main:app --reload    # Start development server
alembic revision --autogenerate  # Generate new migration
alembic upgrade head             # Apply migrations
python -m pytest                # Run tests
```

### Code Style and Standards

- Follow TypeScript strict mode guidelines
- Use Tailwind CSS for styling
- Implement proper error handling and loading states
- Ensure accessibility compliance (WCAG 2.1 AA)
- Write comprehensive tests for new features

### Database Migrations

When making database schema changes:

1. Update SQLAlchemy models in `backend/models/`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review and edit the generated migration file
4. Apply migration: `alembic upgrade head`

## API Documentation

The FastAPI backend provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/portfolio/{account_number}` - Retrieve portfolio information
- `GET /api/transactions/{account_number}` - Get transaction history
- `GET /api/positions/{account_number}` - List portfolio positions

## Database

The application uses PostgreSQL with the following key tables:

- **portfolios** - Portfolio summary information
- **positions** - Individual investment holdings
- **transactions** - Transaction history records
- **accounts** - Account management data

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code of conduct
- Development workflow
- Pull request process
- Issue reporting

### Getting Started with Development

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests
4. Run the test suite: `npm test` and `python -m pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

_Originally written and maintained by contributors and [Devin](https://app.devin.ai), with updates from the core team._
