from django.urls import path
from apps.ai.views import GenerateFlashcardView

urlpatterns = [
    path('generate/', GenerateFlashcardView.as_view(), name='ai-generate'),
]