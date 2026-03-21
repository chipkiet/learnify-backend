# apps/quiz/services/explanation.py
"""
Idea 2 — AI explanation khi user trả lời sai.

Chỉ gọi khi is_correct=False → tiết kiệm ~70% token.
Dùng model nhỏ (8B) thay vì 70B — đủ dùng cho 2 câu giải thích.
Tổng ~140 tokens/câu sai ≈ $0.00014 — không đáng kể.
"""

import logging
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

EXPLANATION_MODEL = "llama-3.1-8b-instant"  # Nhỏ hơn, nhanh hơn, đủ dùng


def get_explanation(
    question_text: str,
    correct_answer: str,
    user_answer: str,
    question_type: str,
    domain: str = "other",
) -> str:
    """
    Gọi Groq để giải thích tại sao user_answer sai.

    Args:
        question_text : front của card / câu hỏi
        correct_answer: đáp án đúng
        user_answer   : đáp án user chọn/gõ
        question_type : 'multiple_choice' | 'fill_in_blank'
        domain        : 'english' | 'academic' | 'other'

    Returns:
        str — 2 câu giải thích, hoặc "" nếu Groq fail
    """
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)

        # Instruction khác nhau theo domain
        if domain == "english":
            lang_instruction = (
                "Explain in 2 short sentences (in Vietnamese) "
                "why the user's answer is wrong and what makes the correct answer right. "
                "Focus on meaning or usage difference."
            )
        else:
            lang_instruction = (
                "Giải thích trong 2 câu ngắn tại sao đáp án của người dùng sai "
                "và tại sao đáp án đúng là chính xác. "
                "Dùng tiếng Việt, súc tích."
            )

        # Context thêm cho fill-in-blank vs MC
        if question_type == "fill_in_blank":
            context = f'Người dùng đã gõ: "{user_answer}"'
        else:
            context = f'Người dùng đã chọn: "{user_answer}"'

        prompt = f"""{lang_instruction}

Câu hỏi: {question_text}
Đáp án đúng: {correct_answer}
{context}

Giải thích (tối đa 2 câu):"""

        response = client.chat.completions.create(
            model=EXPLANATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=120,  # Chặt chẽ — chỉ cần 2 câu
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"[Quiz:Explanation] OK — {len(result)} chars")
        return result

    except Exception as e:
        # Không để lỗi AI block việc submit answer
        logger.warning(f"[Quiz:Explanation] Failed (non-critical): {e}")
        return ""
