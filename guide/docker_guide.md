PHẦN 1 — Bắt đầu dự án mới
# Bước 1: Build image từ Dockerfile
docker-compose build
# Lý do: Đọc Dockerfile, tải python:3.11-slim, cài requirements.txt
# Chạy 1 lần đầu, hoặc khi thay đổi Dockerfile/requirements.txt





# Bước 2: Khởi tạo Django project (chỉ chạy 1 lần duy nhất)
docker-compose run --rm web django-admin startproject core .
# Lý do: Tạo cấu trúc core/ và manage.py
# Dùng run vì container chưa chạy




# Bước 3: Chạy migration lần đầu
docker-compose run --rm web python manage.py migrate
# Lý do: Tạo các bảng mặc định của Django trong PostgreSQL
# (auth, sessions, admin, contenttypes)





# Bước 4: Khởi động server
docker-compose up
# Lý do: Chạy cả web + db containers
# Dùng: docker-compose up -d để chạy ngầm (background)


PHẦN 2 — Workflow hàng ngày

# Buổi sáng bắt đầu làm việc
docker-compose up -d
# Lý do: Khởi động containers chạy ngầm, không chiếm terminal

# Kiểm tra containers đang chạy
docker-compose ps
# Lý do: Xem trạng thái web + db có running không

# Xem log khi có lỗi
docker-compose logs web
docker-compose logs db
docker-compose logs -f web  # -f: theo dõi realtime

# Cuối ngày
docker-compose down
# Lý do: Tắt và xóa containers (data vẫn giữ trong volume)


PHẦN 3 — Lệnh Django trong Docker
# Tạo app mới
docker-compose exec web python manage.py startapp users
# Lý do: exec vì container đang chạy


# Sau khi thay đổi models.py → tạo migration file
docker-compose exec web python manage.py makemigrations
# Lý do: Django đọc models.py, tạo file migration mô tả thay đổi DB


# Áp dụng migration vào PostgreSQL
docker-compose exec web python manage.py migrate
# Lý do: Thực thi các file migration, cập nhật schema trong DB


# Tạo superuser (tài khoản admin)
docker-compose exec web python manage.py createsuperuser

# Vào shell Django (debug, test nhanh)
docker-compose exec web python manage.py shell



docker-compose exec web pip install django-unfold

docker-compose exec web pip freeze > /app/requirements.txt
