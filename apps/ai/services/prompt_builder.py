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
    "intermediate": (
        "Cân bằng giữa nội dung cơ bản và nâng cao. "
        "Bao gồm cả câu hỏi tái hiện và câu hỏi yêu cầu hiểu bài."
    ),
    "hard": (
        "Ưu tiên nội dung nâng cao, chuyên sâu, ít gặp. "
        "Câu hỏi yêu cầu phân tích, tổng hợp, vận dụng — không chỉ nhớ lại."
    ),
}

# ══════════════════════════════════════════════════════
# MATRIX: CARD_MATRIX[domain][card_type] → instruction
#
# Mỗi ô là một instruction độc lập, không dùng chung.
# Tên "grammar" / "phrase" là internal key — label hiển
# thị cho user ở frontend khác nhau theo domain.
# ══════════════════════════════════════════════════════
CARD_MATRIX = {
    # ─── ENGLISH ─────────────────────────────────────
    # Mục tiêu: khai thác NGÔN NGỮ trong text, không phải nội dung/chủ đề.
    # Dù text nói về lịch sử/khoa học, cards vẫn phải là ENGLISH LANGUAGE cards.
    "english": {
        "vocabulary": """
Loại VOCABULARY — Từ vựng tiếng Anh:
  - front : từ hoặc cụm từ tiếng Anh quan trọng, đúng như trong text
  - back  : nghĩa tiếng Việt rõ ràng + phiên âm IPA nếu từ khó đọc
  - example: 1 câu ví dụ ngắn chứa từ đó, trích từ text hoặc tương tự
  Ưu tiên: từ học thuật, từ hay gặp trong văn viết, từ dễ nhầm nghĩa.
  KHÔNG tạo cards về sự kiện/nội dung — chỉ khai thác từ ngữ.""",
        "grammar": """
Loại GRAMMAR — Cấu trúc ngữ pháp tiếng Anh:
  - front : tên cấu trúc ngắn gọn (VD: "Passive Voice — past", "Relative Clause — which")
  - back  : công thức rõ ràng + giải thích ngắn tiếng Việt (khi nào dùng, lưu ý gì)
  - example: câu ví dụ minh họa ĐÚNG cấu trúc đó, trích hoặc tương tự text
  Chỉ tạo grammar card cho cấu trúc THỰC SỰ XUẤT HIỆN trong text.
  KHÔNG bịa cấu trúc không có trong tài liệu.""",
        "phrase": """
Loại PHRASE — Cụm từ cố định tiếng Anh:
  - front : cụm từ / idiom / collocation nguyên văn tiếng Anh
  - back  : nghĩa tiếng Việt + ngữ cảnh sử dụng (formal/informal, lĩnh vực nào)
  - example: câu ví dụ trong ngữ cảnh thực tế, tự nhiên
  Ưu tiên: phrasal verbs, academic phrases, fixed expressions đặc trưng.
  KHÔNG tạo phrase card cho từ đơn — phải là cụm từ 2+ từ.""",
        "qa": """
Loại QA — Câu hỏi hiểu bài BẰNG TIẾNG ANH:
  - front  : câu hỏi tiếng Anh (What / Why / How / Explain / Compare...)
  - back   : câu trả lời tiếng Anh đầy đủ. Nếu cần, thêm giải thích Việt trong ngoặc đơn.
  - example: "" (để trống)
  Câu hỏi phải yêu cầu HIỂU BÀI thực sự — không chỉ điền số/tên vào chỗ trống.
  Tránh câu hỏi "When was X?" — ưu tiên "Why did X happen?" / "How does X work?".""",
    },
    # ─── ACADEMIC ────────────────────────────────────
    # Mục tiêu: khai thác KIẾN THỨC CHUYÊN NGÀNH từ tài liệu học thuật.
    # Hoạt động với mọi lĩnh vực: IT, khoa học, y, lịch sử, kinh tế...
    # TẤT CẢ cards bằng tiếng Việt.
    "academic": {
        "vocabulary": """
Loại THUẬT NGỮ — Khái niệm chuyên ngành:
  - front : thuật ngữ / khái niệm chuyên ngành (giữ nguyên tên gốc nếu là tiếng Anh)
  - back  : định nghĩa chính xác bằng tiếng Việt, bao gồm ngữ cảnh sử dụng
  - example: câu trích từ tài liệu có chứa thuật ngữ đó, hoặc ví dụ ứng dụng thực tế
  Ưu tiên: thuật ngữ kỹ thuật, khái niệm nền tảng, định nghĩa quan trọng.
  KHÔNG tạo card cho từ thông thường — chỉ thuật ngữ đặc thù của lĩnh vực.""",
        "grammar": """
Loại NGUYÊN LÝ — Khái niệm & nguyên lý cốt lõi:
  - front : tên nguyên lý / định luật / mô hình / quy trình (VD: "Định luật Moore", "Mô hình OSI")
  - back  : giải thích đầy đủ tiếng Việt — cơ chế hoạt động, ý nghĩa, điều kiện áp dụng
  - example: ứng dụng thực tế hoặc ví dụ minh họa cụ thể
  Ưu tiên: các nguyên lý có thể áp dụng, không chỉ là sự kiện đơn thuần.
  Nếu có công thức toán/khoa học: ghi rõ ký hiệu và đơn vị.""",
        "phrase": """
Loại QUY TRÌNH — Các bước & phương pháp:
  - front : tên quy trình / phương pháp / thuật toán / framework
  - back  : các bước thực hiện theo thứ tự tiếng Việt, rõ ràng và có thể áp dụng ngay
  - example: tình huống / bài toán điển hình áp dụng quy trình đó
  Ưu tiên: quy trình có bước rõ ràng, phương pháp có thể tái hiện.
  Dùng số thứ tự (1. 2. 3.) trong phần back nếu có nhiều bước.""",
        "qa": """
Loại Q&A TIẾNG VIỆT — Câu hỏi phân tích chuyên ngành (TOÀN tiếng Việt):
  - front  : câu hỏi tiếng Việt — ưu tiên dạng: "Tại sao...?", "Giải thích...", "So sánh...", "Phân tích..."
  - back   : câu trả lời đầy đủ tiếng Việt, dựa hoàn toàn vào nội dung tài liệu
  - example: "" (để trống)
  Câu hỏi phải yêu cầu TƯ DUY — không chỉ tái hiện nguyên văn.
  Nếu tài liệu có dữ liệu/số liệu: tạo câu hỏi khai thác ý nghĩa của số liệu đó.
  KHÔNG hỏi thông tin ngoài phạm vi tài liệu.""",
        "qa_en": """
Loại Q&A TIẾNG ANH — Câu hỏi chuyên ngành sâu bằng tiếng Anh:
  - front  : câu hỏi tiếng Anh — dạng kiểm tra/chứng chỉ chuyên ngành:
             "Explain...", "What is the difference between X and Y?",
             "How does X work?", "Why is X preferred over Y in Z scenario?"
  - back   : câu trả lời tiếng Anh đầy đủ, chính xác về mặt kỹ thuật/học thuật.
             Nếu thuật ngữ quan trọng: thêm giải thích Việt trong ngoặc đơn.
  - example: "" (để trống)
  Câu hỏi phải khai thác KIẾN THỨC CHUYÊN NGÀNH SÂU — không phải comprehension ngôn ngữ.
  Ưu tiên dạng câu hỏi xuất hiện trong đề thi chứng chỉ, phỏng vấn kỹ thuật.
  KHÔNG tạo câu hỏi về từ vựng hay ngữ pháp tiếng Anh.""",
    },
    # ─── OTHER ───────────────────────────────────────
    # Fallback: bám sát 100% nội dung, không áp đặt format.
    "other": {
        "vocabulary": """
Loại TỪ KHÓA — Thuật ngữ & từ khóa trong tài liệu:
  - front : thuật ngữ / từ khóa quan trọng, giữ nguyên ngôn ngữ trong text
  - back  : giải thích ý nghĩa trong ngữ cảnh tài liệu, bằng tiếng Việt
  - example: câu văn trích từ tài liệu có chứa từ khóa đó
  Dựa hoàn toàn vào text — không áp đặt chủ đề.""",
        "grammar": """
Loại KHÁI NIỆM — Ý tưởng cốt lõi trong tài liệu:
  - front : câu hỏi "X là gì?" hoặc tên khái niệm chính
  - back  : giải thích đầy đủ tiếng Việt theo đúng nội dung tài liệu
  - example: ví dụ hoặc ứng dụng từ tài liệu
  Tóm tắt ý chính — không diễn giải thêm ngoài phạm vi text.""",
        "phrase": """
Loại TÓM TẮT — Điểm chính & kết luận:
  - front : câu hỏi về luận điểm chính (VD: "Kết luận chính của tài liệu là gì?")
  - back  : tóm tắt điểm chính hoặc kết luận bằng tiếng Việt
  - example: trích dẫn ngắn từ tài liệu nếu có
  Phục vụ hiểu bài tổng quan.""",
        "qa": """
Loại Q&A — Câu hỏi hiểu bài tổng hợp:
  - front  : câu hỏi tiếng Việt bám sát nội dung (Nêu, Phân tích, So sánh, Giải thích...)
  - back   : câu trả lời đầy đủ tiếng Việt, chỉ dựa vào thông tin trong tài liệu
  - example: "" (để trống)
  KHÔNG hỏi thông tin ngoài tài liệu.""",
    },
}

# ══════════════════════════════════════════════════════
# DOMAIN REMINDER
# Đây là phần quan trọng nhất để ngăn AI "drift".
# Được nhúng nổi bật vào prompt, không phải metadata mờ.
# ══════════════════════════════════════════════════════
DOMAIN_REMINDER = {
    "english": """
QUAN TRỌNG — Đây là tài liệu HỌC TIẾNG ANH:
  ✓ Khai thác NGÔN NGỮ: từ vựng, cấu trúc, cụm từ, cách diễn đạt.
  ✓ QA cards dùng TIẾNG ANH, không dùng tiếng Việt.
  ✗ KHÔNG tạo cards về nội dung/chủ đề của tài liệu.
  ✗ KHÔNG tạo cards lịch sử, khoa học — dù text nói về lịch sử hay khoa học.
  → Ví dụ: text "The treaty was signed in 1945" → card vocabulary: "treaty" (n.) = hiệp ước
    KHÔNG phải: "Hiệp ước được ký vào năm nào?" (đó là history card, sai domain)""",
    "academic": """
QUAN TRỌNG — Đây là tài liệu HỌC THUẬT / CHUYÊN NGÀNH:
  ✓ Khai thác KIẾN THỨC: thuật ngữ, nguyên lý, quy trình, dữ kiện.
  ✓ Card type "qa"    → câu hỏi + trả lời TIẾNG VIỆT hoàn toàn.
  ✓ Card type "qa_en" → câu hỏi + trả lời TIẾNG ANH, chuyên ngành sâu.
  ✓ Vocabulary/grammar/phrase → TIẾNG VIỆT.
  ✗ KHÔNG tạo cards học từ vựng tiếng Anh — dù text có nhiều từ tiếng Anh.
  ✗ KHÔNG tạo grammar/phrase cards kiểu English learning.
  → Ví dụ qa_en: "Explain the difference between TCP and UDP"
                  → trả lời bằng tiếng Anh, kỹ thuật chính xác
  → Ví dụ qa:    "Tại sao TCP đáng tin cậy hơn UDP?"
                  → trả lời bằng tiếng Việt đầy đủ""",
    "other": """
QUAN TRỌNG — Tài liệu tổng hợp, không rõ chủ đề:
  ✓ Bám sát 100% nội dung text được cung cấp.
  ✓ Dùng tiếng Việt cho mọi giải thích.
  ✗ KHÔNG áp đặt format từ domain khác.
  ✗ KHÔNG tạo thông tin ngoài phạm vi tài liệu.""",
}

# ══════════════════════════════════════════════════════
# CARD TYPE DISPLAY NAMES  (dùng trong prompt header)
# Phải đồng bộ với CARD_TYPES_BY_DOMAIN trong GenerateModal.jsx
# ══════════════════════════════════════════════════════
CARD_TYPE_DISPLAY = {
    "english": {
        "vocabulary": "VOCABULARY (từ vựng)",
        "grammar": "GRAMMAR (ngữ pháp)",
        "phrase": "PHRASE (cụm từ cố định)",
        "qa": "Q&A (hiểu bài tiếng Anh)",
    },
    "academic": {
        "vocabulary": "THUẬT NGỮ (khái niệm chuyên ngành)",
        "grammar": "NGUYÊN LÝ (khái niệm & nguyên lý)",
        "phrase": "QUY TRÌNH (các bước & phương pháp)",
        "qa": "Q&A TIẾNG VIỆT (phân tích & dữ kiện)",
        "qa_en": "Q&A TIẾNG ANH (chuyên ngành sâu)",
    },
    "other": {
        "vocabulary": "TỪ KHÓA",
        "grammar": "KHÁI NIỆM",
        "phrase": "TÓM TẮT",
        "qa": "Q&A (tổng hợp)",
    },
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

    Thay đổi so với v1:
    - Domain reminder được nhúng nổi bật (không phải metadata)
    - Mỗi (domain, card_type) có instruction riêng hoàn toàn
    - Card type names hiển thị theo domain → AI hiểu đúng nhiệm vụ
    - Ví dụ phản-ví dụ trong reminder → AI hiểu ranh giới rõ hơn
    """
    # Fallback về 'other' nếu domain không hợp lệ
    if domain not in CARD_MATRIX:
        domain = "other"

    domain_label = DOMAIN_CONTEXT[domain]
    difficulty_note = DIFFICULTY_INSTRUCTION.get(
        difficulty, DIFFICULTY_INSTRUCTION["intermediate"]
    )
    domain_reminder = DOMAIN_REMINDER[domain]

    domain_matrix = CARD_MATRIX[domain]
    domain_display = CARD_TYPE_DISPLAY.get(domain, CARD_TYPE_DISPLAY["other"])

    # Build instructions cho các card types được chọn
    card_instructions = ""
    valid_card_types = []
    for ct in card_types:
        if ct in domain_matrix:
            valid_card_types.append(ct)
            display_name = domain_display.get(ct, ct.upper())
            card_instructions += f"\n### {display_name}\n{domain_matrix[ct].strip()}\n"

    # Fallback nếu không có card type hợp lệ
    if not valid_card_types:
        valid_card_types = ["qa"]
        card_instructions = domain_matrix.get("qa", "")

    # Keywords
    keyword_note = ""
    if keywords:
        kw_str = ", ".join(keywords)
        keyword_note = f"\nƯu tiên tạo cards liên quan đến: {kw_str}.\n"

    # Per-card distribution note
    # Buffer 25% để accommodation validation & filtering
    target_cards = int(max_cards * 1.25) + 1

    if len(valid_card_types) > 1:
        per_type = max(1, target_cards // len(valid_card_types))
        distribution_note = (
            f"Phân bổ đều: khoảng {per_type} cards cho mỗi loại "
            f"({', '.join(valid_card_types)}). Tổng khoảng {target_cards} cards."
        )
    else:
        distribution_note = (
            f"Tạo khoảng {target_cards} cards loại {valid_card_types[0]}."
        )

    prompt = f"""Bạn là chuyên gia tạo flashcard học tập. Phân tích text sau và tạo flashcards chất lượng cao.

## THÔNG TIN ĐẦU VÀO
- Loại tài liệu: **{domain_label}**
- Độ khó: {difficulty_note}
- Phân bổ: {distribution_note}
{keyword_note}
## {domain_reminder.strip()}

## LOẠI CARDS CẦN TẠO
{card_instructions}

## YÊU CẦU BẮT BUỘC
1. Chỉ tạo cards từ nội dung THỰC SỰ CÓ trong text — không bịa đặt.
2. Mỗi card phải độc lập, đầy đủ, học được ngay mà không cần đọc text gốc.
3. Tuân thủ ĐÚNG ngôn ngữ đã chỉ định trong từng loại card.
4. Trường "card_type" trong JSON phải là một trong: {', '.join(f'"{t}"' for t in valid_card_types)}.
5. Trường "difficulty" phải là một trong: "easy", "medium", "hard".
6. KHÔNG trả về bất kỳ text nào ngoài JSON array — không markdown, không giải thích.

## FORMAT JSON (trả về đúng array này, không có gì khác):
[
  {{
    "card_type": "{valid_card_types[0]}",
    "front": "nội dung mặt trước",
    "back": "nội dung mặt sau",
    "example": "câu ví dụ hoặc chuỗi rỗng",
    "difficulty": "easy"
  }}
]

## NỘI DUNG TÀI LIỆU
{extracted_text[:6000]}
"""
    return prompt
