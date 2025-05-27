# Устранение проблем с Webhook на Railway

## Проблема: Бот не отвечает на сообщения

Если ваш Telegram бот развернут на Railway и не отвечает на сообщения, проблема может быть связана с неправильной настройкой webhook. В этом документе собраны рекомендации по диагностике и устранению типичных проблем.

## Диагностика

### 1. Проверка статуса webhook

Для начала необходимо проверить текущий статус webhook:

```bash
python check_railway_status.py --token YOUR_BOT_TOKEN --report
```

Этот скрипт выполнит следующие проверки:
- Доступность бота через Telegram API
- Настройки webhook в Telegram
- Доступность приложения на Railway
- Корректность обработки webhook-запросов

### 2. Просмотр логов Railway

Логи приложения на Railway могут содержать важную информацию о причинах проблем:

1. Перейдите в [Dashboard Railway](https://railway.app/dashboard)
2. Выберите ваш проект
3. Перейдите во вкладку "Deployments"
4. Нажмите на последний деплой для просмотра логов

Обратите внимание на сообщения об ошибках, особенно связанные с webhook, HTTP 404 или другими ошибками сервера.

## Распространенные проблемы и их решения

### Проблема 1: Неправильная команда запуска

**Симптомы**: Ошибка 404 при обращении к webhook URL или сообщение "Application not found"

**Решение**:
1. Убедитесь, что в файле `railway.json` указана правильная команда запуска:
   ```json
   {
     "deploy": {
       "startCommand": "python webhook_server.py"
     }
   }
   ```

2. Перезапустите деплой на Railway.

### Проблема 2: Webhook URL не соответствует ожидаемому формату

**Симптомы**: Бот не отвечает, но ошибок в логах нет

**Решение**:
1. Проверьте URL webhook в настройках бота:
   ```bash
   python -c "import requests; r = requests.get('https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo'); print(r.json())"
   ```

2. Убедитесь, что URL соответствует формату:
   ```
   https://<your-railway-app>.up.railway.app/webhook/<YOUR_BOT_TOKEN>
   ```

3. Если URL неверный, установите правильный:
   ```bash
   python fix_railway_webhook.py
   ```

### Проблема 3: Проблемы с переменными окружения

**Симптомы**: Бот запускается, но не обрабатывает сообщения или возникают ошибки аутентификации

**Решение**:
1. Проверьте переменные окружения в Railway Dashboard
2. Убедитесь, что установлены следующие переменные:
   - `BOT_TOKEN` - токен вашего Telegram бота
   - `WEBHOOK_MODE` - установлено в `true`
   - `WEBHOOK_URL` - полный URL webhook (опционально, может быть сформирован автоматически)

### Проблема 4: Ошибка в коде обработчика webhook

**Симптомы**: Ошибки в логах Railway при получении запросов

**Решение**:
1. Проверьте код обработчика webhook в файле `webhook_server.py`
2. Убедитесь, что путь для webhook соответствует формату `/webhook/<BOT_TOKEN>`
3. Проверьте логи на наличие ошибок Python и исправьте их

## Перенастройка webhook

Если вы не можете определить точную причину проблемы, попробуйте полностью перенастроить webhook:

```bash
python fix_railway_webhook.py
```

Этот скрипт выполнит следующие действия:
1. Удалит текущий webhook
2. Проверит доступность приложения на Railway
3. Установит новый webhook с правильными параметрами
4. Проверит работоспособность webhook

## Переход в режим long polling

Если проблемы с webhook не удается решить, вы можете временно перейти в режим long polling:

```bash
python -c "import requests; requests.get('https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook')"
```

Затем измените `railway.json` для использования long polling:

```json
{
  "deploy": {
    "startCommand": "python start_polling.py"
  }
}
```

## Полезные команды

### Проверка информации о боте

```bash
python -c "import requests; r = requests.get('https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe'); print(r.json())"
```

### Проверка настроек webhook

```bash
python -c "import requests; r = requests.get('https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo'); print(r.json())"
```

### Удаление webhook

```bash
python -c "import requests; r = requests.get('https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook'); print(r.json())"
```

### Установка webhook

```bash
python -c "import requests; r = requests.post('https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook', json={'url': 'https://<your-railway-app>.up.railway.app/webhook/<YOUR_BOT_TOKEN>'}); print(r.json())"
```

## Заключение

Большинство проблем с webhook связаны с неправильной конфигурацией URL или ошибками в коде обработчика. Внимательно проверьте логи и настройки, и используйте приведенные выше инструменты для диагностики и исправления проблем.

Если у вас остаются нерешенные проблемы, обратитесь к [официальной документации Telegram Bot API](https://core.telegram.org/bots/api#setwebhook) и [документации Railway](https://docs.railway.app/). 