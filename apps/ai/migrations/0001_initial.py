# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiUsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(help_text='e.g., generate_flashcards, generate_quiz_explanation', max_length=100)),
                ('model_used', models.CharField(help_text='e.g., llama-3.3-70b-versatile', max_length=100)),
                ('prompt_tokens', models.IntegerField(default=0)),
                ('completion_tokens', models.IntegerField(default=0)),
                ('total_tokens', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_usage_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'API Usage Log',
                'verbose_name_plural': 'API Usage Logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
