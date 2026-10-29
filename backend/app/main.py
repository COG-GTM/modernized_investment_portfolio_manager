from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    # Do not echo the submitted input: it may be non-serialisable (e.g. a non-finite number).
    errors = [{k: v for k, v in err.items() if k in ("type", "loc", "msg")} for err in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


app.include_router(portfolio.router)
app.include_router(accounts.router)
app.include_router(esg.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
