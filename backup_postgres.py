#!/usr/bin/env python
"""
Скрипт для создания резервной копии PostgreSQL базы данных бота ОНА
"""

import os
import sys
import time
import logging
import subprocess
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [POSTGRES_BACKUP] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_backup")

def create_postgres_backup():
    """
    Создает резервную копию PostgreSQL базы данных
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем URL базы данных
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("Переменная DATABASE_URL не найдена в .env или переменных окружения")
        return False
    
    logger.info("Подготовка к созданию резервной копии PostgreSQL базы данных...")
    
    try:
        # Парсим DATABASE_URL
        connection_parts = {}
        
        # Извлекаем протокол
        if "://" in database_url:
            protocol, rest = database_url.split("://", 1)
            connection_parts["protocol"] = protocol
        else:
            logger.error("Неверный формат DATABASE_URL: отсутствует протокол")
            return False
        
        # Извлекаем логин, пароль, хост, порт и имя базы данных
        if "@" in rest:
            auth, host_db = rest.split("@", 1)
            if ":" in auth:
                connection_parts["username"], connection_parts["password"] = auth.split(":", 1)
            else:
                connection_parts["username"] = auth
                connection_parts["password"] = ""
            
            if "/" in host_db:
                host_port, connection_parts["dbname"] = host_db.split("/", 1)
                if ":" in host_port:
                    connection_parts["host"], connection_parts["port"] = host_port.split(":", 1)
                else:
                    connection_parts["host"] = host_port
                    connection_parts["port"] = "5432"  # PostgreSQL порт по умолчанию
                
                # Удаляем параметры из строки подключения
                if "?" in connection_parts["dbname"]:
                    connection_parts["dbname"] = connection_parts["dbname"].split("?", 1)[0]
            else:
                logger.error("Неверный формат DATABASE_URL: отсутствует имя базы данных")
                return False
        else:
            logger.error("Неверный формат DATABASE_URL: отсутствует разделитель @")
            return False
        
        # Создаем директорию для резервных копий, если она не существует
        backup_dir = os.path.join(os.getcwd(), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info(f"Создана директория для резервных копий: {backup_dir}")
        
        # Формируем имя файла резервной копии
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"ona_bot_db_backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Проверяем наличие утилиты pg_dump
        try:
            # Проверяем, есть ли pg_dump в системе
            subprocess.run(["pg_dump", "--version"], capture_output=True, check=True)
            logger.info("Утилита pg_dump найдена в системе")
            
            # Настраиваем переменные окружения для pg_dump
            env = os.environ.copy()
            env["PGHOST"] = connection_parts["host"]
            env["PGPORT"] = connection_parts["port"]
            env["PGUSER"] = connection_parts["username"]
            env["PGPASSWORD"] = connection_parts["password"]
            env["PGDATABASE"] = connection_parts["dbname"]
            
            # Создаем резервную копию с помощью pg_dump
            logger.info(f"Запуск pg_dump для создания резервной копии в {backup_path}...")
            result = subprocess.run(
                ["pg_dump", "--format=plain", "--no-owner", "--no-acl"],
                env=env,
                stdout=open(backup_path, "w"),
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Резервная копия успешно создана: {backup_path}")
                
                # Проверяем размер созданного файла
                backup_size = os.path.getsize(backup_path)
                logger.info(f"Размер резервной копии: {backup_size/1024:.2f} KB")
                
                return True
            else:
                logger.error(f"❌ Ошибка при создании резервной копии: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError:
            logger.warning("Утилита pg_dump не найдена в системе, используем альтернативный метод")
            
            # Альтернативный метод создания резервной копии через psycopg2
            try:
                # Подключаемся к базе данных
                conn = psycopg2.connect(database_url)
                conn.autocommit = False
                
                with open(backup_path, 'w') as f:
                    logger.info("Создание SQL дампа таблиц...")
                    
                    # Получаем список таблиц
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                        tables = cursor.fetchall()
                        
                        if not tables:
                            logger.warning("В базе данных нет таблиц для резервного копирования")
                            return False
                        
                        # Записываем заголовок SQL файла
                        f.write("-- ONA Bot PostgreSQL Database Backup\n")
                        f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("-- This file was generated automatically by backup_postgres.py\n\n")
                        
                        # Экспортируем каждую таблицу
                        for table in tables:
                            table_name = table[0]
                            logger.info(f"Экспорт таблицы: {table_name}")
                            
                            # Получаем структуру таблицы
                            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
                            columns = cursor.fetchall()
                            
                            # Записываем команду CREATE TABLE
                            f.write(f"-- Table: {table_name}\n")
                            f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
                            
                            column_defs = []
                            for i, col in enumerate(columns):
                                column_name, data_type = col
                                column_defs.append(f"    {column_name} {data_type}")
                            
                            # Получаем первичный ключ
                            cursor.execute("""
                                SELECT c.column_name
                                FROM information_schema.table_constraints tc
                                JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                                JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                                    AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                                WHERE constraint_type = 'PRIMARY KEY' AND tc.table_name = %s
                            """, (table_name,))
                            pks = cursor.fetchall()
                            if pks:
                                pk_columns = [pk[0] for pk in pks]
                                column_defs.append(f"    PRIMARY KEY ({', '.join(pk_columns)})")
                            
                            f.write(",\n".join(column_defs))
                            f.write("\n);\n\n")
                            
                            # Получаем данные таблицы
                            cursor.execute(f"SELECT * FROM {table_name}")
                            rows = cursor.fetchall()
                            
                            if rows:
                                col_names = [col[0] for col in columns]
                                f.write(f"-- Data for table: {table_name}\n")
                                
                                for row in rows:
                                    values = []
                                    for val in row:
                                        if val is None:
                                            values.append("NULL")
                                        elif isinstance(val, (int, float)):
                                            values.append(str(val))
                                        else:
                                            # Экранируем строки
                                            values.append(f"'{str(val).replace(\"'\", \"''\")}'")
                                    
                                    f.write(f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({', '.join(values)});\n")
                                
                                f.write("\n")
                
                conn.close()
                logger.info(f"✅ Резервная копия успешно создана: {backup_path}")
                
                # Проверяем размер созданного файла
                backup_size = os.path.getsize(backup_path)
                logger.info(f"Размер резервной копии: {backup_size/1024:.2f} KB")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Ошибка при создании резервной копии через psycopg2: {e}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании резервной копии: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск процесса резервного копирования PostgreSQL...")
    success = create_postgres_backup()
    
    if success:
        logger.info("✅ Резервное копирование PostgreSQL успешно завершено")
        sys.exit(0)
    else:
        logger.error("❌ Резервное копирование PostgreSQL завершилось с ошибкой")
        sys.exit(1) 