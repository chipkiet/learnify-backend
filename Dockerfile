FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files at build time (dummy SECRET_KEY for build only)
RUN SECRET_KEY=dummy-build-key python manage.py collectstatic --noinput

CMD python manage.py migrate --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000}
