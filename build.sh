#!/usr/bin/env bash
# Ten skrypt konfiguruje i buduje aplikację Django + React na platformie Render.com.
# Jest zaprojektowany do działania jako "Build Command".

# Dyrektywa `set -o errexit` powoduje, że skrypt natychmiast zakończy działanie,
# jeśli którakolwiek z komend zwróci błąd. Jest to kluczowe dla niezawodnych wdrożeń.
set -o errexit

echo "--- Rozpoczynanie procesu budowania ---"

# --- Krok 1: Budowanie Frontendu ---
# Przechodzimy do katalogu z kodem Reacta, instalujemy zależności
# i budujemy statyczną wersję aplikacji (pliki HTML, CSS, JS).
echo "Krok 1/4: Budowanie frontendu..."
cd frontend
npm install
npm run build
cd ..
echo "✅ Frontend zbudowany pomyślnie."

# --- Krok 2: Instalacja Zależności Backendu ---
# Instalujemy wszystkie biblioteki Pythona zdefiniowane w pliku requirements.txt.
echo "Krok 2/4: Instalowanie zależności Pythona..."
pip install -r requirements.txt
echo "✅ Zależności Pythona zainstalowane."

# --- Krok 3: Zbieranie Plików Statycznych Django ---
# Komenda `collectstatic` zbiera wszystkie pliki statyczne (w tym te
# zbudowane przez Reacta w kroku 1) do jednego katalogu (`staticfiles_collected`),
# aby serwer produkcyjny (WhiteNoise) mógł je efektywnie serwować.
# Flaga --no-input zapobiega zadawaniu pytań w terminalu.
echo "Krok 3/4: Zbieranie plików statycznych Django..."
python manage.py collectstatic --no-input
echo "✅ Pliki statyczne zebrane."

# --- Krok 4: Uruchamianie Migracji Bazy Danych ---
# TO JEST NAJWAŻNIEJSZY KROK, KTÓRY ZASTĘPUJE "PRE-DEPLOY COMMAND".
# Komenda `migrate` analizuje stan bazy danych i wprowadza wszelkie
# niezbędne zmiany w jej schemacie (tworzy nowe tabele, dodaje kolumny itp.).
# Uruchomienie jej tutaj gwarantuje, że baza danych będzie zawsze
# zsynchronizowana z modelami Django przed startem aplikacji.
echo "Krok 4/4: Aplikowanie migracji bazy danych..."
python manage.py migrate
echo "✅ Migracje bazy danych zaaplikowane."

echo "--- Proces budowania zakończony pomyślnie! ---"
