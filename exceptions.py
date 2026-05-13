"""
Собственные исключения для приложения
"""

class NewsParserError(Exception):
    """Базовое исключение"""
    pass

class NetworkError(NewsParserError):
    """Ошибка сети"""
    pass

class ParsingError(NewsParserError):
    """Ошибка парсинга"""
    pass

class InvalidUrlError(NewsParserError):
    """Некорректный URL"""
    pass

class NoNewsError(NewsParserError):
    """Новости не найдены"""
    pass