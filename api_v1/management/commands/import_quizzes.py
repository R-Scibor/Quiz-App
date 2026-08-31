import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from api_v1.models import Answer, Category, Tag, Test
from api_v1.quiz_import import ImportConflictError, ImportValidationError, import_quiz
from api_v1.quiz_validation import validate_quiz


class Command(BaseCommand):
    """
    Komenda Django do importowania quizów z plików JSON wraz z pełną weryfikacją.
    """
    help = 'Importuje testy i pytania (w tym otwarte i z obrazkami) z plików JSON i weryfikuje poprawność importu.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Ścieżka do katalogu zawierającego pliki JSON z quizami lub do pojedynczego pliku JSON.')
        parser.add_argument('--clean', action='store_true', help='Usuwa wszystkie istniejące dane przed importem.')

    def handle(self, *args, **options):
        input_path = Path(options['path'])

        if options['clean']:
            self.stdout.write(self.style.WARNING("Rozpoczynanie czyszczenia bazy danych..."))
            Test.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Baza danych została wyczyszczona."))

        json_files_to_import = []
        if input_path.is_file():
            if input_path.suffix.lower() == '.json':
                json_files_to_import.append(input_path)
                self.stdout.write(f"Znaleziono 1 plik JSON do zaimportowania: {input_path.name}")
            else:
                raise CommandError(f"Podana ścieżka '{input_path}' nie jest plikiem JSON.")
        elif input_path.is_dir():
            json_files_to_import = list(input_path.glob('*.json'))
            if not json_files_to_import:
                self.stdout.write(self.style.WARNING(f"W katalogu '{input_path}' nie znaleziono żadnych plików .json."))
                return
            self.stdout.write(f"Znaleziono {len(json_files_to_import)} plików JSON do zaimportowania z katalogu '{input_path}'.")
        else:
            raise CommandError(f"Podana ścieżka '{input_path}' nie jest prawidłowym plikiem ani katalogiem.")

        if not json_files_to_import:
            self.stdout.write(self.style.WARNING("Brak plików JSON do zaimportowania."))
            return

        self.imported_files = []
        for file_path in tqdm(json_files_to_import, desc="Importowanie quizów"):
            try:
                data = self.load_json(file_path)
            except CommandError as e:
                self.stdout.write(self.style.ERROR(f"\n{e}. Pomijanie."))
                continue

            issues = validate_quiz(data)
            if issues:
                self.stdout.write(self.style.ERROR(f"\nBłąd walidacji pliku '{file_path.name}'. Pomijanie importu."))
                for issue in issues:
                    self.stdout.write(self.style.ERROR(f"- {issue['path']}: {issue['message']}"))
                continue

            try:
                self.stdout.write(self.style.SUCCESS(f"\nPlik '{file_path.name}' przeszedł walidację. Rozpoczynanie importu..."))
                import_quiz(data)
                self.imported_files.append(file_path)
            except ImportValidationError as e:
                self.stdout.write(self.style.ERROR(f"\nBłąd walidacji pliku '{file_path.name}'. Pomijanie importu."))
                for issue in e.issues:
                    self.stdout.write(self.style.ERROR(f"- {issue['path']}: {issue['message']}"))
            except ImportConflictError as e:
                self.stdout.write(self.style.ERROR(f"\nBłąd podczas importu pliku '{file_path.name}': {e}. Pomijanie."))

        self.stdout.write(self.style.SUCCESS("\nImport zakończony. Rozpoczynanie weryfikacji..."))
        self.verify_import(self.imported_files, len(json_files_to_import))

    def load_json(self, file_path: Path):
        try:
            with file_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Błąd dekodowania JSON w pliku '{file_path}': {e}")

    def verify_import(self, imported_files: list, total_files: int):
        self.stdout.write("=" * 70)
        self.stdout.write("RAPORT WERYFIKACJI IMPORTU")
        self.stdout.write("=" * 70)

        all_ok = True
        total_q_json, total_q_db = 0, 0
        total_a_json, total_a_db = 0, 0

        for file_path in tqdm(imported_files, desc="Weryfikowanie importu"):
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                test_title = data.get('scope', file_path.stem)
                questions_data = data.get('questions', [])
                q_in_json = len(questions_data)
                open_types = ('open', 'open-ended', 'open-text', 'open-cli', 'open-code')
                a_in_json = sum(len(q.get('options', [])) for q in questions_data if q.get('type') not in open_types)

                total_q_json += q_in_json
                total_a_json += a_in_json

                try:
                    test_obj = Test.objects.get(title=test_title)
                    q_in_db = test_obj.questions.count()
                    a_in_db = Answer.objects.filter(question__test=test_obj).count()

                    total_q_db += q_in_db
                    total_a_db += a_in_db

                    has_error = False
                    if q_in_json != q_in_db:
                        self.stdout.write(self.style.ERROR(f"BŁĄD: '{test_title}' -> Niezgodność pytań! JSON: {q_in_json}, DB: {q_in_db}"))
                        has_error = True

                    if a_in_json != a_in_db:
                        self.stdout.write(self.style.ERROR(f"BŁĄD: '{test_title}' -> Niezgodność odpowiedzi! JSON: {a_in_json}, DB: {a_in_db}"))
                        has_error = True

                    if has_error:
                        all_ok = False
                except Test.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"BŁĄD: Nie znaleziono w DB testu '{test_title}' dla pliku {file_path.name}"))
                    all_ok = False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Krytyczny błąd weryfikacji pliku '{file_path.name}': {e}"))
                all_ok = False

        self.stdout.write("-" * 70)
        self.stdout.write(f"Próbowano zaimportować łącznie {total_files} plików.")
        self.stdout.write(f"Pominięto {total_files - len(imported_files)} plików z powodu błędów walidacji lub importu.")
        self.stdout.write(f"Pomyślnie zaimportowano i zweryfikowano {len(imported_files)} plików.")

        self.stdout.write("-" * 70)
        self.stdout.write("Podsumowanie ogólne:")
        self.stdout.write(f"  - Łączna liczba pytań w JSON: {total_q_json} | w DB: {total_q_db}")
        self.stdout.write(f"  - Łączna liczba odpowiedzi w JSON: {total_a_json} | w DB: {total_a_db}")
        self.stdout.write("-" * 70)

        if all_ok and total_q_json == total_q_db and total_a_json == total_a_db:
            self.stdout.write(self.style.SUCCESS("\nWERDYKT: Pełna zgodność. Wszystkie dane wyglądają na poprawnie zaimportowane."))
        else:
            self.stdout.write(self.style.ERROR("\nWERDYKT: Wykryto rozbieżności. Sprawdź powyższe komunikaty o błędach."))
