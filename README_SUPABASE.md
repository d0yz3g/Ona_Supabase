# Fixing Supabase Connection on Railway

This guide will help you fix the error: `WARNING - Не удалось импортировать модуль Supabase: No module named 'supabase'`

## Quick Fix

1. **Update requirements.txt**

   Your `requirements.txt` file has been updated to include Supabase and all its dependencies:
   ```
   supabase-py==2.3.1
   postgrest-py==0.11.0
   httpx
   gotrue==1.3.0
   storage3==0.6.1
   realtime==1.0.0
   ```

2. **Set Environment Variables in Railway**

   In your Railway project dashboard:
   - Go to the Variables tab
   - Add SUPABASE_URL: Your Supabase project URL
   - Add SUPABASE_KEY: Your Supabase service role API key (not the anon key)

3. **Redeploy Your Application**

   Railway will automatically detect changes to your requirements.txt and install the required dependencies during deployment.

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

1. Added Supabase dependencies to requirements.txt
2. Created testing and setup scripts:
   - `test_supabase_connection.py`: Tests Supabase connection
   - `railway_supabase_setup.sh`: Shell script to set up Supabase on Railway
3. Updated Dockerfile to properly install Supabase dependencies
4. Added documentation in `railway_supabase_guide.md`

## Manual Installation (if needed)

If you need to manually install Supabase on Railway:

```bash
pip install supabase-py==2.3.1 postgrest-py==0.11.0 httpx gotrue==1.3.0 storage3==0.6.1 realtime==1.0.0
```

## Troubleshooting

If you still experience issues:
1. Check if you're using the correct Supabase URL and API key
2. Verify that all required tables exist in your Supabase database
3. Check Railway logs for specific error messages
4. See the detailed guide in `railway_supabase_guide.md` 