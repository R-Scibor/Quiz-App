import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Weryfikuje plik JSON z quizem pod kątem kompletności i poprawności struktury danych.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Ścieżka do pliku JSON z quizem.')

    def handle(self, *args, **options):
        file_path = Path(options['path'])

        if not file_path.is_file() or file_path.suffix.lower() != '.json':
            raise CommandError(f"Podana ścieżka '{file_path}' nie wskazuje na prawidłowy plik JSON.")

        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Błąd dekodowania JSON w pliku '{file_path}': {e}")

        validation_errors = self.validate_quiz_data(data)

        if validation_errors:
            self.stdout.write(self.style.ERROR("Znaleziono błędy walidacji:"))
            for error in validation_errors:
                self.stdout.write(self.style.ERROR(f"- {error}"))
            return

        self.stdout.write(self.style.SUCCESS("Plik JSON przeszedł pomyślnie walidację. Można go zaimportować."))

    def validate_quiz_data(self, data):
        errors = []

        # Sprawdzenie podstawowych pól quizu
        if 'scope' not in data:
            errors.append("Brak klucza 'scope' (nazwa quizu).")
        if 'category' not in data:
            errors.append("Brak klucza 'category' (kategoria quizu).")
        if 'questions' not in data or not isinstance(data['questions'], list):
            errors.append("Brak klucza 'questions' lub nie jest listą.")

        # Walidacja pytań
        for i, question in enumerate(data.get('questions', [])):
            q_errors = self.validate_question(question, i)
            errors.extend(q_errors)

        return errors

    def validate_question(self, question, index):
        errors = []

        if not isinstance(question, dict):
            errors.append(f"Pytanie {index + 1}: Nie jest obiektem JSON.")
            return errors  # Dalej nie ma sensu sprawdzać

        if 'questionText' not in question:
            errors.append(f"Pytanie {index + 1}: Brak treści pytania ('questionText').")
        if 'type' not in question:
            errors.append(f"Pytanie {index + 1}: Brak typu pytania ('type').")
        elif question['type'] not in ['single-choice', 'multiple-choice', 'open-ended']:
            errors.append(f"Pytanie {index + 1}: Nieprawidłowy typ pytania ('{question['type']}').")

        # Dodatkowe sprawdzenia w zależności od typu pytania
        if question.get('type') in ['single-choice', 'multiple-choice']:
            if 'options' not in question or not isinstance(question['options'], list) or len(question['options']) < 2:
                errors.append(f"Pytanie {index + 1}: Brak opcji odpowiedzi ('options'), nie jest listą lub ma mniej niż 2 opcje.")
            if 'correctAnswers' not in question or not isinstance(question['correctAnswers'], list) or not question['correctAnswers']:
                errors.append(f"Pytanie {index + 1}: Brak wskazania prawidłowych odpowiedzi ('correctAnswers'), nie jest listą lub jest pusta.")
            else:
                if question['type'] == 'single-choice' and len(question['correctAnswers']) != 1:
                    errors.append(f"Pytanie {index + 1}: Dla pytania jednokrotnego wyboru musi być dokładnie 1 prawidłowa odpowiedź.")
                for correct_index in question['correctAnswers']:
                    if not isinstance(correct_index, int) or not 0 <= correct_index < len(question.get('options', [])):
                        errors.append(f"Pytanie {index + 1}: Nieprawidłowy indeks prawidłowej odpowiedzi ({correct_index}).")
        elif question.get('type') == 'open-ended':
            if 'gradingCriteria' not in question:
                errors.append(f"Pytanie {index + 1}: Brak kryteriów oceny dla pytania otwartego ('gradingCriteria').")
            if 'maxPoints' not in question:
                errors.append(f"Pytanie {index + 1}: Brak maksymalnej liczby punktów ('maxPoints') dla pytania otwartego.")

        # Sprawdzenia opcjonalnych, ale potencjalnie ważnych pól
        if 'explanation' in question and not isinstance(question['explanation'], str):
            errors.append(f"Pytanie {index + 1}: Pole 'explanation' powinno być ciągiem znaków.")
        if 'image' in question and not isinstance(question['image'], str):
            errors.append(f"Pytanie {index + 1}: Pole 'image' (ścieżka do obrazka) powinno być ciągiem znaków.")
        if 'tags' in question and not isinstance(question['tags'], list):
            errors.append(f"Pytanie {index + 1}: Pole 'tags' powinno być listą.")

        return errors