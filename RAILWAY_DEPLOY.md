# ONA Telegram Bot Railway Deployment Guide

This guide provides step-by-step instructions for deploying the ONA (Осознанный Наставник и Аналитик) Telegram bot on Railway platform.

## Prerequisites

- GitHub repository with your ONA bot code
- Telegram Bot Token (from BotFather)
- OpenAI API Key (optional, for AI-powered responses)
- ElevenLabs API Key (optional, for voice functionality)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository contains the following essential files:

- `main.py` - Main bot code
- `requirements.txt` - Python dependencies
- `start.sh` - Startup script (must be executable)
- `install_supabase.sh` - Supabase installation script (must be executable) 
- `Procfile` - Railway process file
- `railway.toml` - Railway configuration
- `supabase_fallback.py` - SQLite fallback for Supabase

### 2. Configure Railway Files

**Procfile**:
```
web: bash start.sh
```

**railway.toml**:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "bash start.sh"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments]
  [environments.production]
    startCommand = "bash start.sh"
```

### 3. Deploy to Railway

1. Go to [Railway](https://railway.app/) and create an account if you don't have one
2. Click on "New Project" → "Deploy from GitHub"
3. Select your GitHub repository
4. Add the following environment variables in the Railway dashboard:
   - `BOT_TOKEN` (required) - Your Telegram bot token
   - `OPENAI_API_KEY` (optional) - For AI-powered responses
   - `ELEVEN_LABS_API_KEY` (optional) - For voice functionality
5. Click "Deploy"

### 4. Verify Deployment

1. Wait for the deployment to complete (this may take a few minutes)
2. Check the deployment logs to verify that the bot has started
3. Look for the message "✅ Bot started successfully" in the logs
4. Test your bot by sending a `/start` command in Telegram

## Troubleshooting

### Supabase Installation Issues

If you see errors related to Supabase dependencies:

```
ERROR: No matching distribution found for gotrue-py==1.2.0
ERROR: Could not find a version that satisfies the requirement supabase-py==2.3.5
```

Don't worry - the bot will automatically fall back to using SQLite as a database. This is expected behavior on Railway's free tier as it has limited support for some Supabase dependencies.

### Bot Not Responding

If your bot isn't responding:

1. Check the logs in Railway dashboard for errors
2. Verify that `BOT_TOKEN` is correctly set in environment variables
3. Make sure your bot is not blocked by Telegram (send `/start` to BotFather to check)

### Database Errors

If you see database-related errors:

1. Confirm that SQLite fallback is working properly
2. Check logs for messages about database initialization
3. Verify that the necessary tables are being created

### Memory/Resource Issues

Railway's free tier has limited resources. If your bot crashes due to memory issues:

1. Reduce batch sizes for AI processing
2. Optimize database queries
3. Remove unnecessary dependencies

## Additional Configuration

### Custom Environment Variables

You can add additional environment variables in the Railway dashboard:

- `SQLITE_DB_PATH` - Custom path for SQLite database (default: `ona.db`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `WEBHOOK_URL` - For webhook mode instead of polling

### Using Webhooks

For better performance, consider using webhooks instead of polling:

1. Add `WEBHOOK_URL` and `WEBHOOK_PATH` environment variables in Railway
2. Modify `main.py` to use webhook mode when these variables are present

## Support and Maintenance

For any issues or questions, please open an issue on the GitHub repository or contact the development team.

Remember to regularly update your dependencies and check for new Railway features that might enhance your deployment. 