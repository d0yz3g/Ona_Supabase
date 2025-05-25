#!/usr/bin/env python3
"""
Dependency checker script for ONA bot.
This script verifies that all required dependencies are installed
and reports any missing or incompatible packages.
"""

import importlib
import sys
import subprocess
import pkg_resources

# Essential dependencies for the bot to function
ESSENTIAL_DEPS = [
    ("aiogram", "3.0.0"),
    ("pydantic", "1.10.12"),
    ("python-dotenv", None),
    ("APScheduler", None),
]

# Optional dependencies that provide additional functionality
OPTIONAL_DEPS = [
    ("openai", None),
    ("elevenlabs", None),
    ("gTTS", None),
    ("ephem", None),
    ("PyYAML", None),
    ("requests", None),
]

def check_dependency(package_name, required_version=None):
    """Check if a package is installed and meets version requirements."""
    try:
        module = importlib.import_module(package_name)
        
        # Special case for some modules that have different import and package names
        if package_name == "python-dotenv":
            package_name = "dotenv"
            module = importlib.import_module(package_name)
        
        # Try to get the version if module is found
        try:
            version = pkg_resources.get_distribution(package_name).version
            if required_version and version != required_version:
                print(f"⚠️ {package_name} version mismatch: found {version}, required {required_version}")
                return False
            print(f"✅ {package_name} {version} is installed")
            return True
        except Exception:
            # If we can import but can't get the version, assume it's working
            print(f"✅ {package_name} is installed (version unknown)")
            return True
            
    except ImportError:
        print(f"❌ {package_name} is not installed")
        return False

def install_package(package_name, required_version=None):
    """Attempt to install a package using pip."""
    package_spec = f"{package_name}=={required_version}" if required_version else package_name
    print(f"📦 Installing {package_spec}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_spec])
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_spec}")
        return False

def main():
    """Main function to check all dependencies."""
    print("=== ONA Bot Dependency Checker ===")
    
    all_essential_found = True
    all_optional_found = True
    
    print("\n== Essential Dependencies ==")
    for package, version in ESSENTIAL_DEPS:
        if not check_dependency(package, version):
            all_essential_found = False
            if input(f"Attempt to install {package}? (y/n): ").lower() == 'y':
                install_package(package, version)
    
    print("\n== Optional Dependencies ==")
    for package, version in OPTIONAL_DEPS:
        if not check_dependency(package, version):
            all_optional_found = False
            if input(f"Attempt to install {package}? (y/n): ").lower() == 'y':
                install_package(package, version)
    
    print("\n== Results ==")
    if all_essential_found:
        print("✅ All essential dependencies are installed")
    else:
        print("❌ Some essential dependencies are missing")
    
    if all_optional_found:
        print("✅ All optional dependencies are installed")
    else:
        print("⚠️ Some optional dependencies are missing")

if __name__ == "__main__":
    main() 