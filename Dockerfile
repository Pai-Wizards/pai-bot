FROM python:3.11.5-alpine3.18 AS builder
RUN apk add --no-cache gcc python3-dev musl-dev linux-headers tzdata make build-base libffi-dev openssl-dev
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --no-compile --prefix=/install -r requirements.txt

FROM python:3.11.5-alpine3.18
RUN pip install --no-cache-dir --upgrade pip
RUN apk add --no-cache ffmpeg libffi-dev openssl-dev
WORKDIR /app
ENV TZ=America/Sao_Paulo
COPY --from=builder /install /usr/local
COPY . .

ENTRYPOINT ["python", "bot.py"]
