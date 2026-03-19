# apps/study/services/sm2.py

from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


def _update_ef(ef: float, quality: int) -> float:
    """Công thức EF chuẩn Wozniak — bậc 2."""
    new_ef = ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    return max(1.3, round(new_ef, 4))


def calculate_sm2(
    ease_factor: float, interval: int, repetitions: int, quality: int
) -> dict:
    """
    Thuật toán SM-2 chuẩn Wozniak.

    quality: 0-5
      0 = Quên hoàn toàn
      1 = Sai nhưng nhớ ra khi thấy đáp án
      2 = Sai nhưng cảm giác dễ nhớ lại
      3 = Đúng nhưng phải suy nghĩ nhiều
      4 = Đúng sau một chút do dự
      5 = Đúng hoàn toàn, nhớ ngay
    """
    if not (0 <= quality <= 5):
        raise ValueError(f"Quality phải từ 0-5, nhận được: {quality}")

    # Tính EF mới trước — dùng cho cả 2 nhánh
    new_ease_factor = _update_ef(ease_factor, quality)

    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * new_ease_factor)

    next_review_at = datetime.now(tz=timezone.utc) + timedelta(days=new_interval)

    result = {
        "ease_factor": new_ease_factor,
        "interval": new_interval,
        "repetitions": new_repetitions,
        "next_review_at": next_review_at,
    }

    logger.debug(
        f"[SM2] q={quality} | "
        f"ef: {ease_factor:.4f}→{new_ease_factor:.4f} | "
        f"interval: {interval}→{new_interval}d | "
        f"rep: {repetitions}→{new_repetitions}"
    )

    return result


def apply_review(card, quality: int) -> dict:
    """
    Wrapper: nhận FlashCard instance + quality.
    Update card fields, KHÔNG gọi save() — để view tự quyết định.
    """
    result = calculate_sm2(
        ease_factor=card.ease_factor,
        interval=card.interval,
        repetitions=card.repetitions,
        quality=quality,
    )

    card.ease_factor = result["ease_factor"]
    card.interval = result["interval"]
    card.repetitions = result["repetitions"]
    card.next_review_at = result["next_review_at"]

    return result
