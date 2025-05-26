#!/usr/bin/env python3
"""
Скрипт для исправления импортов openai в файлах проекта.
Изменяет импорты AsyncOpenAI и OpenAI на использование нашего адаптера.
"""
import os
import re
import sys
import logging

logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("fix_openai_imports")

# Файлы, которые нужно проверить
files_to_check = [
    'survey_handler.py',
    'conversation_handler.py',
    'reminder_handler.py',
    'voice_handler.py',
    'communication_handler.py',
    'profile_generator.py',
]

# Регулярные выражения для поиска импортов
re_from_openai_import = re.compile(r'from\s+openai\s+import\s+([^#\n]*)(AsyncOpenAI|OpenAI)')
re_import_openai = re.compile(r'import\s+openai')
re_from_openai_direct = re.compile(r'from\s+openai\s+import\s+')

def backup_file(file_path):
    """Создает резервную копию файла"""
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info(f"Создана резервная копия {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии {file_path}: {e}")
            return False
    return True

def fix_openai_imports(file_path):
    """Исправляет импорты openai в файле"""
    if not os.path.exists(file_path):
        logger.warning(f"Файл {file_path} не найден")
        return False
    
    # Создаем резервную копию
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли импорты, которые нужно исправить
        if not (re_from_openai_import.search(content) or 
                (re_import_openai.search(content) and 'AsyncOpenAI' in content)):
            logger.info(f"Файл {file_path} не требует исправления")
            return True
        
        # Добавляем импорт нашего адаптера в начало файла
        adapter_import = "from openai_adapter import AsyncOpenAI, OpenAI  # Адаптер для совместимости\n"
        
        # Заменяем импорты OpenAI/AsyncOpenAI на комментарии
        content = re_from_openai_import.sub(r'# \g<0>  # Заменено на адаптер', content)
        
        # Добавляем импорт адаптера после последнего импорта
        import_block_end = 0
        for match in re.finditer(r'^(?:import|from)\s+\w+', content, re.MULTILINE):
            import_block_end = max(import_block_end, match.end())
        
        if import_block_end > 0:
            # Вставляем после последнего импорта
            content_lines = content.splitlines()
            for i in range(len(content_lines)):
                if re.match(r'^(?:import|from)\s+\w+', content_lines[i]):
                    last_import_line = i
            
            content_lines.insert(last_import_line + 1, adapter_import.strip())
            content = '\n'.join(content_lines)
        else:
            # Вставляем в начало файла
            content = adapter_import + content
        
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
    logger.info("=== Начало исправления импортов openai ===")
    success_count = 0
    
    for file_name in files_to_check:
        if os.path.exists(file_name):
            if fix_openai_imports(file_name):
                success_count += 1
        else:
            logger.warning(f"Файл {file_name} не найден")
    
    logger.info(f"=== Завершено. Исправлено файлов: {success_count}/{len(files_to_check)} ===")
    return 0 if success_count == len(files_to_check) else 1

if __name__ == "__main__":
    sys.exit(main()) 