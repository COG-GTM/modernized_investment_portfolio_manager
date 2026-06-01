import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from routers import portfolio, accounts

app = FastAPI(
    title="Portfolio Management API",
    description="FastAPI backend service for investment portfolio management",
    version="1.0.0"
)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(portfolio.router)
app.include_router(accounts.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
