from django.urls import path
from apps.quiz.views import QuizCreateView, QuizAnswerView, QuizResultView, QuizHistoryView

urlpatterns = [
    path('create/', QuizCreateView.as_view(), name='quiz-create'),
    path('<int:session_id>/answer/', QuizAnswerView.as_view(), name='quiz-answer'),
    path('<int:session_id>/result/', QuizResultView.as_view(), name='quiz-result'),
    path('history/', QuizHistoryView.as_view(), name='quiz-history'),
]
