# Multi-stage Docker build for Google Cloud Run
# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: FastAPI backend serving the built frontend as static files
FROM python:3.11-slim
WORKDIR /app

# tesseract gives the measurement layer its primary OCR engine (pytesseract);
# build-essential is needed to compile native wheels where prebuilt ones are missing.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code + bundled demo corpus (see .dockerignore for exclusions)
COPY . .

# Built frontend assets, served by FastAPI at /
COPY --from=frontend-builder /app/frontend/dist /app/static

# Cloud Run injects PORT (defaults to 8080)
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
