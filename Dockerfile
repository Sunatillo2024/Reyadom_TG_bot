FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system bot && useradd --system --gid bot --home-dir /app bot
COPY --chown=bot:bot . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER bot

CMD ["python", "-m", "bot.main"]
