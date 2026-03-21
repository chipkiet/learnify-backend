"""
Fill-in-blank answer checker.

Normalize rồi so sánh — không dùng == cứng vì:
  - "paris" vs "Paris" → case khác
  - "Strait of Hormuz" vs "strait of hormuz" → chấp nhận
  - "Paris (thủ đô)" vs "Paris" → user gõ đủ hoặc thiếu phần Việt

Chiến lược:
  1. Lowercase + strip cả 2 phía
  2. Lấy phần chính của correct (trước dấu ngoặc)
  3. So sánh exact sau normalize
  4. Nếu không khớp: kiểm tra correct có nằm trong user_answer không (partial)
     VD: user gõ "Paris, France" khi đúng là "Paris" → vẫn đúng
"""


import re
import unicodedata


def _normalize(text: str) -> str:
    """Lowercase, strip, bỏ dấu câu thừa."""
    text = text.strip().lower()
    # Bỏ dấu câu ở đầu/cuối
    text = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", text)
    return text


def _extract_main(text: str) -> str:
    """
    Lấy phần chính trước dấu ngoặc.
    "Paris (thủ đô nước Pháp)" → "Paris"
    "TCP (Transmission Control Protocol)" → "TCP"
    """
    m = re.match(r"^(.*?)\s*\(", text.strip())
    return m.group(1).strip() if m else text.strip()


def check_fill_in_blank(user_answer: str, correct_answer: str) ->bool :
    """
    Chấm điểm fill-in-blank.

    Returns True nếu đúng, False nếu sai.
    """

    if not user_answer or not user_answer.strip():
        return False

    user_norm = _normalize(user_answer)
    correct_main = _normalize(_extract_main(correct_answer))
    correct_full = _normalize(correct_answer)

    if user_norm == correct_main:
        return True

    if user_norm == correct_full :
        return True

    if correct_main and correct_main in user_norm:
        return True

    if correct_main and len(correct_main) >= 3 and user_norm.startswith(correct_main):
        return True

    return False


def get_hint(correct_answer: str, hint_level: int = 1) -> str:
    """
    Tạo gợi ý từ đáp án đúng.
    hint_level=1: hiện ký tự đầu + số ký tự còn lại
    "Paris" → "P____" (4 ký tự ẩn)
    """
    main = _extract_main(correct_answer)
    if not main or len(main) < 2:
        return f"{len(main)} ký tự"

    first = main[0]
    rest = len(main) - 1
    return f"{first}{'_' * rest}"


