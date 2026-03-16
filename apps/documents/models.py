from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Document(models.Model):
    class Status(models.TextChoices) :
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'
    
    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'
        TXT = 'txt', 'TXT'
        
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='documents'
    )
    title = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta : 
        ordering = ['-created_at']