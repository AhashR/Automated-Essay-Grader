# Dockerfile for Automated Essay Grader
# From Hasif's Workspace
# Author: Hasif50

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download required NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/outputs logs

# Set permissions
RUN chmod -R 755 /app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK CMD curl --fail http://localhost:5000/health || exit 1

# Set metadata
LABEL maintainer="Hasif50"
LABEL workspace="Hasif's Workspace"
LABEL description="AI-Powered Essay Grading System"
LABEL version="1.0.0"

# Run the application
ENTRYPOINT ["python", "app.py"]