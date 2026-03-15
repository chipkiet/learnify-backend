learnify/
│
├── core/          → NÃO: cấu hình, routing chính
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/          → THÂN: các tính năng
│   ├── users/
│   ├── documents/
│   └── flashcards/
│
├── manage.py      → CLI tool để chạy lệnh Django
├── Dockerfile     → cách build container
├── docker-compose → cách chạy các containers
└── requirements.txt → danh sách thư viện