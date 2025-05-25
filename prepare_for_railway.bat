@echo off
echo === ONA TELEGRAM BOT RAILWAY DEPLOYMENT PREPARATION ===
echo This script prepares your environment for Railway deployment

echo.
echo === CHECKING FILES ===

:: Check requirements.txt
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    exit /b 1
) else (
    echo requirements.txt found
)

:: Check supabase_requirements.txt
if not exist "supabase_requirements.txt" (
    echo ERROR: supabase_requirements.txt not found!
    exit /b 1
) else (
    echo supabase_requirements.txt found
)

:: Check supabase_fallback.py
if not exist "supabase_fallback.py" (
    echo ERROR: supabase_fallback.py not found!
    exit /b 1
) else (
    echo supabase_fallback.py found
)

:: Create Procfile if it doesn't exist
if not exist "Procfile" (
    echo Creating Procfile...
    echo web: bash start.sh > Procfile
    echo Procfile created
) else (
    echo Procfile found
)

:: Create railway.toml if it doesn't exist
if not exist "railway.toml" (
    echo Creating railway.toml...
    (
        echo [build]
        echo builder = "NIXPACKS"
        echo.
        echo [deploy]
        echo startCommand = "bash start.sh"
        echo restartPolicyType = "ON_FAILURE"
        echo restartPolicyMaxRetries = 10
        echo.
        echo [environments]
        echo   [environments.production]
        echo     startCommand = "bash start.sh"
    ) > railway.toml
    echo railway.toml created
) else (
    echo railway.toml found
)

:: Check .env file
if not exist ".env" (
    echo WARNING: .env file not found. Make sure to add environment variables in Railway dashboard.
) else (
    echo .env file found
    
    :: Check for BOT_TOKEN in .env
    findstr /C:"BOT_TOKEN" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo BOT_TOKEN found in .env
    ) else (
        echo WARNING: BOT_TOKEN not found in .env
    )
    
    :: Check for OPENAI_API_KEY in .env
    findstr /C:"OPENAI_API_KEY" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo OPENAI_API_KEY found in .env
    ) else (
        echo WARNING: OPENAI_API_KEY not found in .env
    )
)

echo.
echo === DEPLOYMENT INSTRUCTIONS ===
echo 1. Create a new project on Railway: 'New Project' -^> 'Deploy from GitHub'
echo 2. Select your GitHub repository
echo 3. Add the following environment variables in the Railway dashboard:
echo    - BOT_TOKEN (required)
echo    - OPENAI_API_KEY (optional, for AI functionality)
echo    - ELEVEN_LABS_API_KEY (optional, for voice functionality)
echo 4. Deploy the project
echo 5. Check logs to verify the bot has started

echo.
echo === READY FOR DEPLOYMENT ===
echo Your project is now ready to be deployed to Railway.
echo.
echo Press any key to exit...
pause > nul 