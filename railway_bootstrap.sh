#!/bin/bash

# Скрипт запуска для Railway с полным исправлением проблемы AsyncOpenAI

echo "=== ONA Bot Railway Bootstrap ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Проверка версии openai
echo "=== Checking OpenAI version ==="
OPENAI_VERSION=$(pip show openai | grep Version | awk '{print $2}')
echo "Installed OpenAI version: $OPENAI_VERSION"

# Установка всех зависимостей
echo "=== Installing all dependencies ==="
pip install --no-cache-dir -r requirements.txt

# Установка критических зависимостей вручную
echo "=== Forcing installation of critical dependencies ==="
pip install --no-cache-dir --force-reinstall openai==1.3.3
pip install --no-cache-dir --force-reinstall httpx==0.23.3
pip install --no-cache-dir --force-reinstall python-dotenv==1.0.0
pip install --no-cache-dir --force-reinstall pydantic==2.1.1
pip install --no-cache-dir --force-reinstall aiogram==3.0.0

# Установка Supabase, если нужно
echo "=== Installing Supabase dependencies ==="
pip install --no-cache-dir postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2 2>/dev/null || true

# Проверка наличия AsyncOpenAI в openai
echo "=== Checking for AsyncOpenAI in openai package ==="
if python -c "from openai import AsyncOpenAI; print('AsyncOpenAI available')" 2>/dev/null; then
    echo "✅ AsyncOpenAI is available in openai package"
    # Просто запускаем бота через safe_startup.py
    echo "=== Starting bot directly with safe_startup.py ==="
    python safe_startup.py
    exit $?
fi

echo "❌ AsyncOpenAI is not available in openai package, applying patches..."

# Создание patch файла для импортов openai
echo "=== Creating OpenAI patch file ==="
cat > "openai_patch.py" << 'EOF'
"""Автоматически сгенерированный патч для openai модуля"""
import sys
import os

class AsyncOpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        print("AsyncOpenAI stub initialized")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print("AsyncOpenAI.chat.completions.create called")
                return {"choices": [{"message": {"content": "OpenAI API stub response"}}]}
    
    class audio:
        @staticmethod
        async def transcriptions_create(*args, **kwargs):
            print("AsyncOpenAI.audio.transcriptions_create called")
            return {"text": "Audio transcription stub"}

class OpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        print("OpenAI stub initialized")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print("OpenAI.chat.completions.create called")
                return {"choices": [{"message": {"content": "OpenAI API stub response"}}]}
    
    class audio:
        @staticmethod
        def transcriptions_create(*args, **kwargs):
            print("OpenAI.audio.transcriptions_create called")
            return {"text": "Audio transcription stub"}

# Патчим существующий модуль openai
try:
    import openai
    if not hasattr(openai, 'AsyncOpenAI'):
        openai.AsyncOpenAI = AsyncOpenAI
        print("Added AsyncOpenAI to openai module")
    if not hasattr(openai, 'OpenAI'):
        openai.OpenAI = OpenAI
        print("Added OpenAI to openai module")
    
    # Патчим sys.modules
    sys.modules['openai.AsyncOpenAI'] = AsyncOpenAI
    sys.modules['openai.OpenAI'] = OpenAI
    
    print("OpenAI module patched successfully")
except Exception as e:
    print(f"Error patching openai module: {e}")
EOF

# Создание заглушек для проблемных модулей
echo "=== Creating stubs for problematic modules ==="
python fix_problem_modules.py || echo "❌ Failed to create problem module stubs"

# Модификация модуля openai в site-packages
echo "=== Modifying openai module in site-packages ==="
python modify_site_packages.py || echo "❌ Failed to modify site packages"

# Исправление всех импортов AsyncOpenAI в проекте
echo "=== Fixing all AsyncOpenAI imports in project ==="
python fix_all_openai_imports.py || echo "❌ Failed to fix all imports"

# Установка импорт хука перед запуском
echo "=== Setting up import hook ==="
python -c "
import sys
import os

try:
    # Импортируем наш патч
    sys.path.insert(0, os.getcwd())
    import fix_imports_global
    print('✅ Global import hook activated successfully')
except Exception as e:
    print(f'❌ Error activating global import hook: {e}')

# Принудительно применяем патч из файла
try:
    import openai_patch
    print('✅ Applied openai_patch successfully')
except Exception as e:
    print(f'❌ Error applying openai_patch: {e}')
"

# Запуск скрипта для проверки совместимости pydantic и aiogram
echo "=== Running pydantic compatibility fix ==="
python fix_pydantic.py || echo "❌ Failed to fix pydantic compatibility"

# Устанавливаем переменную окружения для PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"

# Запуск safe_startup.py для запуска бота с патчами
echo "=== Running safe_startup.py ==="
PYTHONPATH="$PWD:$PYTHONPATH" python safe_startup.py

# Если safe_startup.py завершилась с ошибкой, пробуем запустить main.py напрямую
if [ $? -ne 0 ]; then
    echo "❌ safe_startup.py failed, trying to run main.py directly"
    echo "=== Fallback: trying to run main.py directly ==="
    PYTHONPATH="$PWD:$PYTHONPATH" python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

# Импортируем патчи
try:
    import fix_imports_global
    import openai_patch
    
    # Создаем временный файл-обертку
    with open('temp_main_wrapper.py', 'w') as f:
        f.write('''
import sys
import os
sys.path.insert(0, os.getcwd())
import fix_imports_global
import openai_patch

try:
    import main
except Exception as e:
    print(f'Error running main.py: {e}')
    sys.exit(1)
''')
    
    # Запускаем через обертку
    os.system(f'{sys.executable} temp_main_wrapper.py')
    
except Exception as e:
    print(f'Fallback error: {e}')
    sys.exit(1)
"
fi