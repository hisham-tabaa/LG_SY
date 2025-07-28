# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Create start script for Railway compatibility
RUN echo '#!/bin/bash\n\
echo "=== LG Syria App Starting ==="\n\
echo "Testing Tesseract installation:"\n\
tesseract --version || echo "Tesseract not found"\n\
echo "Python path: $(which python)"\n\
echo "Starting Flask application..."\n\
exec python app.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Command to run the application
CMD ["/app/start.sh"] 