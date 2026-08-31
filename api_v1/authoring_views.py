from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .authoring_schema import AUTHORING_SCHEMA
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
