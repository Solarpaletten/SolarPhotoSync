"""
SOLAR PhotoSync v1.0.1 - HEIC Converter Module
Конвертация HEIC/HEIF в JPG с сохранением EXIF
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from src.logger import get_logger


class HeicConverter:
    """Конвертер HEIC/HEIF файлов в JPG"""
    
    HEIC_EXTENSIONS = {'.heic', '.heif'}
    
    def __init__(self, config: dict):
        """
        Инициализация конвертера
        
        Args:
            config: Конфигурация из photosync.config.json
        """
        self.logger = get_logger()
        processing_config = config.get("processing", {})
        
        self.enabled = processing_config.get("convert_heic", True)
        self.quality = processing_config.get("heic_quality", 85)
        self.preserve_exif = processing_config.get("preserve_exif", True)
        
        # Проверяем доступные инструменты конвертации
        self.converter_tool = self._detect_converter()
        
        if self.enabled:
            self.logger.info(f"HEIC converter initialized. Tool: {self.converter_tool}, Quality: {self.quality}%")
    
    def _detect_converter(self) -> Optional[str]:
        """
        Определить доступный инструмент для конвертации
        
        Returns:
            Название инструмента или None
        """
        # Приоритет: ImageMagick -> sips (macOS) -> pillow-heif -> heif-convert
        
        # ImageMagick (кроссплатформенный)
        if shutil.which("magick") or shutil.which("convert"):
            return "imagemagick"
        
        # sips (встроен в macOS)
        if shutil.which("sips"):
            return "sips"
        
        # heif-convert (libheif)
        if shutil.which("heif-convert"):
            return "heif-convert"
        
        # Пробуем pillow-heif (Python библиотека)
        try:
            import pillow_heif
            return "pillow-heif"
        except ImportError:
            pass
        
        self.logger.warning("No HEIC converter found! Install ImageMagick, pillow-heif, or use macOS")
        return None
    
    def is_heic(self, filepath: str) -> bool:
        """
        Проверить, является ли файл HEIC/HEIF
        
        Args:
            filepath: Путь к файлу
        
        Returns:
            True если файл HEIC/HEIF
        """
        ext = Path(filepath).suffix.lower()
        return ext in self.HEIC_EXTENSIONS
    
    def convert(self, input_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Конвертировать HEIC в JPG
        
        Args:
            input_path: Путь к HEIC файлу
            output_path: Путь для сохранения JPG (опционально)
        
        Returns:
            Tuple[success, output_path or error_message]
        """
        if not self.enabled:
            return False, "HEIC conversion disabled"
        
        if not self.converter_tool:
            return False, "No converter tool available"
        
        input_file = Path(input_path)
        if not input_file.exists():
            return False, f"Input file not found: {input_path}"
        
        if not self.is_heic(input_path):
            return False, f"Not a HEIC file: {input_path}"
        
        # Определяем выходной путь
        if output_path is None:
            output_path = str(input_file.with_suffix('.jpg'))
        
        try:
            if self.converter_tool == "imagemagick":
                success = self._convert_imagemagick(input_path, output_path)
            elif self.converter_tool == "sips":
                success = self._convert_sips(input_path, output_path)
            elif self.converter_tool == "heif-convert":
                success = self._convert_heif_convert(input_path, output_path)
            elif self.converter_tool == "pillow-heif":
                success = self._convert_pillow_heif(input_path, output_path)
            else:
                return False, "Unknown converter tool"
            
            if success:
                self.logger.file_converted(
                    input_file.name,
                    Path(output_path).name,
                    "HEIC",
                    "JPG"
                )
                return True, output_path
            else:
                return False, "Conversion failed"
                
        except Exception as e:
            error_msg = f"Conversion error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _convert_imagemagick(self, input_path: str, output_path: str) -> bool:
        """Конвертация через ImageMagick"""
        cmd_name = "magick" if shutil.which("magick") else "convert"
        
        cmd = [
            cmd_name,
            input_path,
            "-quality", str(self.quality),
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _convert_sips(self, input_path: str, output_path: str) -> bool:
        """Конвертация через sips (macOS)"""
        cmd = [
            "sips",
            "-s", "format", "jpeg",
            "-s", "formatOptions", str(self.quality),
            input_path,
            "--out", output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _convert_heif_convert(self, input_path: str, output_path: str) -> bool:
        """Конвертация через heif-convert (libheif)"""
        cmd = [
            "heif-convert",
            "-q", str(self.quality),
            input_path,
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _convert_pillow_heif(self, input_path: str, output_path: str) -> bool:
        """Конвертация через pillow-heif"""
        try:
            import pillow_heif
            from PIL import Image
            
            # Регистрируем HEIF opener
            pillow_heif.register_heif_opener()
            
            # Открываем и конвертируем
            with Image.open(input_path) as img:
                # Сохраняем EXIF если есть
                exif_data = img.info.get('exif', None)
                
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Сохраняем как JPEG
                save_kwargs = {
                    'quality': self.quality,
                    'optimize': True
                }
                
                if self.preserve_exif and exif_data:
                    save_kwargs['exif'] = exif_data
                
                img.save(output_path, 'JPEG', **save_kwargs)
            
            return True
            
        except Exception as e:
            self.logger.error(f"pillow-heif conversion failed: {e}")
            return False
    
    def get_exif_date(self, filepath: str) -> Optional[datetime]:
        """
        Извлечь дату из EXIF данных
        
        Args:
            filepath: Путь к файлу
        
        Returns:
            datetime или None
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(filepath) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal':
                            return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
        
        return None


def create_converter(config: dict) -> HeicConverter:
    """
    Фабричная функция для создания конвертера
    
    Args:
        config: Конфигурация приложения
    
    Returns:
        Экземпляр HeicConverter
    """
    return HeicConverter(config)
