# apps/flashcards/views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q


from apps.flashcards.models import FlashcardSet, FlashCard, GenerationSession
from apps.flashcards.serializers import (
    FlashcardSetSerializer,
    FlashcardSetDetailSerializer,
    FlashcardSetUpdateSerializer,
    GenerationSessionSerializer,
)

logger = logging.getLogger(__name__)


class FlashcardSetListView(APIView):
    """
    GET /api/flashcards/sets/
    List tất cả bộ flashcard của user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        sets = FlashcardSet.objects.filter(user=request.user).annotate(
            reviewed_count=Count(
                "flashcards", filter=Q(flashcards__next_review_at__isnull=False)
            ),
            due_count=Count(
                "flashcards", filter=Q(flashcards__next_review_at__lte=now)
            ),
        )

        # Filter theo domain nếu có
        domain = request.query_params.get("domain")
        if domain:
            sets = sets.filter(domain=domain)

        # Filter theo document nếu có
        document_id = request.query_params.get("document_id")
        if document_id:
            sets = sets.filter(document_id=document_id)

        serializer = FlashcardSetSerializer(sets, many=True)
        return Response(serializer.data)


class FlashcardSetDetailView(APIView):
    """
    GET    /api/flashcards/sets/<pk>/  — xem chi tiết + toàn bộ cards
    DELETE /api/flashcards/sets/<pk>/  — xóa set + toàn bộ cards
    PATCH /api/flashcards/sets/<pk>/
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return FlashcardSet.objects.get(pk=pk, user=user)
        except FlashcardSet.DoesNotExist:
            return None

    def get(self, request, pk):
        fset = self.get_object(pk, request.user)
        if not fset:
            return Response(
                {"error": "Không tìm thấy bộ flashcard."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = FlashcardSetDetailSerializer(fset)
        return Response(serializer.data)

    def delete(self, request, pk):
        fset = self.get_object(pk, request.user)
        if not fset:
            return Response(
                {"error": "Không tìm thấy bộ flashcard."},
                status=status.HTTP_404_NOT_FOUND,
            )
        title = fset.title
        fset.delete()  # cascade xóa luôn toàn bộ FlashCard bên trong
        logger.info(f"FlashcardSet deleted: '{title}' by {request.user.email}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        """
        PATCH /api/flashcards/sets/:id/
        Body: { "title": "Tên mới" }
              hoặc { "title": "Tên mới", "description": "Mô tả mới" }
        """

        fset = self.get_object(pk, request.user)
        if not fset:
            return Response(
                {"error": "Không tìm thấy bộ flashcards"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = FlashcardSetUpdateSerializer(fset, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        logger.info(
            f"FlashcardSet #{pk} updated: '{fset.title}' by {request.user.email}"
        )

        return Response(
            {"id": fset.id, "title": fset.title, "description": fset.description}
        )


class GenerationSessionListView(APIView):
    """
    GET /api/flashcards/sessions/
    Lịch sử các lần generate của user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = GenerationSession.objects.filter(user=request.user)

        # Filter theo document nếu có
        document_id = request.query_params.get("document_id")
        if document_id:
            sessions = sessions.filter(document_id=document_id)

        serializer = GenerationSessionSerializer(sessions, many=True)
        return Response(serializer.data)
