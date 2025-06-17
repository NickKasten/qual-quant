FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user before copying start.sh
RUN useradd -m appuser && chown -R appuser:appuser /app

# Copy start.sh and set permissions
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && chown appuser:appuser /app/start.sh

USER appuser

CMD ["/app/start.sh"] 