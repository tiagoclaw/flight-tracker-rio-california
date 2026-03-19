FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY standalone_monitor.py .
COPY simple_health_server.py .
COPY api.py .
COPY web_server.py .
COPY dashboard.html .
COPY railway_start.py .
COPY railway_start_fixed.py .
COPY simple_api_server.py .
COPY railway.json .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///data/flights.db
ENV PORT=8000

# Expose port for health checks (Railway auto-detects this)
EXPOSE $PORT

# Make scripts executable
RUN chmod +x railway_start.py standalone_monitor.py

# Default command - Railway optimized startup with CORS
CMD ["python", "railway_start_fixed.py"]