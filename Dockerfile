# Minimal Dockerfile for Zeusonic FastAPI backend
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system deps required by some wheels (e.g., greenlet)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Ensure storage dirs exist
RUN mkdir -p /app/backend/storage /app/backend/storage/audio_uploads

# Expose port
EXPOSE 8000

# Use environment variables recommended for containers
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the app (use platform PORT if provided)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
