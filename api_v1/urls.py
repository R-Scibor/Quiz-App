from django.urls import path
from .authoring_views import (
    AuthoringExportView,
    AuthoringInstructionsView,
    AuthoringQuestionDetailView,
    AuthoringSchemaView,
    AuthoringTestListView,
    AuthoringValidateView,
)
from .views import (
    TestListView, QuestionListView, CheckOpenAnswerView, GetTaskResultView,
    ReportIssueView, RegisterView, LoginView, LogoutView,
    SessionStartView, SessionCompleteView, AttemptCreateView, UserStatsView,
    StudyQueueView, StudyStatsView, StatsTestBreakdownView,
)

app_name = 'api_v1'

urlpatterns = [
    path('tests/', TestListView.as_view(), name='test-list'),
    path('questions/', QuestionListView.as_view(), name='question-list'),
    path('check_answer/', CheckOpenAnswerView.as_view(), name='check-answer'),
    path('task_result/<str:task_id>/', GetTaskResultView.as_view(), name='task-result'),
    path('report_issue/', ReportIssueView.as_view(), name='report-issue'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('sessions/start/', SessionStartView.as_view(), name='session-start'),
    path('sessions/<uuid:pk>/complete/', SessionCompleteView.as_view(), name='session-complete'),
    path('attempts/', AttemptCreateView.as_view(), name='attempt-create'),
    path('stats/', UserStatsView.as_view(), name='user-stats'),
    path('stats/tests/', StatsTestBreakdownView.as_view(), name='stats-tests'),
    path('study/queue/', StudyQueueView.as_view(), name='study-queue'),
    path('study/stats/', StudyStatsView.as_view(), name='study-stats'),
    path('authoring/schema/', AuthoringSchemaView.as_view(), name='authoring-schema'),
    path('authoring/instructions/', AuthoringInstructionsView.as_view(), name='authoring-instructions'),
    path('authoring/validate/', AuthoringValidateView.as_view(), name='authoring-validate'),
    path('authoring/tests/', AuthoringTestListView.as_view(), name='authoring-test-list'),
    path('authoring/tests/<uuid:pk>/export/', AuthoringExportView.as_view(), name='authoring-export'),
    path('authoring/tests/<uuid:pk>/questions/<uuid:question_id>/', AuthoringQuestionDetailView.as_view(), name='authoring-question-detail'),
]