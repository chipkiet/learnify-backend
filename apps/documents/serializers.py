import os
from rest_framework import serializers
from apps.documents.models import Document


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Dùng khi upload — không expose extracted_text."""
    class Meta:
        model = Document
        fields = ["id", "title", "file", "original_name", "file_type", 
                  "file_size", "mime_type", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "original_name", "file_type", "file_size", 
                            "mime_type", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        uploaded_file = validated_data.get("file")

        original_name = uploaded_file.name
        _, ext = os.path.splitext(original_name)
        file_type = ext.lstrip(".").lower() if ext else ""

        if file_type not in {"pdf", "docx", "txt"}:
            file_type = "txt"

        mime_type = getattr(uploaded_file, "content_type", "")
        file_size = getattr(uploaded_file, "size", None)
        title = validated_data.get("title") or original_name

        return Document.objects.create(
            user=user,
            title=title,
            original_name=original_name,
            file=uploaded_file,
            file_type=file_type,
            file_size=file_size or 0,
            mime_type=mime_type,
            **{k: v for k, v in validated_data.items() if k not in {"file", "title"}},
        )


class DocumentListSerializer(serializers.ModelSerializer):
    """Dùng cho list — không có extracted_text để response nhẹ."""
    class Meta:
        model = Document
        fields = [
            "id", "title", "original_name", "file_type", "file_size",
            "mime_type", "status", "word_count", "char_count", 
            "page_count", "created_at", "updated_at",
        ]
        read_only_fields = fields


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Dùng cho detail — có đầy đủ extracted_text cho AI và preview."""
    class Meta:
        model = Document
        fields = [
            "id", "title", "original_name", "file_type", "file_size",
            "mime_type", "status", "word_count", "char_count", "page_count",
            "extracted_text",       # ← full text cho AI
            "extraction_error",     # ← debug khi status=failed
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Dùng cho PATCH — chỉ cho phép sửa title."""
    class Meta:
        model = Document
        fields = ["id", "title", "updated_at"]
        read_only_fields = ["id", "updated_at"]