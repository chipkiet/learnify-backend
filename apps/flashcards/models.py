from django.db import models
from django.contrib.auth import get_user_model
from apps.documents.models import Document
from apps.tags.models import Tag

User = get_user_model()

class FlashcardSet(models.Model) :
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='flashcard_sets'
    )
    
    document = models.ForeignKey(
        Document, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flashcard_sets'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='flashcard_sets'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

    class Meta : 
        ordering = ['-created_at']
    
class FlashCard(models.Model):
    set = models.ForeignKey(
        FlashcardSet,
        on_delete=models.CASCADE,
        related_name='flashcards'
    )
    front = models.TextField()
    back = models.TextField()
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.set.title} - Card {self.order}"

    class Meta:
        ordering = ['order']