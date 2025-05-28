#!/usr/bin/env python
"""
Test script to verify Supabase connection and dependency installation.
This script checks if all required Supabase-related dependencies are working properly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_dependency(module_name):
    """Check if a dependency is installed correctly."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing {module_name}: {e}")
        return False

def test_supabase_dependencies():
    """Test all Supabase-related dependencies."""
    dependencies = [
        "httpx",
        "postgrest",
        "gotrue",
        "storage3",
        "supabase"
    ]
    
    all_success = True
    for dep in dependencies:
        if not check_dependency(dep):
            all_success = False
    
    return all_success

def test_supabase_connection():
    """Test connection to Supabase if credentials are available."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️ Supabase credentials not found in environment variables")
        return False
    
    try:
        from supabase import create_client
        
        supabase = create_client(supabase_url, supabase_key)
        # Simple query to verify connection
        response = supabase.table("profiles").select("*").limit(1).execute()
        print(f"✅ Successfully connected to Supabase")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Supabase dependencies and connection...")
    
    if test_supabase_dependencies():
        print("✅ All Supabase dependencies are installed correctly")
    else:
        print("❌ Some Supabase dependencies are missing or installed incorrectly")
    
    # Optional connection test if environment variables are available
    test_supabase_connection()
    
    print("🔍 Supabase dependency test complete") 