# 🦉 올빼미 AI 영상 스튜디오 - Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim-bullseye

WORKDIR /app

# Create non-root user for security
RUN groupadd -r owlstudio && useradd -r -g owlstudio owlstudio

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick security policy
RUN sed -i '/<policy domain="path" rights="none" pattern="@\*"/d' /etc/ImageMagick-6/policy.xml

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs storage/videos && \
    chown -R owlstudio:owlstudio /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    APP_ENV=production

# Expose ports
EXPOSE 8080 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER owlstudio

# Default command: Run FastAPI with Uvicorn
CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

# Alternative: Run Streamlit WebUI
# CMD ["streamlit", "run", "./webui/Main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=true", "--browser.gatherUsageStats=false"]