#!/bin/bash

echo "=== ONA TELEGRAM BOT RAILWAY DEPLOYMENT SCRIPT ==="
echo "This script prepares your environment for Railway deployment"

# Make scripts executable
chmod +x start.sh
chmod +x install_supabase.sh

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found!"
    exit 1
fi

# Verify supabase_requirements.txt exists
if [ ! -f "supabase_requirements.txt" ]; then
    echo "❌ ERROR: supabase_requirements.txt not found!"
    exit 1
fi

# Verify Procfile exists
if [ ! -f "Procfile" ]; then
    echo "Creating Procfile..."
    echo "web: bash start.sh" > Procfile
    echo "✅ Procfile created"
fi

# Verify railway.toml exists
if [ ! -f "railway.toml" ]; then
    echo "Creating railway.toml..."
    cat > railway.toml << EOL
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "bash start.sh"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments]
  [environments.production]
    startCommand = "bash start.sh"
EOL
    echo "✅ railway.toml created"
fi

echo "=== CHECKING SUPABASE FALLBACK ==="
# Verify that supabase_fallback.py exists and contains needed functionality
if [ ! -f "supabase_fallback.py" ]; then
    echo "❌ ERROR: supabase_fallback.py not found!"
    exit 1
fi

# Check for necessary env variables in local .env file
echo "=== CHECKING .ENV FILE ==="
if [ -f ".env" ]; then
    echo "✅ .env file found locally"
    # Check for BOT_TOKEN
    if grep -q "BOT_TOKEN" .env; then
        echo "✅ BOT_TOKEN found in .env"
    else
        echo "⚠️ WARNING: BOT_TOKEN not found in .env"
    fi
    
    # Check for OPENAI_API_KEY
    if grep -q "OPENAI_API_KEY" .env; then
        echo "✅ OPENAI_API_KEY found in .env"
    else
        echo "⚠️ WARNING: OPENAI_API_KEY not found in .env"
    fi
else
    echo "⚠️ WARNING: .env file not found. Make sure to add environment variables in Railway dashboard."
fi

echo "=== DEPLOYMENT INSTRUCTIONS ==="
echo "1. Create a new project on Railway: 'New Project' → 'Deploy from GitHub'"
echo "2. Select your GitHub repository"
echo "3. Add the following environment variables in the Railway dashboard:"
echo "   - BOT_TOKEN (required)"
echo "   - OPENAI_API_KEY (optional, for AI functionality)"
echo "   - ELEVEN_LABS_API_KEY (optional, for voice functionality)"
echo "4. Deploy the project"
echo "5. Check logs to verify the bot has started"

echo "=== READY FOR DEPLOYMENT ==="
echo "Your project is now ready to be deployed to Railway." 