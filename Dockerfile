# Multi-stage Docker build (Oracle Cloud VM via deploy/oracle; also runs on Cloud Run)
# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: FastAPI backend serving the built frontend as static files
FROM python:3.11-slim

# tesseract gives the measurement layer its primary OCR engine (pytesseract);
# build-essential is needed to compile native wheels where prebuilt ones are missing.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Run as an unprivileged user; the app and its model cache live in its home dir.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface
WORKDIR /home/user/app

# CPU-only torch: no GPU at runtime, and the default CUDA wheels add several GB.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Bake both forensic classifiers into the image so a restart never re-downloads them.
RUN python -c "from transformers import pipeline; \
[pipeline('image-classification', model=m) for m in \
('umm-maybe/AI-image-detector', 'haywoodsloan/ai-image-detector-deploy')]"

# Backend code + bundled demo corpus (see .dockerignore for exclusions)
COPY --chown=user . .

# Built frontend assets, served by FastAPI at /
COPY --chown=user --from=frontend-builder /app/frontend/dist ./static

# Cloud Run injects PORT itself; elsewhere the app listens on 8080.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
