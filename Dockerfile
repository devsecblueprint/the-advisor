# Use official Python image as base
FROM python:3.13-slim

# Add Author and Maintainer labels
LABEL maintainer="Damien Burks <damien@devsecblueprint.com>"
LABEL description="Dockerfile for The Advisor application with WeasyPrint support"
LABEL version="1.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    weasyprint

# Copy requirements (if you have requirements.txt)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src /app/src

ENV PYTHONPATH=/app/src

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]