import json
import logging
from groq import Groq
from django.conf import settings
from apps.ai.services.prompt_builder import build_prompt
from apps.ai.models import ApiUsageLog


logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"

VALID_CARD_TYPES = {"vocabulary", "grammar", "phrase", "qa", "qa_en"}


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
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"Không tìm thấy JSON array trong response: {text[:200]}")

    json_str = text[start:end]
    cards = json.loads(json_str)

    if not isinstance(cards, list):
        raise ValueError("Response không phải JSON array")

    return cards


def _validate_card(card: dict) -> bool:
    """
    Kiểm tra card có đủ fields bắt buộc không.
    """
    required = ["card_type", "front", "back"]
    return all(card.get(f) for f in required)


def _chunk_text(text: str, chunk_size: int = 5000, overlap: int = 200) -> list[str]:
    """Chia text thành các chunks có overlap."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # overlap để không mất context ở ranh giới

    return chunks


def _fill_to_max(
    new_cards: list,
    existing_cards: list,
    max_cards: int,
) -> tuple:
    """
    Nếu new_cards < max_cards, bổ sung từ existing_cards cho đủ.
    Returns: (final_cards, reused_count)
    """
    needed = max_cards - len(new_cards)
    if needed <= 0 or not existing_cards:
        for card in new_cards:
            card["is_reused"] = False
        return new_cards, 0

    # Tránh duplicate với new_cards vừa tạo
    new_fronts = {c["front"].lower().strip() for c in new_cards}

    candidates = [
        c for c in existing_cards if c["front"].lower().strip() not in new_fronts
    ]

    # Lấy đủ số cần thiết
    reused = candidates[:needed]

    # Đánh dấu reused để frontend hiển thị badge
    for card in reused:
        card["is_reused"] = True

    for card in new_cards:
        card["is_reused"] = False

    return new_cards + reused, len(reused)


def generate_flashcards(
    user,
    extracted_text: str,
    domain: str,
    card_types: list,
    difficulty: str,
    keywords: list = None,
    max_cards: int = 10,
    existing_cards: list = None,
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

    chunks = _chunk_text(extracted_text)
    logger.info(f"[Groq] Document split into {len(chunks)} chunks")

    all_cards = []
    total_usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    successful_chunks = 0

    chunk_target_cards = max(2, (max_cards + len(chunks) - 1) // len(chunks))

    for i, chunk in enumerate(chunks):
        logger.info(f"[Groq] Processing chunk {i + 1}/{len(chunks)}")

        prompt = build_prompt(
            extracted_text=chunk,
            domain=domain,
            card_types=card_types,
            difficulty=difficulty,
            keywords=keywords or [],
            max_cards=chunk_target_cards,
            existing_cards=existing_cards or [],
        )

        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia tạo flashcard học tập. Chỉ trả về JSON array, không có text nào khác.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=4096,
            )

            raw_text = response.choices[0].message.content
            usage = response.usage

            if usage:
                total_usage_data["prompt_tokens"] += usage.prompt_tokens
                total_usage_data["completion_tokens"] += usage.completion_tokens
                total_usage_data["total_tokens"] += usage.total_tokens
                logger.info(f"[Groq] Chunk {i + 1} tokens: {usage.total_tokens}")

            cards = _parse_ai_response(raw_text)
            valid_chunk_cards = [c for c in cards if _validate_card(c)]

            invalid_count = len(cards) - len(valid_chunk_cards)
            if invalid_count > 0:
                logger.warning(
                    f"[Groq] Chunk {i + 1}: {invalid_count} cards bị loại do thiếu fields"
                )

            all_cards.extend(valid_chunk_cards)
            successful_chunks += 1

        except Exception as e:
            logger.warning(f"[Groq] Chunk {i + 1} failed: {e} — skipping")
            continue

    if successful_chunks == 0:
        return {
            "success": False,
            "cards": [],
            "raw_response": "",
            "model_used": GROQ_MODEL,
            "usage": total_usage_data,
            "error": "Tất cả các phần của tài liệu đều sinh flashcard thất bại.",
        }

    if total_usage_data["total_tokens"] > 0:
        ApiUsageLog.objects.create(
            user=user,
            action=f"generate_flashcards_{len(chunks)}_chunks",
            model_used=GROQ_MODEL,
            prompt_tokens=total_usage_data["prompt_tokens"],
            completion_tokens=total_usage_data["completion_tokens"],
            total_tokens=total_usage_data["total_tokens"],
        )

    # Normalize fields
    for card in all_cards:
        card.setdefault("example", "")
        card.setdefault("difficulty", difficulty)
        if card["card_type"] not in ["vocabulary", "grammar", "phrase", "qa"]:
            card["card_type"] = "vocabulary"

    # ── Hard dedup ──────────────────────────────────────
    unique_cards = []
    seen_fronts = (
        {c["front"].lower().strip() for c in existing_cards}
        if existing_cards
        else set()
    )

    duplicates_removed = 0
    for c in all_cards:
        front = c["front"].lower().strip()
        if front not in seen_fronts:
            seen_fronts.add(front)
            unique_cards.append(c)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        logger.info(f"[Groq] Dedup: removed {duplicates_removed} duplicate cards")

    # ── Fill to max_cards với existing cards ─────────────
    final_cards, reused_count = _fill_to_max(
        new_cards=unique_cards,
        existing_cards=existing_cards or [],
        max_cards=max_cards,
    )

    # ── Truncate nếu vượt max ────────────────────────────
    if len(final_cards) > max_cards:
        final_cards = final_cards[:max_cards]

    # ── Meta ─────────────────────────────────────────────
    new_count = len(unique_cards)
    delivered = len(final_cards)
    is_exhausted = new_count == 0 and reused_count == 0
    is_partial = delivered < max_cards

    logger.info(
        f"[Groq] Done — new={new_count}, reused={reused_count}, total={delivered}"
    )

    return {
        "success": True,
        "cards": final_cards,
        "raw_response": f"Generated successfully from {len(chunks)} chunks using {total_usage_data['total_tokens']} tokens.",
        "model_used": GROQ_MODEL,
        "usage": total_usage_data,
        "error": None,
        "meta": {
            "requested": max_cards,
            "delivered": delivered,
            "new_count": new_count,
            "reused_count": reused_count,
            "duplicates_removed": duplicates_removed,
            "is_exhausted": is_exhausted,
            "is_partial": is_partial,
        },
    }
