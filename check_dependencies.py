#!/usr/bin/env python3
"""
Utility script to check and install critical dependencies.
Used during Docker build and startup to ensure all required packages are available.
"""
import sys
import importlib.util
import subprocess
import os


def is_module_installed(module_name):
    """Check if a module is installed without importing it."""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False


def install_package(package_name, version=None):
    """Attempt to install a package using pip."""
    pkg_str = f"{package_name}=={version}" if version else package_name
    print(f"📦 Installing {pkg_str}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", pkg_str])
        print(f"✅ Successfully installed {pkg_str}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {pkg_str}: {e}")
        return False


def check_and_install_dependencies():
    """Check and install critical dependencies."""
    # List of critical packages (name, version, is_required)
    critical_packages = [
        ("pydantic", "1.10.12", True),
        ("aiogram", "3.0.0", True),
        ("python-dotenv", None, False),  # We have fallback for this
        ("APScheduler", None, False),
    ]
    
    all_required_installed = True
    
    for package, version, is_required in critical_packages:
        if is_module_installed(package):
            print(f"✅ {package} is already installed")
        else:
            success = install_package(package, version)
            if not success and is_required:
                all_required_installed = False
    
    # Check specific modules that might be part of larger packages
    try:
        from aiogram import Bot, Dispatcher
        print("✅ aiogram core modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import aiogram modules: {e}")
        all_required_installed = False
    
    # Create fallback for dotenv if needed
    if not is_module_installed("dotenv"):
        print("⚠️ python-dotenv not found, checking for fallback implementation...")
        if os.path.exists("dotenv.py") or os.path.exists("dotenv_fallback.py"):
            print("✅ Fallback dotenv implementation found")
        else:
            print("⚠️ Creating minimal dotenv fallback...")
            create_dotenv_fallback()
    
    return all_required_installed


def create_dotenv_fallback():
    """Create minimal fallback implementation for dotenv."""
    with open("dotenv_minimal.py", "w") as f:
        f.write("""
'''
Minimal fallback implementation for python-dotenv
'''
import os

def load_dotenv(dotenv_path=None, **kwargs):
    print("[dotenv_minimal] Using minimal fallback implementation")
    if os.path.exists('.env'):
        with open('.env', 'r') as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    return True

def find_dotenv(*args, **kwargs):
    return '.env' if os.path.exists('.env') else ''
""")
    
    # Create symlink to make imports work
    if not os.path.exists("dotenv.py"):
        try:
            with open("dotenv.py", "w") as f:
                f.write("""
'''
Dotenv import redirection
'''
from dotenv_minimal import load_dotenv, find_dotenv
""")
            print("✅ Created dotenv fallback")
        except Exception as e:
            print(f"❌ Failed to create dotenv fallback: {e}")


if __name__ == "__main__":
    print("=== Checking critical dependencies ===")
    success = check_and_install_dependencies()
    
    if success:
        print("✅ All critical dependencies available")
        sys.exit(0)
    else:
        print("❌ Some critical dependencies could not be installed")
        print("⚠️ The application may not function correctly")
        sys.exit(1) 