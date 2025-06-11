from django.urls import path
from .views import TestListView, QuestionListView

app_name = 'api_v1'

urlpatterns = [
    path('tests/', TestListView.as_view(), name='test-list'),
    path('questions/', QuestionListView.as_view(), name='question-list'),
]