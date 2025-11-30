# ☀️ SOLAR PhotoSync — WEBHOOK.md

**Настройка и управление Telegram Webhook**

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Требования](#требования)
3. [Настройка Webhook](#настройка-webhook)
4. [Проверка статуса](#проверка-статуса)
5. [Утилита webhook_setup.py](#утилита-webhook_setuppy)
6. [Формат данных](#формат-данных)
7. [Безопасность](#безопасность)
8. [Troubleshooting](#troubleshooting)

---

## 📖 Обзор

Solar PhotoSync использует **Telegram Webhook** для получения сообщений в реальном времени.

### Как это работает:

```
📱 Пользователь → Telegram → Webhook URL → Solar Server → Сохранение файла
```

### Преимущества Webhook vs Polling:

| Webhook | Polling |
|---------|---------|
| Мгновенная доставка | Задержка до 1 сек |
| Меньше нагрузка | Постоянные запросы |
| Требует HTTPS | Работает везде |
| Нужен публичный IP | Работает за NAT |

---

## 🔧 Требования

### Обязательные

- ✅ HTTPS URL (Telegram требует SSL)
- ✅ Публичный IP или домен
- ✅ Валидный SSL сертификат
- ✅ Открытый порт (443, 80, 88, или 8443)

### Поддерживаемые порты Telegram

- 443 (стандартный HTTPS)
- 80 (HTTP с редиректом на HTTPS)
- 88
- 8443

---

## ⚙️ Настройка Webhook

### Способ 1: Через утилиту (рекомендуется)

```bash
cd /var/www/SolarPhotoSync
./venv/bin/python tools/webhook_setup.py set \
    --url https://www.swapoil.de/api/photosync/webhook
```

### Способ 2: Через curl

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
    -H "Content-Type: application/json" \
    -d '{
        "url": "https://www.swapoil.de/api/photosync/webhook",
        "allowed_updates": ["message"],
        "drop_pending_updates": true
    }'
```

### Способ 3: В браузере

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://www.swapoil.de/api/photosync/webhook
```

---

## 🔍 Проверка статуса

### Через утилиту

```bash
./venv/bin/python tools/webhook_setup.py info
```

### Через curl

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo" | python3 -m json.tool
```

### Ожидаемый ответ

```json
{
    "ok": true,
    "result": {
        "url": "https://www.swapoil.de/api/photosync/webhook",
        "has_custom_certificate": false,
        "pending_update_count": 0,
        "max_connections": 40,
        "allowed_updates": ["message"]
    }
}
```

### Значения полей

| Поле | Описание |
|------|----------|
| `url` | Текущий webhook URL |
| `pending_update_count` | Необработанные сообщения |
| `last_error_date` | Время последней ошибки |
| `last_error_message` | Текст последней ошибки |

---

## 🛠 Утилита webhook_setup.py

### Расположение

```
/var/www/SolarPhotoSync/tools/webhook_setup.py
```

### Команды

#### Тест подключения

```bash
./venv/bin/python tools/webhook_setup.py test
```

Вывод:

```
✅ Bot connected successfully!
   Name: Solar PhotoSync
   Username: @solar_photosync_bot
   Bot ID: 123456789
```

#### Установка webhook

```bash
./venv/bin/python tools/webhook_setup.py set \
    --url https://www.swapoil.de/api/photosync/webhook
```

#### Получение информации

```bash
./venv/bin/python tools/webhook_setup.py info
```

#### Удаление webhook

```bash
./venv/bin/python tools/webhook_setup.py delete
```

### Параметры

| Параметр | Описание |
|----------|----------|
| `--token, -t` | Bot token (или из конфига) |
| `--url, -u` | Webhook URL |
| `--secret, -s` | Secret token для верификации |
| `--config, -c` | Путь к конфигу |

---

## 📦 Формат данных

### Входящий webhook (от Telegram)

```json
{
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {
            "id": 12345,
            "first_name": "Leanid",
            "username": "leanid"
        },
        "chat": {
            "id": 12345,
            "type": "private"
        },
        "date": 1701234567,
        "photo": [
            {
                "file_id": "AgACAgIAAxk...",
                "file_unique_id": "AQADAgAT...",
                "file_size": 1234,
                "width": 90,
                "height": 90
            }
        ],
        "caption": "/sprinter Фото машины"
    }
}
```

### Ответ сервера

```json
{
    "success": true,
    "message": "Saved to Sprinter",
    "file_path": "/var/www/SolarPhotoSync/SOLAR-PhotoSync/2025-11-30/Sprinter/20251130_150000_photo.jpg"
}
```

---

## 🔒 Безопасность

### Secret Token (рекомендуется)

Добавляет заголовок `X-Telegram-Bot-Api-Secret-Token` для верификации.

#### Настройка

1. Добавить в `config/photosync.production.json`:

```json
{
    "bot": {
        "webhook_secret": "your-secret-token-here"
    }
}
```

2. Установить webhook с секретом:

```bash
./venv/bin/python tools/webhook_setup.py set \
    --url https://www.swapoil.de/api/photosync/webhook \
    --secret your-secret-token-here
```

### IP Whitelist (Nginx)

```nginx
location /api/photosync/webhook {
    # Telegram IP ranges
    allow 149.154.160.0/20;
    allow 91.108.4.0/22;
    deny all;
    
    proxy_pass http://127.0.0.1:8080;
}
```

### Rate Limiting (Nginx)

```nginx
limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/s;

location /api/photosync/webhook {
    limit_req zone=webhook burst=20 nodelay;
    proxy_pass http://127.0.0.1:8080;
}
```

---

## ❗ Troubleshooting

### Webhook не устанавливается

**Ошибка:** `wrong response from the webhook`

**Решения:**

1. Проверить SSL сертификат:
```bash
curl -v https://www.swapoil.de/api/photosync/health
```

2. Проверить что endpoint отвечает:
```bash
curl -X POST https://www.swapoil.de/api/photosync/webhook \
    -H "Content-Type: application/json" \
    -d '{}'
```

### pending_update_count растёт

Сервер не обрабатывает сообщения.

```bash
# Проверить сервис
sudo systemctl status solarphotosync

# Проверить логи
tail -f /var/www/SolarPhotoSync/logs/photosync.log
```

### last_error_message

**"Connection timed out"**

- Сервер недоступен
- Firewall блокирует

**"Wrong response from the webhook: 502"**

- Nginx не может подключиться к бэкенду
- Сервис не запущен

**"SSL certificate problem"**

- Невалидный SSL сертификат
- Самоподписанный сертификат

### Сброс webhook

При проблемах можно сбросить и установить заново:

```bash
# Удалить
./venv/bin/python tools/webhook_setup.py delete

# Подождать 5 секунд
sleep 5

# Установить заново
./venv/bin/python tools/webhook_setup.py set \
    --url https://www.swapoil.de/api/photosync/webhook
```

### Тестовый webhook запрос

```bash
curl -X POST http://127.0.0.1:8080/api/photosync/webhook \
    -H "Content-Type: application/json" \
    -d '{
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": 123, "type": "private"},
            "date": 1701234567,
            "text": "test"
        }
    }'
```

---

## 📊 Мониторинг

### Проверка доступности

```bash
# Health
curl https://www.swapoil.de/api/photosync/health

# Ping
curl https://www.swapoil.de/api/photosync/ping

# Webhook info
./venv/bin/python tools/webhook_setup.py info
```

### Алерты

Скрипт для мониторинга:

```bash
#!/bin/bash
# check_webhook.sh

INFO=$(curl -s "https://api.telegram.org/bot$TOKEN/getWebhookInfo")
PENDING=$(echo $INFO | python3 -c "import sys,json; print(json.load(sys.stdin)['result'].get('pending_update_count', 0))")

if [ "$PENDING" -gt 100 ]; then
    echo "⚠️ Warning: $PENDING pending updates!"
    # Отправить алерт
fi
```

---

## 📎 Полезные ссылки

- [Telegram Bot API - setWebhook](https://core.telegram.org/bots/api#setwebhook)
- [Telegram Bot API - getWebhookInfo](https://core.telegram.org/bots/api#getwebhookinfo)
- [Telegram Webhook Guide](https://core.telegram.org/bots/webhooks)

---

**☀️ SOLAR PhotoSync v1.1.0 Deploy Edition**
