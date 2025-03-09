FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev build-essential libffi-dev libssl-dev ffmpeg libopus-dev locales && \
    rm -rf /var/lib/apt/lists/*
RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --no-compile --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN pip install --no-cache-dir --upgrade pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libffi-dev libssl-dev libopus-dev locales && \
    rm -rf /var/lib/apt/lists/*
RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8
WORKDIR /app
ENV TZ=America/Sao_Paulo
COPY --from=builder /install /usr/local
COPY . .
ENTRYPOINT ["python", "bot.py"]
