import math

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from routers import portfolio, accounts, esg

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



def _json_safe(value):
    """Validation errors echo the rejected input; NaN/Infinity are not valid JSON and would turn a 422 into a 500."""
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": _json_safe(exc.errors())})


app.include_router(portfolio.router)
app.include_router(accounts.router)
app.include_router(esg.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
