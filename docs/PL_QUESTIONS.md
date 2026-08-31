# Poradnik Tworzenia i Importowania Quizów

Niniejszy dokument stanowi kompletny przewodnik po tworzeniu nowych testów w formacie JSON oraz ich importowaniu do bazy danych aplikacji "Quiz App".

---

## 📋 Spis treści

- [Struktura Pliku JSON](#-struktura-pliku-json)
- [Struktura Obiektu Pytania](#-struktura-obiektu-pytania)
  - [Pytanie Zamknięte (Jednokrotnego Wyboru)](#pytanie-zamknięte-jednokrotnego-wyboru)
  - [Pytanie Zamknięte (Wielokrotnego Wyboru)](#pytanie-zamknięte-wielokrotnego-wyboru)
  - [Pytania Otwarte](#pytania-otwarte)
    - [open-text — język naturalny](#open-text--język-naturalny)
    - [open-cli — polecenia terminala](#open-cli--polecenia-terminala)
    - [open-code — programowanie](#open-code--programowanie)
- [Markdown i bloki kodu w treści pytania](#-markdown-i-bloki-kodu-w-treści-pytania)
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

### Pytania Otwarte

Użytkownik wpisuje odpowiedź. Quiz App obsługuje trzy typy otwarte z różnymi ścieżkami oceniania — pełny opis w **[GRADING.md](./GRADING.md)**.

> **Przestarzałe:** Typ `"open-ended"` jest nadal akceptowany (traktowany jako `"open-text"`) i przy imporcie wypisuje ostrzeżenie. W nowych plikach używaj `"open-text"`.

Wszystkie typy otwarte mają te pola i **pomijają** `options` / `correctAnswers`:

| Pole | Wymagane | Opis |
|---|---|---|
| `gradingCriteria` | Tak | Zasady oceniania — treść zależy od typu (patrz niżej) |
| `maxPoints` | Tak | Liczba całkowita 1–100. Przyznane punkty mogą być ułamkiem tej wartości. |

#### `open-text` — język naturalny

Wyjaśnienia, definicje, opisy. Najpierw podobieństwo wektorowe; niejednoznaczne odpowiedzi idą do LLM.

**`gradingCriteria`:** opis poprawnej odpowiedzi językiem naturalnym (baza porównania semantycznego).

```json
{
  "id": 104,
  "questionText": "Wymień i krótko opisz co najmniej trzy skutki Zjazdu Gnieźnieńskiego z 1000 roku.",
  "image": "",
  "type": "open-text",
  "tags": ["zjazd gnieźnieński", "dyplomacja"],
  "gradingCriteria": "Odpowiedź musi zawierać co najmniej trzy z: utworzenie niezależnej polskiej metropolii kościelnej, umocnienie pozycji międzynarodowej Polski, symboliczne uznanie suwerenności przez Cesarstwo.",
  "maxPoints": 6
}
```

#### `open-cli` — polecenia terminala

Oczekiwane polecenie (`kubectl`, `git`, `docker`, `bash`). Dopasowanie regex; brak dopasowania eskaluje do LLM.

**`gradingCriteria`:** wzorzec regex zgodny z Pythonem, dopasowywany do całej odpowiedzi. W JSON ukośniki odwrotne trzeba podwoić (`\\s+`). Regex jest walidowany przy imporcie.

```json
{
  "id": 105,
  "questionText": "Napisz polecenie wypisujące pody w przestrzeni kube-system.",
  "image": "",
  "type": "open-cli",
  "tags": ["kubernetes", "cli"],
  "gradingCriteria": "kubectl\\s+get\\s+(pods|po)(\\s+(-n\\s+|--namespace(=|\\s+))kube-system|\\s+(--all-namespaces|-A))?",
  "maxPoints": 1
}
```

Używany jest `re.fullmatch` (cała odpowiedź) oraz `re.IGNORECASE`. Import odrzuca wzorce z katastrofalnym backtrackingiem.

#### `open-code` — programowanie

Oczekiwany kod. Zawsze oceniane przez LLM z rubryką kodową; możliwa ocena cząstkowa.

**`gradingCriteria`:** musi zaczynać się od identyfikatora języka, dwukropka i opisu zachowania.

```json
{
  "id": 210,
  "questionText": "Napisz funkcję Pythona `add`, która przyjmuje dwie liczby i zwraca ich sumę.",
  "image": "",
  "type": "open-code",
  "tags": ["python", "functions"],
  "gradingCriteria": "python: function named 'add' that accepts two numeric arguments and returns their sum; must handle integers and floats",
  "maxPoints": 3
}
```

---

## 📝 Markdown i bloki kodu w treści pytania

Pola `questionText` i `explanation` obsługują **Markdown**, w tym podświetlane bloki kodu. JSON nie pozwala na dosłowne znaki nowej linii — każdą przerwę wiersza zapisz jako `\n`.

Przykład bloku YAML:

```json
"questionText": "Co konfiguruje ten YAML?\n\n```yaml\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app\nspec:\n  replicas: 3\n```"
```

Wewnątrz stringa JSON dosłowny backslash to `\\`.

---

**WAŻNE:** Przed załadowaniem testów do bazy danych, zaleca się użycie komendy `validate_quiz_json`, aby upewnić się, że pliki są poprawne i nie zawierają błędów.

**Przykład użycia:**

```bash
python manage.py validate_quiz_json media/tests/moj_quiz.json
```

**Przykład użycia (wewnątrz kontenera):**

```bash
docker compose exec web python manage.py validate_quiz_json media/tests/moj_quiz.json
```

## 🚀 Jak Załadować Nowe Testy do Bazy Danych

Poniższa instrukcja opisuje proces dodawania nowych plików `.json` z testami do aplikacji działającej w kontenerach Docker na maszynie wirtualnej (VM).

### Krok 1: Przygotuj pliki na swoim komputerze (PC)

1.  **Stwórz nowe pliki z testami**: Przygotuj swoje nowe testy w formacie `.json`.
2.  **Umieść je w odpowiednim folderze**: Na swoim lokalnym komputerze umieść wszystkie nowe pliki `.json` w folderze `media/tests/` w głównym katalogu projektu.

### Krok 2: Zaimportuj testy do aplikacji (w Dockerze)

Gdy pliki są już na serwerze, musimy powiedzieć Django, żeby je przeczytało i dodało do bazy danych.

1.  **Połącz się z serwerem VM**: Upewnij się, że masz otwarty terminal połączony z Twoją maszyną wirtualną.
2.  **Uruchom komendę importu**: Wykonaj poniższą komendę. Działa ona wewnątrz kontenera `web` i wskazuje na folder, do którego właśnie wysłałeś pliki.

    ```bash
    docker compose exec web python manage.py import_quizzes media/tests
    ```
    **Importowanie pojedynczego pliku:**
    Możesz również załadować pojedynczy plik JSON, podając bezpośrednią ścieżkę do niego:
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests/moj_nowy_quiz.json
    ```
    **Czyszczenie bazy:**
    Jeśli chcesz całkowicie wyczyścić bazę i zaimportować wszystko od nowa, użyj flagi `--clean`:
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests --clean
    ```

3.  **Gotowe!** Twoje nowe testy powinny być już widoczne w aplikacji.
