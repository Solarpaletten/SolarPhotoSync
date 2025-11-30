# ☀️ SOLAR PhotoSync v1.1.0 — Deploy Edition

**Production-ready сервис синхронизации медиафайлов из Telegram**

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Что нового в v1.1.0](#что-нового-в-v110)
3. [Архитектура](#архитектура)
4. [Быстрый старт](#быстрый-старт)
5. [Конфигурация](#конфигурация)
6. [API Endpoints](#api-endpoints)
7. [Использование](#использование)
8. [Документация](#документация)
9. [Changelog](#changelog)

---

## 🎯 Обзор

SOLAR PhotoSync — production-ready сервис для автоматической загрузки медиафайлов из Telegram в структурированную файловую систему.

### Workflow

```
📱 Leanid → Telegram → 🤖 Bot → 🌐 Webhook → 💾 /var/www/SolarPhotoSync/
                                    ↓
                           ☀️ "Saved → Category / Date"
```

### Ключевые возможности

- ✅ 24/7 работа через systemd
- ✅ Автоперезапуск при сбоях
- ✅ Классификация по ключевым словам
- ✅ HEIC → JPG конвертация
- ✅ Ротация логов
- ✅ Health/Ping мониторинг
- ✅ Deploy одной командой

---

## 🆕 Что нового в v1.1.0

### 🚀 Production Deploy

- Полная структура `/var/www/SolarPhotoSync/`
- Systemd service с автозапуском
- Nginx reverse proxy конфигурация
- Deploy script `deploy.sh`

### 🔒 Безопасность

- Токен через `secret.env` (не в Git)
- Запуск от `www-data`
- Изоляция через systemd

### 📊 Мониторинг

- `/api/photosync/ping` — alive check
- Улучшенная обработка ошибок webhook
- Логирование невалидных запросов

### 📝 Документация

- `DEPLOY.md` — полное руководство
- `SYSTEMD.md` — управление сервисом
- `WEBHOOK.md` — настройка Telegram

### ⚙️ Конфигурация

- `photosync.production.json` — готовый production конфиг
- Логи: 5MB, 10 backups
- Linux пути по умолчанию

---

## 🏗 Архитектура

### Структура на сервере

```
/var/www/SolarPhotoSync/
├── src/                    # Исходный код
│   ├── bot.py             # Главный модуль
│   ├── webhook_handler.py # Обработчик webhook
│   ├── classifier.py      # Классификатор
│   ├── file_saver.py      # Сохранение файлов
│   ├── heic_converter.py  # Конвертация HEIC
│   └── logger.py          # Логирование
├── config/
│   ├── photosync.config.json  # Конфигурация
│   └── secret.env             # Токен (НЕ в Git!)
├── tools/
│   └── webhook_setup.py   # Утилита webhook
├── service/
│   └── solarphotosync.service # Systemd unit
├── docs/                   # Документация
├── logs/                   # Логи
│   └── photosync.log
├── SOLAR-PhotoSync/       # Медиафайлы
│   └── YYYY-MM-DD/
│       ├── Sprinter/
│       ├── LDZ/
│       ├── Legal/
│       ├── Documents/
│       └── Other/
├── venv/                  # Python virtual environment
└── requirements.txt
```

### Компоненты

| Компонент | Описание |
|-----------|----------|
| **bot.py** | Web-сервер aiohttp, маршруты, uptime |
| **webhook_handler.py** | Приём Telegram updates, скачивание файлов |
| **classifier.py** | Классификация по ключевым словам |
| **file_saver.py** | Сохранение с автосозданием директорий |
| **heic_converter.py** | HEIC → JPG с сохранением EXIF |
| **logger.py** | Ротируемые логи, LAST_SAVED tracking |

---

## 🚀 Быстрый старт

### Автоматическая установка

```bash
sudo ./deploy.sh
```

### Ручная установка

```bash
# 1. Зависимости
sudo apt install python3 python3-venv nginx imagemagick

# 2. Директории
sudo mkdir -p /var/www/SolarPhotoSync
sudo chown www-data:www-data /var/www/SolarPhotoSync

# 3. Virtual environment
cd /var/www/SolarPhotoSync
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 4. Secret token
echo "TELEGRAM_BOT_TOKEN=your_token" > config/secret.env

# 5. Systemd
sudo cp service/solarphotosync.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now solarphotosync

# 6. Webhook
./venv/bin/python tools/webhook_setup.py set \
    --url https://www.swapoil.de/api/photosync/webhook
```

---

## ⚙️ Конфигурация

### config/photosync.production.json

```json
{
  "bot": {
    "token": "",
    "webhook_url": "https://www.swapoil.de/api/photosync/webhook"
  },
  "storage": {
    "root_path": "/var/www/SolarPhotoSync/SOLAR-PhotoSync"
  },
  "logging": {
    "log_path": "/var/www/SolarPhotoSync/logs",
    "max_log_size_mb": 5,
    "backup_count": 10
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8080
  }
}
```

### config/secret.env

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
```

⚠️ **Никогда не коммитьте в Git!**

---

## 🌐 API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/photosync/webhook` | POST | Telegram webhook |
| `/api/photosync/health` | GET | Health check + uptime |
| `/api/photosync/ping` | GET | Alive check |
| `/api/photosync/stats` | GET | Статистика хранилища |

### Health Response

```json
{
  "status": "ok",
  "version": "1.1.0",
  "uptime": "3600s",
  "root_path": "/var/www/SolarPhotoSync/SOLAR-PhotoSync",
  "last_saved": "2025-11-30T15:00:00.000000"
}
```

### Ping Response

```json
{
  "status": "alive",
  "timestamp": "2025-11-30T15:00:00.000000"
}
```

---

## 📱 Использование

### Отправка файлов

1. Найдите бота в Telegram
2. Отправьте фото/видео/документ
3. Получите: `☀️ Saved → Category / 2025-11-30`

### Force Category

```
/sprinter    → Sprinter
/ldz         → LDZ
/legal       → Legal
/documents   → Documents
/other       → Other
```

### Приоритет классификации

1. Команда (`/sprinter`) — **абсолютный приоритет**
2. Ключевые слова в подписи
3. Название чата
4. Имя файла
5. Default: Other

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [DEPLOY.md](docs/DEPLOY.md) | Полное руководство по развёртыванию |
| [SYSTEMD.md](docs/SYSTEMD.md) | Управление systemd сервисом |
| [WEBHOOK.md](docs/WEBHOOK.md) | Настройка Telegram webhook |

---

## 🔄 Git Deploy Workflow

```bash
cd /var/www/SolarPhotoSync
git pull
sudo systemctl restart solarphotosync
sudo systemctl status solarphotosync
```

---

## 🧪 Проверки после деплоя

### 1. Health check

```bash
curl https://www.swapoil.de/api/photosync/health
```

### 2. Ping

```bash
curl https://www.swapoil.de/api/photosync/ping
```

### 3. Systemd статус

```bash
sudo systemctl status solarphotosync
```

### 4. Тест отправки

Отправьте фото боту → проверьте:

```bash
ls -la /var/www/SolarPhotoSync/SOLAR-PhotoSync/$(date +%Y-%m-%d)/
```

### 5. Логи

```bash
tail -f /var/www/SolarPhotoSync/logs/photosync.log
```

---

## 📝 Changelog

### v1.1.0 — Deploy Edition (2025-11-30)

**🚀 Production Ready**
- ✅ Полная структура `/var/www/SolarPhotoSync/`
- ✅ Systemd service с автозапуском
- ✅ Deploy script `deploy.sh`
- ✅ Production config `photosync.production.json`

**🔒 Security**
- ✅ Токен через `secret.env`
- ✅ Запуск от `www-data`
- ✅ `.gitignore` для секретов

**📊 Monitoring**
- ✅ `/api/photosync/ping` endpoint
- ✅ Улучшенная обработка ошибок webhook
- ✅ Логирование невалидных запросов

**📝 Documentation**
- ✅ `DEPLOY.md`
- ✅ `SYSTEMD.md`
- ✅ `WEBHOOK.md`

**⚙️ Configuration**
- ✅ Логи: 5MB max, 10 backups
- ✅ Linux paths по умолчанию
- ✅ python-dotenv для env файлов

---

### v1.0.1 (2025-11-30)
- ☀️ Auto-response: `☀️ Saved → Category / Date`
- 🏥 Health endpoint с uptime
- 📁 Автосоздание root_path
- 🎯 Force category override
- 🔇 Фильтрация empty updates

### v1.0.0 (2025-11-29)
- ✅ Начальный релиз
- ✅ Telegram webhook
- ✅ Автоклассификация
- ✅ HEIC → JPG
- ✅ Логирование

---

## 👥 Команда

- **Dashka** — Senior Architect, координация
- **Claude** — Engineer, разработка
- **Leanid** — Architect Supervisor, приёмка

---

**☀️ SOLAR PhotoSync v1.1.0 Deploy Edition**

*Production-ready. Battle-tested. Solar-powered.*
