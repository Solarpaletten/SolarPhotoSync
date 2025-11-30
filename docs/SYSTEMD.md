# ☀️ SOLAR PhotoSync — SYSTEMD.md

**Управление сервисом через systemd**

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Unit файл](#unit-файл)
3. [Основные команды](#основные-команды)
4. [Логирование](#логирование)
5. [Автозапуск](#автозапуск)
6. [Мониторинг](#мониторинг)
7. [Troubleshooting](#troubleshooting)

---

## 📖 Обзор

Solar PhotoSync использует **systemd** для:

- Автоматического запуска при старте системы
- Автоматического перезапуска при падении
- Управления логами
- Изоляции процесса

---

## 📄 Unit файл

### Расположение

```
/etc/systemd/system/solarphotosync.service
```

### Содержимое

```ini
[Unit]
Description=Solar PhotoSync Bot - Telegram Media Sync Service
Documentation=https://github.com/solar/photosync
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/var/www/SolarPhotoSync
ExecStart=/var/www/SolarPhotoSync/venv/bin/python -m src.bot --config /var/www/SolarPhotoSync/config/photosync.production.json
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=30

# Environment
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-/var/www/SolarPhotoSync/config/secret.env

# Security
User=www-data
Group=www-data
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=append:/var/www/SolarPhotoSync/logs/service.log
StandardError=append:/var/www/SolarPhotoSync/logs/service-error.log

[Install]
WantedBy=multi-user.target
```

### Установка

```bash
sudo cp service/solarphotosync.service /etc/systemd/system/
sudo systemctl daemon-reload
```

---

## 🎮 Основные команды

### Запуск

```bash
sudo systemctl start solarphotosync
```

### Остановка

```bash
sudo systemctl stop solarphotosync
```

### Перезапуск

```bash
sudo systemctl restart solarphotosync
```

### Мягкая перезагрузка (reload)

```bash
sudo systemctl reload solarphotosync
```

### Статус

```bash
sudo systemctl status solarphotosync
```

Пример вывода:

```
● solarphotosync.service - Solar PhotoSync Bot - Telegram Media Sync Service
     Loaded: loaded (/etc/systemd/system/solarphotosync.service; enabled; vendor preset: enabled)
     Active: active (running) since Sat 2025-11-30 15:00:00 UTC; 2h ago
       Docs: https://github.com/solar/photosync
   Main PID: 12345 (python)
      Tasks: 3 (limit: 4915)
     Memory: 45.2M
        CPU: 1min 23s
     CGroup: /system.slice/solarphotosync.service
             └─12345 /var/www/SolarPhotoSync/venv/bin/python -m src.bot
```

---

## 📝 Логирование

### Логи systemd (journald)

```bash
# Последние 100 записей
sudo journalctl -u solarphotosync -n 100

# В реальном времени
sudo journalctl -u solarphotosync -f

# За последний час
sudo journalctl -u solarphotosync --since "1 hour ago"

# За сегодня
sudo journalctl -u solarphotosync --since today

# Только ошибки
sudo journalctl -u solarphotosync -p err
```

### Логи приложения

```bash
# Основной лог
tail -f /var/www/SolarPhotoSync/logs/photosync.log

# Stdout сервиса
tail -f /var/www/SolarPhotoSync/logs/service.log

# Stderr сервиса
tail -f /var/www/SolarPhotoSync/logs/service-error.log
```

### Очистка логов journald

```bash
# Оставить только за последнюю неделю
sudo journalctl --vacuum-time=7d

# Ограничить размером
sudo journalctl --vacuum-size=100M
```

---

## 🔄 Автозапуск

### Включение

```bash
sudo systemctl enable solarphotosync
```

Вывод:

```
Created symlink /etc/systemd/system/multi-user.target.wants/solarphotosync.service → /etc/systemd/system/solarphotosync.service
```

### Отключение

```bash
sudo systemctl disable solarphotosync
```

### Проверка

```bash
sudo systemctl is-enabled solarphotosync
# Ожидаемый вывод: enabled
```

---

## 📊 Мониторинг

### Проверка работоспособности

```bash
# Статус сервиса
systemctl is-active solarphotosync

# Health endpoint
curl -s http://127.0.0.1:8080/api/photosync/health | python3 -m json.tool

# Ping
curl -s http://127.0.0.1:8080/api/photosync/ping
```

### Скрипт мониторинга

```bash
#!/bin/bash
# monitor.sh

SERVICE="solarphotosync"

if systemctl is-active --quiet $SERVICE; then
    HEALTH=$(curl -s http://127.0.0.1:8080/api/photosync/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ $SERVICE is running"
        echo "$HEALTH" | python3 -m json.tool
    else
        echo "⚠️ $SERVICE is running but health check failed"
    fi
else
    echo "❌ $SERVICE is not running"
    exit 1
fi
```

### Watchdog (опционально)

Добавить в `[Service]`:

```ini
WatchdogSec=30
```

---

## ❗ Troubleshooting

### Сервис не запускается

```bash
# Подробный статус
sudo systemctl status solarphotosync -l

# Журнал с момента последнего запуска
sudo journalctl -u solarphotosync -b

# Проверка синтаксиса unit файла
sudo systemd-analyze verify /etc/systemd/system/solarphotosync.service
```

### Ошибка "Failed to start"

1. Проверьте пути:
```bash
ls -la /var/www/SolarPhotoSync/venv/bin/python
ls -la /var/www/SolarPhotoSync/src/bot.py
```

2. Проверьте права:
```bash
ls -la /var/www/SolarPhotoSync/
```

3. Тестовый запуск:
```bash
cd /var/www/SolarPhotoSync
sudo -u www-data ./venv/bin/python -m src.bot
```

### Сервис падает и перезапускается

```bash
# Смотрим логи до падения
sudo journalctl -u solarphotosync --since "10 minutes ago"

# Проверяем память
free -h

# Проверяем диск
df -h
```

### После изменения unit файла

```bash
# Обязательно перезагрузить daemon
sudo systemctl daemon-reload

# Затем перезапустить сервис
sudo systemctl restart solarphotosync
```

---

## 🔒 Безопасность

### Текущие настройки

| Опция | Значение | Описание |
|-------|----------|----------|
| `User` | www-data | Запуск от непривилегированного пользователя |
| `Group` | www-data | Группа пользователя |
| `NoNewPrivileges` | true | Запрет повышения привилегий |
| `PrivateTmp` | true | Изолированная /tmp |

### Дополнительная защита (опционально)

```ini
# Добавить в [Service]
ProtectSystem=full
ProtectHome=true
ReadOnlyDirectories=/
ReadWriteDirectories=/var/www/SolarPhotoSync
```

---

## 📎 Полезные команды

```bash
# Список всех сервисов
systemctl list-units --type=service

# Зависимости сервиса
systemctl list-dependencies solarphotosync

# Время загрузки
systemd-analyze blame | grep solarphotosync

# Перезагрузить конфигурацию без перезапуска
systemctl reload-or-restart solarphotosync
```

---

**☀️ SOLAR PhotoSync v1.1.0 Deploy Edition**
