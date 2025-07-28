# Stage 1: Builder with all dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt update && apt install -y --no-install-recommends \
    build-essential gcc libffi-dev libopenblas-dev liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy everything (app + installed packages)
COPY --from=builder /usr/local /usr/local
COPY . .

# Optional: Clean up site-packages (saves space)
RUN find /usr/local/lib/python3.11/site-packages/ -type d -name "__pycache__" -exec rm -r {} + && \
    find /usr/local/lib/python3.11/site-packages/ -type d -name "tests" -exec rm -r {} + && \
    find /usr/local/lib/python3.11/site-packages/ -type f -name "*.pyc" -delete

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
