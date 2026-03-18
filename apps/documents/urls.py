from django.urls import path
from apps.documents.views import DocumentUploadView, DocumentDetailView, DocumentListView, DocumentPreviewView

urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("<int:pk>", DocumentDetailView.as_view(), name="document-detail"),
    path("<int:pk>/preview", DocumentPreviewView.as_view(), name="document-preview")
]
