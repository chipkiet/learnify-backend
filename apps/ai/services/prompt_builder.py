# apps/ai/services/prompt_builder.py

from typing import List

DOMAIN_CONTEXT = {
    'english': 'tài liệu học tiếng Anh',
    'history': 'tài liệu lịch sử',
    'science': 'tài liệu khoa học',
    'math':    'tài liệu toán học',
    'other':   'tài liệu học tập',
}

CARD_TYPE_INSTRUCTIONS = {
    'vocabulary': """
- VOCABULARY cards: từ/cụm từ quan trọng trong tài liệu
  + front: từ hoặc cụm từ tiếng Anh
  + back: nghĩa tiếng Việt rõ ràng
  + example: 1 câu ví dụ trích từ tài liệu hoặc tương tự""",

    'grammar': """
- GRAMMAR cards: cấu trúc ngữ pháp xuất hiện trong tài liệu
  + front: tên cấu trúc (VD: "Relative Clause - who")
  + back: công thức + giải thích ngắn tiếng Việt
  + example: câu ví dụ minh họa cấu trúc đó""",

    'phrase': """
- PHRASE cards: cụm từ cố định, idiom, collocations
  + front: cụm từ tiếng Anh
  + back: nghĩa + cách dùng tiếng Việt
  + example: câu ví dụ trong ngữ cảnh thực tế""",

    'qa': """
- QA cards: câu hỏi kiểm tra hiểu bài từ nội dung tài liệu
  + front: câu hỏi tiếng Việt về nội dung
  + back: câu trả lời đầy đủ tiếng Việt
  + example: để trống "" """,
}

DIFFICULTY_INSTRUCTION = {
    'easy':         'Ưu tiên từ/cấu trúc đơn giản, phổ biến, dễ nhớ.',
    'intermediate': 'Cân bằng giữa từ phổ biến và từ nâng cao.',
    'hard':         'Ưu tiên từ/cấu trúc nâng cao, học thuật, ít gặp.',
}


def _build_qa_instruction(domain: str) -> str:
    if domain == "english":
        return """
  
  -QA cards: English comprehensive questions to test understanding
    + front: question in English about the content
    + back : answer in English( add Vietnamese explanation in parentheses if helpful)
    + example: ""  
"""
    else:
        return """
  -QA cards: câu hỏi kiểm tra hiểu bài từ nội dung tài liệu
    + front: câu hỏi tiếng Việt về nội dung
    + back : câu trả lời đầy đủ bằng tiếng Việt
    + example : ""
"""


def build_prompt(
    extracted_text: str,
    domain: str,
    card_types: List[str],
    difficulty: str,
    keywords: List[str] = None,
    max_cards: int = 20,
) -> str:
    """
    Build prompt hoàn chỉnh gửi cho Groq.
    Trả về string prompt.
    """

    domain_label    = DOMAIN_CONTEXT.get(domain, DOMAIN_CONTEXT['other'])
    difficulty_note = DIFFICULTY_INSTRUCTION.get(difficulty, DIFFICULTY_INSTRUCTION['intermediate'])

    # Build card type instructions theo những gì user chọn
    card_instructions = ""
    for ct in card_types:
        if ct == "qa":
            card_instructions += _build_qa_instruction(domain)

        elif ct in CARD_TYPE_INSTRUCTIONS:
            card_instructions += CARD_TYPE_INSTRUCTIONS[ct]

    # Keywords section — optional
    keyword_note = ""
    if keywords:
        kw_str = ", ".join(keywords)
        keyword_note = f"\nƯu tiên tạo cards liên quan đến các từ khóa sau: {kw_str}.\n"

    prompt = f"""Bạn là chuyên gia tạo flashcard học tập. Hãy phân tích đoạn text sau và tạo flashcards chất lượng cao.

## THÔNG TIN ĐẦU VÀO
- Loại tài liệu: {domain_label}
- Độ khó: {difficulty_note}
- Số lượng cards tối đa: {max_cards}
{keyword_note}
## LOẠI CARDS CẦN TẠO
{card_instructions}

## YÊU CẦU QUAN TRỌNG
1. Chỉ tạo cards từ nội dung thực sự có trong text, không bịa đặt.
2. Mỗi card phải độc lập, rõ ràng, học được ngay.
3. Phân bổ đều các loại card được yêu cầu.
4. KHÔNG trả về bất kỳ text nào ngoài JSON.
5. Trả về đúng format JSON array sau:

[
  {{
    "card_type": "vocabulary",
    "front": "nội dung mặt trước",
    "back": "nội dung mặt sau",
    "example": "câu ví dụ",
    "difficulty": "easy|medium|hard"
  }}
]

## NỘI DUNG TÀI LIỆU
{extracted_text[:6000]}
"""
    return prompt
