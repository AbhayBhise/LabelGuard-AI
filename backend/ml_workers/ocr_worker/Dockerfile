FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    paddlepaddle paddleocr==2.7.3

# Share application code so workers can import app.services
COPY app ./app
COPY ocr_worker/server.py ./server.py

EXPOSE 8001
CMD ["python", "server.py"]
