import os
import json
import random
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.views.generic import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TestMetadataSerializer, QuestionSerializer

class ReactAppView(View):
    """
    Widok serwujący główny plik index.html aplikacji React.
    To pozwala na obsługę routingu po stronie klienta przez React Router.
    """
    def get(self, request, *args, **kwargs):
        try:
            # Zakładamy, że REACT_APP_BUILD_PATH jest zdefiniowane w settings.py
            # i wskazuje na folder, gdzie znajduje się build aplikacji React.
            with open(os.path.join(settings.REACT_APP_BUILD_PATH, 'index.html')) as f:
                return render(request, 'index.html')
        except FileNotFoundError:
            return Response(
                {"error": "Plik index.html aplikacji React nie został znaleziony."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestListView(APIView):
    """
    Widok API do listowania dostępnych testów.

    Skanuje katalog w poszukiwaniu plików JSON z testami i zwraca
    ich metadane, włącznie ze szczegółowym podziałem na typy pytań.
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
                        
                        question_counts = {'closed': 0, 'open': 0, 'total': 0}
                        if isinstance(questions, list):
                            question_counts['total'] = len(questions)
                            for question in questions:
                                q_type = question.get('type')
                                if q_type == 'open-ended':
                                    question_counts['open'] += 1
                                elif q_type in ['single-choice', 'multiple-choice']:
                                    question_counts['closed'] += 1
                        
                        metadata = {
                            'category': data.get('category'),
                            'scope': data.get('scope'),
                            'version': data.get('version'),
                            'test_id': test_file.stem,
                            'question_counts': question_counts
                        }
                        serializer = TestMetadataSerializer(data=metadata)
                        if serializer.is_valid():
                            available_tests.append(serializer.data)
                        else:
                            # W środowisku produkcyjnym lepiej logować do pliku
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

    Ładuje pytania z wybranych plików JSON, filtruje je wg trybu (mode),
    losuje i przygotowuje do wyświetlenia w teście.
    """
    def get(self, request, *args, **kwargs):
        """
        Obsługuje żądania GET z parametrami.

        Args:
            request: Obiekt żądania zawierający parametry:
                - `categories`: Lista identyfikatorów testów (nazw plików).
                - `num_questions`: Żądana liczba pytań.
                - `mode`: Tryb pytań ('open', 'closed', 'mixed'). Domyślnie 'mixed'.
        """
        tests_dir = Path(settings.MEDIA_ROOT) / 'tests'

        categories_str = request.query_params.get('categories')
        num_questions_str = request.query_params.get('num_questions')
        mode = request.query_params.get('mode', 'mixed').lower() # Domyślnie 'mixed'

        if not categories_str or not num_questions_str:
            return Response(
                {"error": "Parametry 'categories' i 'num_questions' są wymagane."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if mode not in ['open', 'closed', 'mixed']:
            return Response(
                {"error": "Parametr 'mode' musi mieć wartość 'open', 'closed' lub 'mixed'."},
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
        
        # --- NOWA LOGIKA FILTROWANIA ---
        filtered_questions = []
        if mode == 'mixed':
            filtered_questions = all_questions
        elif mode == 'open':
            filtered_questions = [q for q in all_questions if q.get('type') == 'open-ended']
        elif mode == 'closed':
            filtered_questions = [q for q in all_questions if q.get('type') in ['single-choice', 'multiple-choice']]
        # --- KONIEC NOWEJ LOGIKI ---

        if not filtered_questions:
            return Response({"error": f"Nie znaleziono pytań dla wybranych kategorii w trybie '{mode}'."}, status=status.HTTP_404_NOT_FOUND)

        if len(filtered_questions) < num_questions:
            num_questions = len(filtered_questions)

        selected_questions = random.sample(filtered_questions, num_questions)
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
        
class CheckOpenAnswerView(APIView):
    """
    Widok API do sprawdzania odpowiedzi na pytania otwarte przy użyciu AI Gemini.
    """
    def post(self, request, *args, **kwargs):
        """
        Obsługuje żądania POST z odpowiedzią użytkownika do oceny.
        """
        # Pobranie klucza API ze zmiennych środowiskowych
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return Response(
                {"error": "Klucz API Gemini nie jest skonfigurowany na serwerze."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
             return Response(
                {"error": f"Błąd konfiguracji Gemini: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Odbiór danych z frontendu
        user_answer = request.data.get('userAnswer')
        grading_criteria = request.data.get('gradingCriteria')
        question_text = request.data.get('questionText')
        max_points = request.data.get('maxPoints')

        if not all([user_answer, grading_criteria, question_text, max_points]):
            return Response(
                {"error": "Brak wszystkich wymaganych pól: userAnswer, gradingCriteria, questionText, maxPoints."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Zbudowanie precyzyjnego promptu dla AI
        prompt = f"""
        Jesteś precyzyjnym i surowym nauczycielem oceniającym odpowiedź na pytanie w quizie. Twoim zadaniem jest ocenić odpowiedź użytkownika, bazując na podanych kryteriach oceniania.

        Oto szczegóły:
        1. Pytanie: "{question_text}"
        2. Kryteria Oceniania: "{grading_criteria}"
        3. Maksymalna liczba punktów do zdobycia za to pytanie: {max_points}
        4. Odpowiedź Użytkownika: "{user_answer}"

        Twoje zadania:
        - Oceń, w jakim stopniu odpowiedź użytkownika spełnia kryteria oceniania.
        - Przyznaj liczbę punktów od 0 do {max_points}. Bądź sprawiedliwy, ale wymagający. Nie przyznawaj punktów, jeśli odpowiedź nie odnosi się do kryteriów.
        - Napisz krótkie, jedno- lub dwuzdaniowe uzasadnienie swojej oceny w języku polskim, wyjaśniając, dlaczego przyznałeś tyle punktów (np. co było dobrze, a czego zabrakło).

        Zwróć swoją ocenę jako idealnie sformatowany obiekt JSON. Bez żadnych dodatkowych znaków, komentarzy czy formatowania markdown. JSON musi zawierać DOKŁADNIE dwa klucze:
        - "score" (typu integer)
        - "feedback" (typu string)

        Przykład idealnej odpowiedzi JSON:
        {{
            "score": 7,
            "feedback": "Odpowiedź jest w większości poprawna i odnosi się do kluczowych aspektów z kryteriów, jednak brakuje w niej wspomnienia o wpływie na gospodarkę."
        }}
        """

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            ai_response = model.generate_content(prompt)

            # Czyszczenie odpowiedzi i próba parsowania JSON
            cleaned_text = ai_response.text.strip().replace('```json', '').replace('```', '').strip()
            
            response_json = json.loads(cleaned_text)

            # Walidacja, czy odpowiedź zawiera wymagane klucze
            if 'score' not in response_json or 'feedback' not in response_json:
                 raise ValueError("Odpowiedź AI nie zawiera wymaganych kluczy 'score' i 'feedback'.")

            return Response(response_json, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            print(f"Błąd parsowania JSON z odpowiedzi AI. Surowa odpowiedź: {ai_response.text}")
            return Response({"error": "Otrzymano nieprawidłowy format odpowiedzi od AI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd podczas komunikacji z AI: {e}")
            return Response({"error": "Wystąpił wewnętrzny błąd serwera podczas komunikacji z AI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
