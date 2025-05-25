FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install critical Python dependencies first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy essential files first
COPY requirements.txt railway_entry.sh fix_dotenv_import.py dotenv.py dotenv_fallback.py ./
RUN chmod +x railway_entry.sh

# Install direct dependencies for aiogram
RUN pip install --no-cache-dir pydantic==1.10.12 aiogram==3.0.0

# Try to install python-dotenv and other dependencies
RUN pip install --no-cache-dir python-dotenv || echo "Failed to install python-dotenv, will use fallback"
RUN pip install --no-cache-dir -r requirements.txt || echo "Some requirements failed, continuing anyway"

# Copy all application files
COPY . .

# Create necessary directories
RUN mkdir -p logs tmp

# Set up entry point
CMD ["./railway_entry.sh"] 