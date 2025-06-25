import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from tqdm import tqdm

from api_v1.models import Category, Tag, Test, Question, Answer

# -----------------------------------------------------------------------------
# Wprowadzenie do Skryptu Importującego
# -----------------------------------------------------------------------------
#
# Ten skrypt to dedykowana komenda zarządzania Django, zaprojektowana do
# jednorazowego, wydajnego importu danych o quizach z plików JSON do bazy
# danych. Implementuje ona kluczowe założenia z planu migracji:
#
# 1.  **Transakcyjność**: Cały proces importu dla pojedynczego pliku jest
#     opakowany w blok `transaction.atomic`. Gwarantuje to, że albo cały
#     test z pytaniami i odpowiedziami zostanie zaimportowany poprawnie,
#     albo żadne dane z tego pliku nie zostaną zapisane w przypadku błędu.
#
# 2.  **Idempotentność**: Skrypt można uruchamiać wielokrotnie bez ryzyka
#     tworzenia duplikatów. Używa metody `update_or_create` dla Testów,
#     bazując na tytule, oraz `get_or_create` dla Kategorii i Tagów.
#
# 3.  **Pełna Weryfikacja po imporcie**: Po zakończeniu importu skrypt
#     automatycznie uruchamia procedurę weryfikacyjną. Porównuje liczbę
#     pytań ORAZ odpowiedzi w każdym pliku źródłowym z danymi zapisanymi
#     w bazie, dostarczając kompletnego raportu o integralności danych.
#
# 4.  **Obsługa argumentów**: Komenda przyjmuje ścieżkę do folderu z testami
#     oraz opcjonalną flagę `--clean` do wyczyszczenia bazy przed importem.
#
# -----------------------------------------------------------------------------

class Command(BaseCommand):
    """
    Komenda Django do importowania quizów z plików JSON wraz z pełną weryfikacją.
    """
    help = 'Importuje testy, pytania, odpowiedzi, kategorie i tagi z plików JSON i weryfikuje poprawność importu.'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_dir', type=str, help='Ścieżka do katalogu zawierającego pliki JSON z quizami.'
        )
        parser.add_argument(
            '--clean', action='store_true', help='Usuwa wszystkie istniejące dane przed importem.'
        )

    def handle(self, *args, **options):
        json_dir = Path(options['json_dir'])
        if not json_dir.is_dir():
            raise CommandError(f"Podana ścieżka '{json_dir}' nie jest prawidłowym katalogiem.")

        if options['clean']:
            self.stdout.write(self.style.WARNING("Rozpoczynanie czyszczenia bazy danych..."))
            Test.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Baza danych została wyczyszczona."))

        json_files = list(json_dir.glob('*.json'))
        if not json_files:
            self.stdout.write(self.style.WARNING(f"W katalogu '{json_dir}' nie znaleziono żadnych plików .json."))
            return

        self.stdout.write(f"Znaleziono {len(json_files)} plików JSON do zaimportowania.")

        for file_path in tqdm(json_files, desc="Importowanie quizów"):
            self.import_quiz_from_file(file_path)

        self.stdout.write(self.style.SUCCESS("\nImport zakończony. Rozpoczynanie weryfikacji..."))
        self.verify_import(json_files)

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

                    question_obj = Question.objects.create(
                        test=test_obj, text=q_text, explanation=q_data.get('explanation', ''),
                        is_multiple_choice=(q_data.get('type') == 'multiple-choice')
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

                    correct_indices = q_data.get('correctAnswers', [])
                    for i, opt_text in enumerate(q_data.get('options', [])):
                        Answer.objects.create(question=question_obj, text=opt_text, is_correct=(i in correct_indices))

        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Błąd: Plik '{file_path.name}' zawiera nieprawidłowy JSON."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Nieoczekiwany błąd importu pliku '{file_path.name}': {e}"))

    def verify_import(self, json_files: list):
        self.stdout.write("=" * 70)
        self.stdout.write("RAPORT WERYFIKACJI IMPORTU")
        self.stdout.write("=" * 70)

        all_ok = True
        total_q_json, total_q_db = 0, 0
        total_a_json, total_a_db = 0, 0

        for file_path in tqdm(json_files, desc="Weryfikowanie importu"):
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                test_title = data.get('scope', file_path.stem)
                
                # Zlicz pytania i odpowiedzi w pliku JSON
                questions_data = data.get('questions', [])
                q_in_json = len(questions_data)
                a_in_json = sum(len(q.get('options', [])) for q in questions_data)

                total_q_json += q_in_json
                total_a_json += a_in_json

                try:
                    test_obj = Test.objects.get(title=test_title)
                    # Zlicz pytania i odpowiedzi w bazie danych dla danego testu
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
        self.stdout.write("Podsumowanie ogólne:")
        self.stdout.write(f"  - Łączna liczba pytań w JSON: {total_q_json} | w DB: {total_q_db}")
        self.stdout.write(f"  - Łączna liczba odpowiedzi w JSON: {total_a_json} | w DB: {total_a_db}")
        self.stdout.write("-" * 70)

        if all_ok and total_q_json == total_q_db and total_a_json == total_a_db:
            self.stdout.write(self.style.SUCCESS("\nWERDYKT: Pełna zgodność. Wszystkie dane wyglądają na poprawnie zaimportowane."))
        else:
            self.stdout.write(self.style.ERROR("\nWERDYKT: Wykryto rozbieżności. Sprawdź powyższe komunikaty o błędach."))
