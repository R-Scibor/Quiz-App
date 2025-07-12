# Dockerfile

# --- Etap 1: Budowanie Frontendu ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Etap 2: Budowanie Aplikacji Pythonowej ---
FROM python:3.11-slim

# Ustaw zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Odbierz i ustaw zmienną DATABASE_URL na czas budowania
ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}

# Instalacja zależności Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu backendu
COPY . .

# Kopiowanie zbudowanego frontendu z Etapu 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Uruchom collectstatic z fałszywą bazą danych
RUN DATABASE_URL=sqlite:///dummy.db python manage.py collectstatic --no-input

# Uruchomienie aplikacji
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend_project.wsgi"]