# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# 1) Sadece dependency tanımlarını kopyala ve kur (cache-friendly)
COPY pyproject.toml README.md ./
COPY src/velox/__init__.py src/velox/__init__.py
RUN pip install --no-cache-dir --target=/deps .

# 2) Sonra kaynak kodu kopyala (bu katman sık değişir ama pip install cache'i korunur)
COPY src/ src/

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /deps /usr/local/lib/python3.11/site-packages
COPY src/ src/
COPY data/ data/
COPY docs/ docs/

RUN useradd --create-home velox \
    && mkdir -p /app/data/chat_lab_feedback /app/data/chat_lab_imports \
    && chown -R velox:velox /app
USER velox

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

CMD ["python", "-m", "uvicorn", "velox.main:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--forwarded-allow-ips=*"]
