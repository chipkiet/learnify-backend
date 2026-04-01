# apps/flashcards/serializers.py

from rest_framework import serializers
from apps.flashcards.models import GenerationSession, FlashcardSet, FlashCard


class FlashCardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FlashCard
        fields = [
            'id', 'front', 'back', 'example',
            'card_type', 'difficulty',
            'ease_factor', 'interval', 'repetitions', 'next_review_at',
            'created_at',
        ]
        read_only_fields = fields


class FlashcardSetSerializer(serializers.ModelSerializer):
    """Dùng cho List — không trả về cards để response nhẹ."""
    total_cards = serializers.SerializerMethodField()
    document_title = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model  = FlashcardSet
        fields = [
            "id",
            "title",
            "description",
            "domain",
            "status",
            "is_public",
            "total_cards",
            "document_title",
            "progress",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_total_cards(self, obj):
        return obj.flashcards.count()

    def get_document_title(self, obj):
        return obj.document.title if obj.document else None

    def get_progress(self, obj):
        total = obj.flashcards.count()
        reviewed = getattr(obj, "reviewed_count", 0)
        due = getattr(obj, "due_count", 0)

        if reviewed == 0:
            state = "new"
        elif due > 0:
            state = "due"
        elif reviewed < total:
            state = "in_progress"
        else:
            state = "completed"

        return {
            "total": total,
            "reviewed": reviewed,
            "due_today": due,
            "state": state,
            "percent": round((reviewed / total * 100) if total > 0 else 0),
        }


class FlashcardSetDetailSerializer(serializers.ModelSerializer):
    """Dùng cho Detail — trả về đầy đủ cards bên trong."""
    cards        = FlashCardSerializer(source='flashcards', many=True, read_only=True)
    total_cards  = serializers.SerializerMethodField()
    document_title = serializers.SerializerMethodField()
    cards_by_type  = serializers.SerializerMethodField()

    class Meta:
        model  = FlashcardSet
        fields = [
            'id', 'title', 'description', 'domain',
            'status', 'is_public',
            'total_cards', 'cards_by_type',
            'document_title',
            'cards',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_total_cards(self, obj):
        return obj.flashcards.count()

    def get_document_title(self, obj):
        return obj.document.title if obj.document else None

    def get_cards_by_type(self, obj):
        """Thống kê số card theo từng type — tiện cho frontend render tabs."""
        from django.db.models import Count
        result = obj.flashcards.values('card_type').annotate(count=Count('id'))
        return {item['card_type']: item['count'] for item in result}


class GenerationSessionSerializer(serializers.ModelSerializer):
    """Dùng để xem lịch sử generate."""
    document_title = serializers.SerializerMethodField()

    class Meta:
        model  = GenerationSession
        fields = [
            'id', 'document_title', 'domain',
            'card_types', 'extracted_keywords', 'difficulty',
            'status', 'total_cards_generated', 'ai_model_used',
            'generation_error',
            'created_at',
        ]
        read_only_fields = fields

    def get_document_title(self, obj):
        return obj.document.title if obj.document else None


class FlashcardSetUpdateSerializer(serializers.ModelSerializer):
    """Chỉ cho phép update title và description."""

    class Meta:
        model = FlashcardSet
        fields = ["title", "description"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Tên bộ thẻ không được để trống.")
        if len(value) > 255:
            raise serializers.ValidationError("Tên bộ thẻ tối đa 255 ký tự.")
        return value
