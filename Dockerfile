FROM python:3.11-slim

# Working directory
WORKDIR /app

# System packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port 8001 for Mevzuat API
EXPOSE 8001

# Start the Mevzuat API
CMD ["uvicorn", "simple_mevzuat_api:app", "--host", "0.0.0.0", "--port", "8001"]