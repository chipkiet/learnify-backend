from django.contrib import admin
from django.apps import apps
from unfold.admin import ModelAdmin

app = apps.get_app_config("documents")
for model_name, model in app.models.items():
    try:

        class UnfoldModelAdmin(ModelAdmin):
            pass

        admin.site.register(model, UnfoldModelAdmin)
    except admin.sites.AlreadyRegistered:
        pass
