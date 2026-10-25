FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_DIR=

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot

# Run as a normal user. /app/data is where the SQLite file lives; mount a
# volume there so reminders survive a rebuild.
RUN useradd --create-home --uid 1000 bot && mkdir -p /app/data && chown bot /app/data
USER bot
VOLUME /app/data

CMD ["python", "-m", "bot"]
