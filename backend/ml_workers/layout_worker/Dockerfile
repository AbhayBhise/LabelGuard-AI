FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 zbar-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    opencv-python-headless pyzbar

# Share application code so workers can import app.services
COPY app ./app
COPY layout_worker/server.py ./server.py

EXPOSE 8003
CMD ["python", "server.py"]
