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
- [🔌 Dokumentacja API](#-dokumentacja-api)
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
- **Kaskadowe ocenianie:** Pytania otwarte idą przez warstwowy pipeline — podobieństwo wektorowe i regex obsługują większość odpowiedzi lokalnie (bez kosztu i opóźnienia LLM); tylko niejednoznaczne odpowiedzi eskalują do Gemini/Vertex. Typy: `open-text`, `open-cli`, `open-code`.
- **Asynchroniczne ocenianie (AI):** Pytania otwarte są oceniane w tle przez Celery, co pozwala użytkownikowi kontynuować test bez oczekiwania na wynik.
- **Zgłaszanie błędów:** Użytkownicy mogą zgłaszać błędy w pytaniach, odpowiedziach lub w ocenie AI.
- **Formatowanie Markdown:** Pytania i wyjaśnienia obsługują formatowanie tekstu (pogrubienie, kursywa, listy itp.) dla lepszej czytelności.
- **Pasek postępu:** Wizualna reprezentacja postępu w rozwiązywaniu testu.
- **Podsumowanie wyników:** Po zakończeniu testu wyświetlana jest strona z wynikiem.
- **Przegląd odpowiedzi:** Możliwość przejrzenia swoich odpowiedzi i porównania ich z poprawnymi.
- **Tryb Ciemny/Jasny:** Przełącznik motywu dla komfortu użytkowania.
- **Responsywność:** Aplikacja jest w pełni responsywna i działa na urządzeniach mobilnych i desktopowych.
- **Panel Administratora:** Rozbudowany panel do zarządzania quizami, pytaniami i kategoriami bezpośrednio w interfejsie Django admin.
- **Konta użytkowników:** Rejestracja i logowanie za pomocą nazwy użytkownika i hasła. Niezalogowani użytkownicy zachowują pełną funkcjonalność quizu; statystyki i tryb nauki są dostępne dodatkowo dla zalogowanych.
- **Statystyki użytkownika:** Śledzenie liczby odpowiedzi, ogólnej trafności, aktualnej i najdłuższej serii dziennej, średniego czasu na pytanie oraz historii ostatnich sesji.
- **Powtarzanie z odstępami (Tryb Nauki):** Po każdej odpowiedzi oceń trudność jako Łatwe / Normalne / Trudne (opcjonalnie). Algorytm SM-2 planuje powtórki. Tryb Nauki priorytetyzuje zaległe i ostatnio błędnie odpowiedziane pytania, mieszając je z nowymi.

---

## 🛠️ Stos technologiczny

### Frontend

- **React.js:** Biblioteka do budowy interfejsu użytkownika.
- **Vite:** Narzędzie do szybkiego budowania i serwowania aplikacji frontendowych.
- **Zustand:** Proste i wydajne zarządzanie stanem aplikacji.
- **Tailwind CSS:** Framework CSS do szybkiego stylowania.
- **Axios:** Klient HTTP do komunikacji z API.
- **Framer Motion:** Biblioteka do zaawansowanych animacji.
- **React Markdown:** Do renderowania treści w formacie Markdown.

### Backend

- **Django:** Framework webowy Pythona do szybkiego tworzenia bezpiecznych i skalowalnych aplikacji.
- **Django REST Framework:** Potężny zestaw narzędzi do budowy API webowych.
- **Celery:** System do zarządzania zadaniami asynchronicznymi w tle.
- **Python:** Język programowania używany po stronie serwera.
- **PostgreSQL:** Produkcyjna, relacyjna baza danych.
- **Redis:** Baza danych w pamięci, używana jako broker dla Celery.
- **Google Gemini API / Vertex AI:** Ocena niejednoznacznych odpowiedzi i pytań `open-code`. Dostawca wybierany zmienną `LLM_PROVIDER`.

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

Quiz App używa **kaskadowego oceniania** — większość odpowiedzi jest oceniana lokalnie (wektory dla `open-text`, regex dla `open-cli`). Tylko niejednoznaczne odpowiedzi i `open-code` trafiają do LLM.

➡️ **[Dokumentacja systemu oceniania](./GRADING.md)**

Prompt Gemini/Vertex dla pytań `open-text` można zmienić w panelu admina Django bez redeployu.

1.  **Zaloguj się do panelu admina:** `/admin`
2.  **Przejdź do Prompt configurations** w sekcji `API_V1`.
3.  **Edytuj `default_prompt`.**
4.  **Zachowaj placeholdery:** `{question_text}`, `{grading_criteria}`, `{max_points}`, `{user_answer}`.
5.  **Zapisz.** Nowy prompt obowiązuje przy kolejnych ocenach LLM.

---

## 📂 Struktura projektu

Projekt jest podzielony na dwie główne części: `frontend` i resztę katalogów tworzących backend.

```
.
├── ai_grader/        # Mikroserwis podobieństwa wektorowego (FastAPI + sentence-transformers)
├── api_v1/           # Aplikacja Django z logiką API, modelami i widokami
├── backend_project/  # Główny folder konfiguracyjny projektu Django
├── docs/             # Dokumentacja projektu
├── frontend/         # Kod źródłowy aplikacji React (Vite)
├── media/            # Lokalne pliki JSON quizów (gitignorowane poza przykładami)
├── nginx/            # Konfiguracja serwera Nginx
├── postgres/         # Konfiguracja bazy danych PostgreSQL
├── .env.example      # Szablon zmiennych środowiskowych
├── .gitignore
├── docker-compose.yml # Definicja usług i orkiestracja kontenerów Docker
├── Dockerfile        # Instrukcje budowania obrazu Docker dla aplikacji Django
├── Dockerfile.celery # Instrukcje budowania obrazu Docker dla workera Celery
├── entrypoint.sh     # Start kontenera: oczekiwanie na DB, frontend, migracje
├── manage.py         # Narzędzie linii komend Django
├── Readme.md         # Ten plik
└── requirements.txt  # Zależności backendu (Python)
```

---

## ✍️ Tworzenie Treści

Chcesz dodać własne pytania lub całe testy do aplikacji? Przygotowaliśmy szczegółowy poradnik, który krok po kroku wyjaśnia, jak tworzyć pliki JSON z quizami i importować je do bazy danych.

➡️ **[Przeczytaj Poradnik Tworzenia i Importowania Quizów](./PL_QUESTIONS.md)**

➡️ **[Dokumentacja systemu oceniania](./GRADING.md)**

---

## 🔌 Dokumentacja API

Szczegółowy opis dostępnych endpointów API, ich parametrów oraz przykładowych odpowiedzi znajduje się w osobnym dokumencie (w języku angielskim).

➡️ **[Przeczytaj Dokumentację API](./API.md)**

---

## 📝 Plany rozwoju

### Możliwe rozszerzenia (pomysły na przyszłość)

- [ ] **OAuth / Logowanie Społecznościowe:** Logowanie przez Google lub GitHub jako alternatywa dla nazwy użytkownika i hasła.
- [x] **Wykresy Statystyk:** Sparkline trafności, słupki per test i historia sesji — na stronie Statystyk.
- [ ] **Rankingi:** Porównywanie wyników z innymi użytkownikami w różnych kategoriach.
- [ ] **Sandboxowane wykonywanie kodu:** Uruchamianie zgłoszonego kodu względem przypadków testowych (`open-code`, v0.3).
- [ ] **Progi wektorowe per pytanie:** Nadpisanie globalnych progów 0.85/0.30.
- [ ] **Śledzenie kosztu oceniania:** Model Django logujący użycie LLM.

### Ukończone

- [x] **Kaskadowe ocenianie:** Typy `open-text`, `open-cli`, `open-code` — wektory, regex albo LLM. Odznaka „Auto-graded” / „Graded by AI”. Ponowienie po timeoutcie.
- [x] **Powtarzanie z Odstępami (Tryb Nauki):** Algorytm SM-2 z ocenami Łatwe/Normalne/Trudne po każdym pytaniu; Tryb Nauki wybiera zaległe i problematyczne pytania, uzupełniając pozostałe miejsca nowymi.
- [x] **Statystyki użytkownika:** Sesje, trafność, serie dzienne, średni czas na pytanie i historia ostatnich sesji — wszystko śledzone dla zalogowanego użytkownika.
- [x] **System uwierzytelniania:** Rejestracja i logowanie za pomocą nazwy użytkownika i hasła przy użyciu tokenów DRF. Niezalogowani użytkownicy zachowują pełny dostęp do quizów.
- [x] **Zgłaszanie pytań/odpowiedzi** Umożliwienie użytkownikowi zgłoszenia błędu w pytaniu/odpowiedzi lub w ocenie AI
- [x] **Asynchroniczne ocenianie (Celery & Redis):** Wprowadzenie zadań w tle do oceny otwartych pytań przez AI, aby użytkownik nie musiał czekać na wynik i mógł kontynuować test.
- [x] **Panel administratora:** Rozbudowa panelu admina o możliwość wygodnego tworzenia i edycji quizów z poziomu interfejsu graficznego.
- [x] **Migracja danych:** Przeniesiono treść quizów z plików JSON do relacyjnej bazy danych (PostgreSQL) w celu zwiększenia wydajności i skalowalności.
- [x] **Naprawa licznika** - Licznik teraz zatrzymuje się po tym jak użytkownik zatwierdzi odpowiedź na pytanie i wznawia ponownie przy następnym pytaniu.
- [x] **Formatowanie tekstu pytań i wyjaśnień:** Zaimplementowano obsługę formatowania Markdown dla treści pytań i wyjaśnień przy użyciu biblioteki `react-markdown`.
- [x] **Lepsza obsługa błędów:** Wprowadzono kompleksową obsługę błędów na wszystkich poziomach aplikacji.