Chúng ta đang build project Django tên "learnify" từ đầu cùng nhau.

## TECH STACK
- Python 3.11 + Django 4.2
- PostgreSQL 15 (chạy trong Docker, port 5434)
- Django REST Framework + SimpleJWT
- Docker + docker-compose

## CẤU TRÚC PROJECT
learnify/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── .env
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── users/
    ├── documents/
    └── flashcards/

## ĐÃ HOÀN THÀNH
✅ Cấu trúc thư mục
✅ Dockerfile & docker-compose (PostgreSQL port 5434)
✅ Django settings + .env
✅ Custom User model (login bằng email)
   - fields: email, full_name, is_active, is_staff, created_at, updated_at
   - AUTH_USER_MODEL = 'users.User'
✅ Migration thành công → bảng users_user đã có trong DB
✅ Push lên Git: https://github.com/chipkiet/learnify

## ĐANG LÀM
🔄 Bước 4 — Authentication API
   - Đăng ký (register)
   - Đăng nhập (login) - JWT
   - Đổi mật khẩu

## CẤU TRÚC apps/users/
apps/users/
├── models.py          ← Custom User model xong
├── serializers/
│   ├── __init__.py
│   └── auth_serializers.py   ← chưa làm
├── services/
│   └── __init__.py           ← chưa làm
├── urls.py                   ← chưa làm
└── views.py                  ← chưa làm

## YÊU CẦU
Hãy tiếp tục giúp tôi build Authentication API 
theo đúng cấu trúc đã có, giải thích từng bước 
để tôi hiểu chứ không chỉ đưa code.