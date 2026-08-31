import os
import json
import random
import logging
import uuid

from django.conf import settings
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Avg, Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.authtoken.models import Token

from datetime import date, timedelta

from .models import Test, Question, Answer, ReportedIssue, QuizSession, QuestionAttempt
from .serializers import (
    TestMetadataSerializer, QuestionSerializer, ReportedIssueSerializer,
    RegisterSerializer, QuizSessionSerializer, QuestionAttemptSerializer,
)
from .tasks import generate_ai_answer
from celery.result import AsyncResult
from backend_project import celery_app

logger = logging.getLogger(__name__)


def shuffle_options(data):
    """Shuffle answer options and remap correctAnswers indices. Works on serialized question data."""
    for question in data:
        if question.get('type') in ['single-choice', 'multiple-choice']:
            options = question.get('options', [])
            correct = question.get('correctAnswers', [])
            if not options:
                continue
            indexed = list(enumerate(options))
            random.shuffle(indexed)
            new_indices_map, shuffled_options = zip(*indexed)
            old_to_new = {old: new for new, old in enumerate(new_indices_map)}
            question['options'] = list(shuffled_options)
            question['correctAnswers'] = sorted([old_to_new[i] for i in correct])
    return data


def compute_next_sr(rating, is_correct, prev_ease, prev_interval, prev_reps):
    """SM-2 algorithm. Returns (interval_days, ease_factor, next_review_date, repetitions)."""
    q = {'easy': 5, 'normal': 3, 'hard': 1}.get(rating, 3)
    if not is_correct:
        q = min(q, 1)

    if q < 3:
        new_reps = 0
        new_interval = 1
    else:
        if prev_reps == 0:
            new_interval = 1
        elif prev_reps == 1:
            new_interval = 6
        else:
            new_interval = round(prev_interval * prev_ease)
        new_reps = prev_reps + 1

    new_ease = max(1.3, prev_ease + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    return new_interval, new_ease, date.today() + timedelta(days=new_interval), new_reps


def _build_study_buckets(user):
    """Returns (latest_map, due_ids, struggling_ids, studied_test_ids).
    latest_map: {question_id: QuestionAttempt} — most recent attempt per question.
    Single query: fetches all attempts ordered by answered_at desc, keeps first per question.
    """
    today = date.today()
    all_attempts = list(
        QuestionAttempt.objects.filter(user=user).order_by('-answered_at')
    )
    latest_map = {}
    for a in all_attempts:
        if a.question_id not in latest_map:
            latest_map[a.question_id] = a

    due_ids = [
        qid for qid, a in latest_map.items()
        if a.sr_next_review and a.sr_next_review <= today
    ]
    struggling_ids = [
        qid for qid, a in latest_map.items()
        if not a.is_correct and qid not in due_ids
    ]
    studied_test_ids = list({a.test_id for a in all_attempts})
    return latest_map, due_ids, struggling_ids, studied_test_ids


class ReactAppView(View):
    """Serves the React app's index.html for all non-API routes."""
    def get(self, request, *args, **kwargs):
        try:
            with open(os.path.join(settings.REACT_APP_BUILD_PATH, 'index.html')) as f:
                return render(request, 'index.html')
        except FileNotFoundError:
            logger.error("React index.html not found at path: %s", settings.REACT_APP_BUILD_PATH)
            return Response(
                {"error": "REACT_APP_NOT_FOUND", "message": "React app index.html was not found."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestListView(APIView):
    """Returns a list of all available tests with question counts."""
    def get(self, request, *args, **kwargs):
        try:
            tests_with_counts = Test.objects.annotate(
                total_questions_count=Count('questions'),
                open_questions_count=Count('questions', filter=Q(questions__question_type__in=[Question.OPEN_TEXT, Question.OPEN_CLI, Question.OPEN_CODE])),
                closed_questions_count=Count('questions', filter=Q(questions__question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]))
            ).prefetch_related('categories')
            serializer = TestMetadataSerializer(tests_with_counts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Unexpected error listing tests from database.")
            return Response(
                {"error": "DB_LIST_ERROR", "message": "Server error while fetching test list."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestionListView(APIView):
    """Returns a randomised list of questions for the selected tests."""
    def get(self, request, *args, **kwargs):
        test_ids_str = request.query_params.get('categories')
        num_questions_str = request.query_params.get('num_questions')
        mode = request.query_params.get('mode', 'mixed').lower()

        if not test_ids_str or not num_questions_str:
            return Response({"error": "MISSING_PARAMETERS", "message": "Parameters 'categories' and 'num_questions' are required."}, status=status.HTTP_400_BAD_REQUEST)

        if mode not in ['open', 'closed', 'mixed']:
            return Response({"error": "INVALID_MODE_PARAMETER", "message": "Parameter 'mode' must be 'open', 'closed', or 'mixed'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            num_questions = int(num_questions_str)
            test_ids = test_ids_str.split(',')
        except (ValueError, TypeError):
            return Response({"error": "INVALID_PARAMETER_FORMAT", "message": "Invalid parameter format."}, status=status.HTTP_400_BAD_REQUEST)

        if not 1 <= num_questions <= 200:
            return Response({"error": "INVALID_PARAMETER_FORMAT", "message": "num_questions must be between 1 and 200."}, status=status.HTTP_400_BAD_REQUEST)

        questions_queryset = Question.objects.filter(test__id__in=test_ids)
        if mode == 'open':
            questions_queryset = questions_queryset.filter(
                question_type__in=[Question.OPEN_TEXT, Question.OPEN_CLI, Question.OPEN_CODE]
            )
        elif mode == 'closed':
            questions_queryset = questions_queryset.filter(question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE])

        questions_queryset = questions_queryset.prefetch_related('answers', 'tags')
        final_questions = questions_queryset.order_by('?')[:num_questions]
        
        if not final_questions:
             return Response({"error": "NO_QUESTIONS_FOUND", "message": f"No questions found for the selected categories in mode '{mode}'."}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuestionSerializer(final_questions, many=True)
        return Response(shuffle_options(serializer.data), status=status.HTTP_200_OK)

class CheckOpenAnswerView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai_grading'

    OPEN_TYPES = {
        Question.OPEN_TEXT,
        Question.OPEN_CLI,
        Question.OPEN_CODE,
        Question.OPEN_ENDED,
    }

    def post(self, request, *args, **kwargs):
        question_id = request.data.get('question')
        user_answer = request.data.get('userAnswer')
        force_llm = bool(request.data.get('forceAI', False))

        if not question_id or not user_answer:
            return Response(
                {"error": "INCOMPLETE_DATA", "message": "Fields 'question' and 'userAnswer' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uuid.UUID(str(question_id))
        except (ValueError, TypeError, AttributeError):
            return Response(
                {"error": "INVALID_PARAMETER_FORMAT", "message": "Field 'question' must be a UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return Response(
                {"error": "QUESTION_NOT_FOUND", "message": "Question not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if question.question_type not in self.OPEN_TYPES:
            return Response(
                {"error": "INVALID_QUESTION_TYPE", "message": "Only open-ended questions can be graded this way."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not question.grading_criteria or not question.max_points:
            return Response(
                {"error": "MISSING_GRADING_CONFIG", "message": "This question has no grading criteria or max points."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = generate_ai_answer.delay(
            user_answer,
            question.grading_criteria,
            question.text,
            question.max_points,
            question.question_type,
            force_llm,
        )
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class GetTaskResultView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        logger.debug(f"GET_TASK_RESULT: Checking result for task_id: {task_id}")
        # Directly query the result backend to avoid any state caching issues
        backend = celery_app.backend
        meta = backend.get_task_meta(task_id)
        logger.debug(f"GET_TASK_RESULT: Raw meta from backend: {meta}")

        if meta:
            task_status = meta.get('status', 'UNKNOWN')
            if task_status == 'FAILURE':
                result = meta.get('result')
                response_data = {
                    "status": "FAILURE",
                    "task_id": task_id,
                    "data": {"error": "TASK_FAILED", "message": str(result) if result else "Grading task failed unexpectedly."},
                }
            else:
                response_data = {
                    "status": task_status,
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
    """Creates a new reported issue for a question or AI grading result."""
    def post(self, request, *args, **kwargs):
        serializer = ReportedIssueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'username': user.username}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'MISSING_CREDENTIALS', 'message': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'INVALID_CREDENTIALS', 'message': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.username}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        is_study_mode = request.data.get('is_study_mode', False)
        session = QuizSession.objects.create(user=request.user, is_study_mode=is_study_mode)
        return Response({'session_id': str(session.id)}, status=status.HTTP_201_CREATED)


class SessionCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            session = QuizSession.objects.get(pk=pk, user=request.user)
        except QuizSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        session.completed_at = timezone.now()
        session.total_questions = request.data.get('total_questions', 0)
        session.correct_count = request.data.get('correct_count', 0)
        session.score_achieved = request.data.get('score_achieved', 0)
        session.score_possible = request.data.get('score_possible', 0)
        session.save()
        return Response(status=status.HTTP_200_OK)


class AttemptCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        attempts_data = request.data if isinstance(request.data, list) else [request.data]
        serializer = QuestionAttemptSerializer(data=attempts_data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from django.db.models import Max
        for data in serializer.validated_data:
            attempt = QuestionAttempt(user=request.user, **data)
            if attempt.difficulty_rating:
                prev = (
                    QuestionAttempt.objects
                    .filter(user=request.user, question=attempt.question)
                    .order_by('-answered_at')
                    .first()
                )
                prev_ease = prev.sr_ease_factor if prev else 2.5
                prev_interval = prev.sr_interval if prev else 1
                prev_reps = prev.sr_repetitions if prev else 0
                interval, ease, next_review, reps = compute_next_sr(
                    attempt.difficulty_rating, attempt.is_correct,
                    prev_ease, prev_interval, prev_reps
                )
                attempt.sr_interval = interval
                attempt.sr_ease_factor = ease
                attempt.sr_next_review = next_review
                attempt.sr_repetitions = reps
            attempt.save()

        return Response(status=status.HTTP_201_CREATED)


class StudyQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        limit = min(int(request.query_params.get('limit', 20)), 50)

        # Optional topic filter: comma-separated test UUIDs
        raw_ids = request.query_params.get('test_ids', '')
        test_id_filter = {tid.strip() for tid in raw_ids.split(',') if tid.strip()} or None

        latest_map, due_ids, struggling_ids, studied_test_ids = _build_study_buckets(user)

        # Apply topic filter to all buckets
        if test_id_filter:
            latest_map = {
                qid: a for qid, a in latest_map.items()
                if str(a.test_id) in test_id_filter
            }
            due_ids = [
                qid for qid, a in latest_map.items()
                if a.sr_next_review and a.sr_next_review <= date.today()
            ]
            struggling_ids = [
                qid for qid, a in latest_map.items()
                if not a.is_correct and qid not in due_ids
            ]
            studied_test_ids = list(test_id_filter)

        attempted_ids = set(latest_map.keys())

        random.shuffle(due_ids)
        random.shuffle(struggling_ids)

        # Build the queue: all due + up to half-remaining struggling + fill rest with new
        selected_ids = list(due_ids)
        remaining = limit - len(selected_ids)

        if remaining > 0:
            take_struggling = min(len(struggling_ids), max(1, remaining // 2))
            selected_ids += struggling_ids[:take_struggling]
            remaining = limit - len(selected_ids)

        # Fetch rated question objects
        rated_questions = list(
            Question.objects.filter(id__in=selected_ids)
            .prefetch_related('answers', 'tags')
        )

        # Fill remainder with unrated (new) questions from studied tests
        new_questions = []
        if remaining > 0 and studied_test_ids:
            new_questions = list(
                Question.objects.filter(test__in=studied_test_ids)
                .exclude(id__in=attempted_ids)
                .prefetch_related('answers', 'tags')
                .order_by('?')[:remaining]
            )

        all_questions = rated_questions + new_questions
        random.shuffle(all_questions)

        serializer = QuestionSerializer(all_questions, many=True)
        return Response({
            'count': len(all_questions),
            'questions': shuffle_options(serializer.data),
        })


class StudyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        latest_map, due_ids, struggling_ids, studied_test_ids = _build_study_buckets(user)
        attempted_ids = set(latest_map.keys())

        new_count = Question.objects.filter(
            test__in=studied_test_ids
        ).exclude(id__in=attempted_ids).count()

        mastered_count = sum(
            1 for a in latest_map.values()
            if a.sr_repetitions >= 4 and a.sr_interval >= 21
        )

        studied_tests = list(
            Test.objects.filter(id__in=studied_test_ids).values('id', 'title')
        )

        total = len(due_ids) + len(struggling_ids) + min(new_count, 20)
        return Response({
            'due_count': len(due_ids),
            'struggling_count': len(struggling_ids),
            'new_count': new_count,
            'mastered_count': mastered_count,
            'total_queued': min(total, 50),
            'studied_tests': studied_tests,
        })


class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        sessions = QuizSession.objects.filter(user=user, completed_at__isnull=False)

        agg = sessions.aggregate(
            total_sessions=Count('id'),
            total_questions=Sum('total_questions'),
            total_score_achieved=Sum('score_achieved'),
            total_score_possible=Sum('score_possible'),
        )
        total_sessions = agg['total_sessions'] or 0
        total_questions = agg['total_questions'] or 0
        total_score_achieved = agg['total_score_achieved'] or 0
        total_score_possible = agg['total_score_possible'] or 0
        overall_accuracy = round((total_score_achieved / total_score_possible * 100), 1) if total_score_possible > 0 else 0

        # Streak: count consecutive days with at least one completed session ending today
        from datetime import date, timedelta
        completed_dates = sorted(set(
            sessions.values_list('completed_at__date', flat=True)
        ), reverse=True)

        current_streak = 0
        longest_streak = 0
        if completed_dates:
            # Current streak
            check = date.today()
            for d in completed_dates:
                if d == check:
                    current_streak += 1
                    check = d - timedelta(days=1)
                elif d == check - timedelta(days=1) and current_streak == 0:
                    # Allow yesterday to start a streak (not broken yet today)
                    current_streak += 1
                    check = d - timedelta(days=1)
                elif d < check:
                    break

            # Longest streak
            streak = 1
            for i in range(1, len(completed_dates)):
                if completed_dates[i - 1] - completed_dates[i] == timedelta(days=1):
                    streak += 1
                    longest_streak = max(longest_streak, streak)
                else:
                    streak = 1
            longest_streak = max(longest_streak, streak)

        # Average time per question (from individual attempts)
        attempt_agg = QuestionAttempt.objects.filter(user=user).aggregate(
            total_time=Sum('time_spent_secs'),
            count=Count('id'),
            open_count=Count(Case(
                When(question__question_type__startswith='open', then=1),
                output_field=IntegerField(),
            )),
            closed_count=Count(Case(
                When(question__question_type__in=['single-choice', 'multiple-choice'], then=1),
                output_field=IntegerField(),
            )),
        )
        total_time = attempt_agg['total_time'] or 0
        attempt_count = attempt_agg['count'] or 0
        avg_time = round(total_time / attempt_count) if attempt_count > 0 else 0
        open_count = attempt_agg['open_count'] or 0
        closed_count = attempt_agg['closed_count'] or 0

        study_sessions = sessions.filter(is_study_mode=True).count()
        regular_sessions = sessions.filter(is_study_mode=False).count()

        recent = sessions.order_by('-started_at')[:20]
        recent_sessions = [
            {
                'id': str(s.id),
                'date': s.completed_at.strftime('%Y-%m-%d'),
                'total_questions': s.total_questions,
                'score_achieved': s.score_achieved,
                'score_possible': s.score_possible,
                'accuracy': round(s.score_achieved / s.score_possible * 100) if s.score_possible > 0 else 0,
            }
            for s in recent
        ]

        return Response({
            'total_sessions': total_sessions,
            'total_questions_answered': total_questions,
            'overall_accuracy': overall_accuracy,
            'current_streak_days': current_streak,
            'longest_streak_days': longest_streak,
            'avg_time_per_question': avg_time,
            'recent_sessions': recent_sessions,
            'questions_by_type': {'closed': closed_count, 'open': open_count},
            'study_sessions': study_sessions,
            'regular_sessions': regular_sessions,
        })


class StatsTestBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        breakdown = (
            QuestionAttempt.objects
            .filter(user=user)
            .values('test__id', 'test__title')
            .annotate(
                total_attempts=Count('id'),
                points_earned=Sum('points_awarded'),
                points_possible=Sum(Coalesce('question__max_points', Value(1))),
                avg_time_secs=Avg('time_spent_secs'),
            )
            .order_by('-total_attempts')[:20]
        )
        data = [
            {
                'test_id': str(row['test__id']),
                'title': row['test__title'],
                'total_attempts': row['total_attempts'],
                'points_earned': row['points_earned'] or 0,
                'points_possible': row['points_possible'] or 0,
                'accuracy': round((row['points_earned'] or 0) / row['points_possible'] * 100, 1) if row['points_possible'] else 0,
                'avg_time_secs': round(row['avg_time_secs']) if row['avg_time_secs'] else 0,
            }
            for row in breakdown
        ]
        return Response(data)
