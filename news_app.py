"""
Графический интерфейс приложения на Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from news_fetcher import NewsFetcher
from exceptions import NetworkError, ParsingError, InvalidUrlError, NoNewsError

class NewsApp:
    """Главное окно приложения"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Новостной парсер - Веб-скрейпинг")
        self.root.geometry("1100x750")
        
        # Настройка веса строк и колонок для растягивания
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.current_news = []
        self.setup_ui()
        
        # Автоматическая загрузка новостей при запуске
        self.load_news("https://ria.ru/export/rss2/index.xml")
    
    def setup_ui(self):
        """Создаёт интерфейс пользователя"""
        
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # === Строка ввода URL ===
        url_frame = ttk.LabelFrame(main_frame, text="URL источника", padding="5")
        url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        url_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="RSS адрес:").grid(row=0, column=0, padx=(0, 5))
        
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.url_entry.insert(0, "https://ria.ru/export/rss2/index.xml")
        
        self.load_button = ttk.Button(url_frame, text="📰 Загрузить новости", command=self.on_load_click)
        self.load_button.grid(row=0, column=2)
        
        # === Предустановленные источники (ТОЛЬКО РАБОТАЮЩИЕ) ===
        presets_frame = ttk.LabelFrame(main_frame, text="Быстрый выбор (работающие источники)", padding="5")
        presets_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # РИА Новости (работает)
        btn_ria = ttk.Button(
            presets_frame, 
            text="✅ РИА Новости", 
            command=lambda: self.load_news("https://ria.ru/export/rss2/index.xml")
        )
        btn_ria.pack(side=tk.LEFT, padx=5)
        
        # Лента.ру (работает)
        btn_lenta = ttk.Button(
            presets_frame, 
            text="✅ Лента.ру", 
            command=lambda: self.load_news("https://lenta.ru/rss")
        )
        btn_lenta.pack(side=tk.LEFT, padx=5)
        
        # === Таблица новостей ===
        table_frame = ttk.LabelFrame(main_frame, text="Новости", padding="5")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Создаём Treeview с тремя колонками
        columns = ("title", "date", "description")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # Настройка заголовков
        self.tree.heading("title", text="📰 Заголовок")
        self.tree.heading("date", text="📅 Дата")
        self.tree.heading("description", text="📝 Описание")
        
        # Настройка ширины колонок
        self.tree.column("title", width=500, minwidth=200)
        self.tree.column("date", width=180, minwidth=120)
        self.tree.column("description", width=350, minwidth=150)
        
        # Полосы прокрутки
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Двойной клик для открытия ссылки
        self.tree.bind("<Double-1>", self.open_link)
        # Правый клик для контекстного меню
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # === Статусная строка ===
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="✅ Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=0, column=0, sticky="ew")
        
        # Кнопка очистки
        self.clear_button = ttk.Button(status_frame, text="🗑 Очистить", command=self.clear_news)
        self.clear_button.grid(row=0, column=1, padx=(10, 0))
    
    def load_news(self, url):
        """Устанавливает URL и загружает новости"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.on_load_click()
    
    def on_load_click(self):
        """Обработчик нажатия кнопки загрузки"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Ошибка", "Введите URL RSS-ленты")
            return
        
        # Блокируем кнопки
        self.load_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        self.status_label.config(text="⏳ Загрузка новостей... Пожалуйста, подождите...")
        
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Загружаем в отдельном потоке
        thread = threading.Thread(target=self.fetch_news_thread, args=(url,), daemon=True)
        thread.start()
    
    def fetch_news_thread(self, url):
        """Загрузка новостей в отдельном потоке"""
        try:
            fetcher = NewsFetcher(url)
            news_list = fetcher.fetch_news()
            self.current_news = news_list
            
            # Обновляем UI в главном потоке
            self.root.after(0, self.display_news, news_list)
            self.root.after(0, self.status_label.config, {"text": f"✅ Загружено {len(news_list)} новостей"})
            
        except NetworkError as e:
            self.root.after(0, self.show_error, f"Ошибка сети", str(e))
        except InvalidUrlError as e:
            self.root.after(0, self.show_error, f"Неверный URL", str(e))
        except ParsingError as e:
            self.root.after(0, self.show_error, f"Ошибка парсинга", str(e))
        except NoNewsError as e:
            self.root.after(0, self.show_error, f"Новости не найдены", str(e))
        except Exception as e:
            self.root.after(0, self.show_error, f"Ошибка", str(e))
        finally:
            self.root.after(0, self.enable_buttons)
    
    def display_news(self, news_list):
        """Отображает новости в таблице"""
        for news in news_list:
            # Ограничиваем длину заголовка для лучшего отображения
            title = news['title']
            if len(title) > 80:
                title = title[:77] + "..."
            
            self.tree.insert("", tk.END, values=(
                title,
                news['date'],
                news['description']
            ))
        
        if len(news_list) == 0:
            self.status_label.config(text="⚠️ Новости не найдены")
    
    def open_link(self, event):
        """Открывает ссылку в браузере при двойном клике"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.current_news):
                news = self.current_news[index]
                link = news.get('link', '#')
                
                if link and link != '#':
                    result = messagebox.askyesno(
                        "Открыть ссылку",
                        f"Открыть в браузере?\n\n{news['title']}\n\n{link}"
                    )
                    if result:
                        webbrowser.open(link)
    
    def show_context_menu(self, event):
        """Показывает контекстное меню при правом клике"""
        selection = self.tree.selection()
        if selection:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="🌐 Открыть в браузере", command=lambda: self.open_link(None))
            menu.add_separator()
            menu.add_command(label="📋 Копировать заголовок", command=self.copy_title)
            menu.add_command(label="📋 Копировать ссылку", command=self.copy_link)
            menu.post(event.x_root, event.y_root)
    
    def copy_title(self):
        """Копирует заголовок выбранной новости в буфер обмена"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.current_news):
                title = self.current_news[index]['title']
                self.root.clipboard_clear()
                self.root.clipboard_append(title)
                self.status_label.config(text="✅ Заголовок скопирован")
    
    def copy_link(self):
        """Копирует ссылку выбранной новости в буфер обмена"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.current_news):
                link = self.current_news[index]['link']
                self.root.clipboard_clear()
                self.root.clipboard_append(link)
                self.status_label.config(text="✅ Ссылка скопирована")
    
    def clear_news(self):
        """Очищает список новостей"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_news = []
        self.status_label.config(text="🗑 Список очищен")
    
    def show_error(self, title, message):
        """Показывает сообщение об ошибке"""
        self.status_label.config(text=f"❌ {title}: {message}")
        messagebox.showerror(title, message)
    
    def enable_buttons(self):
        """Разблокирует кнопки"""
        self.load_button.config(state="normal")
        self.clear_button.config(state="normal")
    
    def run(self):
        """Запускает главный цикл приложения"""
        self.root.mainloop()