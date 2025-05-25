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

- `BOT_TOKEN` - Your Telegram bot token from BotFather
- `OPENAI_API_KEY` - Your OpenAI API key (if using OpenAI features)
- `ELEVEN_TOKEN` - Your ElevenLabs API token (if using voice features)
- Any other required API keys or configuration values

### 4. Configure the Deployment

Make sure the deployment settings are:

- Build Command: `pip install pydantic==1.10.12 aiogram==3.0.0`
- Start Command: `python main.py`

### 5. Troubleshooting

If you encounter issues with the deployment:

1. **Supabase Connection Issues**
   - The bot will automatically fall back to SQLite if Supabase is not available
   - No additional configuration is needed for the fallback

2. **Pydantic Compatibility Issues**
   - The bot includes automatic patching for pydantic compatibility with aiogram
   - This is handled in patch_pydantic.py

3. **Deployment Fails**
   - Check Railway logs for specific error messages
   - Make sure all environment variables are set correctly
   - Verify that Railway is using the correct Python version (3.11)

## Railway Configuration Files

The repository includes two important files for Railway deployment:

1. `railway.toml` - Configures the Railway project
2. `Dockerfile` - Specifies how to build the Docker container

## Automatic Restart

The bot is configured to automatically restart on failure with:

```toml
[deploy]
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

## Bot Status Monitoring

You can monitor the bot status through Railway's logs and metrics dashboard.

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Aiogram Documentation](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## Support

If you encounter any issues deploying to Railway, please check the [RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md) file for detailed troubleshooting or open an issue in this repository. 