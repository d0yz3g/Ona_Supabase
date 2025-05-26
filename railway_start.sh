#!/bin/bash
# Simple Railway startup script that handles common issues

echo "=== ONA Bot Railway Startup ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Check if openai has AsyncOpenAI
if python -c "from openai import AsyncOpenAI; print('AsyncOpenAI is available')" 2>/dev/null; then
    echo "✅ AsyncOpenAI is available, starting bot normally"
    python main.py
else
    echo "❌ AsyncOpenAI is not available, using bootstrap script"
    # Apply patches and start with bootstrap
    python -c "import sys; sys.path.insert(0, '$(pwd)'); import fix_imports_global"
    python railway_bootstrap.py 