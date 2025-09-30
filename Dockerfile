# ---- Build stage ----
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile --target=/libs -r requirements.txt

COPY app/ .

# ---- Runtime stage (distroless) ----
FROM python:3.11-alpine
WORKDIR /app

RUN apk add --no-cache git

COPY --from=builder /libs /libs
COPY --from=builder /app /app

ENV PYTHONPATH=/libs

CMD ["python", "-m", "main"]
