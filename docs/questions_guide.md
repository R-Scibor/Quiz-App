# Poradnik Tworzenia i Importowania Quizów

Niniejszy dokument stanowi kompletny przewodnik po tworzeniu nowych testów w formacie JSON oraz ich importowaniu do bazy danych aplikacji "Quiz App".

---

## 📋 Spis treści

- [Struktura Pliku JSON](#-struktura-pliku-json)
- [Struktura Obiektu Pytania](#-struktura-obiektu-pytania)
  - [Pytanie Zamknięte (Jednokrotnego Wyboru)](#pytanie-zamknięte-jednokrotnego-wyboru)
  - [Pytanie Zamknięte (Wielokrotnego Wyboru)](#pytanie-zamknięte-wielokrotnego-wyboru)
  - [Pytanie Otwarte](#pytanie-otwarte)
- [Jak Załadować Nowe Testy do Bazy Danych](#-jak-załadować-nowe-testy-do-bazy-danych)

---

## Struktura Pliku JSON

Każdy plik `.json` reprezentuje jeden kompletny test i powinien mieć następującą strukturę główną:

```json
{
  "category": "Nazwa Kategorii",
  "scope": "Nazwa lub Zakres Testu",
  "version": "1.0",
  "questions": [
    // Tablica obiektów z pytaniami...
  ]
}
```

-   `category` (string): Główna kategoria tematyczna testu (np. "Historia", "Biologia"). Będzie ona utworzona w bazie danych, jeśli jeszcze nie istnieje.
-   `scope` (string): Tytuł testu, który będzie widoczny dla użytkownika (np. "Polska Średniowieczna", "Budowa Komórki").
-   `questions` (array): Tablica zawierająca wszystkie obiekty pytań dla danego testu.

---

## 📝 Struktura Obiektu Pytania

Każde pytanie w tablicy `questions` jest obiektem o określonych polach. Poniżej znajdują się przykłady dla każdego z obsługiwanych typów pytań.

### Pytanie Zamknięte (Jednokrotnego Wyboru)

Użytkownik może wybrać tylko jedną poprawną odpowiedź.

```json
{
  "id": 101,
  "questionText": "W którym roku odbyła się koronacja Bolesława Chrobrego?",
  "image": "https://example.com/link_do_obrazka.png",
  "type": "single-choice",
  "tags": ["władcy", "daty", "Polska"],
  "options": [
    "966",
    "1000",
    "1025",
    "1138"
  ],
  "correctAnswers": [2],
  "explanation": "Koronacja odbyła się w 1025 roku, tuż przed jego śmiercią."
}
```

-   `id` (integer): Unikalny identyfikator pytania w ramach pliku (obecnie nieużywany, ale wymagany dla spójności).
-   `questionText` (string): Treść pytania.
-   `image` (string, opcjonalne): Link URL do obrazka, który zostanie wyświetlony przy pytaniu. Może być pustym stringiem `""`.
-   `type` (string): Musi mieć wartość `"single-choice"`.
-   `tags` (array of strings): Lista tagów opisujących pytanie.
-   `options` (array of strings): Lista możliwych odpowiedzi.
-   `correctAnswers` (array of integers): Tablica zawierająca **jeden element** - indeks (zaczynając od 0) poprawnej odpowiedzi w tablicy `options`.
-   `explanation` (string, opcjonalne): Tekst wyjaśnienia, który wyświetli się użytkownikowi po odpowiedzi.

### Pytanie Zamknięte (Wielokrotnego Wyboru)

Użytkownik może wybrać kilka poprawnych odpowiedzi.

```json
{
  "id": 202,
  "questionText": "Które z poniższych elementów występują zarówno w komórkach prokariotycznych, jak i eukariotycznych?",
  "image": "",
  "type": "multiple-choice",
  "tags": ["komórka", "prokariota", "eukariota"],
  "options": [
    "Błona komórkowa",
    "Rybosomy",
    "Mitochondrium",
    "Jądro komórkowe"
  ],
  "correctAnswers": [0, 1],
  "explanation": "Zarówno prokarionty, jak i eukarionty posiadają błonę komórkową oraz rybosomy."
}
```

-   `type` (string): Musi mieć wartość `"multiple-choice"`.
-   `correctAnswers` (array of integers): Tablica zawierająca **indeksy wszystkich poprawnych odpowiedzi**.

### Pytanie Otwarte

Użytkownik musi wpisać odpowiedź tekstową, która jest oceniana przez AI.

```json
{
  "id": 104,
  "questionText": "Wymień i krótko opisz co najmniej trzy skutki Zjazdu Gnieźnieńskiego z 1000 roku.",
  "image": "",
  "type": "open-ended",
  "tags": ["zjazd gnieźnieński", "dyplomacja"],
  "gradingCriteria": "Odpowiedź musi zawierać co najmniej trzy z następujących skutków, z krótkim wyjaśnieniem: 1. Utworzenie niezależnej polskiej metropolii kościelnej. 2. Umocnienie pozycji międzynarodowej Polski. 3. Symboliczne uznanie suwerenności państwa przez Cesarstwo.",
  "maxPoints": 6
}
```

-   `type` (string): Musi mieć wartość `"open-ended"`.
-   `gradingCriteria` (string): **Kluczowe pole.** Dokładny opis, na podstawie którego AI oceni odpowiedź użytkownika. Powinien być precyzyjny i jasno określać, co jest wymagane.
-   `maxPoints` (integer): Maksymalna liczba punktów do zdobycia za to pytanie.
-   Pola `options` i `correctAnswers` **muszą zostać pominięte**.

---

**WAŻNE:** Przed załadowaniem testów do bazy danych, zaleca się użycie komendy `validate_quiz_json`, aby upewnić się, że pliki są poprawne i nie zawierają błędów.

**Przykład użycia:**

```bash
python manage.py validate_quiz_json media/tests/moj_quiz.json
```

## 🚀 Jak Załadować Nowe Testy do Bazy Danych

Po stworzeniu nowych plików `.json` z testami, należy zaimportować je do produkcyjnej bazy danych. Proces ten wykonuje się jednorazowo dla każdego nowego zestawu plików, używając specjalnej komendy Django.

**Wymagania:** Dostęp do **External Database URL** z panelu bazy danych na Render.com.

### Krok 1: Przygotowanie środowiska lokalnego

1.  Umieść swoje nowe pliki `.json` w katalogu `media/tests/` w lokalnej kopii projektu.
2.  W głównym katalogu projektu (obok `manage.py`) znajdź lub utwórz plik `.env`.
3.  Otwórz plik `.env` i wklej do niego zewnętrzny adres URL do Twojej bazy na Render:

    ```env
    # Plik: .env
    DATABASE_URL=postgres://USER:PASSWORD@EXTERNAL_HOST:PORT/DATABASE
    ```
    *Dzięki temu wszystkie komendy Django będą teraz wykonywane na produkcyjnej bazie danych.*

### Krok 2: Uruchomienie skryptu importującego

1.  Otwórz terminal w głównym katalogu projektu na swoim komputerze.
2.  Upewnij się, że Twoje wirtualne środowisko jest aktywne.
3.  Uruchom poniższą komendę:

    ```bash
    python manage.py import_quizzes media/tests
    ```
    **Importowanie pojedynczego pliku:**
    Możesz również załadować pojedynczy plik JSON, podając bezpośrednią ścieżkę do niego:
    ```bash
    python manage.py import_quizzes media/tests/moj_nowy_quiz.json
    ```
    **Uwaga:** Jeśli chcesz całkowicie wyczyścić bazę i zaimportować wszystko od nowa, użyj flagi `--clean` (działa zarówno dla katalogów, jak i pojedynczych plików):
    ```bash
    python manage.py import_quizzes media/tests --clean
    ```
    lub
    ```bash
    python manage.py import_quizzes media/tests/moj_nowy_quiz.json --clean
    ```

4.  Skrypt połączy się z produkcyjną bazą danych i zaimportuje wszystkie pliki `.json` z katalogu `media/tests`. Po zakończeniu zobaczysz raport weryfikacyjny.

### Krok 3: Posprzątanie

Po pomyślnym imporcie, możesz usunąć lub wykomentować linię `DATABASE_URL` w pliku `.env`, aby znów pracować na lokalnej bazie SQLite.
