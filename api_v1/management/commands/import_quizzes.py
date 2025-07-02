import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

# Poprawny import modeli z ich właściwej lokalizacji
from api_v1.models import Category, Tag, Test, Question, Answer
from api_v1.management.commands.validate_quiz_json import Command as ValidateQuizCommand

class Command(BaseCommand):
    """
    Komenda Django do importowania quizów z plików JSON wraz z pełną weryfikacją.
    Obsługuje pytania zamknięte, otwarte oraz linki do obrazków.
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

        self.imported_files = []  # Initialize the list here
        for file_path in tqdm(json_files_to_import, desc="Importowanie quizów"):
            imported = False
            # Uruchamiamy walidację dla każdego pliku
            validator = ValidateQuizCommand()
            validation_errors = validator.validate_quiz_data(self.load_json(file_path))

            if validation_errors:
                self.stdout.write(self.style.ERROR(f"\nBłąd walidacji pliku '{file_path.name}'. Pomijanie importu."))
                for error in validation_errors:
                    self.stdout.write(self.style.ERROR(f"- {error}"))
            else:
                try:
                    self.stdout.write(self.style.SUCCESS(f"\nPlik '{file_path.name}' przeszedł walidację. Rozpoczynanie importu..."))
                    self.import_quiz_from_file(file_path)
                    imported = True
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"\nBłąd podczas importu pliku '{file_path.name}': {e}. Pomijanie."))

            if imported:
                self.imported_files.append(file_path)

        self.stdout.write(self.style.SUCCESS("\nImport zakończony. Rozpoczynanie weryfikacji..."))
        self.verify_import(self.imported_files, len(json_files_to_import))

    def import_quiz_from_file(self, file_path: Path):
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            test_title = data.get('scope', file_path.stem)
            category_name = data.get('category')

            with transaction.atomic():
                category_obj = None
                if category_name:
                    category_obj, _ = Category.objects.get_or_create(name=category_name)

                test_obj, created = Test.objects.update_or_create(
                    title=test_title,
                    defaults={'description': data.get('description', f"Test importowany z pliku {file_path.name}.")}
                )
                if category_obj:
                    test_obj.categories.set([category_obj])

                if not created:
                    test_obj.questions.all().delete()

                tags_cache = {}
                for q_data in data.get('questions', []):
                    q_text = q_data.get('questionText')
                    if not q_text: continue
                    
                    q_type = q_data.get('type', 'single-choice')
                    if q_type not in [Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE, Question.OPEN_ENDED]:
                        q_type = Question.SINGLE_CHOICE

                    question_obj = Question.objects.create(
                        test=test_obj,
                        text=q_text,
                        image=q_data.get('image'), # <-- TUTAJ ZMIANA: Dodajemy import obrazka
                        explanation=q_data.get('explanation', ''),
                        question_type=q_type,
                        grading_criteria=q_data.get('gradingCriteria'),
                        max_points=q_data.get('maxPoints')
                    )

                    tags_to_assign = []
                    for tag_name in q_data.get('tags', []):
                        tag_obj = tags_cache.get(tag_name)
                        if not tag_obj:
                            tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                            tags_cache[tag_name] = tag_obj
                        tags_to_assign.append(tag_obj)
                    if tags_to_assign:
                        question_obj.tags.set(tags_to_assign)

                    if q_type in [Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]:
                        correct_indices = q_data.get('correctAnswers', [])
                        for i, opt_text in enumerate(q_data.get('options', [])):
                            Answer.objects.create(question=question_obj, text=opt_text, is_correct=(i in correct_indices))

        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Błąd: Plik '{file_path.name}' zawiera nieprawidłowy JSON."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Nieoczekiwany błąd importu pliku '{file_path.name}': {e}"))

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
                a_in_json = sum(len(q.get('options', [])) for q in questions_data if q.get('type') != 'open-ended')

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

                    if has_error: all_ok = False
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
