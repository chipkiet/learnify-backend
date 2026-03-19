from django.urls import path
from apps.study.views import CardReviewView, DueCardsView

urlpatterns = [
    path('cards/<int:card_id>/review', CardReviewView.as_view(), name='card-review'),
    path('due/', DueCardsView.as_view(), name='due-cards'),
]