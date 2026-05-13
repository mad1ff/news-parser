"""
Класс для получения и парсинга новостей из RSS
"""

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import re
from exceptions import NetworkError, ParsingError, InvalidUrlError, NoNewsError

class NewsFetcher:
    """Загрузчик новостей из RSS-ленты"""
    
    def __init__(self, rss_url=None):
        if rss_url is None:
            self.rss_url = "https://ria.ru/export/rss2/index.xml"
        else:
            self.rss_url = rss_url
    
    def fetch_news(self):
        """Загружает и парсит новости"""
        
        if not self.rss_url.startswith(('http://', 'https://')):
            raise InvalidUrlError(f"Неверный URL: {self.rss_url}")
        
        try:
            req = urllib.request.Request(
                self.rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            # Устанавливаем таймаут 30 секунд
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')
            
            return self._parse_rss(data)
            
        except urllib.error.HTTPError as e:
            raise NetworkError(f"HTTP ошибка {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise NetworkError(f"Ошибка сети: {e.reason}")
        except UnicodeDecodeError as e:
            raise ParsingError(f"Ошибка декодирования: {e}")
        except ET.ParseError as e:
            raise ParsingError(f"Ошибка парсинга XML: {e}")
        except TimeoutError:
            raise NetworkError("Превышен таймаут ожидания ответа от сервера")
        except Exception as e:
            raise ParsingError(f"Неожиданная ошибка: {e}")
    
    def _parse_rss(self, xml_data):
        """Парсит XML данные и извлекает новости"""
        try:
            root = ET.fromstring(xml_data)
            news_list = []
            
            # Ищем все элементы item
            items = root.findall('.//item')
            
            for item in items[:25]:
                # Заголовок
                title_elem = item.find('title')
                title = title_elem.text if title_elem is not None else 'Без названия'
                title = title.strip()
                
                # Ссылка
                link_elem = item.find('link')
                link = link_elem.text if link_elem is not None else '#'
                
                # Дата
                date_elem = item.find('pubDate')
                date = date_elem.text if date_elem is not None else 'Дата неизвестна'
                
                # Описание
                desc_elem = item.find('description')
                description = desc_elem.text if desc_elem is not None else ''
                if description:
                    # Удаляем HTML теги
                    description = re.sub(r'<[^<]+?>', '', description)
                    # Удаляем лишние пробелы
                    description = re.sub(r'\s+', ' ', description).strip()
                    # Обрезаем длинные описания
                    if len(description) > 150:
                        description = description[:150] + '...'
                else:
                    description = 'Нет описания'
                
                news_list.append({
                    'title': title,
                    'link': link,
                    'date': date,
                    'description': description
                })
            
            if not news_list:
                raise NoNewsError("Новости не найдены в RSS-ленте")
            
            return news_list
            
        except ET.ParseError as e:
            raise ParsingError(f"Ошибка парсинга XML: {e}")