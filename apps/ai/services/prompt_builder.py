# apps/ai/services/prompt_builder.py
"""
Prompt builder v2 — 3 domains thực tế:

  english  → Học ngôn ngữ tiếng Anh:
               vocab/grammar/phrase = khai thác LANGUAGE (từ, cấu trúc, cụm từ)
               qa = câu hỏi hiểu bài bằng tiếng Anh

  academic → Tài liệu học thuật bất kỳ (IT, khoa học, lịch sử, toán, y...):
               vocab   = thuật ngữ chuyên ngành → định nghĩa tiếng Việt
               grammar = khái niệm/nguyên lý cốt lõi → giải thích tiếng Việt
               phrase  = quy trình/công thức/định luật → áp dụng
               qa      = câu hỏi dựa vào dữ kiện + phân tích, TOÀN tiếng Việt

  other    → Tài liệu tổng hợp, không rõ chủ đề:
               bám sát 100% nội dung text, không áp đặt format

VẤN ĐỀ CỦA PHIÊN BẢN CŨ (đã fix):
  - CARD_TYPE_INSTRUCTIONS['vocabulary'] hardcode "từ tiếng Anh"
    → mọi domain đều ra cards kiểu English vocab
  - domain_label chỉ xuất hiện 1 lần, AI bỏ qua
  - Không có domain_reminder → AI "drift" theo nội dung text
"""

from typing import List

# ══════════════════════════════════════════════════════
# DOMAIN LABELS  (hiển thị trong prompt)
# ══════════════════════════════════════════════════════
DOMAIN_CONTEXT = {
    "english": "tài liệu học TIẾNG ANH",
    "academic": "tài liệu học thuật / chuyên ngành",
    "other": "tài liệu tổng hợp",
}

# ══════════════════════════════════════════════════════
# DIFFICULTY
# ══════════════════════════════════════════════════════
DIFFICULTY_INSTRUCTION = {
    "easy": (
        "Ưu tiên nội dung cơ bản, phổ biến, dễ hiểu. "
        "Câu hỏi trực tiếp, câu trả lời ngắn gọn. "
        "Tránh nội dung quá chuyên sâu hoặc hiếm gặp."
    ),
    "medium": (
        "Cân bằng giữa nội dung cơ bản và nâng cao. "
        "Bao gồm cả câu hỏi tái hiện và câu hỏi yêu cầu hiểu bài."
    ),
    "hard": (
        "Ưu tiên nội dung nâng cao, chuyên sâu, ít gặp. "
        "Câu hỏi yêu cầu phân tích, tổng hợp, vận dụng — không chỉ nhớ lại."
    ),
}

# ══════════════════════════════════════════════════════
# CARD_MATRIX — Hybrid v3 (optimized for tokens)
# Giảm ~45% tokens so với v2, vẫn đủ rõ cho AI
# ══════════════════════════════════════════════════════
CARD_MATRIX = {
    "english": {
        "vocabulary": """EN VOCAB | front: word/phrase | back: VI meaning + IPA if needed | example: sentence
✓ from text | ✗ no content/topic questions""",
        "grammar": """EN GRAMMAR | front: structure name | back: formula + VI explanation | example: correct sentence
✓ must appear in text | ✗ no made-up structures""",
        "phrase": """EN PHRASE | front: phrase (2+ words) | back: VI meaning + usage context | example: natural sentence
✓ from text | ✗ single words only""",
        "qa": """EN QA | front: question in English | back: full English answer | example: (empty)
✓ require understanding | ✗ no trivial facts""",
    },
    "academic": {
        "vocabulary": """TERM | front: technical term | back: VI definition | example: usage from text
✓ domain-specific | ✗ common words""",
        "grammar": """PRINCIPLE | front: principle/model/theory name | back: mechanism explanation (VI) + formula if exists | example: application
✓ real concepts | ✗ no borrow from other domains""",
        "phrase": """PROCESS | front: method/algorithm/procedure name | back: step-by-step VI explanation | example: use case
✓ must be reproducible | ✗ vague descriptions""",
        "qa": """QA_VN | front: VI question | back: VI answer from text | example: (empty)
✓ reasoning required | ✗ no outside knowledge""",
        "qa_en": """QA_EN | front: technical question in English | back: technical VI answer (+ EN note if complex) | example: (empty)
✓ deep domain knowledge | ✗ NOT vocabulary/grammar Q""",
    },
    "other": {
        "vocabulary": """KEYWORD | front: keyword from text | back: VI meaning | example: original sentence
✓ from text | ✗ no extra info""",
        "grammar": """CONCEPT | front: concept name or "X là gì?" | back: VI explanation | example: application
✓ stay close to text | ✗ no additions""",
        "phrase": """SUMMARY | front: main idea question | back: VI summary | example: quote if available
✓ core content only""",
        "qa": """QA | front: VI question | back: VI answer | example: (empty)
✓ no outside knowledge | ✗ no content drift""",
    },
}

# ══════════════════════════════════════════════════════
# DOMAIN REMINDER — Short version (prevent AI drift)
# ══════════════════════════════════════════════════════
DOMAIN_REMINDER = {
    "english": """
⚠️ ENGLISH LEARNING: Extract LANGUAGE only (vocab, grammar, phrase, QA in EN).
   NOT: content/topic questions. If text is about history but in English,
   cards are about ENGLISH language, not history facts.""",
    "academic": """
⚠️ ACADEMIC DOMAIN: Extract KNOWLEDGE (concepts, principles, procedures, deep QA).
   Use VIETNAMESE except qa_en cards.
   NOT: English vocabulary/grammar cards.""",
    "other": """
⚠️ NO RIGID FORMAT: Follow text strictly. Use Vietnamese. No outside knowledge.
   Keep close to original content.""",
}

# ══════════════════════════════════════════════════════
# BUILD PROMPT
# ══════════════════════════════════════════════════════
def build_prompt(
    extracted_text: str,
    domain: str,
    card_types: List[str],
    difficulty: str,
    keywords: List[str] = None,
    max_cards: int = 20,
) -> str:
    """
    Build prompt gửi cho Groq.
    Sử dụng CARD_MATRIX hybrid v3: gọn gàng, đủ rõ, giảm ~45% tokens.
    """
    # Fallback về 'other' nếu domain không hợp lệ
    if domain not in CARD_MATRIX:
        domain = "other"

    domain_label = DOMAIN_CONTEXT[domain]
    difficulty_note = DIFFICULTY_INSTRUCTION.get(
        difficulty, DIFFICULTY_INSTRUCTION["medium"]
    )
    domain_reminder = DOMAIN_REMINDER[domain]
    domain_matrix = CARD_MATRIX[domain]

    # Build instructions cho các card types được chọn
    card_instructions = ""
    valid_card_types = []
    for ct in card_types:
        if ct in domain_matrix:
            valid_card_types.append(ct)
            card_instructions += f"\n{domain_matrix[ct].strip()}\n"

    # Fallback nếu không có card type hợp lệ
    if not valid_card_types:
        valid_card_types = ["qa"]
        card_instructions = f"\n{domain_matrix.get('qa', '')}\n"

    # Keywords
    keyword_note = ""
    if keywords:
        kw_str = ", ".join(keywords)
        keyword_note = f"\nFocus on: {kw_str}.\n"

    # Per-card distribution note with buffer
    target_cards = int(max_cards * 1.25) + 1
    if len(valid_card_types) > 1:
        distribution_note = f"Target ~{target_cards} cards, distribute evenly across {len(valid_card_types)} types."
    else:
        distribution_note = f"Target ~{target_cards} {valid_card_types[0]} cards."

    prompt = f"""Bạn là chuyên gia tạo flashcard học tập. Phân tích text và tạo flashcards chất lượng cao.

## THÔNG TIN
- Loại tài liệu: {domain_label}
- Độ khó: {difficulty_note.strip()}
- Mục tiêu: {distribution_note}
{keyword_note}
## ⚠️ QUAN TRỌNG
{domain_reminder.strip()}

## LOẠI CARDS CẦN TẠO
{card_instructions.strip()}

## YÊU CẦU
1. CHỈ dùng nội dung THỰC SỰ CÓ trong text.
2. Mỗi card độc lập, đầy đủ, học được ngay.
3. Tuân thủ ĐÚNG ngôn ngữ được chỉ định.
4. card_type phải là: {', '.join(f'"{t}"' for t in valid_card_types)}.
5. difficulty phải là: "easy", "medium", "hard".
6. Trả về CHỈ JSON array — không markdown.

## FORMAT JSON
[
  {{
    "card_type": "{valid_card_types[0]}",
    "front": "nội dung mặt trước",
    "back": "nội dung mặt sau",
    "example": "ví dụ hoặc empty string",
    "difficulty": "easy"
  }}
]

## NỘI DUNG TÀI LIỆU
{extracted_text[:6000]}
"""
    return prompt
