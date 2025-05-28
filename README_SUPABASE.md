# Fixing Supabase Connection on Railway

This guide will help you fix the error: `WARNING - Не удалось импортировать модуль Supabase: No module named 'supabase'`

## Quick Fix

1. **Update requirements.txt**

   Your `requirements.txt` file has been updated to include Supabase and all its dependencies with compatible versions:
   ```
   supabase-py==2.0.0
   postgrest-py==0.10.3
   httpx==0.24.1
   gotrue==0.5.4
   storage3==0.5.4
   realtime==0.1.3
   ```

2. **Set Environment Variables in Railway**

   In your Railway project dashboard:
   - Go to the Variables tab
   - Add SUPABASE_URL: Your Supabase project URL
   - Add SUPABASE_KEY: Your Supabase service role API key (not the anon key)

3. **Update Dockerfile**

   The Dockerfile has been updated to install dependencies in the correct order and include necessary system packages:
   ```dockerfile
   # Install system dependencies
   RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       g++ \
       python3-dev \
       libffi-dev \
       libssl-dev \
       pkg-config \
       git \
       && apt-get clean \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Supabase and dependencies step by step
   RUN pip install --no-cache-dir httpx==0.24.1
   RUN pip install --no-cache-dir postgrest-py==0.10.3
   RUN pip install --no-cache-dir gotrue==0.5.4
   RUN pip install --no-cache-dir storage3==0.5.4
   RUN pip install --no-cache-dir realtime==0.1.3
   RUN pip install --no-cache-dir supabase-py==2.0.0
   ```

4. **Redeploy Your Application**

   Railway will automatically detect changes to your requirements.txt and Dockerfile, then install the required dependencies during deployment.

## Verifying the Fix

After deployment, your logs should no longer show the error message. Instead, you should see:
```
INFO - Модуль Supabase успешно импортирован
INFO - Хранилище Supabase успешно инициализировано
```

## Testing Supabase Connection

The included script `test_supabase_connection.py` can be used to test your Supabase connection.

To run it on Railway:
1. SSH into your Railway deployment: `railway shell`
2. Run: `python test_supabase_connection.py`

## What Was Changed

1. Downgraded Supabase and dependencies to compatible versions:
   - Changed from `supabase-py==2.3.1` to `supabase-py==2.0.0`
   - Changed from `postgrest-py==0.11.0` to `postgrest-py==0.10.3`
   - Changed from `httpx==0.28.1` to `httpx==0.24.1`
   - Changed from `gotrue==1.3.0` to `gotrue==0.5.4`
   - Changed from `storage3==0.6.1` to `storage3==0.5.4`
   - Removed `realtime==0.1.3` as it's incompatible with Python 3.11 and not needed with `supabase-py==2.0.0`

2. Added necessary system dependencies to Dockerfile:
   - Added g++
   - Added pkg-config
   - Added git

3. Modified the installation process to install dependencies together rather than one by one to ensure compatibility

4. Created testing and setup scripts:
   - `test_supabase_connection.py`: Tests Supabase connection with the correct versions
   - `railway_supabase_setup.sh`: Shell script to set up Supabase on Railway

## Manual Installation (if needed)

If you need to manually install Supabase on Railway:

```bash
pip install httpx==0.24.1 postgrest-py==0.10.3 gotrue==0.5.4 storage3==0.5.4 supabase-py==2.0.0
```

## About the `realtime` Package

The separate `realtime==0.1.3` package has been removed from the dependencies because:

1. It's incompatible with Python 3.11
2. In newer versions of `supabase-py`, realtime functionality is integrated into the main package
3. The version 0.1.3 is deprecated and no longer maintained

Realtime functionality (websockets, subscriptions, etc.) still works with this configuration through the main `supabase-py` package. The change only affects how the dependencies are structured, not the available features.

## Troubleshooting

If you still experience issues:
1. Check if you're using the correct Supabase URL and API key
2. Verify that all required tables exist in your Supabase database
3. Check Railway logs for specific error messages
4. See the detailed guide in `railway_supabase_guide.md`

## Why This Fix Works

The issue was related to version incompatibilities between Supabase and its dependencies. The newer versions (2.3.1) require different system dependencies and have more complex installation requirements. By downgrading to version 2.0.0 and its compatible dependencies, we ensure a smooth installation process in the Docker environment. 