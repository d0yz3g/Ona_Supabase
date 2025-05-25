#!/bin/bash

# ONA Bot Railway Deployment Script
# This script prepares and deploys the ONA bot to Railway

set -e

echo "=== ONA Bot Railway Deployment ==="
echo "Preparing for deployment..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Create .dockerignore if it doesn't exist
if [ ! -f .dockerignore ]; then
    echo "Creating .dockerignore file..."
    cat > .dockerignore << EOF
__pycache__/
*.py[cod]
*$py.class
.git
.env
.venv
venv/
ENV/
logs/
*.log
.DS_Store
EOF
    echo "✅ Created .dockerignore"
fi

# Create simple Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "Creating Dockerfile..."
    cat > Dockerfile << EOF
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
EOF
    echo "✅ Created Dockerfile"
fi

# Create railway.toml if it doesn't exist
if [ ! -f railway.toml ]; then
    echo "Creating railway.toml..."
    cat > railway.toml << EOF
[build]
builder = "nixpacks"
buildCommand = "pip install pydantic==1.10.12"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[nixpacks]
install_packages = ["python3", "python3-pip", "libffi-dev", "python3-dev"]

[phases.setup]
cmds = ["pip install pydantic==1.10.12", "pip install aiogram==3.0.0"]
EOF
    echo "✅ Created railway.toml"
fi

# Create or update README_RAILWAY.md
echo "Creating/updating README_RAILWAY.md..."
cat > README_RAILWAY.md << EOF
# Deploying ONA Bot on Railway

This guide explains how to deploy the ONA Telegram bot on Railway.

## Prerequisites

1. A GitHub account with the ONA bot code repository
2. A Railway account (https://railway.app/)
3. Your Telegram bot token (from BotFather)
4. Any other API keys required by the bot (OpenAI, ElevenLabs, etc.)

## Deployment Steps

### 1. Push your code to GitHub

Make sure your code is in a GitHub repository.

### 2. Connect to Railway

1. Go to Railway.app and log in
2. Click "New Project" → "Deploy from GitHub"
3. Select your GitHub repository
4. Wait for Railway to build the initial deployment

### 3. Configure Environment Variables

Add the following environment variables in Railway dashboard:

- \`BOT_TOKEN\` - Your Telegram bot token from BotFather
- \`OPENAI_API_KEY\` - Your OpenAI API key (if using OpenAI features)
- \`ELEVEN_TOKEN\` - Your ElevenLabs API token (if using voice features)
- Any other required API keys or configuration values

### 4. Troubleshooting

If you encounter issues with the deployment, check Railway logs for specific error messages.
EOF
echo "✅ Created/updated README_RAILWAY.md"

# Commit changes if needed
echo "Checking for changes to commit..."
if git status --porcelain | grep -q "^??\\|^M\\|^A"; then
    echo "Changes detected, committing..."
    git add .dockerignore Dockerfile railway.toml README_RAILWAY.md
    git commit -m "Update Railway deployment files"
    echo "✅ Committed changes"
else
    echo "No changes to commit"
fi

echo "=== Deployment Preparation Complete ==="
echo "Now you can push to GitHub and deploy on Railway with:"
echo "git push origin main" 