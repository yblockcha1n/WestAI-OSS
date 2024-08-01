FROM python:3.11-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY model/west.json ./model/
COPY settings/config.json ./settings/
COPY settings/fixed.json ./settings/

CMD ["python", "main.py"]