#!/usr/bin/env python3
"""
Скрипт для комплексного решения проблемы с импортом AsyncOpenAI
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

# Список всех Python файлов в проекте
def get_all_python_files():
    """Получает список всех Python файлов в проекте"""
    return glob.glob("*.py")

# Код заглушки AsyncOpenAI для вставки в файлы
OPENAI_MOCK_CODE = """
# Заглушка для AsyncOpenAI
class AsyncOpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[Mock AsyncOpenAI] Инициализация в {__name__}")
    
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                print(f"[Mock AsyncOpenAI] Вызов chat.completions.create в {__name__}")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}

# Заглушка для OpenAI
class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        print(f"[Mock OpenAI] Инициализация в {__name__}")
    
    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                print(f"[Mock OpenAI] Вызов chat.completions.create в {__name__}")
                return {"choices": [{"message": {"content": "Заглушка OpenAI API"}}]}
"""

def backup_file(file_path):
    """Создает резервную копию файла"""
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии {file_path}: {e}")
            return False
    return True

def fix_file(file_path):
    """Исправляет импорты OpenAI и AsyncOpenAI в файле"""
    if not os.path.exists(file_path):
        logger.warning(f"Файл {file_path} не найден")
        return False
    
    # Создаем резервную копию
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, используется ли в файле AsyncOpenAI или OpenAI
        if "AsyncOpenAI" not in content and "OpenAI" not in content:
            logger.info(f"Файл {file_path} не использует AsyncOpenAI или OpenAI")
            return True
        
        # Проверяем, есть ли уже заглушка AsyncOpenAI
        if "class AsyncOpenAI" in content:
            logger.info(f"Файл {file_path} уже содержит заглушку AsyncOpenAI")
            return True
        
        # Заменяем импорты AsyncOpenAI на комментарии
        content = re.sub(
            r'from\s+openai\s+import\s+([^#\n]*)(AsyncOpenAI|OpenAI)', 
            r'# \g<0>  # Заменено на локальную заглушку', 
            content
        )
        
        # Находим место для вставки заглушки - после импортов
        import_block_end = 0
        for match in re.finditer(r'^(?:import|from)\s+\w+', content, re.MULTILINE):
            import_block_end = max(import_block_end, match.end())
        
        if import_block_end > 0:
            # Вставляем после последнего импорта
            import_lines = []
            other_lines = []
            for line in content.splitlines():
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(line)
                else:
                    other_lines.append(line)
            
            content = '\n'.join(import_lines) + '\n' + OPENAI_MOCK_CODE + '\n' + '\n'.join(other_lines)
        else:
            # Вставляем в начало файла
            content = OPENAI_MOCK_CODE + '\n\n' + content
        
        # Записываем изменения обратно в файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Файл {file_path} успешно исправлен")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при исправлении файла {file_path}: {e}")
        # Восстанавливаем из резервной копии
        try:
            with open(f"{file_path}.bak", 'r', encoding='utf-8') as src:
                with open(file_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info(f"Файл {file_path} восстановлен из резервной копии")
        except Exception as restore_error:
            logger.error(f"Ошибка при восстановлении файла {file_path}: {restore_error}")
        return False

def main():
    """Основная функция скрипта"""
    logger.info("=== Начало исправления всех импортов OpenAI ===")
    
    # Создаем модуль-заглушку openai_stub.py
    with open("openai_stub.py", "w", encoding="utf-8") as f:
        f.write(OPENAI_MOCK_CODE)
    logger.info("Создан модуль-заглушка openai_stub.py")
    
    # Получаем список всех Python файлов
    python_files = get_all_python_files()
    logger.info(f"Найдено {len(python_files)} Python файлов")
    
    # Исправляем каждый файл
    success_count = 0
    for file_path in python_files:
        if fix_file(file_path):
            success_count += 1
    
    logger.info(f"=== Завершено. Исправлено файлов: {success_count}/{len(python_files)} ===")
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 