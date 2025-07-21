FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV, pyzbar, and Tesseract OCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libzbar0 \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
RUN tesseract --version && \
    tesseract --list-langs

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
# Set Tesseract configurations - use the correct path based on your Tesseract version
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
# If the above path doesn't exist, try these alternatives:
# ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/tessdata
# ENV TESSDATA_PREFIX=/usr/local/share/tesseract-ocr/tessdata

# Create a script to start the application
RUN echo '#!/bin/bash\n\
echo "Testing Tesseract installation:"\n\
tesseract --version\n\
tesseract --list-langs\n\
echo "Starting application..."\n\
PORT="${PORT:-8080}"\n\
exec gunicorn --bind "0.0.0.0:$PORT" app:app\n' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"] 