# Настройка подключения к Supabase в Railway

## Причины проблемы подключения к Supabase

Проблема с сообщением `Не удалось импортировать модуль Supabase: No module named 'supabase'` может возникать по следующим причинам:

1. Пакет `supabase-py` не был корректно установлен при деплое в Railway
2. Неправильные переменные окружения в Railway
3. Некорректная версия пакета `supabase-py`

## Исправление проблемы

### 1. Проверка и обновление файла requirements.txt

Убедитесь, что в файле `requirements.txt` есть следующие зависимости:

```
supabase-py==2.3.1
python-dotenv==1.0.0
```

### 2. Настройка переменных окружения в Railway

1. Откройте свой проект в Railway Dashboard
2. Перейдите в раздел "Variables"
3. Добавьте следующие переменные окружения:
   - `SUPABASE_URL` - URL вашего проекта Supabase (например, `https://xyzproject.supabase.co`)
   - `SUPABASE_KEY` - API ключ сервера Supabase (не публичный ключ!)

### 3. Ручная установка пакета в Railway

Если проблема сохраняется, можно добавить команду установки пакета в Railway:

1. Перейдите в настройки проекта в Railway
2. В разделе "Settings" найдите "Start Command"
3. Измените команду на:
   ```
   pip install supabase-py && python main.py
   ```

### 4. Проверка подключения к Supabase

Вы можете проверить подключение, запустив скрипт:

```bash
python test_supabase.py
```

Этот скрипт проверит:
- Наличие переменных окружения
- Корректность установки модуля supabase
- Работоспособность подключения к Supabase

## Дополнительные рекомендации

1. **Создание таблиц в Supabase**:
   - Откройте панель управления Supabase
   - Перейдите в раздел "Table Editor"
   - Создайте таблицу `user_profiles` со следующими полями:
     - `id` (text, primary key)
     - `profile_data` (jsonb)
     - `created_at` (timestamptz, default: now())

2. **Политики доступа в Supabase**:
   - Настройте RLS (Row Level Security) для таблицы `user_profiles`, чтобы обеспечить безопасность данных
   - Примеры политик:
     ```sql
     -- Политика чтения: Пользователи могут читать только свои данные
     CREATE POLICY "Users can read their own data" ON public.user_profiles
     FOR SELECT USING (auth.uid()::text = id);
     
     -- Политика записи: Пользователи могут изменять только свои данные
     CREATE POLICY "Users can update their own data" ON public.user_profiles
     FOR UPDATE USING (auth.uid()::text = id);
     ```

3. **Функция для тестирования**:
   - Создайте в Supabase SQL Editor следующую функцию для тестирования:
   ```sql
   CREATE OR REPLACE FUNCTION get_postgres_version()
   RETURNS TEXT AS $$
   BEGIN
     RETURN current_setting('server_version');
   END;
   $$ LANGUAGE plpgsql;
   ```

4. **Отладка в Railway**:
   - Включите логи в Railway для отслеживания возможных проблем с подключением
   - При необходимости добавьте дополнительное логирование в код 