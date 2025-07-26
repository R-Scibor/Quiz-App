# Quiz App

![Podgląd aplikacji](./.github/assets/preview.png)

To zaawansowana aplikacja typu "full-stack" do przeprowadzania interaktywnych quizów i testów. Została zaprojektowana z myślą o dynamicznym i angażującym doświadczeniu użytkownika. Aplikacja pozwala nie tylko na rozwiązywanie testów z limitem czasowym, ale także oferuje natychmiastowy feedback, w tym ocenę pytań otwartych przez AI. Po zakończeniu quizu użytkownik otrzymuje szczegółowe podsumowanie wyników oraz ma możliwość przejrzenia swoich odpowiedzi w celu nauki i analizy.

---

## 📋 Spis treści

- [🖼️ Galeria](#️-galeria)
- [✨ Funkcjonalności](#-funkcjonalności)
- [🛠️ Stos technologiczny](#️-stos-technologiczny)
- [🚀 Uruchomienie projektu](#-uruchomienie-projektu)
- [🤖 Konfiguracja AI](#-konfiguracja-ai)
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
- **Google Gemini API:** Wykorzystywane do oceny pytań otwartych przez AI.

### Infrastruktura i Narzędzia

- **Docker & Docker Compose:** Do konteneryzacji i orkiestracji usług.
- **Nginx:** Serwer proxy do obsługi ruchu i serwowania plików statycznych.
- **Gunicorn:** Serwer aplikacyjny WSGI dla Django.

---

## 🚀 Uruchomienie projektu

Szczegółowe instrukcje dotyczące konfiguracji i uruchomienia projektu — zarówno w środowisku produkcyjnym przy użyciu Dockera, jak i lokalnie na maszynie deweloperskiej — zostały przeniesione do osobnego dokumentu.

➡️ **[Przeczytaj Instrukcję Instalacji](./docs/PL_INSTALL.md)**

---

## 🤖 Konfiguracja AI

Aplikacja korzysta z domyślnego promptu dla modelu AI, który ocenia pytania otwarte. Możesz dostosować ten prompt do własnych potrzeb bezpośrednio z panelu administratora Django.

1.  **Zaloguj się do panelu admina:** Przejdź pod adres `/admin` swojej aplikacji i zaloguj się na konto superużytkownika.
2.  **Przejdź do Konfiguracji Promptów:** W sekcji `API_V1` znajdź i kliknij "Prompt configurations".
3.  **Edytuj domyślny prompt:** Zobaczysz domyślny prompt o nazwie `default_prompt`. Kliknij go, aby przejść do edycji.
4.  **Zmodyfikuj prompt:** W polu "System prompt" możesz zmienić treść polecenia. Prompt używa zmiennych (placeholderów) takich jak `{grading_criteria}` i `{user_answer}`, które są dynamicznie podstawiane podczas oceny. Upewnij się, że zachowasz te zmienne, jeśli chcesz, aby AI korzystało z tych danych.
5.  **Zapisz zmiany:** Kliknij przycisk "Zapisz". Nowy prompt będzie używany przy wszystkich kolejnych ocenach AI.

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

➡️ **[Przeczytaj Poradnik Tworzenia i Importowania Quizów](./PL_QUESTIONS.md)**

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