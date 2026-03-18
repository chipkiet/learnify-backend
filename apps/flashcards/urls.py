
from django.urls import path
from apps.flashcards.views import (
    FlashcardSetListView,
    FlashcardSetDetailView,
    GenerationSessionListView,
)

urlpatterns = [
    path('sets/',          FlashcardSetListView.as_view(),   name='flashcard-set-list'),
    path('sets/<int:pk>/', FlashcardSetDetailView.as_view(), name='flashcard-set-detail'),
    path('sessions/',      GenerationSessionListView.as_view(), name='generation-session-list'),
]