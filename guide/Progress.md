════════════════════════════════
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




Tôi đang chuẩn bị làm chức năng admin để quản lý và theo dõi toàn bộ dự án này

Khi dự án Learnify bắt đầu "phình" to về dữ liệu và người dùng, tôi không thể quản lý bằng cách vào database check tay hay đọc log terminal được nữa.

Tôi cần một Dashboard nội bộ để biết chính xác token đang "chảy" đi đâu:

Metric theo Model: Biểu đồ so sánh lượng token tiêu thụ giữa Llama 70B và 8B. Tôi muốnthấy rõ mình đang "đốt" tiền vào con nào nhiều nhất.

Token per User: Đây là tính năng sống còn. Tôi phải biết User nào đang "bào" API của tôi nhiều nhất. Nếu một người dùng tạo 1000 cards/ngày, đó có thể là dấu hiệu của việc lạm dụng hoặc dùng bot.

Token per Action: Phân tích xem chức năng nào tốn kém nhất: Tạo flashcards lần đầu, Regenerate, hay Giải thích lỗi sai trong Quiz.

Cảnh báo ngưỡng (Alerting): Khi lượng token sử dụng trong ngày chạm mức 80% (tầm 80,000 tokens với hạn mức của tôi), hệ thống admin phải gửi một thông báo (qua Gmail hoặc Email) để tôi biết mà điều chỉnh.

Chế độ Phê duyệt (Approval Flow): Đổi cơ chế đăng ký từ "Mở hoàn toàn" sang "Chờ duyệt". Người dùng đăng ký xong sẽ nằm trong danh sách Pending, chỉ khi tôi nhấn Approve trong Admin thì họ mới bắt đầu dùng được AI.

Khóa người dùng (Ban/Suspend): Một nút bấm quyền lực để chặn ngay lập tức những tài khoản có dấu hiệu phá hoại hoặc spam API.

nên có các nút "Gạt" (Toggle) để điều chỉnh logic hệ thống ngay lập tức mà không cần sửa code:

Global Model Switch: Một nút gạt để chuyển toàn bộ hệ thống từ 70B sang 8B trong trường hợp bạn sắp hết token TPD (Tokens Per Day).

Cache Management: Xem danh sách các câu hỏi/tài liệu đã được AI xử lý. Nếu người dùng khác upload cùng một tài liệu, Admin có thể cấu hình để hệ thống lấy luôn kết quả cũ, tốn 0 token.

Đó là những gì mà tôi muốn. Dự án đang sử dụng django admin khá xấu , tôi muốn build luôn 1 react admin dashboard đầy đủ

Email Alerting — Tôi đề xuất Gmail SMTP:

Miễn phí hoàn toàn
Django có built-in support, setup 10 phút
Với scale hiện tại của Learnify hoàn toàn đủ dùng
SendGrid chỉ cần thiết khi gửi email marketing hàng loạt


Admin Dashboard location — Tôi đề xuất tách riêng:
learnify-frontend/     ← user-facing (hiện tại)
learnify-admin/        ← admin dashboard (mới)
Lý do:

Bundle size user app không bị phình vì code admin
Deploy độc lập, update admin không ảnh hưởng user
Bảo mật tốt hơn — admin app có thể restrict IP
Cùng backend API, chỉ thêm prefix /api/admin/