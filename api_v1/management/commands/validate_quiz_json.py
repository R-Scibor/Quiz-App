import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from api_v1.quiz_validation import validate_quiz


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

        issues = validate_quiz(data)

        if issues:
            self.stdout.write(self.style.ERROR("\nZnaleziono błędy walidacji:"))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f"- {issue['path']}: {issue['message']}"))
            return

        self.stdout.write(self.style.SUCCESS("Plik JSON przeszedł pomyślnie walidację. Można go zaimportować."))
