FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Share application code so workers can import app.services
COPY app ./app
COPY vlm_worker/server.py ./server.py

EXPOSE 8002
CMD ["python", "server.py"]
