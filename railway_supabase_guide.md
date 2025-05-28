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

Ensure your `requirements.txt` file includes all the necessary dependencies for Supabase with compatible versions:

```
supabase-py==2.0.0
postgrest-py==0.10.3
httpx==0.24.1
gotrue==0.5.4
storage3==0.5.4
realtime==0.1.3
```

## Step 3: Use Compatible Dockerfile

If you're using Docker deployment, ensure your Dockerfile includes the necessary system dependencies and installs packages in the correct order:

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

# Install Supabase dependencies one by one
RUN pip install --no-cache-dir httpx==0.24.1
RUN pip install --no-cache-dir postgrest-py==0.10.3
RUN pip install --no-cache-dir gotrue==0.5.4
RUN pip install --no-cache-dir storage3==0.5.4
RUN pip install --no-cache-dir realtime==0.1.3
RUN pip install --no-cache-dir supabase-py==2.0.0
```

## Step 4: Test Supabase Connection

After deployment or during local development, you can test your Supabase connection:

```bash
python test_supabase_connection.py
```

If the test passes, you should see a message indicating successful connection to Supabase.

## Step 5: Manual Troubleshooting

If you're experiencing connection issues, try these troubleshooting steps:

1. Verify Supabase module installation:

```bash
python -c "import supabase; print(f'Supabase installed, version: {supabase.__version__ if hasattr(supabase, \"__version__\") else \"unknown\"}')"
```

2. Check if all dependencies are installed with correct versions:

```bash
for module in postgrest httpx gotrue storage3 realtime; do
  python -c "import $module; version = getattr($module, '__version__', 'unknown'); print(f'$module installed, version: {version}')" || echo "$module not installed"
done
```

3. Manually install Supabase and dependencies with specific versions:

```bash
pip install httpx==0.24.1 postgrest-py==0.10.3 gotrue==0.5.4 storage3==0.5.4 realtime==0.1.3 supabase-py==2.0.0
```

4. Check environment variables:

```bash
python -c "import os; print(f'SUPABASE_URL set: {bool(os.getenv(\"SUPABASE_URL\"))}'); print(f'SUPABASE_KEY set: {bool(os.getenv(\"SUPABASE_KEY\"))}')"
```

## Step 6: Using the Supabase Setup Script

We've provided a setup script to automate the process:

```bash
chmod +x railway_supabase_setup.sh
./railway_supabase_setup.sh
```

This script will:
- Install system dependencies
- Install Supabase and its dependencies with compatible versions
- Verify the installation
- Check for environment variables
- Test the connection to your Supabase project

## Common Issues and Solutions

1. **"No module named 'supabase'"**
   - Solution: Run `pip install supabase-py==2.0.0` with compatible dependencies

2. **Installation fails with build errors**
   - Solution: Install required system dependencies:
     ```bash
     apt-get update && apt-get install -y build-essential gcc g++ python3-dev libffi-dev libssl-dev pkg-config git
     ```

3. **ImportError for any Supabase dependency**
   - Solution: Install dependencies one by one in the correct order:
     ```bash
     pip install httpx==0.24.1
     pip install postgrest-py==0.10.3
     pip install gotrue==0.5.4
     pip install storage3==0.5.4
     pip install realtime==0.1.3
     pip install supabase-py==2.0.0
     ```

4. **Connection errors despite correct installation**
   - Verify your Supabase URL and API key
   - Check if your Supabase project is active
   - Ensure your IP is not blocked by Supabase (unlikely but possible)

5. **Table does not exist errors**
   - Create the required tables in your Supabase dashboard

## Why Specific Versions?

We've found that `supabase-py==2.0.0` and its specified dependencies are the most stable combination for Python 3.11 in a Docker environment. Newer versions (like 2.3.1) often require additional system dependencies or have compatibility issues that can cause build failures.

## Additional Resources

- [Supabase Python Client Documentation](https://github.com/supabase-community/supabase-py)
- [Supabase Documentation](https://supabase.com/docs)
- [Railway Documentation](https://docs.railway.app/) 