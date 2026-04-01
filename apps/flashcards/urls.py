from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.flashcards.views import (
    FlashcardSetListView,
    FlashcardSetDetailView,
    GenerationSessionListView,
    FlashcardFolderViewSet,
)

router = DefaultRouter()
router.register(r'folders', FlashcardFolderViewSet, basename='folder')

urlpatterns = [
    path('', include(router.urls)),
    path('sets/',          FlashcardSetListView.as_view(),   name='flashcard-set-list'),
    path('sets/<int:pk>/', FlashcardSetDetailView.as_view(), name='flashcard-set-detail'),
    path('sessions/',      GenerationSessionListView.as_view(), name='generation-session-list'),
]