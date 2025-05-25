FROM python:3.11-slim

WORKDIR /app

# Copy all application files
COPY . .

# Install dependencies directly
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pydantic==1.10.12 aiogram==3.0.0

# Create necessary directories
RUN mkdir -p logs tmp

# Start the bot directly with Python
CMD ["python", "main.py"] 