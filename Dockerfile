FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and pyzbar
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

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

# Create a script to start the application
RUN echo '#!/bin/bash\n\
PORT="${PORT:-8080}"\n\
exec gunicorn --bind "0.0.0.0:$PORT" app:app\n' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"] 