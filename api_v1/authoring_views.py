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
    DeleteBlockedError,
    ImportConflictError,
    ImportValidationError,
    TestNotFoundError,
    create_question,
    create_questions,
    delete_question,
    import_quiz,
    update_question,
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


class AuthoringSearchView(AuthoringAPIView):
    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < 2:
            return Response(
                {
                    "error": "VALIDATION_FAILED",
                    "errors": [{
                        "path": "q",
                        "code": "INVALID_TYPE",
                        "message": "'q' must be at least 2 characters.",
                    }],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            limit = int(request.query_params.get("limit") or 20)
        except (TypeError, ValueError):
            limit = 20
        limit = min(max(limit, 1), 50)

        test_match = (
            Q(title__icontains=query)
            | Q(categories__name__icontains=query)
            | Q(questions__text__icontains=query)
            | Q(questions__tags__name__icontains=query)
        )
        tests = (
            Test.objects.filter(test_match)
            .distinct()
            .prefetch_related("categories")
            .order_by("title")[:limit]
        )
        test_rows = []
        for test in tests:
            cat = test.categories.order_by("name").first()
            test_rows.append({
                "test_id": str(test.id),
                "category": cat.name if cat else "",
                "scope": test.title,
                "version": test.version,
            })

        question_match = (
            Q(text__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(test__title__icontains=query)
            | Q(test__categories__name__icontains=query)
        )
        questions = Question.objects.filter(question_match).distinct()
        test_id = (request.query_params.get("test_id") or "").strip()
        if test_id:
            questions = questions.filter(test_id=test_id)
        tag = (request.query_params.get("tag") or "").strip()
        if tag:
            questions = questions.filter(tags__name=tag)
        questions = (
            questions.select_related("test")
            .prefetch_related("tags", "test__categories")
            .order_by("test__title", "source_id")[:limit]
        )
        question_rows = []
        for question in questions:
            question_rows.append({
                "test_id": str(question.test_id),
                "scope": question.test.title,
                "question_id": str(question.id),
                "id": question.source_id,
                "questionText": question.text,
                "type": question.question_type,
                "tags": [t.name for t in question.tags.all()],
                "retired": question.retired,
            })
        return Response({"tests": test_rows, "questions": question_rows})


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
            retired_questions_count=Count("questions", filter=Q(questions__retired=True)),
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
                    "retired": t.retired_questions_count,
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


def _question_payload(request) -> dict:
    data = request.data
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k != "dry_run"}


class AuthoringQuestionCreateView(AuthoringAPIView):
    def post(self, request, pk):
        try:
            test = Test.objects.get(pk=pk)
        except (Test.DoesNotExist, ValidationError):
            return Response({"error": "TEST_NOT_FOUND", "message": "Test not found."}, status=404)
        dry_run = _parse_dry_run(request)
        try:
            result = create_question(test, _question_payload(request), dry_run=dry_run)
        except ImportValidationError as exc:
            return Response(
                {"error": "VALIDATION_FAILED", "errors": exc.issues},
                status=status.HTTP_400_BAD_REQUEST,
            )
        code = status.HTTP_200_OK if dry_run else status.HTTP_201_CREATED
        return Response(result, status=code)


class AuthoringQuestionBatchView(AuthoringAPIView):
    def post(self, request, pk):
        try:
            test = Test.objects.get(pk=pk)
        except (Test.DoesNotExist, ValidationError):
            return Response({"error": "TEST_NOT_FOUND", "message": "Test not found."}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        try:
            result = create_questions(test, body.get("questions"), dry_run=_parse_dry_run(request))
        except ImportValidationError as exc:
            return Response(
                {"error": "VALIDATION_FAILED", "errors": exc.issues},
                status=status.HTTP_400_BAD_REQUEST,
            )
        code = status.HTTP_200_OK if _parse_dry_run(request) else status.HTTP_201_CREATED
        return Response(result, status=code)


class AuthoringQuestionWriteView(AuthoringAPIView):
    def _get_question(self, question_id):
        try:
            return Question.objects.prefetch_related("answers", "tags").get(pk=question_id)
        except (Question.DoesNotExist, ValidationError):
            return None

    def patch(self, request, question_id):
        question = self._get_question(question_id)
        if question is None:
            return Response(
                {"error": "QUESTION_NOT_FOUND", "message": "Question not found."},
                status=404,
            )
        dry_run = _parse_dry_run(request)
        try:
            result = update_question(question, _question_payload(request), dry_run=dry_run)
        except ImportValidationError as exc:
            return Response(
                {"error": "VALIDATION_FAILED", "errors": exc.issues},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request, question_id):
        question = self._get_question(question_id)
        if question is None:
            return Response(
                {"error": "QUESTION_NOT_FOUND", "message": "Question not found."},
                status=404,
            )
        dry_run = _parse_dry_run(request)
        try:
            result = delete_question(question, dry_run=dry_run)
        except DeleteBlockedError as exc:
            return Response(
                {
                    "error": "DELETE_BLOCKED",
                    "message": "Question has attempts and was not deleted.",
                    "reason": "has_attempts",
                    "attempt_count": exc.attempt_count,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(result, status=status.HTTP_200_OK)


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
        if "description" in request.data:
            description = request.data["description"]
            if description is not None and not isinstance(description, str):
                errors.append({
                    "path": "description",
                    "code": "INVALID_TYPE",
                    "message": "'description' must be a string.",
                })
            else:
                test.description = description
        if "category" in request.data:
            category_name = request.data["category"]
            if not isinstance(category_name, str):
                errors.append({
                    "path": "category",
                    "code": "INVALID_TYPE",
                    "message": "'category' must be a string.",
                })
        if errors:
            return Response(
                {"error": "VALIDATION_FAILED", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
