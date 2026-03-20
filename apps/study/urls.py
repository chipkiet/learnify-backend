from django.urls import path
from apps.study.views import CardReviewView, DueCardsView, NewCardsView

urlpatterns = [
    path("cards/<int:card_id>/review/", CardReviewView.as_view(), name="card-review"),
    path("due/", DueCardsView.as_view(), name="due-cards"),
    path("new/", NewCardsView.as_view(), name="new-cards"),
]
