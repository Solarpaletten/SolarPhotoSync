# ☀️ SOLAR PhotoSync — DEPLOY.md

**Руководство по развёртыванию на production-сервере**

---

## 📋 Содержание

1. [Требования](#требования)
2. [Подготовка сервера](#подготовка-сервера)
3. [Установка](#установка)
4. [Конфигурация](#конфигурация)
5. [Запуск сервиса](#запуск-сервиса)
6. [Настройка Nginx](#настройка-nginx)
7. [Проверка работы](#проверка-работы)
8. [Обновление](#обновление)
9. [Откат](#откат)

---

## 🔧 Требования

### Сервер

- Ubuntu 20.04+ / Debian 11+
- Python 3.9+
- Nginx (для reverse proxy)
- SSL сертификат (Let's Encrypt)
- 512 MB RAM минимум
- 10 GB диска

### Сеть

- Публичный IP или домен
- Открытые порты: 80, 443
- HTTPS обязателен для Telegram Webhook

---

## 🖥 Подготовка сервера

### 1. Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка зависимостей

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    git \
    imagemagick \
    libheif-examples
```

### 3. Создание структуры директорий

```bash
sudo mkdir -p /var/www/SolarPhotoSync
sudo mkdir -p /var/www/SolarPhotoSync/logs
sudo mkdir -p /var/www/SolarPhotoSync/config
sudo mkdir -p /var/www/SolarPhotoSync/SOLAR-PhotoSync

# Права
sudo chown -R www-data:www-data /var/www/SolarPhotoSync
sudo chmod -R 755 /var/www/SolarPhotoSync
```

---

## 📦 Установка

### 1. Клонирование репозитория

```bash
cd /var/www/SolarPhotoSync
sudo -u www-data git clone https://github.com/YOUR_REPO/SOLAR-PhotoSync.git .
```

Или копирование файлов:

```bash
sudo cp -r /path/to/SOLAR-PhotoSync/* /var/www/SolarPhotoSync/
sudo chown -R www-data:www-data /var/www/SolarPhotoSync
```

### 2. Создание виртуального окружения

```bash
cd /var/www/SolarPhotoSync
sudo -u www-data python3 -m venv venv
sudo -u www-data ./venv/bin/pip install --upgrade pip
sudo -u www-data ./venv/bin/pip install -r requirements.txt
```

### 3. Проверка установки

```bash
./venv/bin/python -c "import aiohttp; print('OK')"
```

---

## ⚙️ Конфигурация

### 1. Копирование production конфига

```bash
sudo cp config/photosync.production.json config/photosync.config.json
```

### 2. Создание secret.env (ВАЖНО!)

```bash
sudo nano /var/www/SolarPhotoSync/config/secret.env
```

Содержимое:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**⚠️ Никогда не коммитьте этот файл в Git!**

Права:

```bash
sudo chmod 600 /var/www/SolarPhotoSync/config/secret.env
sudo chown www-data:www-data /var/www/SolarPhotoSync/config/secret.env
```

### 3. Проверка конфигурации

```bash
cat config/photosync.config.json | python3 -m json.tool
```

---

## 🚀 Запуск сервиса

### 1. Установка systemd unit

```bash
sudo cp service/solarphotosync.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. Включение автозапуска

```bash
sudo systemctl enable solarphotosync
```

### 3. Запуск

```bash
sudo systemctl start solarphotosync
```

### 4. Проверка статуса

```bash
sudo systemctl status solarphotosync
```

Ожидаемый вывод:

```
● solarphotosync.service - Solar PhotoSync Bot
     Loaded: loaded (/etc/systemd/system/solarphotosync.service; enabled)
     Active: active (running) since ...
```

### 5. Просмотр логов

```bash
# Логи systemd
sudo journalctl -u solarphotosync -f

# Логи приложения
tail -f /var/www/SolarPhotoSync/logs/photosync.log
```

---

## 🌐 Настройка Nginx

### 1. Создание конфига

```bash
sudo nano /etc/nginx/sites-available/solarphotosync
```

Содержимое:

```nginx
server {
    listen 80;
    server_name www.swapoil.de;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.swapoil.de;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/www.swapoil.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.swapoil.de/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # PhotoSync API
    location /api/photosync/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout for large files
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Увеличиваем лимит для больших файлов
        client_max_body_size 100M;
    }
}
```

### 2. Активация конфига

```bash
sudo ln -s /etc/nginx/sites-available/solarphotosync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## ✅ Проверка работы

### 1. Health check

```bash
curl https://www.swapoil.de/api/photosync/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "version": "1.1.0",
  "uptime": "123s",
  "root_path": "/var/www/SolarPhotoSync/SOLAR-PhotoSync",
  "last_saved": null
}
```

### 2. Ping

```bash
curl https://www.swapoil.de/api/photosync/ping
```

Ожидаемый ответ:

```json
{
  "status": "alive",
  "timestamp": "2025-11-30T15:00:00.000000"
}
```

### 3. Настройка Webhook

```bash
cd /var/www/SolarPhotoSync
./venv/bin/python tools/webhook_setup.py set \
    --url https://www.swapoil.de/api/photosync/webhook
```

### 4. Тест отправки

1. Откройте бота в Telegram
2. Отправьте фото
3. Должен прийти ответ: `☀️ Saved → Other / 2025-11-30`
4. Проверьте файл:

```bash
ls -la /var/www/SolarPhotoSync/SOLAR-PhotoSync/$(date +%Y-%m-%d)/Other/
```

---

## 🔄 Обновление

### Стандартное обновление

```bash
cd /var/www/SolarPhotoSync
sudo -u www-data git pull
sudo -u www-data ./venv/bin/pip install -r requirements.txt
sudo systemctl restart solarphotosync
sudo systemctl status solarphotosync
```

### Скрипт обновления

```bash
#!/bin/bash
# deploy-update.sh

set -e

cd /var/www/SolarPhotoSync

echo "☀️ Pulling latest changes..."
sudo -u www-data git pull

echo "📦 Updating dependencies..."
sudo -u www-data ./venv/bin/pip install -r requirements.txt

echo "🔄 Restarting service..."
sudo systemctl restart solarphotosync

echo "✅ Checking status..."
sleep 2
sudo systemctl status solarphotosync --no-pager

echo ""
echo "☀️ Update complete!"
```

---

## ⏪ Откат

### При проблемах после обновления

```bash
cd /var/www/SolarPhotoSync

# Смотрим историю
git log --oneline -5

# Откатываемся на предыдущий коммит
sudo -u www-data git checkout HEAD~1

# Перезапуск
sudo systemctl restart solarphotosync
```

---

## 📊 Мониторинг

### Проверка логов

```bash
# Последние 100 строк
tail -100 /var/www/SolarPhotoSync/logs/photosync.log

# В реальном времени
tail -f /var/www/SolarPhotoSync/logs/photosync.log

# Ошибки
grep -i error /var/www/SolarPhotoSync/logs/photosync.log
```

### Проверка диска

```bash
du -sh /var/www/SolarPhotoSync/SOLAR-PhotoSync/
df -h /var/www/
```

---

## 🆘 Troubleshooting

### Сервис не запускается

```bash
sudo journalctl -u solarphotosync -n 50 --no-pager
```

### Webhook не работает

```bash
./venv/bin/python tools/webhook_setup.py info
```

### 502 Bad Gateway

```bash
# Проверить что сервис запущен
sudo systemctl status solarphotosync

# Проверить порт
curl http://127.0.0.1:8080/api/photosync/ping
```

---

**☀️ SOLAR PhotoSync v1.1.0 Deploy Edition**
