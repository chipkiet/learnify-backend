from django.db import models
from django.contrib.auth import get_user_model
from apps.flashcards.models import FlashCard

User = get_user_model()

class CardReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='card_reviews')
    card = models.ForeignKey(
        FlashCard, on_delete=models.CASCADE, related_name="reviews"
    )

    quality = models.IntegerField()

    ease_factor_after = models.FloatField()
    interval_after = models.IntegerField() 
    repetitions_after = models.IntegerField()
    next_review_at_after = models.DateTimeField()

    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ['-reviewed_at']
        indexes = [
            models.Index(fields=["card", "reviewed_at"]),
            models.Index(fields=["user", "reviewed_at"]),
        ]
