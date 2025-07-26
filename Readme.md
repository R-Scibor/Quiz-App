# Quiz App

![Podgląd aplikacji](./.github/assets/preview.png)

To zaawansowana aplikacja typu "full-stack" do przeprowadzania interaktywnych quizów i testów. Została zaprojektowana z myślą o dynamicznym i angażującym doświadczeniu użytkownika. Aplikacja pozwala nie tylko na rozwiązywanie testów z limitem czasowym, ale także oferuje natychmiastowy feedback, w tym ocenę pytań otwartych przez AI. Po zakończeniu quizu użytkownik otrzymuje szczegółowe podsumowanie wyników oraz ma możliwość przejrzenia swoich odpowiedzi w celu nauki i analizy.

---

## 📋 Spis treści

- [🖼️ Galeria](#️-galeria)
- [✨ Funkcjonalności](#-funkcjonalności)
- [🛠️ Stos technologiczny](#️-stos-technologiczny)
- [🚀 Uruchomienie projektu](#-uruchomienie-projektu)
  - [Wymagania wstępne](#wymagania-wstępne)
  - [Konfiguracja Backendu (Django)](#konfiguracja-backendu-django)
  - [Konfiguracja Frontendu (React)](#konfiguracja-frontendu-react)
- [📂 Struktura projektu](#-struktura-projektu)
- [✍️ Tworzenie Treści](#️-tworzenie-treści)
- [📝 Plany rozwoju](#-plany-rozwoju)

---

## 🖼️ Galeria

| Konfiguracja Testu | Pytanie i Wyjaśnienie (Tryb Ciemny) | Pytanie i Wyjaśnienie (Tryb Jasny) |
| :---: |:---:|:---:|
| ![Ekran konfiguracji testu](./.github/assets/preview_setup.png) | ![Ekran pytania w trybie ciemnym](./.github/assets/preview_question.png) | ![Ekran pytania w trybie jasnym](./.github/assets/preview_lightmode.png) |
| *Użytkownik wybiera kategorię, liczbę pytań i limit czasu.* | *Widok pytania z zaznaczoną odpowiedzią i szczegółowym wyjaśnieniem.* | *Ten sam widok, ale w komfortowym dla oczu trybie jasnym.* |

| Ocena AI i Zgłaszanie Błędów | Ekran Wyników | Przegląd Odpowiedzi |
| :---: |:---:|:---:|
| ![Ocena AI i zgłaszanie błędów](./.github/assets/preview_llm_and_report.png) | ![Ekran wyników](./.github/assets/preview_results.png) | ![Ekran przeglądu odpowiedzi](./.github/assets/preview_review.png) |
| *Odpowiedź na pytanie otwarte oceniona przez AI oraz modal do zgłaszania uwag.* | *Czytelne podsumowanie wyników testu z procentowym wskaźnikiem.* | *Możliwość przejrzenia wszystkich pytań i odpowiedzi po zakończeniu testu.* |

## ✨ Funkcjonalności

- **Wybór testu:** Użytkownik może wybrać jeden z wielu dostępnych testów z różnych kategorii.
- **Limit czasowy:** Każdy quiz ma zdefiniowany limit czasu, który zatrzymuje się po udzieleniu odpowiedzi i wznawia przy następnym pytaniu.
- **Asynchroniczne ocenianie (AI):** Pytania otwarte są oceniane w tle przez AI, co pozwala użytkownikowi kontynuować test bez oczekiwania na wynik.
- **Zgłaszanie błędów:** Użytkownicy mogą zgłaszać błędy w pytaniach, odpowiedziach lub w ocenie AI.
- **Formatowanie Markdown:** Pytania i wyjaśnienia obsługują formatowanie tekstu (pogrubienie, kursywa, listy itp.) dla lepszej czytelności.
- **Pasek postępu:** Wizualna reprezentacja postępu w rozwiązywaniu testu.
- **Podsumowanie wyników:** Po zakończeniu testu wyświetlana jest strona z wynikiem.
- **Przegląd odpowiedzi:** Możliwość przejrzenia swoich odpowiedzi i porównania ich z poprawnymi.
- **Tryb Ciemny/Jasny:** Przełącznik motywu dla komfortu użytkowania.
- **Responsywność:** Aplikacja jest w pełni responsywna i działa na urządzeniach mobilnych i desktopowych.
- **Panel Administratora:** Rozbudowany panel do zarządzania quizami, pytaniami i kategoriami bezpośrednio w interfejsie Django admin.

---

## 🛠️ Stos technologiczny

### Frontend

- **React.js:** Biblioteka do budowy interfejsu użytkownika.
- **Vite:** Narzędzie do szybkiego budowania i serwowania aplikacji frontendowych.
- **Zustand:** Proste i wydajne zarządzanie stanem aplikacji.
- **Tailwind CSS:** Framework CSS do szybkiego stylowania.
- **Axios:** Klient HTTP do komunikacji z API.
- **Framer Motion:** Biblioteka do zaawansowanych animacji.
- **React Router:** Do obsługi routingu po stronie klienta.
- **React Markdown:** Do renderowania treści w formacie Markdown.

### Backend

- **Django:** Framework webowy Pythona do szybkiego tworzenia bezpiecznych i skalowalnych aplikacji.
- **Django REST Framework:** Potężny zestaw narzędzi do budowy API webowych.
- **Celery:** System do zarządzania zadaniami asynchronicznymi w tle.
- **Python:** Język programowania używany po stronie serwera.
- **PostgreSQL:** Produkcyjna, relacyjna baza danych.
- **Redis:** Baza danych w pamięci, używana jako broker dla Celery.

### Infrastruktura i Narzędzia

- **Docker & Docker Compose:** Do konteneryzacji i orkiestracji usług.
- **Nginx:** Serwer proxy do obsługi ruchu i serwowania plików statycznych.
- **Gunicorn:** Serwer aplikacyjny WSGI dla Django.

---

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
    sudo curl -fsSL [https://download.docker.com/linux/ubuntu/gpg](https://download.docker.com/linux/ubuntu/gpg) -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    ```

3.  **Dodaj repozytorium Dockera do źródeł systemu:**
    ```bash
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] [https://download.docker.com/linux/ubuntu](https://download.docker.com/linux/ubuntu) \
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
    git clone [https://github.com/Zyrandool/Quiz-App](https://github.com/Zyrandool/Quiz-App)
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

    # Gemini API Key (opcjonalne)
    GEMINI_API_KEY='twój_klucz_api_gemini'
    ```
    **Ważne:**
    * Wygeneruj nowy `SECRET_KEY` poleceniem: `openssl rand -base64 48`.
    * Ustaw własne, bezpieczne hasło w `POSTGRES_PASSWORD`.
    * W `DJANGO_ALLOWED_HOSTS` zastąp `twoja_domena.com` swoją prawdziwą domeną lub publicznym adresem IP.

---

### **Krok 5: Generowanie Certyfikatów SSL dla PostgreSQL**

Usługa PostgreSQL jest skonfigurowana do używania SSL, więc musisz wygenerować certyfikat samopodpisany i klucz prywatny.

1.  **Utwórz katalog `certs`:**
    ```bash
    mkdir -p certs
    ```

2.  **Wygeneruj certyfikat i klucz.** Pamiętaj, aby w `CN` (Common Name) podać swoją domenę.
    ```bash
    openssl req -new -x509 -days 365 -nodes -out certs/server.crt -newkey rsa:2048 -keyout certs/server.key -subj "/C=XX/ST=State/L=City/O=Organization/OU=Production/CN=twoja_domena.com"
    ```
    *Zastąp `twoja_domena.com` tą samą wartością, której użyłeś w pliku `.env`.*

---

### **Krok 6: Uruchomienie Aplikacji**

Gdy konfiguracja i certyfikaty są na miejscu, możesz zbudować obrazy Docker i uruchomić wszystkie usługi.

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

### **Krok 7: Przygotowanie Danych Aplikacji**

Po uruchomieniu kontenerów, musisz przygotować bazę danych i załadować do niej treść quizów.

1.  **Uruchom migracje Django.** To polecenie stworzy w bazie danych wszystkie tabele wymagane przez aplikację.
    ```bash
    docker compose exec web python manage.py migrate
    ```

2.  **Zaimportuj quizy do bazy danych.** Aby poprawnie zaimportować quizy, umieść pliki `.json` w folderze `media/tests/`, ponieważ wolumin Dockera jest skonfigurowany do używania tej ścieżki.
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests
    ```

3.  **(Zalecane) Stwórz superużytkownika.** Umożliwi Ci to logowanie do panelu administratora Django (`/admin`).
    ```bash
    docker compose exec web python manage.py createsuperuser
    ```
    Program poprosi Cię o podanie nazwy użytkownika, adresu e-mail i hasła.

4.  **Gotowe!** Twoja aplikacja jest w pełni skonfigurowana, uruchomiona i gotowa do użycia pod adresem Twojej domeny.


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

---

## 📂 Struktura projektu

Projekt jest podzielony na dwie główne części: `frontend` i resztę katalogów tworzących backend.

```
.
├── api_v1/           # Aplikacja Django z logiką API, modelami i widokami
├── backend_project/  # Główny folder konfiguracyjny projektu Django
├── certs/            # Certyfikaty SSL dla Nginx/PostgreSQL
├── docs/             # Dokumentacja projektu
├── frontend/         # Kod źródłowy aplikacji React (Vite)
├── media/            # Pliki multimedialne wgrywane przez użytkowników
├── nginx/            # Konfiguracja serwera Nginx
├── postgres/         # Konfiguracja bazy danych PostgreSQL
├── .gitignore
├── build.sh          # Skrypt do budowania obrazów Docker na produkcję
├── docker-compose.yml # Definicja usług i orkiestracja kontenerów Docker
├── Dockerfile        # Instrukcje budowania obrazu Docker dla aplikacji Django
├── Dockerfile.celery # Instrukcje budowania obrazu Docker dla workera Celery
├── manage.py         # Narzędzie linii komend Django
├── Readme.md         # Ten plik
├── requirements.txt  # Zależności backendu (Python)
└── start_dev.bat     # Skrypt do uruchamiania środowiska deweloperskiego (Windows)
```

---

## ✍️ Tworzenie Treści

Chcesz dodać własne pytania lub całe testy do aplikacji? Przygotowaliśmy szczegółowy poradnik, który krok po kroku wyjaśnia, jak tworzyć pliki JSON z quizami i importować je do bazy danych.

➡️ **[Przeczytaj Poradnik Tworzenia i Importowania Quizów](./docs/questions_guide.md)**

---

## 📝 Plany rozwoju

### Możliwe rozszerzenia (pomysły na przyszłość)

- [ ] **System uwierzytelniania:** Dodanie logowania i rejestracji użytkowników.
- [ ] **Historia wyników:** Zapisywanie wyników testów dla zalogowanych użytkowników.
- [ ] **Rozbudowane statystyki:** Wykresy i bardziej szczegółowe analizy wyników.

### Ukończone

- [x] **Zgłaszanie pytań/odpowiedzi** Umożliwienie użytkownikowi zgłoszenia błędu w pytaniu/odpowiedzi lub w ocenie AI
- [x] **Asynchroniczne ocenianie (Celery & Redis):** Wprowadzenie zadań w tle do oceny otwartych pytań przez AI, aby użytkownik nie musiał czekać na wynik i mógł kontynuować test.
- [x] **Panel administratora:** Rozbudowa panelu admina o możliwość wygodnego tworzenia i edycji quizów z poziomu interfejsu graficznego.
- [x] **Migracja danych:** Przeniesiono treść quizów z plików JSON do relacyjnej bazy danych (PostgreSQL) w celu zwiększenia wydajności i skalowalności.
- [x] **Naprawa licznika** - Licznik teraz zatrzymuje się po tym jak użytkownik zatwierdzi odpowiedź na pytanie i wznawia ponownie przy następnym pytaniu.
- [x] **Formatowanie tekstu pytań i wyjaśnień:** Zaimplementowano obsługę formatowania Markdown dla treści pytań i wyjaśnień przy użyciu biblioteki `react-markdown`.
- [x] **Lepsza obsługa błędów:** Wprowadzono kompleksową obsługę błędów na wszystkich poziomach aplikacji.
