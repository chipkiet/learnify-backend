# apps/quiz/services/distractor.py
"""
Idea 1 — Distractor thông minh từ SRS data.

Logic chọn distractor:
  Với mỗi correct_card, lấy 3 distractor từ các card khác trong set.
  Ưu tiên card có ease_factor THẤP nhất + interval NGẮN nhất của user
  → đây là những card user đang khó nhớ nhất → dễ nhầm nhất → distractor thực tế nhất.

  Fallback theo thứ tự:
    1. Cùng card_type, sort by (ease_factor ASC, interval ASC)
    2. Khác card_type nếu không đủ
    3. Random nếu vẫn thiếu
"""

import random
import re
from apps.flashcards.models import FlashCard


def parse_back_main(text: str) -> str:
    """
    Lấy phần chính của back text, bỏ phần giải thích trong ngoặc.
    "Paris (thủ đô nước Pháp)" → "Paris"
    """
    m = re.match(r"^(.*?)\s*\([^)]+\)\s*$", text.strip(), re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def get_distractors(correct_card: FlashCard, all_cards: list, n: int = 3) -> list:
    """
    Trả về list n FlashCard làm distractor cho correct_card.

    Args:
        correct_card : card đang là câu hỏi
        all_cards    : toàn bộ cards trong set (fetch 1 lần bên ngoài)
        n            : số distractor cần (default 3)
    """
    candidates = [c for c in all_cards if c.id != correct_card.id]

    if len(candidates) <= n:
        return candidates

    def weakness_key(c):
        # Chưa học (next_review_at=None) → ease_factor mặc định 2.5
        # Thấp hơn = yếu hơn = distractor tốt hơn
        return (c.ease_factor, c.interval)

    # Bước 1: ưu tiên cùng card_type
    same_type = sorted(
        [c for c in candidates if c.card_type == correct_card.card_type],
        key=weakness_key,
    )

    if len(same_type) >= n:
        # Lấy top yếu nhất, thêm chút ngẫu nhiên trong pool 2×n
        pool = same_type[: max(n * 2, 6)]
        random.shuffle(pool)
        return pool[:n]

    # Bước 2: bổ sung từ card_type khác
    result = same_type[:]
    other = sorted(
        [c for c in candidates if c.card_type != correct_card.card_type],
        key=weakness_key,
    )
    needed = n - len(result)
    pool = other[: max(needed * 2, 4)]
    random.shuffle(pool)
    result += pool[:needed]
    return result[:n]


def build_options(correct_card: FlashCard, distractor_cards: list) -> dict:
    """
    Ghép correct + 3 distractor → shuffle vào A/B/C/D.

    Returns:
        {
            option_a, option_b, option_c, option_d,
            correct_option: 'a'|'b'|'c'|'d',
            correct_answer: str,   # phần main của correct back
        }
    """
    correct_text = parse_back_main(correct_card.back)
    distractor_texts = [parse_back_main(c.back) for c in distractor_cards[:3]]

    # Pad nếu thiếu distractor (set quá ít cards)
    while len(distractor_texts) < 3:
        distractor_texts.append("—")

    options = distractor_texts[:3] + [correct_text]
    random.shuffle(options)

    labels = ["a", "b", "c", "d"]
    correct_option = labels[options.index(correct_text)]

    return {
        "option_a": options[0],
        "option_b": options[1],
        "option_c": options[2],
        "option_d": options[3],
        "correct_option": correct_option,
        "correct_answer": correct_text,
    }
