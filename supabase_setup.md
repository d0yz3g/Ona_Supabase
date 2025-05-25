# Настройка Supabase для проекта ONA

В этой инструкции описано, как настроить Supabase для проекта ONA, включая создание таблиц, настройку безопасности и подключение к проекту.

## 1. Создание проекта в Supabase

1. Зарегистрируйтесь или войдите на [Supabase](https://supabase.com/).
2. Нажмите кнопку "New Project".
3. Заполните данные проекта:
   - Название проекта (например, "ona-bot")
   - База данных: выберите пароль для базы данных
   - Регион: выберите ближайший к вам регион
   - Ценовой план: Free tier для начала
4. Нажмите "Create new project" и дождитесь создания проекта (обычно занимает несколько минут).

## 2. Получение API ключей

После создания проекта вы увидите панель управления проектом. Здесь нужно получить два ключа:

1. URL проекта (Project URL)
2. Анонимный ключ API (anon/public key)

Эти ключи находятся в разделе "Project Settings" > "API" в боковой панели. Скопируйте их и добавьте в файл `.env`:

```
SUPABASE_URL=ваш_url_проекта
SUPABASE_KEY=ваш_анонимный_ключ
```

## 3. Создание таблиц в базе данных

Перейдите в раздел "Table Editor" и создайте следующие таблицы:

### 3.1. Таблица users

```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Индекс для быстрого поиска по telegram_id
CREATE INDEX idx_users_telegram_id ON public.users(telegram_id);

-- Триггер обновления updated_at при изменении записи
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW
EXECUTE FUNCTION public.moddatetime (updated_at);
```

### 3.2. Таблица profiles

```sql
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    profile_text TEXT,
    details_text TEXT,
    answers JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Индекс для быстрого поиска по telegram_id
CREATE INDEX idx_profiles_telegram_id ON public.profiles(telegram_id);

-- Индекс для быстрого поиска по user_id
CREATE INDEX idx_profiles_user_id ON public.profiles(user_id);

-- Триггер обновления updated_at при изменении записи
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.moddatetime (updated_at);
```

### 3.3. Таблица reminders

```sql
CREATE TABLE public.reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    time TEXT,
    days JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Индекс для быстрого поиска по telegram_id
CREATE INDEX idx_reminders_telegram_id ON public.reminders(telegram_id);

-- Индекс для быстрого поиска по user_id
CREATE INDEX idx_reminders_user_id ON public.reminders(user_id);

-- Индекс для быстрого поиска активных напоминаний
CREATE INDEX idx_reminders_active ON public.reminders(active) WHERE active = TRUE;

-- Триггер обновления updated_at при изменении записи
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON public.reminders
FOR EACH ROW
EXECUTE FUNCTION public.moddatetime (updated_at);
```

### 3.4. Таблица answers

```sql
CREATE TABLE public.answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    question_id TEXT NOT NULL,
    answer_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Индекс для быстрого поиска по telegram_id
CREATE INDEX idx_answers_telegram_id ON public.answers(telegram_id);

-- Индекс для быстрого поиска по user_id
CREATE INDEX idx_answers_user_id ON public.answers(user_id);

-- Индекс для быстрого поиска по question_id
CREATE INDEX idx_answers_question_id ON public.answers(question_id);

-- Триггер обновления updated_at при изменении записи
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON public.answers
FOR EACH ROW
EXECUTE FUNCTION public.moddatetime (updated_at);
```

## 4. Настройка безопасности (Row Level Security)

Для каждой таблицы настройте RLS (Row Level Security), чтобы обеспечить безопасность данных:

### 4.1. Включение RLS для всех таблиц

Выполните следующие SQL-запросы для включения RLS на всех таблицах:

```sql
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.answers ENABLE ROW LEVEL SECURITY;
```

### 4.2. Создание политик безопасности

Для таблицы users:

```sql
CREATE POLICY "Полный доступ для авторизованных пользователей" ON public.users
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
```

Для таблицы profiles:

```sql
CREATE POLICY "Полный доступ для авторизованных пользователей" ON public.profiles
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
```

Для таблицы reminders:

```sql
CREATE POLICY "Полный доступ для авторизованных пользователей" ON public.reminders
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
```

Для таблицы answers:

```sql
CREATE POLICY "Полный доступ для авторизованных пользователей" ON public.answers
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
```

## 5. Настройка функции moddatetime (если она не создана автоматически)

Если функция moddatetime не существует, создайте её с помощью следующего SQL:

```sql
CREATE EXTENSION IF NOT EXISTS moddatetime;
```

## 6. Установка необходимых зависимостей в проекте

Убедитесь, что в вашем проекте установлены необходимые пакеты:

```bash
pip install supabase-py
```

## 7. Миграция существующих данных (опционально)

Если у вас уже есть данные в SQLite, вы можете мигрировать их в Supabase с помощью скрипта `migrate_to_supabase.py`:

1. Убедитесь, что файл базы данных SQLite указан в переменной окружения `SQLITE_DB_PATH` в файле `.env` или используется путь по умолчанию (`ona.db`).
2. Запустите скрипт миграции:

```bash
python migrate_to_supabase.py
```

## 8. Проверка подключения

Для проверки правильности подключения к Supabase запустите следующий тестовый скрипт:

```python
import asyncio
from supabase_db import db

async def test_connection():
    if db.is_connected:
        print("Подключение к Supabase успешно установлено!")
    else:
        print("Ошибка подключения к Supabase. Проверьте переменные окружения.")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

## 9. Настройка real-time уведомлений (опционально)

Для использования real-time функций Supabase (например, для мгновенных уведомлений):

1. Перейдите в "Database" > "Replication".
2. Включите "Realtime" для таблиц, которые требуют real-time функциональности.

## 10. Мониторинг и отладка

Supabase предоставляет инструменты для мониторинга использования вашей базы данных:

1. SQL Editor: для выполнения произвольных SQL-запросов
2. Logs: для просмотра логов запросов и ошибок
3. Usage: для мониторинга использования ресурсов

## Дополнительные ресурсы

- [Документация Supabase](https://supabase.com/docs)
- [Python SDK для Supabase](https://supabase.com/docs/reference/python/introduction)
- [Примеры использования Supabase с Python](https://supabase.com/docs/reference/python/select) 