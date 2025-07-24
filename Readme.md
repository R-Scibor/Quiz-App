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

## 🚀 Uruchomienie projektu

Projekt można uruchomić na dwa sposoby: za pomocą Dockera (zalecane, szczególnie na produkcji) lub lokalnie na maszynie deweloperskiej.

### Metoda 1: Uruchomienie za pomocą Docker (Zalecane)

Ta metoda automatycznie konfiguruje i uruchamia wszystkie potrzebne usługi (backend, frontend, baza danych, Redis, Celery) w odizolowanych kontenerach.

**Wymagania wstępne:**
- **Docker** i **Docker Compose**

**Kroki:**

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/Zyrandool/Quiz-App
    cd Quiz-App
    ```

2.  **Skonfiguruj zmienne środowiskowe:**
    Utwórz plik `.env` w głównym katalogu projektu, kopiując zawartość z przykładowego szablonu (jeśli istnieje) lub tworząc go od zera. Plik ten jest wymagany przez `docker-compose.yml` do ustawienia kluczowych zmiennych, takich jak `SECRET_KEY` czy `DATABASE_URL`.
    ```env
    # Przykład zawartości pliku .env
    SECRET_KEY='twoj-super-tajny-klucz'
    DEBUG=1
    DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
    DATABASE_URL=postgres://quiz_user:quiz_password@db:5432/quiz_db
    ```

3.  **Zbuduj i uruchom kontenery:**
    To polecenie zbuduje obrazy (jeśli nie istnieją) i uruchomi wszystkie usługi w tle.
    ```bash
    docker-compose up --build -d
    ```

4.  **Gotowe!**
    Aplikacja powinna być dostępna pod adresem `http://localhost`.

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
