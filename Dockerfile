# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir --target=/deps .

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /deps /usr/local/lib/python3.11/site-packages
COPY src/ src/
COPY data/ data/
COPY docs/ docs/

RUN useradd --create-home velox
USER velox

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

CMD ["python", "-m", "uvicorn", "velox.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
