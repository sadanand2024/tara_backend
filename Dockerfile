# ---------- STAGE 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies including curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environmen
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- STAGE 2: Runtime ----------
FROM python:3.12-slim

# Runtime environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime dependencies including curl (temporarily)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libpq5 \
    fontconfig \
    xfonts-75dpi \
    xfonts-base \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf from verified .deb packageee
RUN curl -fSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb -o /tmp/wkhtmltopdf.deb \
    && apt-get install -y --no-install-recommends /tmp/wkhtmltopdf.deb \
    && rm -f /tmp/wkhtmltopdf.deb \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && wkhtmltopdf --version

# Copy from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application
COPY . /app

# Healthcheck
#HEALTHCHECK --interval=30s --timeout=5s \
#    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1

WORKDIR /app/Tara

#CMD ["uvicorn", "Tara.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
