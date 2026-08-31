from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .authoring_schema import AUTHORING_SCHEMA
from .models import Category, Question, Test
from .quiz_export import question_to_interchange, test_to_interchange
from .quiz_import import (
    ImportConflictError,
    ImportValidationError,
    TestNotFoundError,
    import_quiz,
)
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


def _parse_dry_run(request) -> bool:
    if "dry_run" in request.query_params:
        value = request.query_params.get("dry_run")
        return str(value).lower() in ("true", "1", "yes")
    value = request.data.get("dry_run")
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in ("true", "1", "yes")


class AuthoringImportView(AuthoringAPIView):
    def post(self, request, *args, **kwargs):
        dry_run = _parse_dry_run(request)
        test_id = request.data.get("test_id") or None
        try:
            result = import_quiz(request.data, test_id=test_id, dry_run=dry_run)
        except ImportValidationError as exc:
            return Response(
                {"error": "VALIDATION_FAILED", "errors": exc.issues},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (TestNotFoundError, ValidationError):
            return Response(
                {"error": "TEST_NOT_FOUND", "message": "Test not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ImportConflictError:
            return Response(
                {"error": "IMPORT_CONFLICT", "message": "Import conflict."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(result, status=status.HTTP_200_OK)


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


class AuthoringTestDetailView(AuthoringAPIView):
    def patch(self, request, pk):
        try:
            test = Test.objects.get(pk=pk)
        except Test.DoesNotExist:
            return Response({"error": "TEST_NOT_FOUND", "message": "Test not found."}, status=404)

        errors = []
        if "scope" in request.data:
            scope = request.data["scope"]
            if not isinstance(scope, str) or not scope.strip():
                errors.append({
                    "path": "scope",
                    "code": "INVALID_TYPE",
                    "message": "'scope' must be a non-empty string.",
                })
            elif len(scope) > 255:
                errors.append({
                    "path": "scope",
                    "code": "INVALID_TYPE",
                    "message": "'scope' must be at most 255 characters.",
                })
            else:
                test.title = scope
        if "version" in request.data:
            version = request.data["version"]
            if not isinstance(version, str):
                errors.append({
                    "path": "version",
                    "code": "INVALID_TYPE",
                    "message": "'version' must be a string.",
                })
            elif len(version) > 32:
                errors.append({
                    "path": "version",
                    "code": "INVALID_TYPE",
                    "message": "'version' must be at most 32 characters.",
                })
            else:
                test.version = version
        if errors:
            return Response(
                {"error": "VALIDATION_FAILED", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if "description" in request.data:
            test.description = request.data["description"]
        test.save()

        if "category" in request.data:
            category_name = request.data["category"] or ""
            if category_name:
                cat, _ = Category.objects.get_or_create(name=category_name)
                test.categories.set([cat])
            else:
                test.categories.clear()

        test = Test.objects.get(pk=test.pk)
        return Response(test_to_interchange(test))
