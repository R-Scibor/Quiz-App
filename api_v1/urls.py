from django.urls import path
from .views import (
    TestListView, QuestionListView, CheckOpenAnswerView, GetTaskResultView,
    ReportIssueView, RegisterView, LoginView, LogoutView,
    SessionStartView, SessionCompleteView, AttemptCreateView, UserStatsView,
    StudyQueueView,
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
    path('study/queue/', StudyQueueView.as_view(), name='study-queue'),
]