FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev build-essential libffi-dev libssl-dev \
    ffmpeg libopus-dev locales && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libopus-dev locales curl && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

RUN groupadd -r botuser && useradd -r -g botuser botuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=botuser:botuser . .

USER botuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health

ENTRYPOINT ["python", "bot.py"]