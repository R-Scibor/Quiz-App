import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Weryfikuje plik JSON z quizem pod kątem kompletności i poprawności struktury danych.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validation_errors = []

    def _add_error(self, message):
        self.validation_errors.append(message)

    def _format_question_error(self, index, question_id, message):
        if question_id != 'brak_id':
            return f"Pytanie {index + 1} (id: {question_id}): {message}"
        else:
            return f"Pytanie {index + 1}: {message}"

    def _validate_required_fields(self, data, required_fields, object_name="obiektu"):
        for field in required_fields:
            if field not in data:
                self._add_error(f"Brak klucza '{field}' w {object_name}.")

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
            self.stdout.write(self.style.ERROR("\nZnaleziono błędy walidacji:"))
            for error in validation_errors:
                self.stdout.write(self.style.ERROR(f"- {error}"))
            return

        self.stdout.write(self.style.SUCCESS("Plik JSON przeszedł pomyślnie walidację. Można go zaimportować."))

    def validate_quiz_data(self, data):
        self.validation_errors = []  # Reset errors for each file

        self._validate_required_fields(data, ['scope', 'category', 'questions'], "quizu")

        if 'questions' in data and not isinstance(data['questions'], list):
            self._add_error("Klucz 'questions' musi zawierać listę pytań.")

        # Walidacja pytań
        for i, question in enumerate(data.get('questions', [])):
            self.validate_question(question, i)

        return self.validation_errors

    def validate_question(self, question, index):
        if not isinstance(question, dict):
            self._add_error(f"Pytanie {index + 1}: Nie jest obiektem JSON.")
            return  # Dalej nie ma sensu sprawdzać

        question_id = question.get('id', 'brak_id')
        error_prefix = self._format_question_error(index, question_id, "")

        self._validate_required_fields(question, ['questionText', 'type'], error_prefix.strip())

        if 'type' in question:
            q_type = question['type']
            if q_type not in ['single-choice', 'multiple-choice', 'open-ended']:
                self._add_error(f"{error_prefix}Nieprawidłowy typ pytania ('{q_type}').")

            if q_type in ['single-choice', 'multiple-choice']:
                self._validate_required_fields(question, ['options', 'correctAnswers'], error_prefix.strip())

                if 'options' in question and (not isinstance(question['options'], list) or len(question['options']) < 2):
                    self._add_error(f"{error_prefix}Opcje odpowiedzi ('options') muszą być listą z co najmniej 2 elementami.")

                if 'correctAnswers' in question:
                    if not isinstance(question['correctAnswers'], list) or not question['correctAnswers']:
                        self._add_error(f"{error_prefix}Należy wskazać prawidłowe odpowiedzi ('correctAnswers') w formie niepustej listy.")
                    else:
                        if q_type == 'single-choice' and len(question['correctAnswers']) != 1:
                            self._add_error(f"{error_prefix}Dla pytania jednokrotnego wyboru musi być dokładnie 1 prawidłowa odpowiedź.")
                        if 'options' in question and isinstance(question['options'], list):
                            for correct_index in question['correctAnswers']:
                                if not isinstance(correct_index, int) or not 0 <= correct_index < len(question['options']):
                                    self._add_error(f"{error_prefix}Nieprawidłowy indeks prawidłowej odpowiedzi: {correct_index}.")

            elif q_type == 'open-ended':
                self._validate_required_fields(question, ['gradingCriteria', 'maxPoints'], error_prefix.strip())

        # Validate optional fields
        if 'explanation' in question and not isinstance(question['explanation'], str):
            self._add_error(f"{error_prefix}Pole 'explanation' powinno być ciągiem znaków.")

        if 'image' in question and not isinstance(question['image'], str):
            self._add_error(f"{error_prefix}Pole 'image' (ścieżka do obrazka) powinno być ciągiem znaków.")

        if 'tags' in question and not isinstance(question['tags'], list):
            self._add_error(f"{error_prefix}Pole 'tags' powinno być listą.")