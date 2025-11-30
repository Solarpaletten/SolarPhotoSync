"""
SOLAR PhotoSync v1.0.1 - Main Bot Module
Telegram Bot для автоматической загрузки медиафайлов в SOLAR

Автор: Claude (инженер)
Координатор: Dashka (senior)
Архитектор: Leanid
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from aiohttp import web

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import get_logger, PhotoSyncLogger, get_last_saved
from src.classifier import create_classifier
from src.heic_converter import create_converter
from src.file_saver import create_file_saver
from src.webhook_handler import create_webhook_handler


class SolarPhotoSyncBot:
    """Главный класс бота Solar PhotoSync"""
    
    VERSION = "1.0.1"
    
    def __init__(self, config_path: str = None):
        """
        Инициализация бота
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        # Фиксируем время старта для uptime
        self.start_time = time.time()
        
        # Загружаем конфигурацию
        self.config = self._load_config(config_path)
        
        # Инициализируем логгер
        self.logger = get_logger()
        self.logger.setup(self.config)
        
        self.logger.info(f"=" * 50)
        self.logger.info(f"SOLAR PhotoSync v{self.VERSION} starting...")
        self.logger.info(f"=" * 50)
        
        # Инициализируем компоненты
        self.classifier = create_classifier(self.config)
        self.heic_converter = create_converter(self.config)
        self.file_saver = create_file_saver(self.config, self.heic_converter)
        self.webhook_handler = create_webhook_handler(
            self.config, 
            self.classifier, 
            self.file_saver
        )
        
        # Web приложение
        self.app = web.Application()
        self._setup_routes()
        
        self.logger.info("All components initialized successfully")
    
    def _load_config(self, config_path: str = None) -> dict:
        """
        Загрузить конфигурацию из файла
        
        Args:
            config_path: Путь к файлу конфигурации
        
        Returns:
            Словарь конфигурации
        """
        if config_path is None:
            # Ищем конфиг относительно этого файла
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "photosync.config.json"
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            print(f"Config file not found: {config_path}")
            print("Creating default config...")
            return self._create_default_config(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_default_config(self, config_path: Path) -> dict:
        """Создать конфигурацию по умолчанию"""
        default_config = {
            "bot": {
                "token": os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE"),
                "webhook_url": "",
                "webhook_secret": ""
            },
            "storage": {
                "root_path": str(Path.home() / "SOLAR" / "PhotoSync"),
                "allowed_types": ["photo", "document", "video", "animation"],
                "allowed_extensions": [".jpg", ".jpeg", ".png", ".heic", ".pdf", ".mp4"]
            },
            "processing": {
                "convert_heic": True,
                "heic_quality": 85,
                "preserve_exif": True
            },
            "classification": {
                "auto_classification": True,
                "default_category": "Other",
                "categories": {
                    "Sprinter": ["sprinter"],
                    "LDZ": ["ldz", "vagon"],
                    "Legal": ["court", "суд"],
                    "Documents": ["document", "паспорт"]
                }
            },
            "logging": {
                "enabled": True,
                "log_path": str(Path.home() / "SOLAR" / "PhotoSync" / "logs"),
                "log_file": "photosync.log",
                "log_level": "INFO"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080
            }
        }
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    def _setup_routes(self):
        """Настройка маршрутов веб-сервера"""
        self.app.router.add_post('/api/photosync/webhook', self.handle_webhook)
        self.app.router.add_get('/api/photosync/health', self.handle_health)
        self.app.router.add_get('/api/photosync/stats', self.handle_stats)
        self.app.router.add_get('/', self.handle_root)
    
    async def handle_webhook(self, request: web.Request) -> web.Response:
        """
        Обработчик webhook от Telegram
        
        POST /api/photosync/webhook
        """
        try:
            update = await request.json()
            result = await self.webhook_handler.handle_update(update)
            
            return web.json_response(result)
            
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400
            )
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """
        Health check endpoint
        
        GET /api/photosync/health
        """
        # Вычисляем uptime
        uptime_seconds = int(time.time() - self.start_time)
        
        # Получаем last_saved
        last_saved = get_last_saved()
        last_saved_str = last_saved.isoformat() if last_saved else None
        
        # Получаем root_path
        root_path = self.config.get("storage", {}).get("root_path", "/SOLAR/PhotoSync")
        
        return web.json_response({
            "status": "ok",
            "version": self.VERSION,
            "uptime": f"{uptime_seconds}s",
            "root_path": root_path,
            "last_saved": last_saved_str
        })
    
    async def handle_stats(self, request: web.Request) -> web.Response:
        """
        Статистика хранилища
        
        GET /api/photosync/stats
        """
        stats = self.file_saver.get_storage_stats()
        stats["version"] = self.VERSION
        return web.json_response(stats)
    
    async def handle_root(self, request: web.Request) -> web.Response:
        """Корневой endpoint"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SOLAR PhotoSync v{self.VERSION}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                       max-width: 800px; margin: 50px auto; padding: 20px; }}
                h1 {{ color: #FF6B00; }}
                .status {{ color: #00AA00; font-weight: bold; }}
                code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>☀️ SOLAR PhotoSync</h1>
            <p>Version: <strong>{self.VERSION}</strong></p>
            <p>Status: <span class="status">● Running</span></p>
            
            <h2>Endpoints</h2>
            <ul>
                <li><code>POST /api/photosync/webhook</code> - Telegram webhook</li>
                <li><code>GET /api/photosync/health</code> - Health check</li>
                <li><code>GET /api/photosync/stats</code> - Storage statistics</li>
            </ul>
            
            <h2>Categories</h2>
            <ul>
                <li>📦 Sprinter</li>
                <li>🚂 LDZ</li>
                <li>⚖️ Legal</li>
                <li>📄 Documents</li>
                <li>📁 Other</li>
            </ul>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    def run(self):
        """Запуск бота"""
        server_config = self.config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8080)
        
        self.logger.info(f"Starting server on {host}:{port}")
        self.logger.info(f"Webhook endpoint: http://{host}:{port}/api/photosync/webhook")
        
        web.run_app(self.app, host=host, port=port, print=None)


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SOLAR PhotoSync Bot')
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to config file',
        default=None
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        help='Server port (overrides config)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Создаём и запускаем бота
    bot = SolarPhotoSyncBot(config_path=args.config)
    
    # Переопределяем порт если указан
    if args.port:
        bot.config["server"]["port"] = args.port
    
    bot.run()


if __name__ == "__main__":
    main()
