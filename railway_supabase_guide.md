# Railway Supabase Integration Guide

This guide provides step-by-step instructions on how to set up, test, and troubleshoot Supabase integration with your Telegram bot running on Railway.

## Prerequisites

- A Railway account with a project set up
- A Supabase account with a project set up
- Your bot code already deployed to Railway or ready to be deployed

## Step 1: Set Up Environment Variables

1. In your Railway project dashboard, navigate to the **Variables** tab
2. Add the following environment variables:
   - `SUPABASE_URL`: Your Supabase project URL (e.g., `https://abcdefghijklm.supabase.co`)
   - `SUPABASE_KEY`: Your Supabase service role API key (found in Project Settings > API)

> **Important**: Use the **service role key** for your backend, not the public anon key.

## Step 2: Update Dependencies

Ensure your `requirements.txt` file includes all the necessary dependencies for Supabase:

```
supabase-py==2.3.1
postgrest-py==0.11.0
httpx
gotrue==1.3.0
storage3==0.6.1
realtime==1.0.0
```

## Step 3: Test Supabase Connection

1. SSH into your Railway deployment or use the Railway CLI to access your deployment
2. Run the test script:

```bash
python test_supabase_connection.py
```

If the test passes, you should see a message indicating successful connection to Supabase.

## Step 4: Manual Troubleshooting

If you're experiencing connection issues, try these troubleshooting steps:

1. Verify Supabase module installation:

```bash
python -c "import supabase; print(f'Supabase installed, version: {supabase.__version__ if hasattr(supabase, \"__version__\") else \"unknown\"}')"
```

2. Check if all dependencies are installed:

```bash
for module in postgrest httpx gotrue storage3 realtime; do
  python -c "import $module; print(f'$module installed successfully')" || echo "$module not installed"
done
```

3. Manually install Supabase and dependencies:

```bash
pip install supabase-py==2.3.1 postgrest-py==0.11.0 httpx gotrue==1.3.0 storage3==0.6.1 realtime==1.0.0
```

4. Check environment variables:

```bash
python -c "import os; print(f'SUPABASE_URL set: {bool(os.getenv(\"SUPABASE_URL\"))}'); print(f'SUPABASE_KEY set: {bool(os.getenv(\"SUPABASE_KEY\"))}')"
```

## Step 5: Using the Supabase Setup Script

We've provided a setup script to automate the process:

```bash
chmod +x railway_supabase_setup.sh
./railway_supabase_setup.sh
```

This script will:
- Install Supabase and its dependencies
- Verify the installation
- Check for environment variables
- Test the connection to your Supabase project

## Step 6: Docker Deployment Notes

If you're using Docker deployment on Railway:

1. Make sure your Dockerfile explicitly installs Supabase dependencies
2. Include a step to test Supabase connection before starting your application
3. Mount your environment variables correctly

Example Dockerfile section:

```dockerfile
# Install Supabase dependencies
RUN pip install --no-cache-dir --force-reinstall postgrest-py==0.11.0 httpx gotrue==1.3.0 storage3==0.6.1 realtime==1.0.0 supabase-py==2.3.1

# Test Supabase connection
RUN python -c "import supabase; print('Supabase imported successfully')"
```

## Common Issues and Solutions

1. **"No module named 'supabase'"**
   - Solution: Run `pip install supabase-py==2.3.1`

2. **Supabase installed but dependencies missing**
   - Solution: Install all dependencies separately:
     ```
     pip install postgrest-py httpx gotrue storage3 realtime
     ```

3. **Connection errors despite correct installation**
   - Verify your Supabase URL and API key
   - Check if your Supabase project is active
   - Ensure your IP is not blocked by Supabase (unlikely but possible)

4. **Table does not exist errors**
   - Create the required tables in your Supabase dashboard

## Additional Resources

- [Supabase Python Client Documentation](https://github.com/supabase-community/supabase-py)
- [Supabase Documentation](https://supabase.com/docs)
- [Railway Documentation](https://docs.railway.app/) 