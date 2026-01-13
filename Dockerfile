FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ \
    libstdc++6 libglib2.0-0 libgomp1 libffi-dev \
    libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 libcairo2 \
    libfreetype6 poppler-utils shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 🔑 copy ONLY requirements first
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN mkdir -p loan_assets vector_db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
