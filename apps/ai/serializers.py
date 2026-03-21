from rest_framework import serializers
from apps.flashcards.models import GenerationSession

VALID_DOMAINS = ["english", "academic", "other"]
VALID_CARD_TYPES = ["vocabulary", "grammar", "phrase", "qa", "qa_en"]
VALID_DIFFICULTIES = ["easy", "intermediate", "hard"]


class GenerateFlashcardSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    domain = serializers.ChoiceField(choices=VALID_DOMAINS)
    card_types = serializers.ListField(
        child=serializers.ChoiceField(choices=VALID_CARD_TYPES),
        min_length=1,
        max_length=5,  # tăng từ 4 → 5 vì academic có thêm qa_en
    )
    difficulty = serializers.ChoiceField(
        choices=VALID_DIFFICULTIES, default="intermediate"
    )
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        max_length=10,
    )

    def validate_document_id(self, value):
        from apps.documents.models import Document

        request = self.context.get("request")
        try:
            doc = Document.objects.get(pk=value, user=request.user)
        except Document.DoesNotExist:
            raise serializers.ValidationError("Document không tồn tại.")

        if doc.status != "done":
            raise serializers.ValidationError("Document chưa được extract xong.")

        if not doc.extracted_text:
            raise serializers.ValidationError("Document không có nội dung.")

        return value
