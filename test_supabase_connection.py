#!/usr/bin/env python
"""
Script to test Supabase connection in Railway environment.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("supabase_test")

# Load environment variables
load_dotenv()

def check_supabase_installation():
    """Check if Supabase module is installed correctly."""
    try:
        import supabase
        logger.info(f"✅ Supabase module successfully imported (version: {supabase.__version__ if hasattr(supabase, '__version__') else 'unknown'})")
        
        # Check for required dependencies
        for module_name in ["postgrest", "httpx", "gotrue", "storage3", "realtime"]:
            try:
                module = __import__(module_name)
                logger.info(f"✅ Dependency {module_name} successfully imported")
            except ImportError as e:
                logger.error(f"❌ Dependency {module_name} import failed: {e}")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Supabase module import failed: {e}")
        logger.error("   Please run: pip install supabase-py postgrest-py httpx gotrue storage3 realtime")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error when importing Supabase: {e}")
        return False

def test_supabase_connection():
    """Test connection to Supabase using credentials from environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Missing required environment variables:")
        logger.error(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
        logger.error(f"   SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
        return False
    
    try:
        from supabase import create_client
        
        logger.info("Creating Supabase client...")
        client = create_client(supabase_url, supabase_key)
        
        # Test connection with a simple query
        logger.info("Testing connection to Supabase...")
        try:
            # Check if user_profiles table exists by trying to access it
            response = client.table("user_profiles").select("id").limit(1).execute()
            logger.info(f"✅ Successfully connected to Supabase and queried user_profiles table!")
            logger.info(f"   Response data: {response.data}")
            return True
        except Exception as query_error:
            logger.warning(f"⚠️ Could not query user_profiles table: {query_error}")
            
            # Try a more basic test
            logger.info("Trying a basic test query...")
            try:
                # Try a simpler query to check connectivity
                health = client.table("healthcheck").select("*").limit(1).execute()
                logger.info("✅ Successfully connected to Supabase with basic query")
                return True
            except Exception as basic_error:
                logger.error(f"❌ Basic query also failed: {basic_error}")
                return False
    except Exception as e:
        logger.error(f"❌ Error when connecting to Supabase: {e}")
        return False

def main():
    """Main function that runs all tests."""
    logger.info("=== SUPABASE CONNECTION TEST ===")
    
    # Check if Supabase module is installed correctly
    if not check_supabase_installation():
        logger.error("❌ Supabase module installation check failed. Test cannot continue.")
        sys.exit(1)
    
    # Test connection to Supabase
    if test_supabase_connection():
        logger.info("✅ Supabase connection test completed successfully!")
    else:
        logger.error("❌ Supabase connection test failed.")
        logger.error("   Please check your SUPABASE_URL and SUPABASE_KEY environment variables.")

if __name__ == "__main__":
    main() 