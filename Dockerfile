# Dockerfile para la app FastAPI
FROM python:3.11-slim

WORKDIR /app

# instalar ffmpeg y dependencias
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY worker.py ./worker.py
COPY video_worker.py ./video_worker.py

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
