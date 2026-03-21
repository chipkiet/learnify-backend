# apps/quiz/models.py
from django.db import models
from django.contrib.auth import get_user_model
from apps.flashcards.models import FlashcardSet, FlashCard

User = get_user_model()


class QuizSession(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quiz_sessions"
    )
    flashcard_set = models.ForeignKey(
        FlashcardSet, on_delete=models.CASCADE, related_name="quiz_sessions"
    )

    total_questions = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    @property
    def score_percent(self):
        if self.total_questions == 0:
            return 0
        return round(self.correct_count / self.total_questions * 100)

    def __str__(self):
        return f"Quiz #{self.id} — {self.flashcard_set.title} ({self.status})"

    class Meta:
        ordering = ["-created_at"]


class QuizQuestion(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        FILL_IN_BLANK = "fill_in_blank", "Fill in Blank"

    class CorrectOption(models.TextChoices):
        A = "a", "A"
        B = "b", "B"
        C = "c", "C"
        D = "d", "D"

    session = models.ForeignKey(
        QuizSession, on_delete=models.CASCADE, related_name="questions"
    )
    card = models.ForeignKey(
        FlashCard, on_delete=models.SET_NULL, null=True, related_name="quiz_questions"
    )

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
    )
    question_text = models.TextField()

    # Multiple choice — blank nếu là fill_in_blank
    option_a = models.TextField(blank=True)
    option_b = models.TextField(blank=True)
    option_c = models.TextField(blank=True)
    option_d = models.TextField(blank=True)
    correct_option = models.CharField(
        max_length=1, choices=CorrectOption.choices, blank=True
    )

    # Đáp án chuẩn — dùng cho cả 2 loại
    correct_answer = models.TextField()

    # MC → 'a'|'b'|'c'|'d'   FIB → text user gõ
    user_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    # AI explanation — chỉ fill khi sai
    ai_explanation = models.TextField(blank=True)

    order = models.IntegerField(default=0)
    answered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{self.question_type}] Q{self.order}: {self.question_text[:50]}"

    class Meta:
        ordering = ["order"]
