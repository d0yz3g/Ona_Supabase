#!/bin/bash
# Railway startup script that fixes OpenAI imports first

echo "=== ONA Bot Railway Startup ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Content of site-packages openai:"
ls -la /usr/local/lib/python3.11/site-packages/openai/ || echo "Не удалось показать содержимое директории openai"

echo "=== Проверка версии OpenAI ==="
pip show openai || echo "Не удалось получить информацию о пакете OpenAI"

# Попытка принудительно установить нужную версию OpenAI
echo "=== Принудительная установка openai==1.3.3 ==="
pip install --force-reinstall openai==1.3.3 || echo "❌ Не удалось установить openai==1.3.3"

# Применяем патч к main.py (добавляем import pre_import_fix в начало)
echo "=== Патчинг main.py ==="
python patch_main.py || echo "❌ Не удалось пропатчить main.py"

# Проверяем, что AsyncOpenAI теперь доступен
if python -c "import pre_import_fix; from openai import AsyncOpenAI; print('✅ AsyncOpenAI теперь доступен!')" 2>/dev/null; then
    echo "✅ Проверка успешна, AsyncOpenAI доступен через pre_import_fix"
    echo "=== Запуск бота через main.py ==="
    # Запускаем бота с переменной окружения, указывающей что мы в Railway
    RAILWAY_ENV=1 python main.py
else
    echo "❌ AsyncOpenAI всё ещё недоступен, запускаем через railway_bootstrap.py"
    echo "=== Запуск бота через railway_bootstrap.py ==="
    
    # Предварительно импортируем pre_import_fix
    python -c "
import sys
import os
sys.path.insert(0, '$(pwd)')
try:
    import pre_import_fix
    print('✅ pre_import_fix импортирован успешно')
except Exception as e:
    print(f'❌ Ошибка при импорте pre_import_fix: {e}')
"
    
    # Запускаем бота через bootstrap с переменной окружения
    RAILWAY_ENV=1 python railway_bootstrap.py
fi 