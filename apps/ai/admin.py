from django.contrib import admin
from django.apps import apps
from unfold.admin import ModelAdmin

from apps.ai.models import ApiUsageLog


class ApiUsageLogAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "model_used",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "created_at",
    )
    list_filter = ("action", "model_used", "created_at")
    search_fields = ("user__email", "user__username", "action", "model_used")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
    )
    ordering = ("-created_at",)


admin.site.register(ApiUsageLog, ApiUsageLogAdmin)

app = apps.get_app_config("ai")
for model_name, model in app.models.items():
    if model is ApiUsageLog:
        continue
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
