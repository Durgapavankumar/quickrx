# QuickRx backend — FastAPI + faster-whisper (CPU).
# The Whisper model (~145 MB) downloads on first transcription and is cached
# in the whisper-models volume, so it is fetched once, not on every rebuild.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests

# Model cache + persistent data live in volumes (see docker-compose.yml)
ENV HF_HOME=/models \
    QUICKRX_DB_PATH=/data/quickrx.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
