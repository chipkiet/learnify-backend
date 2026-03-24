# apps/ai/services/groq_service.py

import json
import logging
from groq import Groq
from django.conf import settings
from apps.ai.services.prompt_builder import build_prompt

from apps.ai.models import ApiUsageLog


logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-8b-versatile"

def _parse_ai_response(raw_text: str) -> list:
    """
    Parse JSON từ response của Groq.
    Xử lý các trường hợp AI trả về text thừa xung quanh JSON.
    """
    text = raw_text.strip()

    # Trường hợp AI bọc trong ```json ... ```
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Tìm array JSON trong text
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"Không tìm thấy JSON array trong response: {text[:200]}")

    json_str = text[start:end]
    cards    = json.loads(json_str)

    if not isinstance(cards, list):
        raise ValueError("Response không phải JSON array")

    return cards


def _validate_card(card: dict) -> bool:
    """
    Kiểm tra card có đủ fields bắt buộc không.
    """
    required = ["card_type", "front", "back"]
    return all(card.get(f) for f in required)


def generate_flashcards(
    user,
    extracted_text: str,
    domain: str,
    card_types: list,
    difficulty: str,
    keywords: list = None,
    max_cards: int = 20,
) -> dict:
    """
    Gọi Groq API → parse response → trả về dict kết quả.

    Returns:
        {
            "success": True/False,
            "cards": [...],
            "raw_response": "...",
            "model_used": "...",
            "error": "..." (nếu fail)
        }
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = build_prompt(
        extracted_text=extracted_text,
        domain=domain,
        card_types=card_types,
        difficulty=difficulty,
        keywords=keywords or [],
        max_cards=max_cards,
    )

    logger.info(f"[Groq] Calling API — model={GROQ_MODEL} | domain={domain} | card_types={card_types}")

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là chuyên gia tạo flashcard học tập. Chỉ trả về JSON array, không có text nào khác."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,     # thấp → output ổn định, ít hallucinate
            max_tokens=4096,
        )

        raw_text = response.choices[0].message.content
        usage = response.usage
        usage_data = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

        if usage_data["total_tokens"] > 0:
            ApiUsageLog.objects.create(
                user=user,
                action="generate_flashcards",
                model_used=GROQ_MODEL,
                prompt_tokens=usage_data["prompt_tokens"],
                completion_tokens=usage_data["completion_tokens"],
                total_tokens=usage_data["total_tokens"],
            )

        logger.info(
            f"[Groq] Response received — length={len(raw_text)}, total_tokens={usage_data['total_tokens']}"
        )

        # Parse JSON
        cards = _parse_ai_response(raw_text)

        # Validate từng card
        valid_cards   = [c for c in cards if _validate_card(c)]
        invalid_count = len(cards) - len(valid_cards)

        if invalid_count > 0:
            logger.warning(f"[Groq] {invalid_count} cards bị loại do thiếu fields")

        # Normalize fields — đảm bảo luôn có example
        for card in valid_cards:
            card.setdefault("example",    "")
            card.setdefault("difficulty", difficulty)
            # Giới hạn card_type trong choices hợp lệ
            if card["card_type"] not in ["vocabulary", "grammar", "phrase", "qa"]:
                card["card_type"] = "vocabulary"

        logger.info(f"[Groq] Done — {len(valid_cards)} valid cards")

        return {
            "success": True,
            "cards": valid_cards,
            "raw_response": raw_text,
            "model_used": GROQ_MODEL,
            "usage": usage_data,
            "error": None,
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Groq] JSON parse error: {e}")
        return {
            "success": False,
            "cards": [],
            "raw_response": raw_text if "raw_text" in locals() else "",
            "model_used": GROQ_MODEL,
            "usage": (
                usage_data
                if "usage_data" in locals()
                else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            ),
            "error": f"JSON parse error: {str(e)}",
        }

    except Exception as e:
        logger.error(f"[Groq] API error: {e}")
        return {
            "success": False,
            "cards": [],
            "raw_response": "",
            "model_used": GROQ_MODEL,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "error": str(e),
        }
