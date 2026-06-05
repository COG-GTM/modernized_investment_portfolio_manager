# syntax=docker/dockerfile:1

# ---- Stage 1: builder ----
# Install dependencies into an isolated in-project virtualenv with Poetry.
FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install "poetry==${POETRY_VERSION}"

# Copy only dependency manifests first to maximize layer caching.
COPY pyproject.toml poetry.lock ./

# Install only main (runtime) dependencies; project itself is not a package.
RUN poetry install --only main --no-root


# ---- Stage 2: runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create an unprivileged user to run the app, plus a writable data dir for
# the SQLite database (mounted as a named volume by docker-compose).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

WORKDIR /app

# Bring in the prebuilt virtualenv from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy application source.
COPY . .

# entrypoint runs migrations + seed, then starts the server.
RUN chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Python-based healthcheck avoids shipping curl (smaller, fewer CVEs).
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
