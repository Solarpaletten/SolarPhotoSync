"""
SOLAR PhotoSync v1.1.0 - Logger Module (Deploy Edition)
Модуль логирования для отслеживания всех операций
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Глобальная переменная для отслеживания последнего сохранения
LAST_SAVED_TIMESTAMP: datetime = None


def update_last_saved():
    """Обновить timestamp последнего сохранения"""
    global LAST_SAVED_TIMESTAMP
    LAST_SAVED_TIMESTAMP = datetime.now()


def get_last_saved() -> datetime:
    """Получить timestamp последнего сохранения"""
    return LAST_SAVED_TIMESTAMP


class PhotoSyncLogger:
    """Централизованный логгер для PhotoSync"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if PhotoSyncLogger._initialized:
            return
        
        self.logger = logging.getLogger("PhotoSync")
        self.logger.setLevel(logging.DEBUG)
        PhotoSyncLogger._initialized = True
    
    def setup(self, config: dict):
        """Настройка логгера из конфигурации"""
        log_config = config.get("logging", {})
        
        if not log_config.get("enabled", True):
            self.logger.disabled = True
            return
        
        log_path = Path(log_config.get("log_path", "/SOLAR/PhotoSync/logs"))
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / log_config.get("log_file", "photosync.log")
        max_size = log_config.get("max_log_size_mb", 10) * 1024 * 1024
        backup_count = log_config.get("backup_count", 5)
        log_level = getattr(logging, log_config.get("log_level", "INFO").upper())
        
        # Формат лога
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Файловый хендлер с ротацией
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Консольный хендлер
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Очистка старых хендлеров и добавление новых
        self.logger.handlers.clear()
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.info(f"Logger initialized. Log file: {log_file}")
    
    def info(self, message: str):
        """Информационное сообщение"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Сообщение об ошибке"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Предупреждение"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Отладочное сообщение"""
        self.logger.debug(message)
    
    def file_received(self, filename: str, file_type: str, size: int):
        """Лог получения файла"""
        size_kb = size / 1024
        self.info(f"Received {file_type}: {filename} ({size_kb:.1f} KB)")
    
    def file_saved(self, original_name: str, saved_path: str, category: str):
        """Лог сохранения файла"""
        self.info(f"Saved: {original_name} -> {saved_path} [Category: {category}]")
    
    def file_converted(self, original_name: str, new_name: str, format_from: str, format_to: str):
        """Лог конвертации файла"""
        self.info(f"Converted: {original_name} ({format_from}) -> {new_name} ({format_to})")
    
    def classification_result(self, filename: str, category: str, reason: str):
        """Лог результата классификации"""
        self.info(f"Classified: {filename} -> {category} (reason: {reason})")
    
    def webhook_received(self, update_id: int, chat_id: int):
        """Лог получения webhook"""
        self.debug(f"Webhook received: update_id={update_id}, chat_id={chat_id}")
    
    def error_processing(self, filename: str, error: str):
        """Лог ошибки обработки"""
        self.error(f"Error processing {filename}: {error}")


# Глобальный экземпляр логгера
logger = PhotoSyncLogger()


def get_logger() -> PhotoSyncLogger:
    """Получить экземпляр логгера"""
    return logger


def root_path_created(path: str):
    """Лог создания корневой директории"""
    logger.info(f"Root path not found, created: {path}")
