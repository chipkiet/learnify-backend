Spaced Repetition System (SRS) như Anki

Thuật toán SM-2 của Anki:
Mỗi lần user review flashcard → đánh giá độ khó:

0 - Blackout    → không nhớ gì
1 - Wrong       → sai hoàn toàn
2 - Hard        → nhớ ra nhưng khó
3 - Good        → nhớ được
4 - Easy        → dễ dàng
5 - Perfect     → quá dễ
Dựa vào đánh giá → tính interval (số ngày đến lần review tiếp theo):
Lần 1: interval = 1 ngày
Lần 2: interval = 6 ngày
Lần 3: interval = interval * easiness_factor
                            ↑
                  mặc định 2.5, thay đổi theo đánh giá

Database cần thêm:
Flashcard                    FlashcardReview
────────────────             ────────────────
id                           id
set_id (FK)                  flashcard_id (FK)
front                        user_id (FK)
back                         rating (0-5)
order                        reviewed_at
status                       
                             
FlashcardProgress (quan trọng nhất!)
────────────────────────────────────
id
flashcard_id (FK)
user_id (FK)
status          → new/learning/review/mastered
interval        → số ngày đến lần review tiếp
easiness_factor → độ khó (mặc định 2.5)
repetitions     → số lần đã review
due_date        → ngày review tiếp theo  ← QUAN TRỌNG NHẤT
last_reviewed   → lần review cuối

Flow SRS:
User mở app
      ↓
Lấy tất cả flashcard có due_date <= hôm nay
      ↓
Hiển thị flashcard
      ↓
User lật card → đánh giá (0-5)
      ↓
Tính interval mới theo SM-2
      ↓
Cập nhật due_date = hôm nay + interval mới
      ↓
Lần sau hiện đúng lúc cần review!

Thuật toán SM-2 cụ thể:
pythondef calculate_sm2(rating, repetitions, easiness_factor, interval):
    
    if rating >= 3:  # nhớ được
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness_factor)
        repetitions += 1
    else:  # không nhớ → reset
        repetitions = 0
        interval = 1

    # Cập nhật easiness_factor
    easiness_factor = easiness_factor + (
        0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)
    )
    easiness_factor = max(1.3, easiness_factor)  # tối thiểu 1.3

    return interval, easiness_factor, repetitions
```

---

### Status flow:
```
new → learning → review → mastered
 ↑                  ↓
 └──────────────────┘ (nếu rating < 3 → quay lại learning)
```

---

### Schema hoàn chỉnh:
```
User
 ├── Document (nhiều)
 │    └── FlashcardSet (nhiều)
 │         └── Flashcard (nhiều)
 │              └── FlashcardProgress (1 per user)
 │              └── FlashcardReview (nhiều - lịch sử)
 └── FlashcardSet (tự tạo, không từ document)
```

---

User ────────────────────── nhiều Document
User ────────────────────── nhiều FlashcardSet
User ────────────────────── nhiều FlashcardProgress
User ────────────────────── nhiều FlashcardReview

Document ────────────────── nhiều FlashcardSet

FlashcardSet ──────────────nhiều Flashcard
FlashcardSet ──────────────nhiều Tag (nhiều-nhiều)

Flashcard ─────────────────nhiều FlashcardProgress
Flashcard ─────────────────nhiều FlashcardReview