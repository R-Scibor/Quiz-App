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

2.  **Utwórz plik `.env` na podstawie szablonu.**

    ```bash
    cp .env.example .env
    ```

    Edytuj `.env` i zastąp każdy placeholder. **Nie commituj pliku `.env`.**

    **Ważne:**
    * Wygeneruj nowy `SECRET_KEY` poleceniem: `python -c "import secrets; print(secrets.token_urlsafe(50))"` (albo `openssl rand -base64 48`).
    * Ustaw silne hasło w `POSTGRES_PASSWORD`. `DATABASE_URL` jest składane z pozostałych zmiennych bazy — musi być z nimi zgodny.
    * W `DJANGO_ALLOWED_HOSTS` podaj prawdziwą domenę lub publiczny adres IP.
    * Ustaw `LLM_PROVIDER` na `gemini` (wymaga `GEMINI_API_KEY`) albo `vertex` (wymaga `VERTEX_*` oraz `secrets/vertex-sa-key.json`). Szczegóły w `docs/GRADING.md`.

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