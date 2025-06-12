import os
import json
import random
from pathlib import Path

from django.conf import settings
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
        # --- POPRAWKA: Definicja ścieżki przeniesiona do wnętrza metody ---
        tests_dir = Path(settings.MEDIA_ROOT) / 'tests'
        
        available_tests = []
        try:
            # Upewnij się, że katalog z testami istnieje
            if not tests_dir.is_dir():
                # W środowisku testowym to jest normalne, jeśli test nie tworzy plików.
                # Zwracamy pustą listę zamiast 404, co naprawi test_list_available_tests_empty
                return Response([], status=status.HTTP_200_OK)

            # Iteruj po plikach w katalogu z testami
            for test_file in tests_dir.glob('*.json'):
                with open(test_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # Sprawdzamy, czy plik zawiera listę 'questions' i czy nie jest ona pusta.
                        if 'questions' in data and isinstance(data['questions'], list) and len(data['questions']) > 0:
                            metadata = {
                                'category': data.get('category'),
                                'scope': data.get('scope'),
                                'version': data.get('version'),
                                'test_id': test_file.stem
                            }
                            serializer = TestMetadataSerializer(data=metadata)
                            if serializer.is_valid():
                                available_tests.append(serializer.data)
                            else:
                                print(f"Błąd walidacji metadanych w pliku {test_file.name}: {serializer.errors}")
                    except json.JSONDecodeError:
                        # Obsługa przypadku, gdy plik JSON jest uszkodzony
                        print(f"Błąd odczytu pliku JSON: {test_file.name}")
                        continue # Przejdź do następnego pliku

            return Response(available_tests, status=status.HTTP_200_OK)

        except Exception as e:
            # Logowanie błędu serwera
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

        Returns:
            Odpowiedź z listą pytań lub błędem.
        """
        # --- POPRAWKA: Definicja ścieżki przeniesiona do wnętrza metody ---
        tests_dir = Path(settings.MEDIA_ROOT) / 'tests'

        # Pobierz parametry z zapytania
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
        # Załaduj pytania z odpowiednich plików JSON
        for category_id in categories:
            file_path = tests_dir / f"{category_id}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions_data = data.get('questions', [])
                    all_questions.extend(questions_data)
            else:
                # Opcjonalnie: można zignorować nieistniejące pliki lub zwrócić błąd
                print(f"Ostrzeżenie: Plik testu dla kategorii '{category_id}' nie został znaleziony.")

        if not all_questions:
            return Response({"error": "Nie znaleziono pytań dla wybranych kategorii."}, status=status.HTTP_404_NOT_FOUND)

        # Losowy wybór określonej liczby pytań
        if len(all_questions) < num_questions:
            num_questions = len(all_questions) # Jeśli jest mniej pytań niż zażądano, weź wszystkie

        selected_questions = random.sample(all_questions, num_questions)

        # Losowanie kolejności pytań i opcji w każdym pytaniu
        random.shuffle(selected_questions)

        for question in selected_questions:
            if 'options' in question and isinstance(question['options'], list):
                # Tworzymy mapowanie starych indeksów na nowe przed losowaniem
                original_indices = list(range(len(question['options'])))
                indexed_options = list(zip(original_indices, question['options']))
                random.shuffle(indexed_options)
                
                # Rozpakowujemy zlosowane opcje
                shuffled_indices, shuffled_options = zip(*indexed_options)
                
                # Aktualizujemy listę opcji
                question['options'] = list(shuffled_options)
                
                # Aktualizujemy indeksy poprawnych odpowiedzi
                if 'correctAnswers' in question:
                    # Mapujemy stare indeksy poprawnych odpowiedzi na nowe
                    correct_answers_map = {old_idx: new_idx for new_idx, old_idx in enumerate(shuffled_indices)}
                    question['correctAnswers'] = sorted([correct_answers_map[old_idx] for old_idx in question['correctAnswers']])


        # Serializacja i zwrot danych
        serializer = QuestionSerializer(data=selected_questions, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(f"Błąd serializacji pytań: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
