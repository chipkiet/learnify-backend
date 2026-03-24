from django.db import models
from django.conf import settings

class ApiUsageLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_usage_logs')
    action = models.CharField(max_length=100, help_text="e.g., generate_flashcards, generate_quiz_explanation")
    model_used = models.CharField(max_length=100, help_text="e.g., llama-3.3-70b-versatile")
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "API Usage Log"
        verbose_name_plural = "API Usage Logs"

    def __str__(self):
        return f"{self.user.email} - {self.action} ({self.total_tokens} tokens)"
