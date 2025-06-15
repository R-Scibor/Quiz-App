#!/usr/bin/env bash
# exit on error
set -o errexit

# Krok 1: Zbuduj frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Krok 2: Zainstaluj zależności Pythona
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Krok 3: Zbierz pliki statyczne
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Krok 4: Uruchom migracje bazy danych
echo "Applying database migrations..."
python manage.py migrate