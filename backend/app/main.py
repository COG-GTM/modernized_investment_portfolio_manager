from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from routers import portfolio, accounts

app = FastAPI(
    title="Portfolio Management API",
    description="FastAPI backend service for investment portfolio management",
    version="1.0.0"
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(portfolio.router)
app.include_router(accounts.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
