# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary directories
RUN mkdir -p intel consolidated static

# Expose port 8000 for FastAPI
EXPOSE 8000

# Set environment variables (optional, can also be passed via docker-compose)
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "api.py"]
