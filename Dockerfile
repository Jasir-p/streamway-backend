
FROM python:3.13-slim

# Create appuser and app directory
RUN useradd -m -u 1000 appuser && mkdir /app && chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Install system dependencies required for django-tenants
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=streamway.settings

# Create directories for static and media files
RUN mkdir -p /app/static /app/media && chown -R appuser:appuser /app/static /app/media

# Use non-root user
USER appuser

EXPOSE 8000

# # Health check for django-tenants
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000// || exit 1

# Default command - can be overridden in docker-compose
CMD [ "daphne", "-b", "0.0.0.0", "-p", "8000", "streamway.asgi:application" ]
