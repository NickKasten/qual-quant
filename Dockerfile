FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create startup script in /tmp first
RUN echo '#!/bin/bash' > /tmp/start.sh && \
    echo 'echo "Checking environment variables..."' >> /tmp/start.sh && \
    echo 'echo "TIINGO_API_KEY: ${TIINGO_API_KEY:+set}"' >> /tmp/start.sh && \
    echo 'echo "ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY:+set}"' >> /tmp/start.sh && \
    echo 'echo "ALPACA_API_KEY: ${ALPACA_API_KEY:+set}"' >> /tmp/start.sh && \
    echo 'echo "ALPACA_SECRET_KEY: ${ALPACA_SECRET_KEY:+set}"' >> /tmp/start.sh && \
    echo 'echo "SUPABASE_URL: ${SUPABASE_URL:+set}"' >> /tmp/start.sh && \
    echo 'echo "SUPABASE_KEY: ${SUPABASE_KEY:+set}"' >> /tmp/start.sh && \
    echo 'exec python main.py' >> /tmp/start.sh && \
    chmod +x /tmp/start.sh

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app

# Move start.sh to /app and set permissions
RUN mv /tmp/start.sh /app/start.sh && \
    chown appuser:appuser /app/start.sh

USER appuser

CMD ["/app/start.sh"] 