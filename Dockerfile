# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Odbierz argument przekazany z docker-compose.yml
ARG DATABASE_URL
# Ustaw go jako zmienną środowiskową dla kolejnych komend
ENV DATABASE_URL=${DATABASE_URL}

# Collect static files (teraz ta komenda będzie widzieć DATABASE_URL)
RUN python manage.py collectstatic --no-input

# Run the app. Gunicorn is a production-ready WSGI server.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "your_project_name.wsgi"]