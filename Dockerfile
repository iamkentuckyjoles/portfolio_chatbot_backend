# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2 + cron
RUN apt-get update && apt-get install -y \
    libpq-dev gcc cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files (optional, for admin UI)
RUN python manage.py collectstatic --noinput || true

# Add cron job
COPY cron/quotes-cron /etc/cron.d/quotes-cron
RUN chmod 0644 /etc/cron.d/quotes-cron
RUN crontab /etc/cron.d/quotes-cron

# Expose Django port
EXPOSE 8000

# Start cron + Django
CMD service cron start && python manage.py runserver 0.0.0.0:8000
