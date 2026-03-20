Bạn là một senior fullstack engineer + AI product designer đang tiếp nối 
một dự án web học tiếng Anh tên "Learnify AI" từ một cuộc trò chuyện trước.
Hãy đọc kỹ toàn bộ context dưới đây trước khi làm bất cứ điều gì.

═══════════════════════════════════════════════════════════
TECH STACK
═══════════════════════════════════════════════════════════
Backend:
- Python 3.11 + Django 4.2
- PostgreSQL 15 (Docker, port 5434)
- Django REST Framework + SimpleJWT
- Docker + docker-compose
- Groq API (llama-3.3-70b-versatile) cho AI generation
- PyMuPDF (fitz) cho PDF extraction
- python-docx cho DOCX extraction

Frontend:
- React + Vite
- React Router DOM
- Tailwind CSS (hạn chế dùng, ưu tiên inline styles)
- Lucide React icons
- Axios (axiosInstance với JWT interceptor)

═══════════════════════════════════════════════════════════
NHỮNG GÌ ĐÃ HOÀN THÀNH
═══════════════════════════════════════════════════════════

── BACKEND ──────────────────────────────────────────────

apps/users/
  ✅ Authentication: Register, Login, Logout
  ✅ JWT (SimpleJWT): access + refresh token
  ✅ Custom User model

apps/documents/
  ✅ Upload document (PDF, DOCX, TXT)
  ✅ Text extraction → lưu vào DB field extracted_text
  ✅ Extractor fix QUAN TRỌNG: đọc được cả bảng trong DOCX
     dùng doc.element.body thay vì doc.paragraphs
  ✅ CRUD: List, Detail, Delete, Preview
  ✅ Serializers: DocumentListSerializer, DocumentDetailSerializer
                  DocumentUpdateSerializer
  ✅ Endpoints:
     GET    /api/documents/
     POST   /api/documents/upload/
     GET    /api/documents/:id/
     PATCH  /api/documents/:id/
     DELETE /api/documents/:id/
     GET    /api/documents/:id/preview/

apps/flashcards/
  ✅ Models:
     - GenerationSession: lưu context mỗi lần generate
       (user_intent, extracted_keywords, card_types,
        domain, difficulty, status, ai_model_used,
        raw_ai_response, total_cards_generated)
     - FlashcardSet: bộ flashcard (link Document + Session)
       có field domain, is_public, status
     - FlashCard: front, back, example, card_type, difficulty
       SRS fields đã có slot sẵn:
       ease_factor=2.5, interval=0, repetitions=0,
       next_review_at=null
  ✅ FlashcardSetSerializer có progress field (annotated):
     {total, reviewed, due_today, state, percent}
     state: "new" | "in_progress" | "due" | "completed"
  ✅ Endpoints:
     GET    /api/flashcards/sets/         (có progress annotation)
     GET    /api/flashcards/sets/:id/     (có cards_by_type)
     DELETE /api/flashcards/sets/:id/
     GET    /api/flashcards/sessions/

apps/ai/
  ✅ services/prompt_builder.py:
     - DOMAIN_CONTEXT: map domain → mô tả cho AI
     - CARD_TYPE_INSTRUCTIONS: static cho vocab/grammar/phrase
     - _build_qa_instruction(domain): DYNAMIC theo domain
       → domain=english: câu hỏi+trả lời tiếng Anh
       → domain khác: câu hỏi+trả lời tiếng Việt
     - DIFFICULTY_INSTRUCTION: easy/intermediate/hard
     - build_prompt(): tổng hợp → prompt string

  ✅ services/groq_service.py:
     - Model: llama-3.3-70b-versatile
     - temperature=0.4
     - _parse_ai_response(): handle ```json wrapper
     - _validate_card(): check required fields
     - Normalize card_type nếu AI trả sai

  ✅ POST /api/ai/generate/
     Flow: Validate → Create Session(PROCESSING) →
           Call Groq → Create FlashcardSet →
           bulk_create FlashCards → Update Session(DONE)

apps/study/
  ✅ Model CardReview:
     user, card (FK), quality (0-5),
     ease_factor_after, interval_after,
     repetitions_after, next_review_at_after,
     reviewed_at (auto)
     indexes: [card+reviewed_at], [user+reviewed_at]

  ✅ services/sm2.py — SM-2 thuần algorithm:
     - _update_ef(ef, quality): công thức Wozniak bậc 2
       ef + 0.1 - (5-q) * (0.08 + (5-q) * 0.02)
     - quality < 3  → reset rep=0, interval=1
     - quality >= 3 → tăng interval * ease_factor
     - MAX_INTERVAL = 120 days
     - timezone.utc cho next_review_at

  ✅ Endpoints:
     POST /api/study/cards/:id/review/  (nhận quality, chạy SM-2)
     GET  /api/study/due/               (cards next_review_at <= now)
     GET  /api/study/new/               (cards next_review_at = null)

  ✅ Phân biệt rõ 2 loại:
     due = đã học + đến hạn ôn lại
     new = chưa học lần nào

── FRONTEND ─────────────────────────────────────────────

Design System: "Warm Editorial"
  Inspired by Claude.ai — warm cream, terracotta accent
  Tokens:
    bg: #f9f6f1, surface: #ffffff
    border: #e8e1d9, borderHover: #d4ccc3
    textPrimary: #1a1411, textSecondary: #6b5f57
    textMuted: #a89e96
    accent: #d4724a (terracotta)
    accentBg: #fef4ef, accentBorder: #f5c9b0
    hover: #f2ece4
  Fonts: DM Serif Display (headings) + DM Sans (body)
  KHÔNG dùng tím/indigo bất kỳ đâu

Pages hoàn chỉnh:
  ✅ LoginPage, RegisterPage
  ✅ DashboardPage (inline: Sidebar, Header, HeroSection,
                    RecentDecks, DueBanner, NewBanner)
     - DueBanner: hiện khi due_count > 0 (terracotta)
     - NewBanner: hiện khi new_count > 0 (green)
     - RecentDecks: 3 sets gần nhất với progress bar
  ✅ DocumentsPage (list + upload modal)
  ✅ DocumentDetailPage:
     - Tabs: Thông tin | Nội dung | Flashcards
     - Tab Nội dung: lazy load từ /preview/
     - Tab Flashcards: mở GenerateModal (3-step wizard)
  ✅ FlashcardSetsPage (My Decks):
     - Stats: tổng sets, tổng cards, số domain
     - Filter chips theo domain
     - DeckCard: state badge + progress bar + 2 buttons
       "Xem thẻ" → /flashcards/:id (browse)
       "Bắt đầu học" → /study/:id (study)
     - 4 states: new/in_progress/due/completed
  ✅ FlashcardSetDetailPage (Browse mode):
     - Tab bar theo card_type
     - FlipCard: CSS 3D rotateY(180deg)
       fc-inner.is-flipped, backface-visibility:hidden
     - Keyboard: ← → chuyển, ↑↓ lật
     - Dot navigator, Reset button
     - Parse back: "answer (Giải thích Việt)"
       main → terracotta, vi → nhỏ italic pill
  ✅ StudyPage (/study/:setId — Focus mode):
     - Dark bg không, dùng warm indigo tinted
       linear-gradient(#f3f2ff → #faf8f5)
     - FlipCard + 4 Rating buttons (sau khi lật)
       Quên(q=0)/Lờ mờ(q=2)/Nhớ(q=3)/Thuộc(q=5)
     - Auto next card sau khi rate
     - Keyboard: Space/↑↓ lật, 1/2/3/4 chọn rating
     - Progress bar header
     - Summary screen khi xong

API files:
  ✅ authApi.js
  ✅ documentApi.js: getPreviewDocument, getDetailDocument...
  ✅ aiApi.js: generateFlashcards(payload)
  ✅ flashcardApi.js: getFlashcardSets, getFlashcardSetDetail,
                      deleteFlashcardSet, getGenerationSessions
  ✅ studyApi.js: reviewCard(cardId, quality),
                  getDueCards(), getNewCards()

Router /src/router/index.jsx:
  /dashboard, /documents, /documents/:id
  /flashcards, /flashcards/:id
  /study/:setId
  /study/due  ← chưa có page, cần làm
  /change-password, /profile

═══════════════════════════════════════════════════════════
CÒN LẠI CẦN LÀM
═══════════════════════════════════════════════════════════

Backend:
  🔲 GET /api/study/stats/ — streak, total reviewed, due count
     (dùng cho dashboard analytics sau này)

Frontend:
  🔲 /study/due — trang học tất cả cards due hôm nay
     (tương tự StudyPage nhưng lấy cards từ getDueCards()
      thay vì getFlashcardSetDetail())
  🔲 Add route /study/due vào router
  🔲 DueBanner button "Ôn ngay" → /study/due (đã có button,
     cần có page)

═══════════════════════════════════════════════════════════
KIẾN TRÚC QUAN TRỌNG CẦN NẮM
═══════════════════════════════════════════════════════════

1. AI PIPELINE:
   extracted_text → prompt_builder → Groq API → parse JSON
   → bulk_create FlashCards → update GenerationSession

2. DOMAIN ảnh hưởng PROMPT không phải DATA:
   english → QA tiếng Anh + giải thích Việt trong ngoặc
   history/science/math → QA tiếng Việt hoàn toàn

3. DOCX extraction: doc.element.body (đọc được tables)

4. SRS flow:
   FlashCard.next_review_at = null  → new (chưa học)
   FlashCard.next_review_at <= now  → due (cần ôn)
   FlashCard.next_review_at > now   → scheduled (chờ)

5. Progress annotation (1 query duy nhất):
   FlashcardSet.annotate(reviewed_count, due_count)
   → không N+1 queries

6. Back text parsing:
   /^(.*?)\s*\(([^)]+)\)\s*$/
   "answer (Giải thích)" → main + vi text

7. Design: KHÔNG dùng tím/indigo
   Accent duy nhất = #d4724a terracotta

═══════════════════════════════════════════════════════════
QUY TẮC LÀM VIỆC
═══════════════════════════════════════════════════════════
- Docker: docker-compose exec web python manage.py ...
- Model thay đổi → makemigrations → migrate
- Test Postman trước → frontend sau
- Phân tích trước, code sau
- Design tokens T = {...} đặt đầu file
- Inline styles, không dùng Tailwind cho màu sắc
- Warm Editorial palette — xem Design System ở trên