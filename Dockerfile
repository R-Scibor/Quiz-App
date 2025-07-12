# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files (including the React build)
RUN python manage.py collectstatic --no-input

# Run the app. Gunicorn is a production-ready WSGI server.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "your_project_name.wsgi"]