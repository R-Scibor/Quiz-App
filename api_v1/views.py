import os
import json
import random
from pathlib import Path

from django.conf import settings
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TestMetadataSerializer, QuestionSerializer

class TestListView(APIView):
    """
    Widok API do listowania dostępnych testów.

    Skanuje katalog w poszukiwaniu plików JSON z testami i zwraca
    ich metadane.
    """
    def get(self, request, *args, **kwargs):
        """
        Obsługuje żądania GET.

        Zwraca listę metadanych dla każdego znalezionego pliku testowego.
        """
        tests_dir = Path(settings.MEDIA_ROOT) / 'tests'
        
        available_tests = []
        try:
            if not tests_dir.is_dir():
                return Response([], status=status.HTTP_200_OK)

            for test_file in tests_dir.glob('*.json'):
                with open(test_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        questions = data.get('questions', [])
                        
                        if isinstance(questions, list):
                            question_count = len(questions)
                            
                            metadata = {
                                'category': data.get('category'),
                                'scope': data.get('scope'),
                                'version': data.get('version'),
                                'test_id': test_file.stem,
                                'question_count': question_count
                            }
                            serializer = TestMetadataSerializer(data=metadata)
                            if serializer.is_valid():
                                available_tests.append(serializer.data)
                            else:
                                print(f"Błąd walidacji metadanych w pliku {test_file.name}: {serializer.errors}")
                    except json.JSONDecodeError:
                        print(f"Błąd odczytu pliku JSON: {test_file.name}")
                        continue

            return Response(available_tests, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd: {e}")
            return Response({"error": "Wystąpił wewnętrzny błąd serwera."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuestionListView(APIView):
    """
    Widok API do pobierania listy pytań do testu.

    Ładuje pytania z wybranych plików JSON, losuje je i przygotowuje
    do wyświetlenia w teście.
    """
    def get(self, request, *args, **kwargs):
        """
        Obsługuje żądania GET z parametrami.

        Args:
            request: Obiekt żądania zawierający parametry:
                - `categories`: Lista identyfikatorów testów (nazw plików).
                - `num_questions`: Żądana liczba pytań.
        """
        tests_dir = Path(settings.MEDIA_ROOT) / 'tests'

        categories_str = request.query_params.get('categories')
        num_questions_str = request.query_params.get('num_questions')

        if not categories_str or not num_questions_str:
            return Response(
                {"error": "Parametry 'categories' i 'num_questions' są wymagane."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            num_questions = int(num_questions_str)
            categories = categories_str.split(',')
        except (ValueError, TypeError):
            return Response(
                {"error": "Nieprawidłowy format parametrów."},
                status=status.HTTP_400_BAD_REQUEST
            )

        all_questions = []
        for category_id in categories:
            file_path = tests_dir / f"{category_id}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions_data = data.get('questions', [])
                    all_questions.extend(questions_data)
            else:
                print(f"Ostrzeżenie: Plik testu dla kategorii '{category_id}' nie został znaleziony.")

        if not all_questions:
            return Response({"error": "Nie znaleziono pytań dla wybranych kategorii."}, status=status.HTTP_404_NOT_FOUND)

        if len(all_questions) < num_questions:
            num_questions = len(all_questions)

        selected_questions = random.sample(all_questions, num_questions)
        random.shuffle(selected_questions)

        for question in selected_questions:
            if 'options' in question and isinstance(question['options'], list):
                original_indices = list(range(len(question['options'])))
                indexed_options = list(zip(original_indices, question['options']))
                random.shuffle(indexed_options)
                
                shuffled_indices, shuffled_options = zip(*indexed_options)
                
                question['options'] = list(shuffled_options)
                
                if 'correctAnswers' in question:
                    correct_answers_map = {old_idx: new_idx for new_idx, old_idx in enumerate(shuffled_indices)}
                    question['correctAnswers'] = sorted([correct_answers_map[old_idx] for old_idx in question['correctAnswers']])

        serializer = QuestionSerializer(data=selected_questions, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(f"Błąd serializacji pytań: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReactAppView(TemplateView):
    template_name = 'index.html'