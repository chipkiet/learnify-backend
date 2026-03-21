# apps/quiz/views.py
import logging
import random
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.flashcards.models import FlashcardSet, FlashCard
from apps.quiz.models import QuizSession, QuizQuestion
from apps.quiz.services.distractor import get_distractors, build_options
from apps.quiz.services.checker import check_fill_in_blank
from apps.quiz.services.explanation import get_explanation

logger = logging.getLogger(__name__)

MIN_CARDS_REQUIRED = 4
MAX_QUESTIONS = 20
DEFAULT_QUESTIONS = 10

# Tỷ lệ FIB user tự chọn — 0 | 25 | 50 | 75 | 100
VALID_FIB_PERCENTS = [0, 25, 50, 75, 100]
DEFAULT_FIB_PERCENT = 0  # default: chỉ MC


def _assign_question_types(n: int, fib_percent: int = 0) -> list:
    """
    Trả về list question_type cho n câu hỏi theo tỷ lệ user chọn.

    fib_percent: 0=chỉ MC | 25=25% FIB | 50=50/50 | 75=75% FIB | 100=chỉ FIB
    VD: n=10, fib_percent=25 → 7 MC + 3 FIB → shuffled
    """
    fib_count = round(n * fib_percent / 100)
    mc_count = n - fib_count
    types = [QuizQuestion.QuestionType.MULTIPLE_CHOICE] * mc_count + [
        QuizQuestion.QuestionType.FILL_IN_BLANK
    ] * fib_count
    random.shuffle(types)
    return types


class QuizCreateView(APIView):
    """
    POST /api/quiz/create/

    Body:
        { "flashcard_set_id": 22, "num_questions": 10 }

    Response:
        session_id, set_title, total, questions[]
        → MC: có option_a/b/c/d, KHÔNG có correct_option
        → FIB: không có options, user gõ tự do
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        set_id = request.data.get("flashcard_set_id")
        num_q = min(
            int(request.data.get("num_questions", DEFAULT_QUESTIONS)), MAX_QUESTIONS
        )
        fib_percent = int(request.data.get("fib_percent", DEFAULT_FIB_PERCENT))
        if fib_percent not in VALID_FIB_PERCENTS:
            return Response(
                {"error": f"fib_percent phải là một trong: {VALID_FIB_PERCENTS}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Validate ──────────────────────────────────
        try:
            fset = FlashcardSet.objects.get(pk=set_id, user=request.user)
        except FlashcardSet.DoesNotExist:
            return Response(
                {"error": "Flashcard set không tồn tại."},
                status=status.HTTP_404_NOT_FOUND,
            )

        all_cards = list(FlashCard.objects.filter(set=fset))

        if len(all_cards) < MIN_CARDS_REQUIRED:
            return Response(
                {
                    "error": f"Set cần ít nhất {MIN_CARDS_REQUIRED} cards. Hiện có {len(all_cards)}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Chọn cards + assign types ─────────────────
        num_q = min(num_q, len(all_cards))
        question_cards = random.sample(all_cards, num_q)
        question_types = _assign_question_types(num_q, fib_percent)

        # ── Tạo session ───────────────────────────────
        session = QuizSession.objects.create(
            user=request.user,
            flashcard_set=fset,
            total_questions=num_q,
            status=QuizSession.Status.IN_PROGRESS,
        )

        # ── Build questions ───────────────────────────
        questions_to_create = []
        questions_response = []

        for i, (card, qtype) in enumerate(zip(question_cards, question_types)):
            if qtype == QuizQuestion.QuestionType.MULTIPLE_CHOICE:
                distractors = get_distractors(card, all_cards, n=3)
                opts = build_options(card, distractors)

                q = QuizQuestion(
                    session=session,
                    card=card,
                    question_type=qtype,
                    question_text=card.front,
                    option_a=opts["option_a"],
                    option_b=opts["option_b"],
                    option_c=opts["option_c"],
                    option_d=opts["option_d"],
                    correct_option=opts["correct_option"],
                    correct_answer=opts["correct_answer"],
                    order=i + 1,
                )
                questions_to_create.append(q)
                questions_response.append(
                    {
                        "_idx": i,
                        "order": i + 1,
                        "question_type": qtype,
                        "question_text": card.front,
                        "option_a": opts["option_a"],
                        "option_b": opts["option_b"],
                        "option_c": opts["option_c"],
                        "option_d": opts["option_d"],
                        # correct_option KHÔNG có trong response create
                    }
                )

            else:  # FILL_IN_BLANK
                from apps.quiz.services.distractor import parse_back_main

                correct_text = parse_back_main(card.back)

                q = QuizQuestion(
                    session=session,
                    card=card,
                    question_type=qtype,
                    question_text=card.front,
                    correct_answer=correct_text,
                    order=i + 1,
                )
                questions_to_create.append(q)
                questions_response.append(
                    {
                        "_idx": i,
                        "order": i + 1,
                        "question_type": qtype,
                        "question_text": card.front,
                        # Gõ tự do — không hint, không answer_length
                    }
                )

        QuizQuestion.objects.bulk_create(questions_to_create)

        # Re-fetch để có ID, gắn vào response
        created_qs = list(session.questions.order_by("order"))
        for idx, q in enumerate(created_qs):
            questions_response[idx]["id"] = q.id

        # Bỏ _idx helper
        for qr in questions_response:
            qr.pop("_idx", None)

        logger.info(
            f"[Quiz] Session #{session.id}: {num_q} questions (fib={fib_percent}%)"
        )

        return Response(
            {
                "session_id": session.id,
                "set_title": fset.title,
                "total": num_q,
                "questions": questions_response,
            },
            status=status.HTTP_201_CREATED,
        )


class QuizAnswerView(APIView):
    """
    POST /api/quiz/<session_id>/answer/

    Body (MC):  { "question_id": 5, "answer": "b" }
    Body (FIB): { "question_id": 6, "answer": "Paris" }

    Response:
        is_correct, correct_answer, explanation (nếu sai),
        answered (số câu đã làm), completed (bool)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        question_id = request.data.get("question_id")
        user_answer = request.data.get("answer", "")

        if not user_answer and user_answer != 0:
            return Response(
                {"error": "Thiếu field 'answer'."}, status=status.HTTP_400_BAD_REQUEST
            )

        user_answer = str(user_answer).strip()

        # ── Validate session ──────────────────────────
        try:
            session = QuizSession.objects.get(pk=session_id, user=request.user)
        except QuizSession.DoesNotExist:
            return Response(
                {"error": "Session không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )

        if session.status == QuizSession.Status.COMPLETED:
            return Response(
                {"error": "Quiz đã hoàn thành."}, status=status.HTTP_400_BAD_REQUEST
            )

        # ── Validate question ─────────────────────────
        try:
            question = QuizQuestion.objects.get(pk=question_id, session=session)
        except QuizQuestion.DoesNotExist:
            return Response(
                {"error": "Câu hỏi không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )

        if question.user_answer is not None:
            return Response(
                {"error": "Câu hỏi này đã được trả lời."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Chấm điểm theo loại câu ───────────────────
        if question.question_type == QuizQuestion.QuestionType.MULTIPLE_CHOICE:
            if user_answer.lower() not in ["a", "b", "c", "d"]:
                return Response(
                    {"error": "MC answer phải là 'a', 'b', 'c' hoặc 'd'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_answer = user_answer.lower()
            is_correct = user_answer == question.correct_option
            display_answer = getattr(question, f"option_{user_answer}", user_answer)

        else:  # FILL_IN_BLANK
            is_correct = check_fill_in_blank(user_answer, question.correct_answer)
            display_answer = user_answer

        # ── AI Explanation nếu sai ────────────────────
        explanation = ""
        if not is_correct:
            explanation = get_explanation(
                question_text=question.question_text,
                correct_answer=question.correct_answer,
                user_answer=display_answer,
                question_type=question.question_type,
                domain=session.flashcard_set.domain or "other",
            )

        # ── Save question ─────────────────────────────
        question.user_answer = user_answer
        question.is_correct = is_correct
        question.ai_explanation = explanation
        question.answered_at = timezone.now()
        question.save(
            update_fields=["user_answer", "is_correct", "ai_explanation", "answered_at"]
        )

        # ── Update session score ──────────────────────
        if is_correct:
            QuizSession.objects.filter(pk=session.id).update(
                correct_count=session.correct_count + 1
            )

        # ── Auto-complete nếu xong hết ────────────────
        answered_count = session.questions.filter(user_answer__isnull=False).count()
        is_completed = answered_count >= session.total_questions

        if is_completed:
            session.refresh_from_db()
            session.status = QuizSession.Status.COMPLETED
            session.finished_at = timezone.now()
            session.save(update_fields=["status", "finished_at"])

        logger.info(
            f"[Quiz] Answer: session={session_id} q={question_id} "
            f"type={question.question_type} correct={is_correct}"
        )

        response_data = {
            "question_id": question_id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": explanation,
            "answered": answered_count,
            "total": session.total_questions,
            "completed": is_completed,
        }

        # Với MC: reveal đáp án đúng là option nào
        if question.question_type == QuizQuestion.QuestionType.MULTIPLE_CHOICE:
            response_data["correct_option"] = question.correct_option

        return Response(response_data)


class QuizResultView(APIView):
    """
    GET /api/quiz/<session_id>/result/
    Kết quả đầy đủ sau khi hoàn thành — reveal correct_option.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = QuizSession.objects.get(pk=session_id, user=request.user)
        except QuizSession.DoesNotExist:
            return Response(
                {"error": "Session không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )

        questions_data = []
        for q in session.questions.order_by("order"):
            qd = {
                "id": q.id,
                "order": q.order,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "correct_answer": q.correct_answer,
                "user_answer": q.user_answer,
                "is_correct": q.is_correct,
                "ai_explanation": q.ai_explanation,
            }
            if q.question_type == QuizQuestion.QuestionType.MULTIPLE_CHOICE:
                qd.update(
                    {
                        "option_a": q.option_a,
                        "option_b": q.option_b,
                        "option_c": q.option_c,
                        "option_d": q.option_d,
                        "correct_option": q.correct_option,
                    }
                )
            questions_data.append(qd)

        return Response(
            {
                "session_id": session.id,
                "set_title": session.flashcard_set.title,
                "status": session.status,
                "total": session.total_questions,
                "correct": session.correct_count,
                "score_percent": session.score_percent,
                "created_at": session.created_at,
                "finished_at": session.finished_at,
                "questions": questions_data,
            }
        )


class QuizHistoryView(APIView):
    """
    GET /api/quiz/history/
    GET /api/quiz/history/?set_id=22
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = QuizSession.objects.filter(user=request.user).select_related(
            "flashcard_set"
        )

        set_id = request.query_params.get("set_id")
        if set_id:
            sessions = sessions.filter(flashcard_set_id=set_id)

        data = [
            {
                "session_id": s.id,
                "set_id": s.flashcard_set_id,
                "set_title": s.flashcard_set.title,
                "total": s.total_questions,
                "correct": s.correct_count,
                "score_percent": s.score_percent,
                "status": s.status,
                "created_at": s.created_at,
                "finished_at": s.finished_at,
            }
            for s in sessions
        ]

        return Response({"count": len(data), "results": data})
