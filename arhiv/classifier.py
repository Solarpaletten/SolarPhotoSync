"""
SOLAR PhotoSync v1.1.0 - Classifier Module (Deploy Edition)
Мини-ИИ классификация v1.0 по ключевым словам
"""

import re
from typing import Optional, Tuple
from logger import get_logger


class FileClassifier:
    """Классификатор файлов по ключевым словам"""
    
    def __init__(self, config: dict):
        """
        Инициализация классификатора
        
        Args:
            config: Конфигурация из photosync.config.json
        """
        self.logger = get_logger()
        classification_config = config.get("classification", {})
        
        self.enabled = classification_config.get("auto_classification", True)
        self.default_category = classification_config.get("default_category", "Other")
        self.categories = classification_config.get("categories", {})
        
        # Компилируем регулярные выражения для быстрого поиска
        self._compiled_patterns = {}
        for category, keywords in self.categories.items():
            patterns = [re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE) for kw in keywords]
            self._compiled_patterns[category] = patterns
        
        self.logger.debug(f"Classifier initialized with {len(self.categories)} categories")
    
    def classify(
        self,
        filename: str,
        caption: Optional[str] = None,
        chat_title: Optional[str] = None,
        command: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Классифицировать файл и определить категорию
        
        Args:
            filename: Имя файла
            caption: Подпись к файлу (если есть)
            chat_title: Название чата
            command: Команда от пользователя (например /sprinter)
        
        Returns:
            Tuple[category, reason]: Категория и причина классификации
        """
        if not self.enabled:
            return self.default_category, "classification_disabled"
        
        # 1. Приоритет: явная команда от пользователя
        if command:
            category = self._match_command(command)
            if category:
                self.logger.classification_result(filename, category, f"command: {command}")
                return category, f"command: {command}"
        
        # 2. Проверка подписи к файлу
        if caption:
            category = self._match_text(caption)
            if category:
                self.logger.classification_result(filename, category, f"caption match")
                return category, "caption_match"
        
        # 3. Проверка названия чата
        if chat_title:
            category = self._match_text(chat_title)
            if category:
                self.logger.classification_result(filename, category, f"chat_title: {chat_title}")
                return category, "chat_title_match"
        
        # 4. Проверка имени файла
        category = self._match_text(filename)
        if category:
            self.logger.classification_result(filename, category, "filename_match")
            return category, "filename_match"
        
        # 5. Не удалось классифицировать -> Other
        self.logger.classification_result(filename, self.default_category, "no_match")
        return self.default_category, "no_match"
    
    def _match_command(self, command: str) -> Optional[str]:
        """
        Сопоставить команду с категорией
        
        Args:
            command: Команда (например /sprinter или sprinter)
        
        Returns:
            Название категории или None
        """
        # Убираем слеш и приводим к нижнему регистру
        cmd = command.lstrip('/').lower().strip()
        
        # Прямое совпадение с названием категории
        for category in self.categories:
            if cmd == category.lower():
                return category
        
        # Проверка по ключевым словам
        for category, keywords in self.categories.items():
            if cmd in [kw.lower() for kw in keywords]:
                return category
        
        return None
    
    def _match_text(self, text: str) -> Optional[str]:
        """
        Найти категорию по ключевым словам в тексте
        
        Args:
            text: Текст для анализа
        
        Returns:
            Название категории или None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Проверяем каждую категорию
        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return category
        
        return None
    
    def get_categories(self) -> list:
        """Получить список всех категорий"""
        return list(self.categories.keys()) + [self.default_category]
    
    def add_category(self, name: str, keywords: list):
        """
        Добавить новую категорию
        
        Args:
            name: Название категории
            keywords: Список ключевых слов
        """
        self.categories[name] = keywords
        patterns = [re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE) for kw in keywords]
        self._compiled_patterns[name] = patterns
        self.logger.info(f"Added category: {name} with {len(keywords)} keywords")
    
    def extract_command_from_text(self, text: str) -> Optional[str]:
        """
        Извлечь команду из текста сообщения
        
        Args:
            text: Текст сообщения
        
        Returns:
            Команда без слеша или None
        """
        if not text:
            return None
        
        # Ищем команду в начале текста
        match = re.match(r'^/(\w+)', text.strip())
        if match:
            return match.group(1)
        
        return None


def create_classifier(config: dict) -> FileClassifier:
    """
    Фабричная функция для создания классификатора
    
    Args:
        config: Конфигурация приложения
    
    Returns:
        Экземпляр FileClassifier
    """
    return FileClassifier(config)
