FROM python:3.12-slim

# Install system dependencies (libsndfile for audio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face Spaces expects a web port on 7860
EXPOSE 7860

CMD ["python", "main.py"]
