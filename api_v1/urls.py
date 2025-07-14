from django.urls import path
from .views import TestListView, QuestionListView, CheckOpenAnswerView, GetTaskResultView

app_name = 'api_v1'

urlpatterns = [
    path('tests/', TestListView.as_view(), name='test-list'),
    path('questions/', QuestionListView.as_view(), name='question-list'),
    path('check_answer/', CheckOpenAnswerView.as_view(), name='check-answer'),
    path('task_result/<str:task_id>/', GetTaskResultView.as_view(), name='task-result'),
]