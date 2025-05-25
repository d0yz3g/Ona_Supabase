# ONA Telegram Bot - Railway Deployment

This repository contains ONA (Осознанный Наставник и Аналитик) - a powerful Telegram bot designed for psychological profiling and intelligent conversations. This guide focuses specifically on deploying the bot to the Railway platform.

## Railway Deployment Quick Start

Railway is a platform that makes it easy to deploy and manage your applications. It's particularly well-suited for Telegram bots due to its simplicity and reliability.

### Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app/))
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key (optional, for AI-powered responses)
- ElevenLabs API Key (optional, for voice functionality)

### Deployment Steps

1. **Prepare Your Repository**
   - Ensure your code is pushed to GitHub
   - Make sure `requirements.txt`, `start.sh`, and other essential files are present

2. **Deploy to Railway**
   - Go to [Railway](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub"
   - Select your GitHub repository
   - Add the following environment variables:
     - `BOT_TOKEN` (required)
     - `OPENAI_API_KEY` (optional)
     - `ELEVEN_LABS_API_KEY` (optional)
   - Click "Deploy"

3. **Verify Deployment**
   - Wait for the deployment to complete
   - Check logs for "✅ Bot started successfully"
   - Test the bot by sending `/start` in Telegram

## Files for Railway Deployment

The following files are essential for successful Railway deployment:

- `main.py` - Main bot code
- `requirements.txt` - Python dependencies
- `start.sh` - Startup script that installs dependencies and runs the bot
- `install_supabase.sh` - Script to install Supabase dependencies
- `supabase_fallback.py` - SQLite fallback for when Supabase is unavailable
- `Procfile` - Tells Railway how to run the application
- `railway.toml` - Railway configuration file

## Automatic SQLite Fallback

ONA bot is designed to work with either Supabase or SQLite as a database. If Supabase dependencies cannot be installed (which is common on Railway's free tier), the bot will automatically fall back to using SQLite.

This fallback mechanism ensures your bot will work even if the Supabase installation fails.

## Deployment Troubleshooting

### Common Issues and Solutions

1. **Bot Not Starting**
   - Check logs for specific error messages
   - Verify `BOT_TOKEN` is correctly set
   - Make sure all required dependencies are in `requirements.txt`

2. **Supabase Dependency Errors**
   - These are expected on Railway's free tier
   - The bot will automatically use SQLite instead
   - You should see "⚠️ Supabase is not installed, will use SQLite fallback" in logs

3. **Memory/CPU Issues**
   - Railway free tier has resource limitations
   - Consider optimizing your code to reduce resource usage
   - Use webhooks instead of polling if possible

### Deployment Scripts

For your convenience, this repository includes helper scripts:

- `prepare_for_railway.bat` - Windows script to prepare your project for Railway deployment
- `railway_deploy.sh` - Linux/Mac script to prepare your project for Railway deployment

Running these scripts will check your project for necessary files and create them if missing.

## Using the Bot on Railway

Once deployed, your bot will run continuously on Railway. The free tier provides enough resources for basic usage.

To update your bot:
1. Push changes to your GitHub repository
2. Railway will automatically detect the changes and redeploy

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Aiogram Documentation](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## Support

If you encounter any issues deploying to Railway, please check the [RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md) file for detailed troubleshooting or open an issue in this repository. 