# Настройка постоянного хранилища для SQLite на Railway

При развертывании бота на Railway важно обеспечить сохранность базы данных между деплоями и перезапусками.

## Проблема

Railway по умолчанию использует эфемерную файловую систему. Это означает, что при каждом новом деплое все файлы, которые не являются частью репозитория, удаляются. Ваша база данных SQLite в файле `data/database.db` может быть потеряна при новом деплое.

## Решение: PostgreSQL вместо SQLite

Для продакшн-окружения на Railway рекомендуется использовать PostgreSQL вместо SQLite. Railway предоставляет постоянное хранилище для PostgreSQL.

### Шаги для настройки PostgreSQL на Railway:

1. В интерфейсе Railway нажмите "New" и выберите "Database" → "PostgreSQL".
2. После создания базы данных, перейдите в раздел "Variables" вашего проекта с ботом.
3. Добавьте переменную окружения `DATABASE_URL` с URL-адресом вашей PostgreSQL базы данных.

## Решение для SQLite (если необходимо сохранить)

Если вы все же хотите использовать SQLite на Railway, можно настроить постоянное хранилище:

### 1. Модифицируйте модуль базы данных для поддержки различных окружений

Отредактируйте файл `db.py`, чтобы он проверял наличие переменной окружения `DATABASE_URL`:

```python
# В начале файла db.py
import os

# Определяем путь к базе данных в зависимости от окружения
if os.getenv("DATABASE_URL"):
    # Мы на Railway или другом хостинге с PostgreSQL
    DB_PATH = os.getenv("DATABASE_URL")
    USE_POSTGRES = True
else:
    # Локальная разработка с SQLite
    DB_DIR = os.path.join(os.getcwd(), "data")
    DB_PATH = os.path.join(DB_DIR, "database.db")
    os.makedirs(DB_DIR, exist_ok=True)
    USE_POSTGRES = False
```

### 2. Сохраняйте базу данных в репозитории

Важно, чтобы файл `data/database.db` сохранялся в вашем репозитории. Убедитесь, что вы исключили его из `.gitignore`:

```
# В файле .gitignore
# База данных
*.db
*.sqlite
*.sqlite3
# Исключение для основной базы данных
!data/database.db
```

### 3. Настройте бэкапы базы данных

Для дополнительной безопасности рекомендуется настроить регулярные бэкапы базы данных:

```python
# Функция для создания бэкапа базы данных
async def backup_database():
    if not USE_POSTGRES:
        import shutil
        from datetime import datetime
        
        # Создаем бэкап базы данных с текущей датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.getcwd(), "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, f"database_{timestamp}.db")
        
        try:
            shutil.copy2(DB_PATH, backup_path)
            logger.info(f"Создан бэкап базы данных: {backup_path}")
            
            # Очищаем старые бэкапы (оставляем только 5 последних)
            backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
            if len(backup_files) > 5:
                for old_backup in backup_files[:-5]:
                    os.remove(old_backup)
                    logger.info(f"Удален старый бэкап: {old_backup}")
        except Exception as e:
            logger.error(f"Ошибка при создании бэкапа базы данных: {e}")
```

## Рекомендации для Railway

1. **Используйте переменные окружения** для конфигурации базы данных.
2. **Настройте автоматические бэкапы** на регулярной основе.
3. **Рассмотрите возможность использования PostgreSQL** для продакшн-окружения.
4. **Настройте pre-commit хук** для автоматического коммита базы данных перед деплоем:

```bash
#!/bin/bash
# Этот скрипт должен быть сохранен как .git/hooks/pre-commit и иметь разрешение на выполнение (chmod +x)

# Добавляем базу данных в коммит, если она изменилась
git add data/database.db
```

## Заключение

При использовании SQLite в продакшн-окружении всегда существует риск потери данных. Для критически важных приложений рекомендуется использовать полноценную СУБД, такую как PostgreSQL или MySQL. Railway предоставляет удобные инструменты для интеграции с этими базами данных. 