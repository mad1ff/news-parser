"""
Точка входа в приложение (Tkinter версия)
"""

from news_app import NewsApp

def main():
    """Главная функция"""
    app = NewsApp()
    app.run()

if __name__ == "__main__":
    main()