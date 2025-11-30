# 🍎 Инструкция для Leanid: Запуск на Mac Mini

## Быстрый старт (5 минут)

### Шаг 1: Скопировать проект

```bash
# Скопируй папку SOLAR-PhotoSync на Mac Mini
# Например в ~/Projects/
cd ~/Projects/SOLAR-PhotoSync
```

### Шаг 2: Настроить токен бота

Открой файл `config/photosync.config.json` и вставь токен:

```json
{
  "bot": {
    "token": "ВСТАВЬ_СЮДА_ТОКЕН_ОТ_BOTFATHER"
  }
}
```

### Шаг 3: Запустить

```bash
chmod +x start.sh
./start.sh
```

Готово! ✅

---

## Детальная инструкция

### 1. Создание Telegram бота

1. Открой Telegram → найди `@BotFather`
2. Напиши `/newbot`
3. Имя: `Solar PhotoSync`
4. Username: `solar_photosync_leanid_bot` (любой уникальный)
5. Скопируй токен (выглядит как: `123456789:ABCdef...`)

### 2. Настройка webhook (для доступа извне)

**Вариант A: Через ngrok (быстро для теста)**

```bash
# Установи ngrok
brew install ngrok

# В одном терминале запусти бота
./start.sh

# В другом терминале запусти туннель
ngrok http 8080

# Скопируй https URL (например https://abc123.ngrok.io)
```

Затем установи webhook:

```bash
python tools/webhook_setup.py set --url https://abc123.ngrok.io/api/photosync/webhook
```

**Вариант B: Постоянный сервер (для продакшена)**

Если Mac Mini имеет публичный IP или домен:

1. Настрой SSL через Caddy или nginx
2. Проксируй на localhost:8080
3. Установи webhook на твой домен

### 3. Проверка работы

```bash
# Тест бота
python tools/webhook_setup.py test

# Должно показать:
# ✅ Bot connected successfully!
# Name: Solar PhotoSync
# Username: @your_bot_name
```

### 4. Отправка фото

1. Найди своего бота в Telegram
2. Нажми Start
3. Отправь любое фото
4. Бот ответит: `✅ Принято → Other`

### 5. Где файлы?

По умолчанию: `/SOLAR/PhotoSync/`

```
/SOLAR/PhotoSync/
└── 2025-11-29/
    ├── Sprinter/
    ├── LDZ/
    ├── Legal/
    ├── Documents/
    └── Other/
        └── 20251129_143022_photo.jpg  ← твоё фото тут
```

Чтобы изменить путь, отредактируй в конфиге:

```json
"storage": {
  "root_path": "/Users/leanid/SOLAR/PhotoSync"
}
```

### 6. Классификация

Чтобы фото попало в нужную папку:

**Способ 1:** Отправь с подписью-командой
```
/sprinter
[фото]
```

**Способ 2:** Напиши ключевое слово в подписи
```
Фото вагона LDZ
[фото]
```

**Способ 3:** Отправь из чата с нужным названием
```
Чат "Sprinter Project" → все фото в Sprinter/
```

### 7. Логи

```bash
# Смотреть логи в реальном времени
tail -f /SOLAR/PhotoSync/logs/photosync.log
```

### 8. Автозапуск при старте Mac

Создай файл `~/Library/LaunchAgents/com.solar.photosync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.solar.photosync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/leanid/Projects/SOLAR-PhotoSync/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/leanid/Projects/SOLAR-PhotoSync</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.solar.photosync.plist
```

---

## Частые вопросы

**Q: Бот не отвечает**
```bash
python tools/webhook_setup.py info
# Проверь что webhook установлен и нет ошибок
```

**Q: Файлы не сохраняются**
```bash
# Проверь права на папку
sudo mkdir -p /SOLAR/PhotoSync
sudo chown -R $(whoami) /SOLAR
```

**Q: HEIC не конвертируется**
```bash
brew install imagemagick
```

---

## Контакты

Вопросы → Dashka
Баги → Claude (через чат)

---

**Удачи, Leanid! 🚀**
