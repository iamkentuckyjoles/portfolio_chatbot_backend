# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2 + cron + pg_isready
RUN apt-get update && apt-get install -y \
    libpq-dev cron postgresql-client \
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

# Start cron + wait for Postgres + run Django
CMD ["sh", "-c", "service cron start && until pg_isready -h db -p 5432 -U $POSTGRES_USER; do echo 'Waiting for Postgres...'; sleep 2; done && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
