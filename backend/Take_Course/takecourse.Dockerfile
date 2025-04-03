# Use official Python runtime as base image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ===========================================
# Runtime stage
# ===========================================
FROM python:3.11-slim

# Create non-root user
RUN useradd -m appuser && \
    mkdir -p /app && \
    chown appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory and copy application
WORKDIR /app
COPY --chown=appuser:appuser . .

# Environment variables for services
ENV COURSE_SERVICE_URL="http://course:5000" \
    COURSE_LOGS_URL="http://courselogs:5003" \
    QUIZ_SERVICE_URL="http://quizzes:8000" \
    FLASK_ENV="production" \
    GUNICORN_CMD_ARGS="--workers=4 --bind=0.0.0.0:5001 --timeout=120"

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:5001/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", "app:app"]