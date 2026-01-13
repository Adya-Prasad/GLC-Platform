FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies required by ML + PDF libs
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libstdc++6 \
    libglib2.0-0 \
    libgomp1 \
    libffi-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libcairo2 \
    libfreetype6 \
    poppler-utils \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p loan_assets vector_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
