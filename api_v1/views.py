import os
import json
import random
import logging

from django.conf import settings
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import google.generativeai as genai

# Importujemy nowe serializery i modele
from .models import Test, Question, Answer, ReportedIssue
from .serializers import TestMetadataSerializer, QuestionSerializer, ReportedIssueSerializer
from .tasks import generate_ai_answer
from celery.result import AsyncResult
from backend_project import celery_app

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Wprowadzenie do Widoków
# -----------------------------------------------------------------------------
#
# Widoki zostały przepisane, aby w pełni korzystać z bazy danych, co
# radykalnie zwiększa wydajność i elastyczność w porównaniu do operacji
# na plikach.
#
# Kluczowe zmiany:
#
# 1.  **ORM Django zamiast Plików**: Cała logika pobierania danych została
#     zastąpiona zapytaniami do bazy danych za pomocą ORM Django.
#
# 2.  **Optymalizacja Zapytań**:
#     - `prefetch_related`: Używane do "dociągania" powiązanych obiektów
#       (np. odpowiedzi i tagów dla pytań) w jednym dodatkowym zapytaniu,
#       co eliminuje problem "N+1" i drastycznie przyspiesza działanie.
#     - `annotate`: Używane w `TestListView` do obliczania liczby pytañ
#       bezpośrednio w zapytaniu do bazy danych, co jest niezwykle wydajne.
#
# 3.  **Logika Biznesowa**: Logika filtrowania pytań ('open', 'closed', 'mixed')
#     i losowania została zaimplementowana przy użyciu metod ORM, takich
#     jak `.filter()`, `.order_by('?')` i `Q objects`.
#
# 4.  **Kompatybilność**: Mimo całkowitej zmiany backendu, widoki używają
#     serializerów, aby zwracać dane w formacie identycznym z poprzednią
#     wersją, zapewniając pełną kompatybilność z istniejącym frontendem.
#
# -----------------------------------------------------------------------------


class ReactAppView(View):
    """
    Widok serwujący główny plik index.html aplikacji React.
    Pozostaje bez zmian.
    """
    def get(self, request, *args, **kwargs):
        try:
            with open(os.path.join(settings.REACT_APP_BUILD_PATH, 'index.html')) as f:
                return render(request, 'index.html')
        except FileNotFoundError:
            logger.error("Nie znaleziono pliku index.html aplikacji React w ścieżce: %s", settings.REACT_APP_BUILD_PATH)
            return Response(
                {"error": "REACT_APP_NOT_FOUND", "message": "Plik index.html aplikacji React nie został znaleziony."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestListView(APIView):
    """
    Widok API do listowania dostępnych testów, teraz oparty na bazie danych.
    """
    def get(self, request, *args, **kwargs):
        try:
            # Używamy adnotacji, aby baza danych sama policzyła nam pytania
            # dla każdego testu. Jest to bardzo wydajne.
            tests_with_counts = Test.objects.annotate(
                total_questions_count=Count('questions'),
                open_questions_count=Count('questions', filter=Q(questions__question_type=Question.OPEN_ENDED)),
                closed_questions_count=Count('questions', filter=Q(questions__question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]))
            ).prefetch_related('categories')

            # Przekazujemy queryset do serializera
            serializer = TestMetadataSerializer(tests_with_counts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Wystąpił nieoczekiwany błąd podczas listowania testów z bazy danych.")
            return Response(
                {"error": "DB_LIST_ERROR", "message": "Wystąpił błąd serwera podczas pobierania listy testów."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestionListView(APIView):
    """
    Widok API do pobierania listy pytań do testu z bazy danych.
    """
    def get(self, request, *args, **kwargs):
        test_ids_str = request.query_params.get('categories')
        num_questions_str = request.query_params.get('num_questions')
        mode = request.query_params.get('mode', 'mixed').lower()

        if not test_ids_str or not num_questions_str:
            return Response({"error": "MISSING_PARAMETERS", "message": "Parametry 'categories' i 'num_questions' są wymagane."}, status=status.HTTP_400_BAD_REQUEST)
        
        if mode not in ['open', 'closed', 'mixed']:
            return Response({"error": "INVALID_MODE_PARAMETER", "message": "Parametr 'mode' musi mieć wartość 'open', 'closed' lub 'mixed'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            num_questions = int(num_questions_str)
            test_ids = test_ids_str.split(',')
        except (ValueError, TypeError):
            return Response({"error": "INVALID_PARAMETER_FORMAT", "message": "Nieprawidłowy format parametrów."}, status=status.HTTP_400_BAD_REQUEST)

        # Budujemy queryset pytań na podstawie wybranych testów (ich ID)
        questions_queryset = Question.objects.filter(test__id__in=test_ids)

        # Filtrujemy pytania zgodnie z wybranym trybem ('mode')
        if mode == 'open':
            questions_queryset = questions_queryset.filter(question_type=Question.OPEN_ENDED)
        elif mode == 'closed':
            questions_queryset = questions_queryset.filter(question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE])

        # Optymalizacja: pobieramy z góry powiązane odpowiedzi i tagi
        questions_queryset = questions_queryset.prefetch_related('answers', 'tags')

        # Losujemy zadaną liczbę pytañ. `order_by('?')` jest kluczowe.
        final_questions = questions_queryset.order_by('?')[:num_questions]
        
        if not final_questions:
             return Response({"error": "NO_QUESTIONS_FOUND", "message": f"Nie znaleziono pytań dla wybranych kategorii w trybie '{mode}'."}, status=status.HTTP_404_NOT_FOUND)

        # Serializer zajmie się resztą, włącznie z tasowaniem odpowiedzi wewnątrz pytania
        serializer = QuestionSerializer(final_questions, many=True)
        
        # Opcjonalne: Ręczne tasowanie opcji, aby idealnie naśladować starą logikę.
        # To zapewnia 100% kompatybilność z frontendem bez żadnych zmian po jego stronie.
        shuffled_data = self.shuffle_options_in_serialized_data(serializer.data)

        return Response(shuffled_data, status=status.HTTP_200_OK)

    def shuffle_options_in_serialized_data(self, data):
        """
        Tasuje opcje wewnątrz każdego pytania i aktualizuje indeksy
        poprawnych odpowiedzi. Działa na danych już po serializacji.
        """
        for question in data:
            if question.get('type') in ['single-choice', 'multiple-choice']:
                options = question.get('options', [])
                correct_answers_indices = question.get('correctAnswers', [])

                if not options:
                    continue

                # Tworzymy listę par (stary_indeks, tekst_opcji)
                indexed_options = list(enumerate(options))
                random.shuffle(indexed_options)

                # Rozpakowujemy potasowane pary
                new_indices_map, shuffled_options = zip(*indexed_options)
                
                # Tworzymy mapowanie stary_indeks -> nowy_indeks
                old_to_new_index_map = {old_idx: new_idx for new_idx, old_idx in enumerate(new_indices_map)}

                # Aktualizujemy dane pytania
                question['options'] = list(shuffled_options)
                question['correctAnswers'] = sorted([old_to_new_index_map[old_idx] for old_idx in correct_answers_indices])

        return data

class CheckOpenAnswerView(APIView):
    def post(self, request, *args, **kwargs):
        user_answer = request.data.get('userAnswer')
        grading_criteria = request.data.get('gradingCriteria')
        question_text = request.data.get('questionText')
        max_points = request.data.get('maxPoints')

        if not all([user_answer, grading_criteria, question_text, max_points]):
            return Response({"error": "INCOMPLETE_DATA", "message": "Brak wszystkich wymaganych pól."}, status=status.HTTP_400_BAD_REQUEST)

        task = generate_ai_answer.delay(user_answer, grading_criteria, question_text, max_points) # type: ignore
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class GetTaskResultView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        logger.debug(f"GET_TASK_RESULT: Checking result for task_id: {task_id}")
        # Directly query the result backend to avoid any state caching issues
        backend = celery_app.backend
        meta = backend.get_task_meta(task_id)
        logger.debug(f"GET_TASK_RESULT: Raw meta from backend: {meta}")

        if meta:
            response_data = {
                "status": meta.get('status', 'UNKNOWN'),
                "task_id": task_id,
                "data": meta.get('result')
            }
        else:
            # If there's no metadata, the task is likely still pending or unknown
            response_data = {
                "status": "PENDING",
                "task_id": task_id,
                "data": None
            }
        
        logger.debug(f"GET_TASK_RESULT: Sending response: {response_data}")
        return Response(response_data, status=status.HTTP_200_OK)


class ReportIssueView(APIView):
    """
    Widok API do tworzenia nowego zgłoszenia problemu.
    """
    def post(self, request, *args, **kwargs):
        serializer = ReportedIssueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

