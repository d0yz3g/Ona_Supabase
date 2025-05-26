# Ona AI Telegram Bot

Telegram бот с использованием aiogram и деплоем на Railway.

## Описание

Бот представляет собой интеллектуального ассистента, который помогает пользователям разобраться в своих эмоциях и предоставляет персонализированные ответы и рекомендации.

## Особенности

- Обработка сообщений пользователя с использованием AI
- Персонализированные ответы
- Режимы работы webhook и long polling
- Поддержка различных команд (/start, /help, /about, /meditate)
- Автоматическое определение и настройка для деплоя на Railway

## Установка и запуск

### Необходимые зависимости

```bash
pip install -r requirements.txt
```

### Настройка переменных окружения

Создайте файл `.env` со следующими переменными:

```
BOT_TOKEN=ваш_токен_бота
ADMIN_CHAT_ID=ваш_chat_id_для_администратора
```

### Режимы работы

Бот поддерживает два режима работы:

1. **Long polling** - для локальной разработки:
   ```bash
   python start_polling.py
   ```

2. **Webhook** - для production-окружения:
   ```bash
   python simple_server.py
   ```

## Деплой на Railway

1. Зарегистрируйтесь на [Railway](https://railway.app/)
2. Создайте новый проект и подключите репозиторий GitHub
3. Добавьте переменные окружения:
   - `BOT_TOKEN` - токен вашего Telegram бота
   - `ADMIN_CHAT_ID` - ID администратора для получения уведомлений
4. Railway автоматически развернет ваше приложение

## Диагностика и устранение проблем

### Проверка статуса бота

Для проверки статуса бота используйте:

```bash
python check_railway_service.py --report
```

### Исправление проблем с webhook

Если webhook настроен неправильно:

```bash
python railway_fix.py --set-webhook
```

Для отключения webhook и перехода в режим long polling:

```bash
python railway_fix.py --disable-webhook
```

### Отправка тестового сообщения

```bash
python railway_fix.py --test-message --chat-id=ваш_chat_id
```

## Структура проекта

- `simple_server.py` - основной сервер для webhook режима
- `start_polling.py` - скрипт для запуска в режиме long polling
- `railway_fix.py` - утилита для исправления проблем с webhook
- `check_railway_service.py` - утилита для диагностики сервиса
- `railway_helper.py` - вспомогательные функции для работы с Railway

## Полезные команды

### Полная диагностика

```bash
python check_railway_service.py --report --output=report.txt
```

### Сброс webhook и очистка очереди обновлений

```bash
python railway_fix.py --disable-webhook --drop-updates
```

### Установка webhook на конкретный URL

```bash
python railway_fix.py --set-webhook --webhook-url="https://ваш-домен/webhook/BOT_TOKEN"
```

## Устранение проблем

При возникновении проблем с деплоем на Railway, обратитесь к документации в файле [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md).

## Рекомендации по дальнейшему развитию

Детальные рекомендации по устранению проблем и улучшению бота доступны в файле [RECOMMENDATIONS.md](RECOMMENDATIONS.md). 