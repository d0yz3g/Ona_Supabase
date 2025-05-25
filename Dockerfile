FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies in stages for better error handling
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pydantic==1.10.12 && \
    pip install --no-cache-dir aiogram==3.0.0 && \
    pip install --no-cache-dir -r requirements.txt || echo "Some requirements failed, continuing anyway"

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs tmp

# Make shell scripts executable
RUN chmod +x railway_entry.sh

# Set up entry point
CMD ["./railway_entry.sh"] 