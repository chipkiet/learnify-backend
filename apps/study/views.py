# apps/study/views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Q

from apps.flashcards.models import FlashCard
from apps.study.models import CardReview
from apps.study.services.sm2 import apply_review

logger = logging.getLogger(__name__)


class CardReviewView(APIView):
    """
    POST /api/study/cards/<card_id>/review/
    Nhận quality (0-5), chạy SM-2, lưu DB.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, card_id):
        # ── Validate card ownership ────────────────────────
        try:
            card = FlashCard.objects.get(pk=card_id, user=request.user)
        except FlashCard.DoesNotExist:
            return Response(
                {"error": "Card không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )

        # ── Validate quality ───────────────────────────────
        quality = request.data.get("quality")
        if quality is None:
            return Response(
                {"error": "Thiếu field 'quality'."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            quality = int(quality)
            if not (0 <= quality <= 5):
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "quality phải là số nguyên từ 0 đến 5."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Chạy SM-2 + update card ────────────────────────
        result = apply_review(card, quality)  # update card fields, chưa save
        card.save(
            update_fields=[
                "ease_factor",
                "interval",
                "repetitions",
                "next_review_at",
            ]
        )

        # ── Lưu CardReview (snapshot) ──────────────────────
        CardReview.objects.create(
            user=request.user,
            card=card,
            quality=quality,
            ease_factor_after=result["ease_factor"],
            interval_after=result["interval"],
            repetitions_after=result["repetitions"],
            next_review_at_after=result["next_review_at"],
        )

        logger.info(
            f"[Review] user={request.user.email} | "
            f"card={card_id} | q={quality} | "
            f"next={result['next_review_at'].date()}"
        )

        return Response(
            {
                "card_id": card_id,
                "quality": quality,
                "ease_factor": result["ease_factor"],
                "interval": result["interval"],
                "repetitions": result["repetitions"],
                "next_review_at": result["next_review_at"],
            },
            status=status.HTTP_200_OK,
        )


class DueCardsView(APIView):
    """
    GET /api/study/due/
    Trả về tất cả cards đến hạn ôn hôm nay.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()

        due_cards = (
            FlashCard.objects.filter(user=request.user)
            .filter(
                Q(next_review_at__isnull=True)  # chưa học lần nào
                | Q(next_review_at__lte=now)  # đã đến hạn
            )
            .order_by("next_review_at")
        )

        data = []
        for card in due_cards:
            data.append(
                {
                    "id": card.id,
                    "front": card.front,
                    "back": card.back,
                    "example": card.example,
                    "card_type": card.card_type,
                    "difficulty": card.difficulty,
                    "ease_factor": card.ease_factor,
                    "interval": card.interval,
                    "repetitions": card.repetitions,
                    "next_review_at": card.next_review_at,
                    "set_id": card.set_id,
                }
            )

        return Response(
            {
                "due_count": len(data),
                "cards": data,
            }
        )
