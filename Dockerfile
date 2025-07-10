# Use slim Python image to reduce size
FROM python:3.11-slim

# Set environment variables to reduce size and avoid Python warnings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install pip dependencies with no cache
COPY requirements.txt ./
RUN apt-get update && apt-get install -y build-essential gcc \
  && pip install --no-cache-dir -r requirements.txt \
  && apt-get remove -y build-essential gcc \
  && apt-get autoremove -y && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . .

# Run app
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
