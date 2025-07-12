# Dockerfile

# --- Etap 1: Budowanie Frontendu ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- KROK DEBUGUJĄCY 1: Sprawdź, czy pliki frontendu w ogóle się zbudowały ---
RUN echo "--- DEBUG: Zawartość /app/frontend/dist w etapie budowania frontendu: ---" && ls -lR /app/frontend/dist


# --- Etap 2: Budowanie Aplikacji Pythonowej ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# --- KROK DEBUGUJĄCY 2: Sprawdź, co jest w finalnym obrazie PO skopiowaniu wszystkiego ---
RUN echo "--- DEBUG: Zawartość /app w finalnym obrazie: ---" && ls -lR /app

# Uruchom collectstatic z fałszywą bazą danych
RUN DATABASE_URL=sqlite:///dummy.db python manage.py collectstatic --no-input

# Uruchomienie aplikacji
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend_project.wsgi"]