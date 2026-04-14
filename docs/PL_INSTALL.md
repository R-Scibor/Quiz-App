# 🚀 Uruchomienie projektu

Projekt można uruchomić na dwa sposoby: za pomocą Dockera (zalecane, szczególnie na produkcji) lub lokalnie na maszynie deweloperskiej. Poniższy poradnik skupia się na zalecanej metodzie z użyciem Dockera.

## Metoda 1: Uruchomienie za pomocą Docker (Zalecane)

Ten przewodnik przedstawia kompleksowy proces konfiguracji i uruchomienia projektu na maszynie wirtualnej z systemem Ubuntu, przygotowany specjalnie pod środowisko produkcyjne. Postępując zgodnie z instrukcjami, zainstalujesz wszystkie niezbędne zależności, skonfigurujesz środowisko i uruchomisz aplikację, minimalizując ryzyko błędów.

---
### **Krok 1: Instalacja Dockera i Docker Compose**

Najpierw musimy zainstalować silnik Dockera oraz wtyczkę Docker Compose. Narzędzia te będą zarządzać usługami aplikacji w odizolowanych kontenerach.

1.  **Zaktualizuj listę pakietów i zainstaluj zależności:**
    ```bash
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    ```

2.  **Dodaj oficjalny klucz GPG Dockera, aby zapewnić autentyczność pakietów:**
    ```bash
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    ```

3.  **Dodaj repozytorium Dockera do źródeł systemu:**
    ```bash
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    ```

4.  **Zainstaluj silnik Dockera, interfejs linii poleceń (CLI) oraz wtyczkę Docker Compose:**
    ```bash
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

---

### **Krok 2: Konfiguracja Uprawnień Dockera**

Aby uruchamiać polecenia `docker` bez `sudo` i uniknąć błędów uprawnień, musisz dodać swojego użytkownika do grupy `docker`.

1.  **Dodaj swojego obecnego użytkownika do grupy `docker`:**
    ```bash
    sudo usermod -aG docker $USER
    ```

2.  **Zastosuj zmiany.** Aby nowe członkostwo w grupie zaczęło obowiązywać, **musisz zrestartować maszynę wirtualną**.
    ```bash
    sudo reboot
    ```
    Po ponownym uruchomieniu maszyny zaloguj się i przejdź do następnego kroku.

---

### **Krok 3: Instalacja Gita**

Git jest wymagany do pobrania plików projektu z repozytorium.

1.  **Zainstaluj Gita za pomocą menedżera pakietów:**
    ```bash
    sudo apt-get install git -y
    ```

---

### **Krok 4: Konfiguracja Projektu Quiz App (Środowisko Produkcyjne)**

Gdy wszystkie zależności są gotowe, możesz sklonować repozytorium i skonfigurować je dla środowiska produkcyjnego.

1.  **Sklonuj repozytorium z GitHub:**
    ```bash
    git clone https://github.com/Zyrandool/Quiz-App
    cd Quiz-App
    ```

2.  **Skonfiguruj zmienne środowiskowe w pliku `.env`.**

    > **Uwaga:** Poniższe polecenie używa edytora `nano`. Jeśli nie jest zainstalowany, możesz go dodać poleceniem `sudo apt-get install nano -y`.

    ```bash
    nano .env
    ```
    Skopiuj i wklej poniższą zawartość do pliku. **Pamiętaj, aby zmienić wrażliwe dane!**

    ```env
    # Django Core Settings
    SECRET_KEY='tutaj_wklej_swój_bardzo_bezpieczny_klucz'
    DEBUG=0
    DJANGO_ALLOWED_HOSTS=twoja_domena.com,www.twoja_domena.com

    # Database Settings - ZMIEŃ PONIŻSZE WARTOŚCI NA WŁASNE!
    POSTGRES_DB=quiz_db
    POSTGRES_USER=quiz_user
    POSTGRES_PASSWORD='twoje_super_bezpieczne_haslo_do_bazy'

    # Ta zmienna jest budowana automatycznie z powyższych wartości.
    DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

    # Celery Settings
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0

    # Ocenianie AI — wybierz jednego dostawcę:

    # Opcja A: bezpośredni klucz API Gemini (domyślne)
    LLM_PROVIDER=gemini
    GEMINI_API_KEY='twój_klucz_api_gemini'

    # Opcja B: Google Vertex AI przez konto usługi
    # LLM_PROVIDER=vertex
    # VERTEX_PROJECT_ID=twoj-projekt-gcp
    # VERTEX_LOCATION=us-central1
    # VERTEX_MODEL=gemini-2.5-flash
    # (umieść plik JSON konta usługi w secrets/vertex-sa-key.json)
    ```
    **Ważne:**
    * Wygeneruj nowy `SECRET_KEY` poleceniem: `openssl rand -base64 48`.
    * Ustaw własne, bezpieczne hasło w `POSTGRES_PASSWORD`.
    * W `DJANGO_ALLOWED_HOSTS` zastąp `twoja_domena.com` swoją prawdziwą domeną lub publicznym adresem IP.
    * Dla Vertex AI utwórz katalog `secrets/` w głównym katalogu projektu i umieść tam plik JSON konta usługi jako `vertex-sa-key.json` przed uruchomieniem kontenerów. Szczegóły w `docs/GRADING.md`.

---

### **Krok 5: Uruchomienie Aplikacji**

Gdy konfiguracja jest gotowa, możesz zbudować obrazy Docker i uruchomić wszystkie usługi. Certyfikaty SSL dla bazy danych zostaną wygenerowane automatycznie.

1.  **Zbuduj i uruchom kontenery w tle:**
    ```bash
    docker compose up --build -d
    ```

2.  **Sprawdzenie statusu.** Upewnij się, że wszystkie kontenery działają poprawnie.
    ```bash
    docker compose ps
    ```
    Powinieneś zobaczyć status `running` lub `up` dla wszystkich usług.

---

### **Krok 6: Przygotowanie Danych Aplikacji**

Po uruchomieniu kontenerów migracje bazy danych zostaną wykonane automatycznie. Musisz jedynie załadować treść quizów.

1.  **Zaimportuj quizy do bazy danych.** Aby poprawnie zaimportować quizy, umieść pliki `.json` w folderze `media/tests/`, ponieważ wolumin Dockera jest skonfigurowany do używania tej ścieżki.
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests
    ```

2.  **(Zalecane) Stwórz superużytkownika.** Umożliwi Ci to logowanie do panelu administratora Django (`/admin`).
    ```bash
    docker compose exec web python manage.py createsuperuser
    ```
    Program poprosi Cię o podanie nazwy użytkownika, adresu e-mail i hasła.

3.  **Gotowe!** Twoja aplikacja jest w pełni skonfigurowana, uruchomiona i gotowa do użycia pod adresem Twojej domeny.


### Metoda 2: Uruchomienie lokalne (dla deweloperów Windows)

Ta metoda jest przeznaczona do dewelopmentu i testowania na maszynie lokalnej. Używa bazy danych SQLite i wymaga ręcznej instalacji niektórych zależności.

**Wymagania wstępne:**
- **Python** (wersja 3.8 lub nowsza)
- **Node.js** i **npm**
- **Redis** (wymagany dla Celery) - [Instrukcje instalacji dla Windows](https://redis.io/docs/getting-started/installation/install-redis-on-windows/)

**Kroki:**

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/Zyrandool/Quiz-App
    cd Quiz-App
    ```

2.  **Skonfiguruj Backend:**
    - Utwórz i aktywuj wirtualne środowisko:
      ```bash
      python -m venv env
      .\env\Scripts\activate
      ```
    - Zainstaluj zależności Pythona:
      ```bash
      pip install -r requirements.txt
      ```

3.  **Skonfiguruj Frontend:**
    - Przejdź do katalogu `frontend`:
      ```bash
      cd frontend
      ```
    - Zainstaluj zależności Node.js:
      ```bash
      npm install
      ```
    - Wróć do głównego katalogu projektu:
      ```bash
      cd ..
      ```

4.  **Uruchom środowisko deweloperskie:**
    Użyj dostarczonego skryptu, aby uruchomić wszystkie komponenty (Django, Vite, Celery) w jednym oknie Windows Terminal.
    ```bash
    .\start_dev.bat
    ```
    - **Backend (Django)** będzie dostępny pod adresem `http://127.0.0.1:8000`.
    - **Frontend (Vite)** będzie dostępny pod adresem `http://localhost:5173`.
    - **Celery Worker** będzie działał w tle, obsługując zadania asynchroniczne.