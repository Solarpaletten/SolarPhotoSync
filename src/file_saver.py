"""
SOLAR PhotoSync v1.0.1 - File Saver Module
Сохранение файлов в структурированную файловую систему
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from src.logger import get_logger, update_last_saved, root_path_created
from src.heic_converter import HeicConverter


class FileSaver:
    """Менеджер сохранения файлов в файловую систему SOLAR"""
    
    def __init__(self, config: dict, heic_converter: HeicConverter):
        """
        Инициализация сохранятеля файлов
        
        Args:
            config: Конфигурация из photosync.config.json
            heic_converter: Экземпляр HEIC конвертера
        """
        self.logger = get_logger()
        self.heic_converter = heic_converter
        
        storage_config = config.get("storage", {})
        self.root_path = Path(storage_config.get("root_path", "/SOLAR/PhotoSync"))
        self.allowed_extensions = set(storage_config.get("allowed_extensions", []))
        
        # Автосоздание корневой директории если не существует
        if not self.root_path.exists():
            self.root_path.mkdir(parents=True, exist_ok=True)
            root_path_created(str(self.root_path))
        
        self.logger.info(f"FileSaver initialized. Root: {self.root_path}")
    
    def save_file(
        self,
        source_path: str,
        category: str,
        original_filename: str,
        file_date: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Сохранить файл в структурированную директорию
        
        Args:
            source_path: Путь к исходному файлу (временный)
            category: Категория (Sprinter, LDZ, Legal, Documents, Other)
            original_filename: Оригинальное имя файла
            file_date: Дата файла для именования (опционально)
        
        Returns:
            Tuple[success, saved_path or error_message]
        """
        source = Path(source_path)
        
        if not source.exists():
            return False, f"Source file not found: {source_path}"
        
        # Определяем дату
        if file_date is None:
            file_date = datetime.now()
        
        # Проверяем нужна ли конвертация HEIC
        if self.heic_converter.is_heic(source_path):
            success, result = self.heic_converter.convert(source_path)
            if success:
                source = Path(result)
                original_filename = Path(original_filename).stem + ".jpg"
            else:
                self.logger.warning(f"HEIC conversion failed, saving original: {result}")
        
        # Создаём структуру директорий: /SOLAR/PhotoSync/YYYY-MM-DD/Category/
        date_folder = file_date.strftime("%Y-%m-%d")
        target_dir = self.root_path / date_folder / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Формируем имя файла: YYYYMMDD_HHMMSS_originalname.ext
        timestamp = file_date.strftime("%Y%m%d_%H%M%S")
        clean_name = self._sanitize_filename(original_filename)
        extension = Path(clean_name).suffix.lower()
        base_name = Path(clean_name).stem
        
        new_filename = f"{timestamp}_{base_name}{extension}"
        target_path = target_dir / new_filename
        
        # Если файл уже существует, добавляем счётчик
        counter = 1
        while target_path.exists():
            new_filename = f"{timestamp}_{base_name}_{counter}{extension}"
            target_path = target_dir / new_filename
            counter += 1
        
        try:
            # Копируем файл
            shutil.copy2(source, target_path)
            
            # Обновляем timestamp последнего сохранения
            update_last_saved()
            
            self.logger.file_saved(original_filename, str(target_path), category)
            
            return True, str(target_path)
            
        except Exception as e:
            error_msg = f"Failed to save file: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def save_from_bytes(
        self,
        file_bytes: bytes,
        category: str,
        original_filename: str,
        file_date: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Сохранить файл из байтов
        
        Args:
            file_bytes: Содержимое файла в байтах
            category: Категория
            original_filename: Оригинальное имя файла
            file_date: Дата файла
        
        Returns:
            Tuple[success, saved_path or error_message]
        """
        import tempfile
        
        # Создаём временный файл
        extension = Path(original_filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            result = self.save_file(tmp_path, category, original_filename, file_date)
            return result
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Очистить имя файла от недопустимых символов
        
        Args:
            filename: Исходное имя файла
        
        Returns:
            Очищенное имя файла
        """
        # Заменяем недопустимые символы
        invalid_chars = '<>:"/\\|?*'
        result = filename
        
        for char in invalid_chars:
            result = result.replace(char, '_')
        
        # Убираем пробелы в начале/конце
        result = result.strip()
        
        # Заменяем множественные пробелы/подчёркивания
        while '__' in result:
            result = result.replace('__', '_')
        while '  ' in result:
            result = result.replace('  ', ' ')
        
        # Если имя пустое, генерируем
        if not result or result == '.':
            result = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return result
    
    def get_storage_stats(self) -> dict:
        """
        Получить статистику хранилища
        
        Returns:
            Словарь со статистикой
        """
        stats = {
            "root_path": str(self.root_path),
            "total_files": 0,
            "total_size_mb": 0,
            "categories": {},
            "dates": []
        }
        
        if not self.root_path.exists():
            return stats
        
        total_size = 0
        
        for date_dir in self.root_path.iterdir():
            if date_dir.is_dir() and not date_dir.name.startswith('.'):
                if date_dir.name != 'logs':
                    stats["dates"].append(date_dir.name)
                    
                    for cat_dir in date_dir.iterdir():
                        if cat_dir.is_dir():
                            cat_name = cat_dir.name
                            if cat_name not in stats["categories"]:
                                stats["categories"][cat_name] = 0
                            
                            for file in cat_dir.iterdir():
                                if file.is_file():
                                    stats["total_files"] += 1
                                    stats["categories"][cat_name] += 1
                                    total_size += file.stat().st_size
        
        stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        stats["dates"].sort(reverse=True)
        
        return stats
    
    def cleanup_temp_files(self, temp_dir: str = "/tmp/photosync"):
        """
        Очистить временные файлы
        
        Args:
            temp_dir: Путь к временной директории
        """
        temp_path = Path(temp_dir)
        if temp_path.exists():
            try:
                shutil.rmtree(temp_path)
                self.logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup temp: {e}")


def create_file_saver(config: dict, heic_converter: HeicConverter) -> FileSaver:
    """
    Фабричная функция для создания FileSaver
    
    Args:
        config: Конфигурация приложения
        heic_converter: Экземпляр HEIC конвертера
    
    Returns:
        Экземпляр FileSaver
    """
    return FileSaver(config, heic_converter)
