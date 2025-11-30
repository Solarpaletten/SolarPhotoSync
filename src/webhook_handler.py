"""
SOLAR PhotoSync v1.0.1 - Webhook Handler
Обработчик webhook запросов от Telegram
"""

import json
import aiohttp
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from src.logger import get_logger
from src.classifier import FileClassifier
from src.file_saver import FileSaver


class WebhookHandler:
    """Обработчик Telegram Webhook"""
    
    TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"
    TELEGRAM_FILE_BASE = "https://api.telegram.org/file/bot{token}"
    
    def __init__(
        self,
        config: dict,
        classifier: FileClassifier,
        file_saver: FileSaver
    ):
        """
        Инициализация обработчика webhook
        
        Args:
            config: Конфигурация приложения
            classifier: Классификатор файлов
            file_saver: Сохранятель файлов
        """
        self.logger = get_logger()
        self.config = config
        self.classifier = classifier
        self.file_saver = file_saver
        
        self.bot_token = config.get("bot", {}).get("token", "")
        self.api_base = self.TELEGRAM_API_BASE.format(token=self.bot_token)
        self.file_base = self.TELEGRAM_FILE_BASE.format(token=self.bot_token)
        
        storage_config = config.get("storage", {})
        self.allowed_types = set(storage_config.get("allowed_types", []))
        
        self.logger.info("WebhookHandler initialized")
    
    async def handle_update(self, update: dict) -> Dict[str, Any]:
        """
        Обработать update от Telegram
        
        Args:
            update: JSON объект update от Telegram
        
        Returns:
            Результат обработки
        """
        result = {
            "success": False,
            "message": "",
            "file_path": None
        }
        
        update_id = update.get("update_id", 0)
        message = update.get("message", {})
        
        # Фильтрация пустых updates (webhook ping) - return 200 silently
        if not message:
            result["success"] = True
            result["message"] = "empty_update"
            return result
        
        chat_id = message.get("chat", {}).get("id")
        chat_title = message.get("chat", {}).get("title", "")
        caption = message.get("caption", "")
        text = message.get("text", "")
        
        self.logger.webhook_received(update_id, chat_id)
        
        # Извлекаем команду если есть
        command = self.classifier.extract_command_from_text(text or caption)
        
        # Определяем тип медиа и получаем file_id
        file_info = self._extract_file_info(message)
        
        if not file_info:
            # Если это просто текстовое сообщение с командой - игнорируем
            if text and text.startswith('/'):
                result["message"] = "Command received, waiting for media"
                result["success"] = True
                return result
            
            result["message"] = "No supported media found"
            return result
        
        file_id = file_info["file_id"]
        file_name = file_info.get("file_name", f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        file_type = file_info["type"]
        file_size = file_info.get("file_size", 0)
        
        self.logger.file_received(file_name, file_type, file_size)
        
        try:
            # Скачиваем файл
            file_bytes, actual_filename = await self._download_file(file_id, file_name)
            
            if not file_bytes:
                result["message"] = "Failed to download file"
                return result
            
            # Классифицируем
            category, reason = self.classifier.classify(
                filename=actual_filename,
                caption=caption,
                chat_title=chat_title,
                command=command
            )
            
            # Определяем дату сохранения
            save_date = datetime.now()
            
            # Сохраняем
            success, saved_path = self.file_saver.save_from_bytes(
                file_bytes=file_bytes,
                category=category,
                original_filename=actual_filename,
                file_date=save_date
            )
            
            if success:
                result["success"] = True
                result["message"] = f"Saved to {category}"
                result["file_path"] = saved_path
                
                # Отправляем подтверждение пользователю
                await self._send_confirmation(chat_id, category, actual_filename, save_date)
            else:
                result["message"] = f"Failed to save: {saved_path}"
                self.logger.error_processing(actual_filename, saved_path)
                
        except Exception as e:
            error_msg = str(e)
            result["message"] = f"Error: {error_msg}"
            self.logger.error_processing(file_name, error_msg)
        
        return result
    
    def _extract_file_info(self, message: dict) -> Optional[Dict[str, Any]]:
        """
        Извлечь информацию о файле из сообщения
        
        Args:
            message: Объект сообщения Telegram
        
        Returns:
            Словарь с информацией о файле или None
        """
        # Фото (берём самое большое)
        if "photo" in message and message["photo"]:
            photo = message["photo"][-1]  # Последнее = самое большое
            return {
                "file_id": photo["file_id"],
                "file_name": f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                "type": "photo",
                "file_size": photo.get("file_size", 0)
            }
        
        # Документ
        if "document" in message:
            doc = message["document"]
            return {
                "file_id": doc["file_id"],
                "file_name": doc.get("file_name", "document"),
                "type": "document",
                "file_size": doc.get("file_size", 0),
                "mime_type": doc.get("mime_type", "")
            }
        
        # Видео
        if "video" in message:
            video = message["video"]
            return {
                "file_id": video["file_id"],
                "file_name": video.get("file_name", f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"),
                "type": "video",
                "file_size": video.get("file_size", 0)
            }
        
        # Анимация (GIF)
        if "animation" in message:
            anim = message["animation"]
            return {
                "file_id": anim["file_id"],
                "file_name": anim.get("file_name", f"animation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif"),
                "type": "animation",
                "file_size": anim.get("file_size", 0)
            }
        
        # Аудио
        if "audio" in message:
            audio = message["audio"]
            return {
                "file_id": audio["file_id"],
                "file_name": audio.get("file_name", f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"),
                "type": "audio",
                "file_size": audio.get("file_size", 0)
            }
        
        # Голосовое сообщение
        if "voice" in message:
            voice = message["voice"]
            return {
                "file_id": voice["file_id"],
                "file_name": f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg",
                "type": "voice",
                "file_size": voice.get("file_size", 0)
            }
        
        # Видео-сообщение (кружок)
        if "video_note" in message:
            vnote = message["video_note"]
            return {
                "file_id": vnote["file_id"],
                "file_name": f"video_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                "type": "video_note",
                "file_size": vnote.get("file_size", 0)
            }
        
        return None
    
    async def _download_file(self, file_id: str, default_name: str) -> Tuple[Optional[bytes], str]:
        """
        Скачать файл из Telegram
        
        Args:
            file_id: ID файла в Telegram
            default_name: Имя файла по умолчанию
        
        Returns:
            Tuple[bytes содержимое, имя файла]
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем путь к файлу
                get_file_url = f"{self.api_base}/getFile?file_id={file_id}"
                
                async with session.get(get_file_url) as resp:
                    if resp.status != 200:
                        self.logger.error(f"Failed to get file info: {resp.status}")
                        return None, default_name
                    
                    data = await resp.json()
                    
                    if not data.get("ok"):
                        self.logger.error(f"Telegram API error: {data}")
                        return None, default_name
                    
                    file_path = data["result"]["file_path"]
                    
                    # Извлекаем имя файла из пути если есть
                    actual_name = Path(file_path).name if '/' in file_path else default_name
                
                # Скачиваем файл
                download_url = f"{self.file_base}/{file_path}"
                
                async with session.get(download_url) as resp:
                    if resp.status != 200:
                        self.logger.error(f"Failed to download file: {resp.status}")
                        return None, actual_name
                    
                    file_bytes = await resp.read()
                    self.logger.debug(f"Downloaded {len(file_bytes)} bytes")
                    
                    return file_bytes, actual_name
                    
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            return None, default_name
    
    async def _send_confirmation(self, chat_id: int, category: str, filename: str, save_date: datetime = None):
        """
        Отправить подтверждение пользователю
        
        Args:
            chat_id: ID чата
            category: Категория сохранения
            filename: Имя файла
            save_date: Дата сохранения
        """
        try:
            if save_date is None:
                save_date = datetime.now()
            
            date_str = save_date.strftime("%Y-%m-%d")
            message = f"☀️ Saved → {category} / {date_str}"
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        self.logger.warning(f"Failed to send confirmation: {resp.status}")
                        
        except Exception as e:
            self.logger.warning(f"Confirmation error: {e}")


def create_webhook_handler(
    config: dict,
    classifier: FileClassifier,
    file_saver: FileSaver
) -> WebhookHandler:
    """
    Фабричная функция для создания WebhookHandler
    """
    return WebhookHandler(config, classifier, file_saver)
