FROM python:3.12-alpine

# Don't generate .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Force unbuffered output
ENV PYTHONUNBUFFERED=1

LABEL app_name="Popcat Bot"
LABEL description="Popcat Bot is a Public Version of the Popcat Discord Bot"
LABEL version="1.0.0"
LABEL maintainer="Herr Erde"

WORKDIR /app

COPY src/ .

RUN apk add build-base linux-headers && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
