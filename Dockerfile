FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install critical Python dependencies first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Create a dependency check script
COPY requirements.txt ./
RUN echo '#!/usr/bin/env python3\n\
import sys\n\
import pkg_resources\n\
import subprocess\n\
\n\
def check_install(package_name, version=None):\n\
    package_str = package_name if version is None else f"{package_name}=={version}"\n\
    try:\n\
        if version is not None:\n\
            pkg_resources.require(package_str)\n\
            print(f"✅ {package_str} is already installed")\n\
            return True\n\
        else:\n\
            __import__(package_name)\n\
            print(f"✅ {package_name} is already installed")\n\
            return True\n\
    except (ImportError, pkg_resources.DistributionNotFound):\n\
        print(f"⚠️ {package_str} is not installed, attempting to install...")\n\
        try:\n\
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", package_str])\n\
            print(f"✅ Successfully installed {package_str}")\n\
            return True\n\
        except subprocess.CalledProcessError as e:\n\
            print(f"❌ Failed to install {package_str}: {e}")\n\
            return False\n\
\n\
def main():\n\
    # List of critical dependencies\n\
    dependencies = [\n\
        ("pydantic", "1.10.12"),\n\
        ("aiogram", "3.0.0"),\n\
        "python-dotenv",\n\
        "APScheduler",\n\
    ]\n\
\n\
    success = True\n\
    for dep in dependencies:\n\
        if isinstance(dep, tuple):\n\
            pkg_name, version = dep\n\
            success = check_install(pkg_name, version) and success\n\
        else:\n\
            success = check_install(dep) and success\n\
\n\
    if not success:\n\
        print("❌ Some critical dependencies failed to install")\n\
        sys.exit(1)\n\
    else:\n\
        print("✅ All critical dependencies installed successfully")\n\
\n\
if __name__ == "__main__":\n\
    main()\n\
' > check_dependencies.py && chmod +x check_dependencies.py

# Install core dependencies one by one with error handling
RUN pip install --no-cache-dir pydantic==1.10.12 || echo "Failed to install pydantic, will try again later"
RUN pip install --no-cache-dir aiogram==3.0.0 || echo "Failed to install aiogram, will try again later"
RUN pip install --no-cache-dir python-dotenv || echo "Failed to install python-dotenv, will use fallback"
RUN pip install --no-cache-dir APScheduler || echo "Failed to install APScheduler, will try again later"

# Copy entry point script and fallback implementations
COPY railway_entry.sh fix_dotenv_import.py dotenv.py dotenv_fallback.py ./
RUN chmod +x railway_entry.sh

# Verify critical dependencies
RUN python check_dependencies.py || echo "Will attempt to install remaining dependencies during startup"

# Try to install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt || echo "Some requirements failed, continuing anyway"

# Copy all application files
COPY . .

# Create necessary directories
RUN mkdir -p logs tmp

# Set up entry point
CMD ["./railway_entry.sh"] 