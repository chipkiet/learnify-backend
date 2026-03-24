import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.ai.serializers import GenerateFlashcardSerializer
from apps.ai.services.groq_service import generate_flashcards
from apps.documents.models import Document
from apps.flashcards.models import GenerationSession, FlashcardSet, FlashCard

logger = logging.getLogger(__name__)


class GenerateFlashcardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # ── Bước 1: Validate input ─────────────────────────
        serializer = GenerateFlashcardSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data        = serializer.validated_data
        document    = Document.objects.get(pk=data['document_id'])
        domain      = data['domain']
        card_types  = data['card_types']
        difficulty  = data['difficulty']
        keywords    = data.get('keywords', [])

        # ── Bước 2: Tạo GenerationSession ──────────────────
        session = GenerationSession.objects.create(
            user               = request.user,
            document           = document,
            domain             = domain,
            card_types         = card_types,
            difficulty         = difficulty,
            extracted_keywords = keywords,
            user_intent        = f"Domain: {domain} | Types: {card_types} | Keywords: {keywords}",
            status             = GenerationSession.Status.PROCESSING,
        )
        logger.info(f"[AI] Session created: #{session.id} — doc={document.id} user={request.user.email}")

        # ── Bước 3: Gọi Groq API ────────────────────────────
        result = generate_flashcards(
            user=request.user,
            extracted_text=document.extracted_text,
            domain=domain,
            card_types=card_types,
            difficulty=difficulty,
            keywords=keywords,
        )

        # ── Bước 4: Xử lý nếu AI thất bại ──────────────────
        if not result['success']:
            session.status           = GenerationSession.Status.FAILED
            session.generation_error = result['error']
            session.raw_ai_response  = result['raw_response']
            session.ai_model_used    = result['model_used']
            session.save()
            logger.error(f"[AI] Generation failed: session=#{session.id} | error={result['error']}")
            return Response(
                {"error": "AI generation thất bại.", "detail": result['error']},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # ── Bước 5: Tạo FlashcardSet ────────────────────────
        flashcard_set = FlashcardSet.objects.create(
            user     = request.user,
            document = document,
            session  = session,
            domain   = domain,
            title    = f"{document.title} — {domain.capitalize()}",
            description = f"Tạo tự động từ tài liệu '{document.title}' | {len(result['cards'])} cards",
            status   = FlashcardSet.Status.DRAFT,
        )

        # ── Bước 6: Tạo từng FlashCard ──────────────────────
        cards_to_create = []
        for card_data in result['cards']:
            cards_to_create.append(FlashCard(
                set        = flashcard_set,
                user       = request.user,
                front      = card_data.get('front', ''),
                back       = card_data.get('back', ''),
                example    = card_data.get('example', ''),
                card_type  = card_data.get('card_type', 'vocabulary'),
                difficulty = card_data.get('difficulty', difficulty),
            ))

        FlashCard.objects.bulk_create(cards_to_create)  # 1 query duy nhất

        # ── Bước 7: Update session ───────────────────────────
        session.status                = GenerationSession.Status.DONE
        session.total_cards_generated = len(cards_to_create)
        session.ai_model_used         = result['model_used']
        session.raw_ai_response       = result['raw_response']
        session.save()

        logger.info(f"[AI] Done: session=#{session.id} | {len(cards_to_create)} cards created")

        # ── Bước 8: Trả về response ──────────────────────────
        return Response({
            "session_id":     session.id,
            "flashcard_set_id": flashcard_set.id,
            "total_cards":    len(cards_to_create),
            "domain":         domain,
            "card_types":     card_types,
            "message":        f"Đã tạo thành công {len(cards_to_create)} flashcards!",
        }, status=status.HTTP_201_CREATED)
