FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        libpq-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

ENV DEBUG=False \
    DB_ENGINE=sqlite \
    SECRET_KEY=docker-build-temporary-secret \
    ALLOWED_HOSTS=localhost,127.0.0.1,testserver \
    SECURE_SSL_REDIRECT=False

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "/app/start.sh"]
