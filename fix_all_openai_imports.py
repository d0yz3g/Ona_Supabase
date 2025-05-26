#!/usr/bin/env python3
"""
Сканирует все Python файлы в проекте и заменяет импорты AsyncOpenAI на наши заглушки.
"""
import os
import re
import sys
import glob
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_all_openai_imports")

# Шаблоны для поиска импортов
IMPORT_PATTERNS = [
    r'from\s+openai\s+import\s+AsyncOpenAI',
    r'from\s+openai\s+import\s+.*?,\s*AsyncOpenAI',
    r'from\s+openai\s+import\s+AsyncOpenAI\s*,\s*.*?',
    r'import\s+openai'
]

# Шаблон для использования AsyncOpenAI
USAGE_PATTERN = r'AsyncOpenAI\s*\('

# Заглушка для AsyncOpenAI
ASYNC_OPENAI_STUB = """
# === BEGIN AsyncOpenAI Stub ===
class AsyncOpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        print(f"[Stub in {os.path.basename(__file__)}] AsyncOpenAI initialized")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print(f"[Stub in {os.path.basename(__file__)}] AsyncOpenAI.chat.completions.create called")
                return {"choices": [{"message": {"content": "OpenAI API stub response"}}]}
    
    class audio:
        @staticmethod
        async def transcriptions_create(*args, **kwargs):
            print(f"[Stub in {os.path.basename(__file__)}] AsyncOpenAI.audio.transcriptions_create called")
            return {"text": "Audio transcription stub"}
# === END AsyncOpenAI Stub ===
"""

# Заглушка для OpenAI
OPENAI_STUB = """
# === BEGIN OpenAI Stub ===
class OpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        print(f"[Stub in {os.path.basename(__file__)}] OpenAI initialized")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print(f"[Stub in {os.path.basename(__file__)}] OpenAI.chat.completions.create called")
                return {"choices": [{"message": {"content": "OpenAI API stub response"}}]}
    
    class audio:
        @staticmethod
        def transcriptions_create(*args, **kwargs):
            print(f"[Stub in {os.path.basename(__file__)}] OpenAI.audio.transcriptions_create called")
            return {"text": "Audio transcription stub"}
# === END OpenAI Stub ===
"""

def find_python_files(directory="."):
    """Находит все Python файлы в указанной директории"""
    python_files = []
    
    # Находим все .py файлы
    for py_file in glob.glob(os.path.join(directory, "**", "*.py"), recursive=True):
        # Игнорируем текущий скрипт
        if os.path.basename(py_file) != os.path.basename(__file__):
            python_files.append(py_file)
    
    return python_files

def check_file_for_openai_imports(file_path):
    """Проверяет файл на наличие импортов openai и AsyncOpenAI"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие импортов
        has_import = any(re.search(pattern, content) for pattern in IMPORT_PATTERNS)
        
        # Проверяем использование AsyncOpenAI
        uses_async_openai = bool(re.search(USAGE_PATTERN, content))
        
        return has_import or uses_async_openai
    
    except Exception as e:
        logger.error(f"Ошибка при проверке файла {file_path}: {e}")
        return False

def add_stubs_to_file(file_path):
    """Добавляет заглушки в файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Создаем резервную копию файла
        backup_path = f"{file_path}.bak"
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Создана резервная копия файла {backup_path}")
        
        # Проверяем, есть ли уже заглушки
        if "# === BEGIN AsyncOpenAI Stub ===" in content:
            logger.info(f"Файл {file_path} уже содержит заглушки")
            return True
        
        # Находим место для вставки заглушек (после импортов)
        import_end = 0
        for line_num, line in enumerate(content.split('\n')):
            if line.startswith('import ') or line.startswith('from '):
                import_end = line_num + 1
        
        # Вставляем заглушки после импортов
        lines = content.split('\n')
        lines.insert(import_end, ASYNC_OPENAI_STUB)
        lines.insert(import_end + 1, OPENAI_STUB)
        
        # Записываем модифицированный файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Добавлены заглушки в файл {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении заглушек в файл {file_path}: {e}")
        return False

def modify_imports_in_file(file_path):
    """Модифицирует импорты в файле, добавляя заглушки"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Создаем резервную копию файла
        backup_path = f"{file_path}.bak"
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Создана резервная копия файла {backup_path}")
        
        # Добавляем заглушки в файл
        if add_stubs_to_file(file_path):
            logger.info(f"Файл {file_path} успешно модифицирован")
            return True
        else:
            logger.error(f"Не удалось модифицировать файл {file_path}")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при модификации файла {file_path}: {e}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало сканирования и модификации файлов ===")
    
    # Находим все Python файлы
    python_files = find_python_files()
    logger.info(f"Найдено Python файлов: {len(python_files)}")
    
    # Проверяем файлы на наличие импортов openai
    files_with_openai = []
    for file_path in python_files:
        if check_file_for_openai_imports(file_path):
            files_with_openai.append(file_path)
    
    logger.info(f"Файлов с импортами openai: {len(files_with_openai)}")
    
    # Модифицируем файлы с импортами
    success_count = 0
    for file_path in files_with_openai:
        logger.info(f"Модификация файла {file_path}")
        if modify_imports_in_file(file_path):
            success_count += 1
    
    logger.info(f"=== Завершено. Успешно модифицировано файлов: {success_count}/{len(files_with_openai)} ===")
    return 0 if success_count == len(files_with_openai) else 1

if __name__ == "__main__":
    sys.exit(main()) 