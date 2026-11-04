FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Fix Windows CRLF line endings on entrypoint.sh and set permissions
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Ensure uploads directories exist
RUN mkdir -p /app/app/static/uploads/covers \
    /app/app/static/uploads/banners \
    /app/app/static/uploads/avatars

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]

