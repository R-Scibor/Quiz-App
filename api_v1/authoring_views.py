from django.conf import settings
from django.db.models import Count, Q
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .authoring_schema import AUTHORING_SCHEMA
from .models import Question, Test
from .quiz_export import question_to_interchange, test_to_interchange
from .quiz_validation import validate_quiz

INSTRUCTIONS_PATH = settings.BASE_DIR / "docs" / "AI_QUIZ_INSTRUCTIONS_GENERIC.md"


class IsStaffAuthor(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        if not request.user.is_staff:
            raise PermissionDenied()
        return True


class AuthoringAPIView(APIView):
    permission_classes = [IsStaffAuthor]
    authentication_classes = [TokenAuthentication]

    def handle_exception(self, exc):
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            return Response(
                {
                    "error": "AUTHENTICATION_FAILED",
                    "message": "Authentication credentials were not provided or are invalid.",
                },
                status=401,
            )
        if isinstance(exc, PermissionDenied):
            return Response(
                {"error": "PERMISSION_DENIED", "message": "Staff access required."},
                status=403,
            )
        return super().handle_exception(exc)


class AuthoringSchemaView(AuthoringAPIView):
    def get(self, request, *args, **kwargs):
        return Response(AUTHORING_SCHEMA, status=status.HTTP_200_OK)


class AuthoringInstructionsView(AuthoringAPIView):
    def get(self, request, *args, **kwargs):
        markdown = INSTRUCTIONS_PATH.read_text(encoding="utf-8")
        return Response({"markdown": markdown}, status=status.HTTP_200_OK)


class AuthoringValidateView(AuthoringAPIView):
    def post(self, request, *args, **kwargs):
        errors = validate_quiz(request.data)
        return Response({"valid": not errors, "errors": errors}, status=status.HTTP_200_OK)


class AuthoringTestListView(AuthoringAPIView):
    def get(self, request):
        tests = Test.objects.annotate(
            total_questions_count=Count("questions"),
            open_questions_count=Count(
                "questions",
                filter=Q(questions__question_type__in=[Question.OPEN_TEXT, Question.OPEN_CLI, Question.OPEN_CODE]),
            ),
            closed_questions_count=Count(
                "questions",
                filter=Q(questions__question_type__in=[Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]),
            ),
        ).prefetch_related("categories")
        payload = []
        for t in tests:
            cat = t.categories.order_by("name").first()
            payload.append({
                "test_id": str(t.id),
                "category": cat.name if cat else "",
                "scope": t.title,
                "version": t.version,
                "description": t.description or "",
                "question_counts": {
                    "open": t.open_questions_count,
                    "closed": t.closed_questions_count,
                    "total": t.total_questions_count,
                },
                "updated_at": t.updated_at.isoformat(),
            })
        return Response(payload)


class AuthoringExportView(AuthoringAPIView):
    def get(self, request, pk):
        try:
            test = Test.objects.get(pk=pk)
        except Test.DoesNotExist:
            return Response({"error": "TEST_NOT_FOUND", "message": "Test not found."}, status=404)
        return Response(test_to_interchange(test))


class AuthoringQuestionDetailView(AuthoringAPIView):
    def get(self, request, pk, question_id):
        try:
            test = Test.objects.get(pk=pk)
        except Test.DoesNotExist:
            return Response({"error": "TEST_NOT_FOUND", "message": "Test not found."}, status=404)
        try:
            question = test.questions.prefetch_related("answers", "tags").get(pk=question_id)
        except Question.DoesNotExist:
            return Response({"error": "QUESTION_NOT_FOUND", "message": "Question not found."}, status=404)
        return Response(question_to_interchange(question))
