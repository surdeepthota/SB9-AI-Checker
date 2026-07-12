# Multi-stage Docker build for Google Cloud Run
# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the FastAPI backend and serve the static files
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies required for c2pa-python and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend assets to serve them via FastAPI
COPY --from=frontend-builder /app/frontend/dist /app/static

# We need to slightly update app.py to serve the static files (handled via UI/UX instructions)
# Expose port (Cloud Run defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Command to run uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
