#!/usr/bin/env python3
"""
Патчит main.py для добавления строки импорта pre_import_fix в начало файла.
"""
import os
import re
import sys
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("patch_main")

def patch_main_py():
    """
    Патчит main.py для добавления import pre_import_fix в начало файла.
    """
    main_py_path = "main.py"
    
    # Проверяем существование файла
    if not os.path.exists(main_py_path):
        logger.error(f"Файл {main_py_path} не найден")
        return False
    
    # Читаем содержимое файла
    try:
        with open(main_py_path, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {main_py_path}: {e}")
        return False
    
    # Проверяем, есть ли уже импорт pre_import_fix
    if "import pre_import_fix" in content:
        logger.info(f"Файл {main_py_path} уже содержит import pre_import_fix")
        return True
    
    # Находим начало файла
    try:
        # Ищем место после шебанга или заголовка
        import_pos = 0
        
        # Если есть шебанг, находим его конец
        shebang_match = re.search(r'^#!.*?\n', content)
        if shebang_match:
            import_pos = shebang_match.end()
        
        # Если есть docstring, находим его конец
        docstring_match = re.search(r'""".*?"""\s*\n', content[import_pos:], re.DOTALL)
        if docstring_match:
            import_pos += docstring_match.end()
        
        # Если есть импорты, вставляем перед первым импортом
        import_matches = list(re.finditer(r'^import\s+|^from\s+', content[import_pos:], re.MULTILINE))
        if import_matches:
            import_pos += import_matches[0].start()
        
        # Создаем новое содержимое
        new_content = (
            content[:import_pos] + 
            "# Railway fix для импорта AsyncOpenAI\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "try:\n"
            "    import pre_import_fix\n"
            "    print('✅ pre_import_fix импортирован успешно')\n"
            "except Exception as e:\n"
            "    print(f'❌ Ошибка при импорте pre_import_fix: {e}')\n\n" + 
            content[import_pos:]
        )
        
        # Записываем новое содержимое
        with open(main_py_path, "w", encoding="utf-8") as file:
            file.write(new_content)
        
        logger.info(f"Файл {main_py_path} успешно пропатчен")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при патчинге файла {main_py_path}: {e}")
        return False

if __name__ == "__main__":
    # Сначала добавляем текущую директорию в sys.path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        logger.info(f"Добавлен {os.getcwd()} в sys.path")
    
    # Запускаем патчинг
    if patch_main_py():
        logger.info("Патчинг main.py выполнен успешно")
        sys.exit(0)
    else:
        logger.error("Ошибка при патчинге main.py")
        sys.exit(1) 