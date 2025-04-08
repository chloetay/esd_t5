FROM python:3.9-slim

WORKDIR /app

# Install PostgreSQL client (needed for psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8005

# Command to run the application
# Use single process to avoid worker conflicts
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]