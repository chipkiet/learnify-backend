from django.db import models
from django.contrib.auth import get_user_model
from apps.documents.models import Document
from apps.tags.models import Tag

User = get_user_model()


class GenerationSession(models.Model):
    """
    Lưu context của 1 lần user request tạo flashcard.
    Cầu nối: Document → AI → FlashcardSet
    """
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE       = 'done',       'Done'
        FAILED     = 'failed',     'Failed'

    class Domain(models.TextChoices):
        ENGLISH = 'english', 'English Learning'
        HISTORY = 'history', 'History'
        SCIENCE = 'science', 'Science'
        MATH    = 'math',    'Math'
        OTHER   = 'other',   'Other'

    # ── Relations ──────────────────────────────────────────
    user     = models.ForeignKey(User,     on_delete=models.CASCADE, related_name='generation_sessions')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='generation_sessions')

    # ── User intent ────────────────────────────────────────
    user_intent        = models.TextField(blank=True)       # raw text user nhập
    extracted_keywords = models.JSONField(default=list)     # ["war", "dynasty"]
    card_types         = models.JSONField(default=list)     # ["vocabulary", "qa"]
    domain             = models.CharField(max_length=20, choices=Domain.choices, default=Domain.OTHER)
    difficulty         = models.CharField(max_length=20, default='intermediate')

    # ── AI result ──────────────────────────────────────────
    status                = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_cards_generated = models.IntegerField(default=0)
    ai_model_used         = models.CharField(max_length=100, blank=True)
    generation_error      = models.TextField(blank=True, null=True)
    raw_ai_response       = models.TextField(blank=True, null=True)  # debug

    # ── Timestamps ─────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session #{self.id} — {self.document.title} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class FlashcardSet(models.Model):
    """
    Bộ flashcard — được tạo từ 1 GenerationSession hoặc thủ công.
    """
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'

    # ── Relations ──────────────────────────────────────────
    user     = models.ForeignKey(User,     on_delete=models.CASCADE,  related_name='flashcard_sets')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='flashcard_sets')
    session  = models.OneToOneField(GenerationSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='flashcard_set')
    tags     = models.ManyToManyField(Tag, blank=True, related_name='flashcard_sets')

    # ── Metadata ───────────────────────────────────────────
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    domain      = models.CharField(max_length=20, blank=True)
    is_public   = models.BooleanField(default=False)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # ── Timestamps ─────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class FlashCard(models.Model):
    """
    1 flashcard trong 1 set.
    SRS fields có sẵn slot — Phase 2 sẽ activate.
    """
    class CardType(models.TextChoices):
        VOCABULARY = 'vocabulary', 'Vocabulary'
        GRAMMAR    = 'grammar',    'Grammar'
        PHRASE     = 'phrase',     'Phrase'
        QA         = 'qa',         'Q&A'

    class Difficulty(models.TextChoices):
        EASY   = 'easy',   'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD   = 'hard',   'Hard'

    # ── Relations ──────────────────────────────────────────
    set  = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='flashcards')
    user = models.ForeignKey(User,         on_delete=models.CASCADE, related_name='flashcards')

    # ── Content ────────────────────────────────────────────
    front      = models.TextField()
    back       = models.TextField()
    example    = models.TextField(blank=True)
    card_type  = models.CharField(max_length=20, choices=CardType.choices, default=CardType.VOCABULARY)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)

    # ── SRS — Phase 2 (slot sẵn, chưa dùng) ───────────────
    ease_factor    = models.FloatField(default=2.5)
    interval       = models.IntegerField(default=0)   # days
    repetitions    = models.IntegerField(default=0)
    next_review_at = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ─────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.card_type}] {self.front[:50]}"

    class Meta:
        ordering = ['card_type', 'difficulty']