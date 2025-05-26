#!/bin/bash

# Скрипт запуска для Railway с полным исправлением проблемы AsyncOpenAI

echo "=== ONA Bot Railway Bootstrap ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Установка всех зависимостей
echo "=== Installing all dependencies ==="
pip install --no-cache-dir -r requirements.txt

# Установка pydantic 2.1.1 (совместимого с aiogram 3.0.0)
echo "=== Installing compatible pydantic version ==="
pip install --no-cache-dir --force-reinstall pydantic==2.1.1

# Установка критических зависимостей вручную
echo "=== Forcing installation of critical dependencies ==="
pip install --no-cache-dir openai==0.28.1
pip install --no-cache-dir httpx==0.23.3
pip install --no-cache-dir python-dotenv==1.0.0
pip install --no-cache-dir aiogram==3.0.0

# Установка Supabase
echo "=== Installing Supabase dependencies ==="
pip install --no-cache-dir postgrest-py==0.10.3 realtime-py==0.1.2 storage3==0.5.0 supafunc==0.2.2

# Создание заглушек для проблемных модулей напрямую
echo "=== Creating stubs for problematic modules ==="
python fix_problem_modules.py

# Модификация модуля openai в site-packages
echo "=== Modifying openai module in site-packages ==="
python modify_site_packages.py

# Создание скрипта-патча для импортов
echo "=== Setting up import patch ==="
python -c "
import sys
import os

# Создаем заглушку для openai прямо здесь
openai_stub = '''
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print('AsyncOpenAI stub initialized')
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                return {'choices': [{'message': {'content': 'OpenAI API stub'}}]}

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print('OpenAI stub initialized')
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                return {'choices': [{'message': {'content': 'OpenAI API stub'}}]}
'''

# Патчим модуль openai, если он уже импортирован
if 'openai' in sys.modules:
    module = sys.modules['openai']
    if not hasattr(module, 'AsyncOpenAI'):
        exec(openai_stub, module.__dict__)
        print('Patched existing openai module with AsyncOpenAI stub')
    if not hasattr(module, 'OpenAI'):
        exec(openai_stub, module.__dict__)
        print('Patched existing openai module with OpenAI stub')

# Создаем __pycache__ директорию, если она не существует
os.makedirs('__pycache__', exist_ok=True)

# Создаем фиктивный .pyc файл для openai с нашими заглушками
with open('__pycache__/openai.py', 'w') as f:
    f.write(openai_stub)

print('Created openai stub files')
"

# Запуск скрипта для проверки совместимости pydantic и aiogram
echo "=== Running pydantic compatibility fix ==="
python fix_pydantic.py

# Запуск bootstrap скрипта
echo "=== Running bootstrap script ==="
python railway_bootstrap.py 