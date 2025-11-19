import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import pulp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os


class ForestHarvestingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Оптимизация лесозаготовки")

        # Устанавливаем размер окна 4:3
        window_width = 1024
        window_height = 768

        # Получаем размеры экрана
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Вычисляем позицию для центрирования
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Устанавливаем геометрию (размер + позиция)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.file_path = "lesozagotovka.xlsx"
        self.is_editing = False
        self.edited_data = {}
        self.current_edit_cell = None

        # Создаем файл если его нет
        self.create_default_excel()

        # Загружаем данные
        self.load_data()

        # Создаем интерфейс
        self.create_widgets()

    def create_default_excel(self):
        """Создает файл Excel с данными по умолчанию если его нет"""
        if not os.path.exists(self.file_path):
            # Данные по умолчанию
            df_c = pd.DataFrame({
                'Участок': [1, 1, 1, 2, 2, 2],
                'Месяц': [1, 2, 3, 1, 2, 3],
                'Доход (тыс. руб./га)': [10, 12, 11, 9, 13, 10]
            })

            df_a = pd.DataFrame({
                'Участок': [1, 1, 1, 2, 2, 2],
                'Месяц': [1, 2, 3, 1, 2, 3],
                'Трудозатраты (ч/га)': [8, 7, 9, 6, 8, 7]
            })

            df_b = pd.DataFrame({
                'Месяц': [1, 2, 3],
                'Ресурсы (часы)': [200, 180, 220]
            })

            df_bj = pd.DataFrame({
                'Участок': [1, 2],
                'Площадь (га)': [50, 40]
            })

            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                df_c.to_excel(writer, sheet_name='Доход', index=False)
                df_a.to_excel(writer, sheet_name='Труд', index=False)
                df_b.to_excel(writer, sheet_name='Ресурсы', index=False)
                df_bj.to_excel(writer, sheet_name='Площадь', index=False)

    def load_data(self):
        """Загружает данные из Excel файла"""
        try:
            self.df_c = pd.read_excel(self.file_path, sheet_name="Доход")
            self.df_a = pd.read_excel(self.file_path, sheet_name="Труд")
            self.df_b = pd.read_excel(self.file_path, sheet_name="Ресурсы")
            self.df_bj = pd.read_excel(self.file_path, sheet_name="Площадь")

            # ПРЕОБРАЗУЕМ ДАННЫЕ ДЛЯ ОТОБРАЖЕНИЯ
            self.df_c['Доход (тыс. руб./га)'] = self.df_c['Доход (тыс. руб./га)'].apply(
                lambda x: "Не указано" if pd.isna(x) else (int(x) if x == int(x) else round(x, 2))
            )
            self.df_a['Трудозатраты (ч/га)'] = self.df_a['Трудозатраты (ч/га)'].apply(
                lambda x: "Не указано" if pd.isna(x) else (int(x) if x == int(x) else round(x, 2))
            )

            # УБИРАЕМ ЛИШНИЕ ЗНАКИ ПОСЛЕ ТОЧКИ ДЛЯ ОСТАЛЬНЫХ ТАБЛИЦ
            self.df_b['Ресурсы (часы)'] = self.df_b['Ресурсы (часы)'].apply(
                lambda x: int(x) if x == int(x) else round(x, 2)
            )
            self.df_bj['Площадь (га)'] = self.df_bj['Площадь (га)'].apply(
                lambda x: int(x) if x == int(x) else round(x, 2)
            )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def save_data(self):
        """Сохраняет данные в Excel файл"""
        try:
            # ПОДГОТАВЛИВАЕМ ДАННЫЕ НАПРЯМУЮ, БЕЗ СОЗДАНИЯ КОПИЙ
            # Заменяем "Не указано" на пустые значения для числовых колонок
            self.df_c['Доход (тыс. руб./га)'] = pd.to_numeric(
                self.df_c['Доход (тыс. руб./га)'], errors='coerce'
            )
            self.df_a['Трудозатраты (ч/га)'] = pd.to_numeric(
                self.df_a['Трудозатраты (ч/га)'], errors='coerce'
            )

            # УБИРАЕМ ЛИШНИЕ ЗНАКИ ПОСЛЕ ТОЧКИ - округляем до 2 знаков
            self.df_c['Доход (тыс. руб./га)'] = self.df_c['Доход (тыс. руб./га)'].round(2)
            self.df_a['Трудозатраты (ч/га)'] = self.df_a['Трудозатраты (ч/га)'].round(2)
            self.df_b['Ресурсы (часы)'] = self.df_b['Ресурсы (часы)'].round(2)
            self.df_bj['Площадь (га)'] = self.df_bj['Площадь (га)'].round(2)

            # Сохраняем данные
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                self.df_c.to_excel(writer, sheet_name='Доход', index=False)
                self.df_a.to_excel(writer, sheet_name='Труд', index=False)
                self.df_b.to_excel(writer, sheet_name='Ресурсы', index=False)
                self.df_bj.to_excel(writer, sheet_name='Площадь', index=False)

            # ВОССТАНАВЛИВАЕМ "Не указано" ДЛЯ ОТОБРАЖЕНИЯ В ПРИЛОЖЕНИИ
            self.df_c['Доход (тыс. руб./га)'] = self.df_c['Доход (тыс. руб./га)'].apply(
                lambda x: "Не указано" if pd.isna(x) else (int(x) if x == int(x) else x)
            )
            self.df_a['Трудозатраты (ч/га)'] = self.df_a['Трудозатраты (ч/га)'].apply(
                lambda x: "Не указано" if pd.isna(x) else (int(x) if x == int(x) else x)
            )

            return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {str(e)}")
            return False

    def create_widgets(self):
        """Создает элементы интерфейса"""
        # Основной фрейм с вкладками
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Вкладка с данными
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Данные")

        # Вкладка с результатами
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="Результаты")

        # Создаем вкладки для данных
        data_notebook = ttk.Notebook(data_frame)
        data_notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Фреймы для каждой таблицы
        self.create_income_tab(data_notebook)
        self.create_labor_tab(data_notebook)
        self.create_resources_tab(data_notebook)
        self.create_area_tab(data_notebook)

        # Панель управления
        control_frame = ttk.Frame(data_frame)
        control_frame.pack(fill='x', padx=10, pady=5)

        # Фрейм для обычных кнопок
        self.normal_buttons_frame = ttk.Frame(control_frame)
        self.normal_buttons_frame.pack(fill='x')

        # Обычные кнопки
        self.edit_button = ttk.Button(self.normal_buttons_frame, text="Редактировать",
                                      command=self.start_editing)
        self.edit_button.pack(side='left', padx=5)

        ttk.Button(self.normal_buttons_frame, text="Добавить участок",
                   command=self.add_site).pack(side='left', padx=5)

        ttk.Button(self.normal_buttons_frame, text="Добавить месяц",
                   command=self.add_month).pack(side='left', padx=5)

        ttk.Button(self.normal_buttons_frame, text="Обновить данные",
                   command=self.refresh_data).pack(side='left', padx=5)

        # Фрейм для кнопок редактирования (изначально скрыт)
        self.edit_buttons_frame = ttk.Frame(control_frame)

        # Кнопки редактирования
        self.save_button = ttk.Button(self.edit_buttons_frame, text="Сохранить",
                                      command=self.save_changes)
        self.save_button.pack(side='left', padx=5)

        self.cancel_button = ttk.Button(self.edit_buttons_frame, text="Отменить",
                                        command=self.cancel_editing)
        self.cancel_button.pack(side='left', padx=5)

        # Метка режима редактирования
        self.edit_label = ttk.Label(self.edit_buttons_frame, text="(режим редактирования...)",
                                    foreground="blue")
        self.edit_label.pack(side='left', padx=10)

        # Фрейм для результатов
        self.create_results_tab(result_frame)

        # Кнопка расчета
        ttk.Button(result_frame, text="Рассчитать оптимальный план",
                   command=self.calculate).pack(pady=10)

    def create_income_tab(self, parent):
        """Создает вкладку с данными о доходах"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Доход")

        # Treeview для отображения данных
        tree = ttk.Treeview(frame, columns=('Участок', 'Месяц', 'Доход'), show='headings')
        tree.heading('Участок', text='Участок')
        tree.heading('Месяц', text='Месяц')
        tree.heading('Доход', text='Доход (тыс. руб./га)')

        tree.column('Участок', width=100)
        tree.column('Месяц', width=100)
        tree.column('Доход', width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Привязываем обработчик двойного клика для редактирования
        tree.bind('<Double-1>', self.on_double_click_income)

        self.income_tree = tree
        self.refresh_income_data()

    def create_labor_tab(self, parent):
        """Создает вкладку с данными о трудозатратах"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Трудозатраты")

        tree = ttk.Treeview(frame, columns=('Участок', 'Месяц', 'Трудозатраты'), show='headings')
        tree.heading('Участок', text='Участок')
        tree.heading('Месяц', text='Месяц')
        tree.heading('Трудозатраты', text='Трудозатраты (ч/га)')

        tree.column('Участок', width=100)
        tree.column('Месяц', width=100)
        tree.column('Трудозатраты', width=150)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Привязываем обработчик двойного клика для редактирования
        tree.bind('<Double-1>', self.on_double_click_labor)

        self.labor_tree = tree
        self.refresh_labor_data()

    def create_resources_tab(self, parent):
        """Создает вкладку с данными о ресурсах"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Ресурсы")

        tree = ttk.Treeview(frame, columns=('Месяц', 'Ресурсы'), show='headings')
        tree.heading('Месяц', text='Месяц')
        tree.heading('Ресурсы', text='Ресурсы (часы)')

        tree.column('Месяц', width=100)
        tree.column('Ресурсы', width=150)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Привязываем обработчик двойного клика для редактирования
        tree.bind('<Double-1>', self.on_double_click_resources)

        self.resources_tree = tree
        self.refresh_resources_data()

    def create_area_tab(self, parent):
        """Создает вкладку с данными о площадях"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Площадь")

        tree = ttk.Treeview(frame, columns=('Участок', 'Площадь'), show='headings')
        tree.heading('Участок', text='Участок')
        tree.heading('Площадь', text='Площадь (га)')

        tree.column('Участок', width=100)
        tree.column('Площадь', width=150)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Привязываем обработчик двойного клика для редактирования
        tree.bind('<Double-1>', self.on_double_click_area)

        self.area_tree = tree
        self.refresh_area_data()

    def create_results_tab(self, parent):
        """Создает вкладку для отображения результатов"""
        # Фрейм для результатов
        result_text_frame = ttk.Frame(parent)
        result_text_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Текстовое поле для результатов
        self.result_text = tk.Text(result_text_frame, height=20, width=80)
        scrollbar = ttk.Scrollbar(result_text_frame, orient='vertical', command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def refresh_income_data(self):
        """Обновляет данные о доходах в treeview"""
        for item in self.income_tree.get_children():
            self.income_tree.delete(item)

        for _, row in self.df_c.iterrows():
            self.income_tree.insert('', 'end', values=(
                row['Участок'], row['Месяц'], row['Доход (тыс. руб./га)']
            ))

    def refresh_labor_data(self):
        """Обновляет данные о трудозатратах в treeview"""
        for item in self.labor_tree.get_children():
            self.labor_tree.delete(item)

        for _, row in self.df_a.iterrows():
            self.labor_tree.insert('', 'end', values=(
                row['Участок'], row['Месяц'], row['Трудозатраты (ч/га)']
            ))

    def refresh_resources_data(self):
        """Обновляет данные о ресурсах в treeview"""
        for item in self.resources_tree.get_children():
            self.resources_tree.delete(item)

        for _, row in self.df_b.iterrows():
            self.resources_tree.insert('', 'end', values=(
                row['Месяц'], row['Ресурсы (часы)']
            ))

    def refresh_area_data(self):
        """Обновляет данные о площадях в treeview"""
        for item in self.area_tree.get_children():
            self.area_tree.delete(item)

        for _, row in self.df_bj.iterrows():
            self.area_tree.insert('', 'end', values=(
                row['Участок'], row['Площадь (га)']
            ))

    def refresh_data(self):
        """Обновляет все данные"""
        self.load_data()
        self.refresh_income_data()
        self.refresh_labor_data()
        self.refresh_resources_data()
        self.refresh_area_data()

    def start_editing(self):
        """Начинает режим редактирования"""
        self.is_editing = True

        # Скрываем обычные кнопки
        self.normal_buttons_frame.pack_forget()

        # Показываем кнопки редактирования
        self.edit_buttons_frame.pack(fill='x')

        # Сохраняем текущие данные для возможности отмены
        self.edited_data = {
            'income': self.df_c.copy(),
            'labor': self.df_a.copy(),
            'resources': self.df_b.copy(),
            'area': self.df_bj.copy()
        }

        messagebox.showinfo("Редактирование",
                            "Режим редактирования включен. Дважды щелкните по ячейке для изменения значения.")

    def save_changes(self):
        """Сохраняет изменения и завершает редактирование"""
        if self.save_data():
            self.is_editing = False
            self.edit_buttons_frame.pack_forget()
            self.normal_buttons_frame.pack(fill='x')
            messagebox.showinfo("Успех", "Изменения сохранены!")

    def cancel_editing(self):
        """Отменяет изменения и завершает редактирование"""
        self.is_editing = False

        # Скрываем кнопки редактирования
        self.edit_buttons_frame.pack_forget()

        # Показываем обычные кнопки
        self.normal_buttons_frame.pack(fill='x')

        # Восстанавливаем исходные данные
        self.df_c = self.edited_data['income']
        self.df_a = self.edited_data['labor']
        self.df_b = self.edited_data['resources']
        self.df_bj = self.edited_data['area']

        self.refresh_data()
        messagebox.showinfo("Отменено", "Изменения отменены!")

    # Методы для редактирования ячеек
    def on_double_click_income(self, event):
        """Обработчик двойного клика для таблицы доходов"""
        if not self.is_editing:
            return

        region = self.income_tree.identify("region", event.x, event.y)
        if region == "cell":
            self.edit_cell(self.income_tree, event, 'income')

    def on_double_click_labor(self, event):
        """Обработчик двойного клика для таблицы трудозатрат"""
        if not self.is_editing:
            return

        region = self.labor_tree.identify("region", event.x, event.y)
        if region == "cell":
            self.edit_cell(self.labor_tree, event, 'labor')

    def on_double_click_resources(self, event):
        """Обработчик двойного клика для таблицы ресурсов"""
        region = self.resources_tree.identify("region", event.x, event.y)
        if region == "cell":
            if not self.is_editing:
                # ОБЫЧНЫЙ РЕЖИМ: открываем комплексный редактор
                item = self.resources_tree.selection()[0]
                month = int(self.resources_tree.item(item)['values'][0])
                dialog = EditMonthDialog(self.root, self, month)
                self.root.wait_window(dialog.dialog)

    def on_double_click_area(self, event):
        """Обработчик двойного клика для таблицы площадей"""
        region = self.area_tree.identify("region", event.x, event.y)
        if region == "cell":
            if not self.is_editing:
                # ОБЫЧНЫЙ РЕЖИМ: открываем комплексный редактор
                item = self.area_tree.selection()[0]
                site = int(self.area_tree.item(item)['values'][0])
                dialog = EditSiteDialog(self.root, self, site)
                self.root.wait_window(dialog.dialog)

    def edit_cell(self, tree, event, table_type):
        """Редактирование ячейки"""
        # Определяем ячейку
        column = tree.identify_column(event.x)
        row = tree.identify_row(event.y)

        if not row:
            return

        # Получаем текущее значение
        item = tree.item(row)
        values = item['values']
        col_index = int(column[1:]) - 1

        if col_index >= len(values):
            return

        # Создаем поле для редактирования
        x, y, width, height = tree.bbox(row, column)

        # Создаем Entry для редактирования
        entry = ttk.Entry(tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, values[col_index])
        entry.select_range(0, tk.END)
        entry.focus()

        def save_edit(event=None):
            """Сохраняет изменения"""
            new_value = entry.get()
            entry.destroy()

            # Обновляем значение в treeview
            values[col_index] = new_value
            tree.item(row, values=values)

            # Обновляем значение в DataFrame
            self.update_dataframe(table_type, row, col_index, new_value)

        def cancel_edit(event=None):
            """Отменяет редактирование"""
            entry.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', lambda e: save_edit())

    def update_dataframe(self, table_type, row_id, col_index, new_value):
        """Обновляет DataFrame после редактирования ячейки"""
        try:
            if table_type == 'income':
                df = self.df_c
                item_values = self.income_tree.item(row_id)['values']
                old_site = item_values[0]
                old_month = item_values[1]

                # Находим строку в DataFrame
                mask = (df['Участок'] == old_site) & (df['Месяц'] == old_month)
                if col_index == 0:  # Участок
                    site_val = int(new_value)
                    if site_val <= 0:
                        messagebox.showerror("Ошибка", "Номер участка должен быть положительным!")
                        return False
                    df.loc[mask, 'Участок'] = site_val
                elif col_index == 1:  # Месяц
                    month_val = int(new_value)
                    if month_val < 1 or month_val > 12:
                        messagebox.showerror("Ошибка", "Месяц должен быть в диапазоне от 1 до 12!")
                        return False
                    df.loc[mask, 'Месяц'] = month_val
                elif col_index == 2:  # Доход
                    income_val = float(new_value)
                    if income_val < 0:
                        messagebox.showerror("Ошибка", "Доход не может быть отрицательным!")
                        return False
                    df.loc[mask, 'Доход (тыс. руб./га)'] = income_val

            elif table_type == 'labor':
                df = self.df_a
                item_values = self.labor_tree.item(row_id)['values']
                old_site = item_values[0]
                old_month = item_values[1]

                # Находим строку в DataFrame
                mask = (df['Участок'] == old_site) & (df['Месяц'] == old_month)
                if col_index == 0:  # Участок
                    site_val = int(new_value)
                    if site_val <= 0:
                        messagebox.showerror("Ошибка", "Номер участка должен быть положительным!")
                        return False
                    df.loc[mask, 'Участок'] = site_val
                elif col_index == 1:  # Месяц
                    month_val = int(new_value)
                    if month_val < 1 or month_val > 12:
                        messagebox.showerror("Ошибка", "Месяц должен быть в диапазоне от 1 до 12!")
                        return False
                    df.loc[mask, 'Месяц'] = month_val
                elif col_index == 2:  # Трудозатраты
                    labor_val = float(new_value)
                    if labor_val < 0:
                        messagebox.showerror("Ошибка", "Трудозатраты не могут быть отрицательными!")
                        return False
                    df.loc[mask, 'Трудозатраты (ч/га)'] = labor_val

            elif table_type == 'resources':
                df = self.df_b
                item_values = self.resources_tree.item(row_id)['values']
                old_month = item_values[0]

                # Находим строку в DataFrame
                mask = (df['Месяц'] == old_month)
                if col_index == 0:  # Месяц
                    month_val = int(new_value)
                    if month_val < 1 or month_val > 12:
                        messagebox.showerror("Ошибка", "Месяц должен быть в диапазоне от 1 до 12!")
                        return False
                    df.loc[mask, 'Месяц'] = month_val
                elif col_index == 1:  # Ресурсы
                    resources_val = float(new_value)
                    if resources_val < 0:
                        messagebox.showerror("Ошибка", "Ресурсы не могут быть отрицательными!")
                        return False
                    df.loc[mask, 'Ресурсы (часы)'] = resources_val

            elif table_type == 'area':
                df = self.df_bj
                item_values = self.area_tree.item(row_id)['values']
                old_site = item_values[0]

                # Находим строку в DataFrame
                mask = (df['Участок'] == old_site)
                if col_index == 0:  # Участок
                    site_val = int(new_value)
                    if site_val <= 0:
                        messagebox.showerror("Ошибка", "Номер участка должен быть положительным!")
                        return False
                    df.loc[mask, 'Участок'] = site_val
                elif col_index == 1:  # Площадь
                    area_val = float(new_value)
                    if area_val < 0:
                        messagebox.showerror("Ошибка", "Площадь не может быть отрицательной!")
                        return False
                    df.loc[mask, 'Площадь (га)'] = area_val

            # ОБНОВЛЯЕМ ОТОБРАЖЕНИЕ ПОСЛЕ УСПЕШНОГО ОБНОВЛЕНИЯ
            return True

        except ValueError as e:
            messagebox.showerror("Ошибка", "Введите числовое значение!")
            self.refresh_data()  # Восстанавливаем исходные данные
            return False

    def remove_related_month_data(self, month):
        """Удаляет все данные, связанные с указанным месяцем"""
        # Удаляем из таблицы доходов
        self.df_c = self.df_c[self.df_c['Месяц'] != month]
        # Удаляем из таблицы трудозатрат
        self.df_a = self.df_a[self.df_a['Месяц'] != month]
        # Удаляем из таблицы ресурсов
        self.df_b = self.df_b[self.df_b['Месяц'] != month]

    def remove_related_site_data(self, site):
        """Удаляет все данные, связанные с указанным участком"""
        # Удаляем из таблицы доходов
        self.df_c = self.df_c[self.df_c['Участок'] != site]
        # Удаляем из таблицы трудозатрат
        self.df_a = self.df_a[self.df_a['Участок'] != site]
        # Удаляем из таблицы площадей
        self.df_bj = self.df_bj[self.df_bj['Участок'] != site]

    def add_site(self):
        """Добавляет новый участок"""
        dialog = AddSiteDialog(self.root, self)
        self.root.wait_window(dialog.dialog)

    def add_month(self):
        """Добавляет новый месяц"""
        dialog = AddMonthDialog(self.root, self)
        self.root.wait_window(dialog.dialog)

    def calculate(self):
        """Выполняет расчет оптимального плана"""
        try:
            # Преобразуем данные в словари, пропуская "Не указано"
            c = {}
            for _, row in self.df_c.iterrows():
                # Пропускаем строки с "Не указано"
                if row["Доход (тыс. руб./га)"] == "Не указано":
                    continue
                key = (int(row["Участок"]), int(row["Месяц"]))
                value = float(row["Доход (тыс. руб./га)"])
                c[key] = value

            a = {}
            for _, row in self.df_a.iterrows():
                # Пропускаем строки с "Не указано"
                if row["Трудозатраты (ч/га)"] == "Не указано":
                    continue
                key = (int(row["Участок"]), int(row["Месяц"]))
                value = float(row["Трудозатраты (ч/га)"])
                a[key] = value

            b = {}
            for _, row in self.df_b.iterrows():
                key = int(row["Месяц"])
                value = float(row["Ресурсы (часы)"])
                b[key] = value

            b_j = {}
            for _, row in self.df_bj.iterrows():
                key = int(row["Участок"])
                value = float(row["Площадь (га)"])
                b_j[key] = value

            # Проверка полноты данных (теперь будет показывать "Не указано" как отсутствующие данные)
            missing_data = self.check_data_completeness(c, a, b, b_j)

            if missing_data:
                response = self.ask_about_missing_data(missing_data)
                if response == "cancel":
                    return
                elif response == "continue":
                    # Удаляем проблемные данные
                    c, a, b, b_j = self.remove_problematic_data(c, a, b, b_j, missing_data)

            # Проверяем, остались ли данные для расчета
            if not b_j or not b:
                messagebox.showerror("Ошибка", "Недостаточно данных для расчета!")
                return

            model = LpProblem("Оптимизация_лесозаготовки", LpMaximize)
            x = {(j, t): LpVariable(f"x_{j}_{t}", lowBound=0) for j in b_j.keys() for t in b.keys()}

            # Функция цели (пропускаем отсутствующие данные)
            objective_terms = []
            for j in b_j.keys():
                for t in b.keys():
                    if (j, t) in c and (j, t) in a:
                        objective_terms.append(c[j, t] * x[j, t])

            if not objective_terms:
                messagebox.showerror("Ошибка", "Нет данных для расчета целевой функции!")
                return

            model += lpSum(objective_terms)

            # Ограничения по трудовым ресурсам с явными именами
            for t in b.keys():
                labor_terms = []
                for j in b_j.keys():
                    if (j, t) in a:
                        labor_terms.append(a[j, t] * x[j, t])
                if labor_terms:
                    model += lpSum(labor_terms) <= b[t], f"Ресурсы_месяц_{t}"

            # Ограничения по площади участков с явными именами
            for j in b_j.keys():
                area_terms = []
                for t in b.keys():
                    if (j, t) in c and (j, t) in a:
                        area_terms.append(x[j, t])
                if area_terms:
                    model += lpSum(area_terms) <= b_j[j], f"Площадь_участок_{j}"

            # РЕШАЕМ СИМПЛЕКС-МЕТОДОМ
            # Попробуем разные решатели, которые поддерживают симплекс-метод
            try:
                # Первый вариант: используем GLPK если установлен
                model.solve(pulp.GLPK(msg=True, options=["--simplex"]))
            except:
                try:
                    # Второй вариант: используем COIN с симплекс-методом
                    model.solve(PULP_CBC_CMD(msg=True, options=["simplex"]))
                except:
                    # Третий вариант: стандартный решатель (часто использует симплекс)
                    model.solve(PULP_CBC_CMD(msg=True))

            # Вывод результатов
            self.result_text.delete(1.0, tk.END)

            if model.status == 1:
                self.result_text.insert(tk.END, f"Максимальный доход: {model.objective.value():.2f} тыс. руб.\n\n")
                self.result_text.insert(tk.END, "План лесозаготовки:\n")

                found_plan = False
                for t in sorted(b.keys()):
                    for j in sorted(b_j.keys()):
                        if (j, t) in c and (j, t) in a:
                            harvested_area = x[j, t].value()
                            if harvested_area and harvested_area > 0.001:
                                self.result_text.insert(tk.END, f"Месяц {t}, участок {j}: {harvested_area:.2f} га\n")
                                found_plan = True

                if not found_plan:
                    self.result_text.insert(tk.END, "Нет активных планов заготовки\n")

                # ВЫВОД ДВОЙСТВЕННЫХ ПЕРЕМЕННЫХ
                self.result_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                self.result_text.insert(tk.END, "ДВОЙСТВЕННЫЕ ПЕРЕМЕННЫЕ:\n\n")

                # Теневые цены ресурсов (по месяцам)
                self.result_text.insert(tk.END, "Теневые цены ресурсов (по месяцам):\n")
                for t in sorted(b.keys()):
                    constraint_name = f"Ресурсы_месяц_{t}"
                    if constraint_name in model.constraints:
                        shadow_price = model.constraints[constraint_name].pi
                        if shadow_price is not None:
                            if abs(shadow_price) < 0.0001:  # Если значение очень близко к нулю
                                shadow_price = 0.0
                            self.result_text.insert(tk.END, f"Месяц {t}: {shadow_price:.4f} тыс. руб./час\n")
                        else:
                            self.result_text.insert(tk.END, f"Месяц {t}: 0.0000 тыс. руб./час\n")
                    else:
                        self.result_text.insert(tk.END, f"Месяц {t}: ограничение не создано\n")

                # Теневые цены площадей (по участкам)
                self.result_text.insert(tk.END, "\nТеневые цены площадей (по участкам):\n")
                for j in sorted(b_j.keys()):
                    constraint_name = f"Площадь_участок_{j}"
                    if constraint_name in model.constraints:
                        shadow_price = model.constraints[constraint_name].pi
                        if shadow_price is not None:
                            if abs(shadow_price) < 0.0001:  # Если значение очень близко к нулю
                                shadow_price = 0.0
                            self.result_text.insert(tk.END, f"Участок {j}: {shadow_price:.4f} тыс. руб./га\n")
                        else:
                            self.result_text.insert(tk.END, f"Участок {j}: 0.0000 тыс. руб./га\n")
                    else:
                        self.result_text.insert(tk.END, f"Участок {j}: ограничение не создано\n")

            else:
                self.result_text.insert(tk.END, f"Решение не найдено. Статус: {model.status}\n")

        except Exception as e:
            messagebox.showerror("Ошибка расчета", f"Произошла ошибка при расчете: {str(e)}")


    def check_data_completeness(self, c, a, b, b_j):
        """Проверяет полноту данных и возвращает список отсутствующих данных"""
        missing_data = {
            'income': [],  # Отсутствующие доходы
            'labor': [],  # Отсутствующие трудозатраты
            'resources': [],  # Отсутствующие ресурсы
            'area': []  # Отсутствующие площади
        }

        # Проверяем все возможные комбинации участков и месяцев
        for site in b_j.keys():
            for month in b.keys():
                # Проверяем доходы
                if (site, month) not in c:
                    missing_data['income'].append((site, month))

                # Проверяем трудозатраты
                if (site, month) not in a:
                    missing_data['labor'].append((site, month))

        # Проверяем ресурсы для месяцев
        for site in b_j.keys():
            if site not in b_j:
                missing_data['area'].append(site)

        # Убираем пустые категории
        missing_data = {k: v for k, v in missing_data.items() if v}

        return missing_data

    def ask_about_missing_data(self, missing_data):
        """Спрашивает пользователя как поступить с отсутствующими данными"""
        message = "Обнаружены отсутствующие данные:\n\n"

        if missing_data.get('income'):
            message += "Отсутствуют доходы для:\n"
            for site, month in missing_data['income'][:10]:  # Показываем первые 10
                message += f"  - Участок {site}, Месяц {month}\n"
            if len(missing_data['income']) > 10:
                message += f"  ... и еще {len(missing_data['income']) - 10} записей\n"

        if missing_data.get('labor'):
            message += "\nОтсутствуют трудозатраты для:\n"
            for site, month in missing_data['labor'][:10]:
                message += f"  - Участок {site}, Месяц {month}\n"
            if len(missing_data['labor']) > 10:
                message += f"  ... и еще {len(missing_data['labor']) - 10} записей\n"

        if missing_data.get('resources'):
            message += "\nОтсутствуют ресурсы для месяцев:\n"
            for month in missing_data['resources'][:10]:
                message += f"  - Месяц {month}\n"

        if missing_data.get('area'):
            message += "\nОтсутствуют площади для участков:\n"
            for site in missing_data['area'][:10]:
                message += f"  - Участок {site}\n"

        message += "\nВыберите действие:"

        # Создаем диалоговое окно с тремя кнопками
        dialog = tk.Toplevel(self.root)
        dialog.title("Неполные данные")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем окно
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Текст с прокруткой
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, wrap='word', height=15)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        text_widget.insert('1.0', message)
        text_widget.config(state='disabled')

        # Переменная для результата
        result = tk.StringVar(value="cancel")

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="Продолжить без учета\nотсутствующих данных",
                   command=lambda: result.set("continue")).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отменить расчет",
                   command=lambda: result.set("cancel")).pack(side='right', padx=5)

        # Ждем выбора пользователя
        dialog.wait_variable(result)
        dialog.destroy()

        return result.get()

    def remove_problematic_data(self, c, a, b, b_j, missing_data):
        """Удаляет проблемные данные из словарей"""
        # Удаляем отсутствующие доходы и трудозатраты
        for site, month in missing_data.get('income', []):
            if (site, month) in c:
                del c[(site, month)]

        for site, month in missing_data.get('labor', []):
            if (site, month) in a:
                del a[(site, month)]

        # Удаляем участки без площади
        for site in missing_data.get('area', []):
            if site in b_j:
                del b_j[site]
                # Также удаляем все связанные данные
                keys_to_remove = [key for key in c.keys() if key[0] == site]
                for key in keys_to_remove:
                    del c[key]

                keys_to_remove = [key for key in a.keys() if key[0] == site]
                for key in keys_to_remove:
                    del a[key]

        # Удаляем месяцы без ресурсов
        for month in missing_data.get('resources', []):
            if month in b:
                del b[month]
                # Также удаляем все связанные данные
                keys_to_remove = [key for key in c.keys() if key[1] == month]
                for key in keys_to_remove:
                    del c[key]

                keys_to_remove = [key for key in a.keys() if key[1] == month]
                for key in keys_to_remove:
                    del a[key]

        return c, a, b, b_j


class EditMonthDialog:
    def __init__(self, parent, app, month):
        self.app = app
        self.month = month
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Редактирование месяца {month}")
        self.dialog.geometry("750x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)  # Запрет масштабирования

        # Центрируем окно
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Основной фрейм
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(expand=True, fill='both', padx=20, pady=15)

        # Заголовок
        ttk.Label(main_frame, text=f"Редактирование месяца {month}",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Ресурсы месяца
        resources_frame = ttk.Frame(main_frame)
        resources_frame.pack(fill='x', pady=10)
        ttk.Label(resources_frame, text="Ресурсы (часы):", width=15, anchor='w').pack(side='left')
        self.resources_entry = ttk.Entry(resources_frame, width=25, font=('Arial', 10))
        self.resources_entry.pack(side='right', fill='x', expand=True)

        # Загружаем текущие ресурсы
        current_resources = self.app.df_b[self.app.df_b['Месяц'] == month]['Ресурсы (часы)'].values
        if len(current_resources) > 0:
            self.resources_entry.insert(0, str(current_resources[0]))

        # Таблица трудозатрат по участкам
        ttk.Label(main_frame, text="Трудозатраты по участкам:",
                  font=('Arial', 11, 'bold')).pack(pady=(20, 10))

        # Создаем таблицу для редактирования трудозатрат С ПРОКРУТКОЙ
        self.create_scrollable_labor_table(main_frame)

        # Таблица доходов по участкам
        ttk.Label(main_frame, text="Доходы по участкам:",
                  font=('Arial', 11, 'bold')).pack(pady=(20, 10))

        # Создаем таблицу для редактирования доходов С ПРОКРУТКОЙ
        self.create_scrollable_income_table(main_frame)

        # Фрейм-заполнитель чтобы кнопки были в самом низу
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.pack(fill='both', expand=True)

        # Кнопки сохранения/отмены - ФИКСИРОВАННЫЕ В НИЗУ
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))

        # Кнопка удаления с большей шириной
        ttk.Button(button_frame, text="Удалить",
                   command=self.delete_month, width=15).pack(side='left', padx=5)

        ttk.Button(button_frame, text="Сохранить",
                   command=self.save_changes, width=12).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=self.dialog.destroy, width=12).pack(side='right', padx=5)

    def create_scrollable_labor_table(self, parent):
        """Создает таблицу для редактирования трудозатрат с прокруткой"""
        # Основной контейнер для таблицы
        table_outer_frame = ttk.Frame(parent)
        table_outer_frame.pack(fill='both', expand=True, pady=5)

        # Фрейм для заголовков таблицы
        header_frame = ttk.Frame(table_outer_frame)
        header_frame.pack(fill='x', pady=(0, 5))

        # Заголовки таблицы
        ttk.Label(header_frame, text="Участок", width=15, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')
        ttk.Label(header_frame, text="Трудозатраты (ч/га)", width=20, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')

        # Фрейм для скроллбара и контента
        scroll_frame = ttk.Frame(table_outer_frame)
        scroll_frame.pack(fill='both', expand=True)

        # Canvas и скроллбар для прокрутки
        canvas = tk.Canvas(scroll_frame, height=150)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)

        # Фрейм для контента внутри canvas
        self.labor_content_frame = ttk.Frame(canvas)

        # Настройка прокрутки
        canvas.create_window((0, 0), window=self.labor_content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и скроллбара
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обновление скроллрегиона при изменении размера
        self.labor_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Контейнер для полей ввода внутри content_frame
        labor_container = ttk.Frame(self.labor_content_frame)
        labor_container.pack(fill='x')

        # Загружаем данные для этого месяца
        month_labor_data = self.app.df_a[self.app.df_a['Месяц'] == self.month]
        self.labor_entries = {}

        # Получаем все участки
        all_sites = self.app.df_bj['Участок'].unique()

        for site in all_sites:
            site = int(site)
            row_frame = ttk.Frame(labor_container)
            row_frame.pack(fill='x', pady=2)

            ttk.Label(row_frame, text=str(site), width=15, anchor='w').pack(side='left')

            labor_entry = ttk.Entry(row_frame, width=20, font=('Arial', 10))
            labor_entry.pack(side='left')

            # Загружаем текущее значение
            site_data = month_labor_data[month_labor_data['Участок'] == site]
            if len(site_data) > 0:
                labor_value = site_data['Трудозатраты (ч/га)'].values[0]
                if labor_value != "Не указано":
                    labor_entry.insert(0, str(labor_value))

            self.labor_entries[site] = labor_entry

    def create_scrollable_income_table(self, parent):
        """Создает таблицу для редактирования доходов с прокруткой"""
        # Основной контейнер для таблицы
        table_outer_frame = ttk.Frame(parent)
        table_outer_frame.pack(fill='both', expand=True, pady=5)

        # Фрейм для заголовков таблицы
        header_frame = ttk.Frame(table_outer_frame)
        header_frame.pack(fill='x', pady=(0, 5))

        # Заголовки таблицы
        ttk.Label(header_frame, text="Участок", width=15, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')
        ttk.Label(header_frame, text="Доход (тыс. руб./га)", width=20, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')

        # Фрейм для скроллбара и контента
        scroll_frame = ttk.Frame(table_outer_frame)
        scroll_frame.pack(fill='both', expand=True)

        # Canvas и скроллбар для прокрутки
        canvas = tk.Canvas(scroll_frame, height=150)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)

        # Фрейм для контента внутри canvas
        self.income_content_frame = ttk.Frame(canvas)

        # Настройка прокрутки
        canvas.create_window((0, 0), window=self.income_content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и скроллбара
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обновление скроллрегиона при изменении размера
        self.income_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Контейнер для полей ввода внутри content_frame
        income_container = ttk.Frame(self.income_content_frame)
        income_container.pack(fill='x')

        # Загружаем данные для этого месяца
        month_income_data = self.app.df_c[self.app.df_c['Месяц'] == self.month]
        self.income_entries = {}

        # Получаем все участки
        all_sites = self.app.df_bj['Участок'].unique()

        for site in all_sites:
            site = int(site)
            row_frame = ttk.Frame(income_container)
            row_frame.pack(fill='x', pady=2)

            ttk.Label(row_frame, text=str(site), width=15, anchor='w').pack(side='left')

            income_entry = ttk.Entry(row_frame, width=20, font=('Arial', 10))
            income_entry.pack(side='left')

            # Загружаем текущее значение
            site_data = month_income_data[month_income_data['Участок'] == site]
            if len(site_data) > 0:
                income_value = site_data['Доход (тыс. руб./га)'].values[0]
                if income_value != "Не указано":
                    income_entry.insert(0, str(income_value))

            self.income_entries[site] = income_entry

    def save_changes(self):
        """Сохраняет изменения"""
        try:
            # ПРОВЕРКА РЕСУРСОВ
            if self.resources_entry.get():
                resources = float(self.resources_entry.get())
                if resources < 0:
                    messagebox.showerror("Ошибка", "Ресурсы не могут быть отрицательными!")
                    return

            # ПРОВЕРКА ТРУДОЗАТРАТ
            for site, entry in self.labor_entries.items():
                if entry.get():
                    labor = float(entry.get())
                    if labor < 0:
                        messagebox.showerror("Ошибка", "Трудозатраты не могут быть отрицательными!")
                        return

            # ПРОВЕРКА ДОХОДОВ
            for site, entry in self.income_entries.items():
                if entry.get():
                    income = float(entry.get())
                    if income < 0:
                        messagebox.showerror("Ошибка", "Доход не может быть отрицательным!")
                        return

            # Сохраняем ресурсы
            if self.resources_entry.get():
                resources = float(self.resources_entry.get())
                # Проверяем, существует ли уже запись для этого месяца
                if self.month in self.app.df_b['Месяц'].values:
                    self.app.df_b.loc[self.app.df_b['Месяц'] == self.month, 'Ресурсы (часы)'] = resources
                else:
                    # Создаем новую запись
                    new_resource = pd.DataFrame({
                        'Месяц': [self.month],
                        'Ресурсы (часы)': [resources]
                    })
                    self.app.df_b = pd.concat([self.app.df_b, new_resource], ignore_index=True)

            # Сохраняем трудозатраты
            for site, entry in self.labor_entries.items():
                if entry.get():
                    labor = float(entry.get())
                    mask = (self.app.df_a['Участок'] == site) & (self.app.df_a['Месяц'] == self.month)
                    if mask.any():
                        self.app.df_a.loc[mask, 'Трудозатраты (ч/га)'] = labor
                    else:
                        # Создаем новую запись
                        new_labor = pd.DataFrame({
                            'Участок': [site],
                            'Месяц': [self.month],
                            'Трудозатраты (ч/га)': [labor]
                        })
                        self.app.df_a = pd.concat([self.app.df_a, new_labor], ignore_index=True)
                else:
                    # Если поле пустое, удаляем запись если она существует
                    mask = (self.app.df_a['Участок'] == site) & (self.app.df_a['Месяц'] == self.month)
                    if mask.any():
                        self.app.df_a = self.app.df_a[~mask]

            # Сохраняем доходы
            for site, entry in self.income_entries.items():
                if entry.get():
                    income = float(entry.get())
                    mask = (self.app.df_c['Участок'] == site) & (self.app.df_c['Месяц'] == self.month)
                    if mask.any():
                        self.app.df_c.loc[mask, 'Доход (тыс. руб./га)'] = income
                    else:
                        # Создаем новую запись
                        new_income = pd.DataFrame({
                            'Участок': [site],
                            'Месяц': [self.month],
                            'Доход (тыс. руб./га)': [income]
                        })
                        self.app.df_c = pd.concat([self.app.df_c, new_income], ignore_index=True)
                else:
                    # Если поле пустое, удаляем запись если она существует
                    mask = (self.app.df_c['Участок'] == site) & (self.app.df_c['Месяц'] == self.month)
                    if mask.any():
                        self.app.df_c = self.app.df_c[~mask]

            if self.app.save_data():
                self.app.refresh_data()
                self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Ошибка",
                                 "Проверьте правильность введенных данных! Все числовые поля должны содержать числа.")

    def delete_month(self):
        """Удаляет месяц и все связанные данные"""
        result = messagebox.askyesno("Подтверждение удаления",
                                     f"Вы уверены, что хотите удалить месяц {self.month}?\n\n"
                                     "Это действие удалит все данные, связанные с этим месяцем.")
        if result:
            self.app.remove_related_month_data(self.month)
            if self.app.save_data():
                self.app.refresh_data()
                self.dialog.destroy()
                messagebox.showinfo("Успех", f"Месяц {self.month} и все связанные данные удалены!")


class EditSiteDialog:
    def __init__(self, parent, app, site):
        self.app = app
        self.site = site
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Редактирование участка {site}")
        self.dialog.geometry("750x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)  # Запрет масштабирования

        # Центрируем окно
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Основной фрейм
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(expand=True, fill='both', padx=20, pady=15)

        # Заголовок
        ttk.Label(main_frame, text=f"Редактирование участка {site}",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Площадь участка
        area_frame = ttk.Frame(main_frame)
        area_frame.pack(fill='x', pady=10)
        ttk.Label(area_frame, text="Площадь (га):", width=15, anchor='w').pack(side='left')
        self.area_entry = ttk.Entry(area_frame, width=25, font=('Arial', 10))
        self.area_entry.pack(side='right', fill='x', expand=True)

        # Загружаем текущую площадь
        current_area = self.app.df_bj[self.app.df_bj['Участок'] == site]['Площадь (га)'].values
        if len(current_area) > 0:
            self.area_entry.insert(0, str(current_area[0]))

        # Таблица доходов по месяцам
        ttk.Label(main_frame, text="Доходы по месяцам:",
                  font=('Arial', 11, 'bold')).pack(pady=(20, 10))

        # Создаем таблицу для редактирования доходов С ПРОКРУТКОЙ
        self.create_scrollable_income_table(main_frame)

        # Таблица трудозатрат по месяцам
        ttk.Label(main_frame, text="Трудозатраты по месяцам:",
                  font=('Arial', 11, 'bold')).pack(pady=(20, 10))

        # Создаем таблицу для редактирования трудозатрат С ПРОКРУТКОЙ
        self.create_scrollable_labor_table(main_frame)

        # Фрейм-заполнитель чтобы кнопки были в самом низу
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.pack(fill='both', expand=True)

        # Кнопки сохранения/отмены - ФИКСИРОВАННЫЕ ВНИЗУ
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))

        # Кнопка удаления с большей шириной
        ttk.Button(button_frame, text="Удалить ",
                   command=self.delete_site, width=15).pack(side='left', padx=5)

        ttk.Button(button_frame, text="Сохранить",
                   command=self.save_changes, width=12).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=self.dialog.destroy, width=12).pack(side='right', padx=5)

    def create_scrollable_income_table(self, parent):
        """Создает таблицу для редактирования доходов с прокруткой"""
        # Основной контейнер для таблицы
        table_outer_frame = ttk.Frame(parent)
        table_outer_frame.pack(fill='both', expand=True, pady=5)

        # Фрейм для заголовков таблицы
        header_frame = ttk.Frame(table_outer_frame)
        header_frame.pack(fill='x', pady=(0, 5))

        # Заголовки таблицы
        ttk.Label(header_frame, text="Месяц", width=15, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')
        ttk.Label(header_frame, text="Доход (тыс. руб./га)", width=20, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')

        # Фрейм для скроллбара и контента
        scroll_frame = ttk.Frame(table_outer_frame)
        scroll_frame.pack(fill='both', expand=True)

        # Canvas и скроллбар для прокрутки
        canvas = tk.Canvas(scroll_frame, height=150)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)

        # Фрейм для контента внутри canvas
        self.income_content_frame = ttk.Frame(canvas)

        # Настройка прокрутки
        canvas.create_window((0, 0), window=self.income_content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и скроллбара
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обновление скроллрегиона при изменении размера
        self.income_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Контейнер для полей ввода внутри content_frame
        income_container = ttk.Frame(self.income_content_frame)
        income_container.pack(fill='x')

        # Загружаем данные для этого участка
        site_income_data = self.app.df_c[self.app.df_c['Участок'] == self.site]
        self.income_entries = {}

        # Получаем все месяцы
        all_months = self.app.df_b['Месяц'].unique()

        for month in all_months:
            month = int(month)
            row_frame = ttk.Frame(income_container)
            row_frame.pack(fill='x', pady=2)

            ttk.Label(row_frame, text=str(month), width=15, anchor='w').pack(side='left')

            income_entry = ttk.Entry(row_frame, width=20, font=('Arial', 10))
            income_entry.pack(side='left')

            # Загружаем текущее значение
            month_data = site_income_data[site_income_data['Месяц'] == month]
            if len(month_data) > 0:
                income_value = month_data['Доход (тыс. руб./га)'].values[0]
                if income_value != "Не указано":
                    income_entry.insert(0, str(income_value))

            self.income_entries[month] = income_entry

    def create_scrollable_labor_table(self, parent):
        """Создает таблицу для редактирования трудозатрат с прокруткой"""
        # Основной контейнер для таблицы
        table_outer_frame = ttk.Frame(parent)
        table_outer_frame.pack(fill='both', expand=True, pady=5)

        # Фрейм для заголовков таблицы
        header_frame = ttk.Frame(table_outer_frame)
        header_frame.pack(fill='x', pady=(0, 5))

        # Заголовки таблицы
        ttk.Label(header_frame, text="Месяц", width=15, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')
        ttk.Label(header_frame, text="Трудозатраты (ч/га)", width=20, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left')

        # Фрейм для скроллбара и контента
        scroll_frame = ttk.Frame(table_outer_frame)
        scroll_frame.pack(fill='both', expand=True)

        # Canvas и скроллбар для прокрутки
        canvas = tk.Canvas(scroll_frame, height=150)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)

        # Фрейм для контента внутри canvas
        self.labor_content_frame = ttk.Frame(canvas)

        # Настройка прокрутки
        canvas.create_window((0, 0), window=self.labor_content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и скроллбара
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обновление скроллрегиона при изменении размера
        self.labor_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Контейнер для полей ввода внутри content_frame
        labor_container = ttk.Frame(self.labor_content_frame)
        labor_container.pack(fill='x')

        # Загружаем данные для этого участка
        site_labor_data = self.app.df_a[self.app.df_a['Участок'] == self.site]
        self.labor_entries = {}

        # Получаем все месяцы
        all_months = self.app.df_b['Месяц'].unique()

        for month in all_months:
            month = int(month)
            row_frame = ttk.Frame(labor_container)
            row_frame.pack(fill='x', pady=2)

            ttk.Label(row_frame, text=str(month), width=15, anchor='w').pack(side='left')

            labor_entry = ttk.Entry(row_frame, width=20, font=('Arial', 10))
            labor_entry.pack(side='left')

            # Загружаем текущее значение
            month_data = site_labor_data[site_labor_data['Месяц'] == month]
            if len(month_data) > 0:
                labor_value = month_data['Трудозатраты (ч/га)'].values[0]
                if labor_value != "Не указано":
                    labor_entry.insert(0, str(labor_value))

            self.labor_entries[month] = labor_entry

    def save_changes(self):
        """Сохраняет изменения"""
        try:
            # ПРОВЕРКА ПЛОЩАДИ
            if self.area_entry.get():
                area = float(self.area_entry.get())
                if area < 0:
                    messagebox.showerror("Ошибка", "Площадь не может быть отрицательной!")
                    return

            # ПРОВЕРКА ДОХОДОВ
            for month, entry in self.income_entries.items():
                if entry.get():
                    income = float(entry.get())
                    if income < 0:
                        messagebox.showerror("Ошибка", "Доход не может быть отрицательным!")
                        return

            # ПРОВЕРКА ТРУДОЗАТРАТ
            for month, entry in self.labor_entries.items():
                if entry.get():
                    labor = float(entry.get())
                    if labor < 0:
                        messagebox.showerror("Ошибка", "Трудозатраты не могут быть отрицательными!")

            # Сохраняем площадь
            if self.area_entry.get():
                area = float(self.area_entry.get())
                # Проверяем, существует ли уже запись для этого участка
                if self.site in self.app.df_bj['Участок'].values:
                    self.app.df_bj.loc[self.app.df_bj['Участок'] == self.site, 'Площадь (га)'] = area
                else:
                    # Создаем новую запись
                    new_area = pd.DataFrame({
                        'Участок': [self.site],
                        'Площадь (га)': [area]
                    })
                    self.app.df_bj = pd.concat([self.app.df_bj, new_area], ignore_index=True)

            # Сохраняем доходы
            for month, entry in self.income_entries.items():
                if entry.get():
                    income = float(entry.get())
                    mask = (self.app.df_c['Участок'] == self.site) & (self.app.df_c['Месяц'] == month)
                    if mask.any():
                        self.app.df_c.loc[mask, 'Доход (тыс. руб./га)'] = income
                    else:
                        # Создаем новую запись
                        new_income = pd.DataFrame({
                            'Участок': [self.site],
                            'Месяц': [month],
                            'Доход (тыс. руб./га)': [income]
                        })
                        self.app.df_c = pd.concat([self.app.df_c, new_income], ignore_index=True)
                else:
                    # Если поле пустое, удаляем запись если она существует
                    mask = (self.app.df_c['Участок'] == self.site) & (self.app.df_c['Месяц'] == month)
                    if mask.any():
                        self.app.df_c = self.app.df_c[~mask]

            # Сохраняем трудозатраты
            for month, entry in self.labor_entries.items():
                if entry.get():
                    labor = float(entry.get())
                    mask = (self.app.df_a['Участок'] == self.site) & (self.app.df_a['Месяц'] == month)
                    if mask.any():
                        self.app.df_a.loc[mask, 'Трудозатраты (ч/га)'] = labor
                    else:
                        # Создаем новую запись
                        new_labor = pd.DataFrame({
                            'Участок': [self.site],
                            'Месяц': [month],
                            'Трудозатраты (ч/га)': [labor]
                        })
                        self.app.df_a = pd.concat([self.app.df_a, new_labor], ignore_index=True)
                else:
                    # Если поле пустое, удаляем запись если она существует
                    mask = (self.app.df_a['Участок'] == self.site) & (self.app.df_a['Месяц'] == month)
                    if mask.any():
                        self.app.df_a = self.app.df_a[~mask]

            if self.app.save_data():
                self.app.refresh_data()
                self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Ошибка",
                                 "Проверьте правильность введенных данных! Все числовые поля должны содержать числа.")

    def delete_site(self):
        """Удаляет участок и все связанные данные"""
        result = messagebox.askyesno("Подтверждение удаления",
                                     f"Вы уверены, что хотите удалить участок {self.site}?\n\n"
                                     "Это действие удалит все данные, связанные с этим участком.")
        if result:
            self.app.remove_related_site_data(self.site)
            if self.app.save_data():
                self.app.refresh_data()
                self.dialog.destroy()
                messagebox.showinfo("Успех", f"Участок {self.site} и все связанные данные удалены!")


class AddSiteDialog:
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить участок")
        self.dialog.geometry("550x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Центрируем окно
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.income_entries = []

        # Основной фрейм
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(expand=True, fill='both', padx=20, pady=15)

        # Заголовок
        ttk.Label(main_frame, text="Добавление участка",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Фрейм для основных данных с ФИКСИРОВАННОЙ ШИРИНОЙ
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill='x', pady=10)

        # Номер участка - ширина как у таблицы
        site_frame = ttk.Frame(data_frame)
        site_frame.pack(fill='x', pady=8)
        ttk.Label(site_frame, text="Номер участка:", width=15, anchor='w').pack(side='left')
        self.site_entry = ttk.Entry(site_frame, width=35, font=('Arial', 10))  # Увеличили ширину
        self.site_entry.pack(side='right', fill='x', expand=True)

        # Площадь - ширина как у таблицы
        area_frame = ttk.Frame(data_frame)
        area_frame.pack(fill='x', pady=8)
        ttk.Label(area_frame, text="Площадь (га):", width=15, anchor='w').pack(side='left')
        self.area_entry = ttk.Entry(area_frame, width=35, font=('Arial', 10))  # Увеличили ширину
        self.area_entry.pack(side='right', fill='x', expand=True)

        # Заголовок таблицы
        ttk.Label(main_frame, text="Доходы по месяцам:",
                  font=('Arial', 11, 'bold')).pack(pady=(20, 10))

        # Основной контейнер для таблицы с ФИКСИРОВАННОЙ ШИРИНОЙ
        table_outer_frame = ttk.Frame(main_frame)
        table_outer_frame.pack(fill='x', pady=5)

        # Фрейм для заголовков таблицы
        header_frame = ttk.Frame(table_outer_frame)
        header_frame.pack(fill='x', pady=(0, 5))

        # Заголовки таблицы - ШИРИНА КАК У ОСНОВНЫХ ПОЛЕЙ
        ttk.Label(header_frame, text="Месяц", width=25, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 12))
        ttk.Label(header_frame, text="Доход (тыс. руб./га)", width=30, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))

        # Фрейм для скроллбара и контента с ФИКСИРОВАННОЙ ШИРИНОЙ
        scroll_frame = ttk.Frame(table_outer_frame)
        scroll_frame.pack(fill='x')

        # Canvas и скроллбар для прокрутки - ШИРИНА КАК У ОСНОВНЫХ ПОЛЕЙ
        self.canvas = tk.Canvas(scroll_frame, height=150, width=450)  # Фиксированная ширина
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)

        # Фрейм для контента внутри canvas
        self.income_content_frame = ttk.Frame(self.canvas)

        # Настройка прокрутки
        self.canvas.create_window((0, 0), window=self.income_content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и скроллбара
        self.canvas.pack(side="left", fill="x", expand=True)  # fill='x' вместо fill='both'
        scrollbar.pack(side="right", fill="y")

        # Обновление скроллрегиона при изменении размера
        self.income_content_frame.bind("<Configure>", self.on_frame_configure)

        # Контейнер для полей ввода внутри content_frame
        self.income_container = ttk.Frame(self.income_content_frame)
        self.income_container.pack(fill='x')

        # Добавляем первую строку
        self.add_income_field()

        # Кнопка добавления полей дохода - выравниваем по правому краю
        self.add_button_frame = ttk.Frame(main_frame)
        self.add_button_frame.pack(fill='x', pady=10)
        self.add_button = ttk.Button(self.add_button_frame, text="+ Добавить месяц",
                                     command=self.add_income_field)
        self.add_button.pack(side='top')

        # Фрейм-заполнитель чтобы кнопки были в самом низу
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.pack(fill='both', expand=True)

        # Кнопки сохранения/отмены - ФИКСИРОВАННЫЕ В НИЗУ
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=(20, 0))
        ttk.Button(action_frame, text="Отмена",
                   command=self.dialog.destroy, width=12).pack(side='left')
        ttk.Button(action_frame, text="Добавить",
                   command=self.add_site, width=12).pack(side='right')

    def on_frame_configure(self, event=None):
        """Обновление скроллрегиона при изменении размера фрейма"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_income_field(self):
        """Добавляет поля для ввода дохода за месяц"""
        # Проверяем ограничение в 12 строк
        if len(self.income_entries) >= 12:
            messagebox.showwarning("Предупреждение", "Можно добавить не более 12 месяцев!")
            return

        frame = ttk.Frame(self.income_container)
        frame.pack(fill='x', pady=2)

        # Месяц - ширина как у заголовков
        month_entry = ttk.Entry(frame, width=25, font=('Arial', 10), justify='left')
        month_entry.pack(side='left', padx=(0, 10))

        # Доход - ширина как у заголовков
        income_entry = ttk.Entry(frame, width=30, font=('Arial', 10), justify='left')
        income_entry.pack(side='left', padx=(0, 10))

        # Кнопка удаления строки (скрываем для первой строки)
        remove_btn = ttk.Button(frame, text="×", width=4,
                                command=lambda f=frame, me=month_entry, ie=income_entry: self.remove_income_field(f, me,
                                                                                                                  ie))
        remove_btn.pack(side='right', padx=(10, 0))

        self.income_entries.append((month_entry, income_entry, remove_btn))

        # Скрываем кнопку удаления если это первая строка
        if len(self.income_entries) == 1:
            remove_btn.pack_forget()

        # Отключаем кнопку добавления если достигли лимита
        if len(self.income_entries) >= 12:
            self.add_button.config(state='disabled')

        # Обновляем скроллрегион
        self.dialog.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_site(self):
        """Добавляет новый участок"""
        try:
            site = int(self.site_entry.get())
            area = float(self.area_entry.get())

            # ПРОВЕРКИ
            if site <= 0:
                messagebox.showerror("Ошибка", "Номер участка должен быть положительным!")
                return

            if area <= 0:
                messagebox.showerror("Ошибка", "Площадь должна быть положительной!")
                return

            # Проверяем, существует ли уже участок
            if site in self.app.df_bj['Участок'].values:
                messagebox.showerror("Ошибка", f"Участок {site} уже существует!")
                return

            # Добавляем в таблицу площадей с явным указанием типов
            new_area = pd.DataFrame({
                'Участок': [int(site)],  # Явно преобразуем в int
                'Площадь (га)': [float(area)]  # Явно преобразуем в float
            })
            self.app.df_bj = pd.concat([self.app.df_bj, new_area], ignore_index=True)

            # Добавляем доходы с явным указанием типов
            for month_entry, income_entry, _ in self.income_entries:
                if month_entry.get() and income_entry.get():
                    month = int(month_entry.get())
                    income = float(income_entry.get())

                    # ПРОВЕРКА МЕСЯЦА
                    if month < 1 or month > 12:
                        messagebox.showerror("Ошибка", "Месяц должен быть в диапазоне от 1 до 12!")
                        return

                    if income < 0:
                        messagebox.showerror("Ошибка", "Доход не может быть отрицательным!")
                        return

                    new_income = pd.DataFrame({
                        'Участок': [int(site)],  # Явно преобразуем в int
                        'Месяц': [int(month)],  # Явно преобразуем в int
                        'Доход (тыс. руб./га)': [float(income)]  # Явно преобразуем в float
                    })
                    self.app.df_c = pd.concat([self.app.df_c, new_income], ignore_index=True)

            months = [int(m) for m in self.app.df_b['Месяц'].unique()]  # Преобразуем месяцы

            # ДОБАВЛЯЕМ ДОХОДЫ "Не указано" для всех месяцев, которые не были указаны
            specified_months = [int(month_entry.get()) for month_entry, income_entry, _ in self.income_entries
                                if month_entry.get() and income_entry.get()]

            for month in months:
                if month not in specified_months:
                    new_income = pd.DataFrame({
                        'Участок': [int(site)],  # Явно преобразуем в int
                        'Месяц': [int(month)],  # Явно преобразуем в int
                        'Доход (тыс. руб./га)': ["Не указано"]  # Вместо числа - строка
                    })
                    self.app.df_c = pd.concat([self.app.df_c, new_income], ignore_index=True)

            # Добавляем трудозатраты как "Не указано" для всех месяцев
            for month in months:
                new_labor = pd.DataFrame({
                    'Участок': [int(site)],  # Явно преобразуем в int
                    'Месяц': [int(month)],  # Явно преобразуем в int
                    'Трудозатраты (ч/га)': ["Не указано"]  # Вместо числа - строка
                })
                self.app.df_a = pd.concat([self.app.df_a, new_labor], ignore_index=True)

            if self.app.save_data():
                self.app.refresh_data()
                self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Ошибка", "Проверьте правильность введенных данных! Все поля должны содержать числа.")


class AddMonthDialog:
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить месяц")
        self.dialog.geometry("550x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Центрируем окно
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.labor_entries = []

        # Основной фрейм
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(expand=True, fill='both', padx=20, pady=15)

        # Заголовок
        ttk.Label(main_frame, text="Добавление месяца",
                  font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # Фрейм для основных данных с ФИКСИРОВАННОЙ ШИРИНОЙ
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill='x', pady=10)

        # Номер месяца - ширина как у таблицы
        month_frame = ttk.Frame(data_frame)
        month_frame.pack(fill='x', pady=8)
        ttk.Label(month_frame, text="Номер месяца:", width=15, anchor='w').pack(side='left')
        self.month_entry = ttk.Entry(month_frame, width=35, font=('Arial', 10))  # Увеличили ширину
        self.month_entry.pack(side='right', fill='x', expand=True)

        # Ресурсы - ширина как у таблицы
        resources_frame = ttk.Frame(data_frame)
        resources_frame.pack(fill='x', pady=8)
        ttk.Label(resources_frame, text="Ресурсы (часы):", width=15, anchor='w').pack(side='left')
        self.resources_entry = ttk.Entry(resources_frame, width=35, font=('Arial', 10))  # Увеличили ширину
        self.resources_entry.pack(side='right', fill='x', expand=True)

        # Заголовок таблицы
        ttk.Label(main_frame, text="Трудозатраты по участкам:",
                  font=('Arial', 11, 'bold')).pack(pady=(20, 10))

        # Основной контейнер для таблицы с ФИКСИРОВАННОЙ ШИРИНОЙ
        table_outer_frame = ttk.Frame(main_frame)
        table_outer_frame.pack(fill='x', pady=5)

        # Фрейм для заголовков таблицы
        header_frame = ttk.Frame(table_outer_frame)
        header_frame.pack(fill='x', pady=(0, 5))

        # Заголовки таблицы - ШИРИНА КАК У ОСНОВНЫХ ПОЛЕЙ
        ttk.Label(header_frame, text="Участок", width=25, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        ttk.Label(header_frame, text="Трудозатраты (ч/га)", width=30, anchor='w',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))

        # Фрейм для скроллбара и контента с ФИКСИРОВАННОЙ ШИРИНОЙ
        scroll_frame = ttk.Frame(table_outer_frame)
        scroll_frame.pack(fill='x')

        # Canvas и скроллбар для прокрутки - ШИРИНА КАК У ОСНОВНЫХ ПОЛЕЙ
        self.canvas = tk.Canvas(scroll_frame, height=150, width=450)  # Фиксированная ширина
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)

        # Фрейм для контента внутри canvas
        self.labor_content_frame = ttk.Frame(self.canvas)

        # Настройка прокрутки
        self.canvas.create_window((0, 0), window=self.labor_content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и скроллбара
        self.canvas.pack(side="left", fill="x", expand=True)  # fill='x' вместо fill='both'
        scrollbar.pack(side="right", fill="y")

        # Обновление скроллрегиона при изменении размера
        self.labor_content_frame.bind("<Configure>", self.on_frame_configure)

        # Контейнер для полей ввода внутри content_frame
        self.labor_container = ttk.Frame(self.labor_content_frame)
        self.labor_container.pack(fill='x')

        # Добавляем первую строку
        self.add_labor_field()

        # Кнопка добавления полей трудозатрат - выравниваем по правому краю
        self.add_button_frame = ttk.Frame(main_frame)
        self.add_button_frame.pack(fill='x', pady=10)
        self.add_button = ttk.Button(self.add_button_frame, text="+ Добавить участок",
                                     command=self.add_labor_field)
        self.add_button.pack(side='top')

        # Фрейм-заполнитель чтобы кнопки были в самом низу
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.pack(fill='both', expand=True)

        # Кнопки сохранения/отмены - ФИКСИРОВАННЫЕ В НИЗУ
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=(20, 0))
        ttk.Button(action_frame, text="Отмена",
                   command=self.dialog.destroy, width=12).pack(side='left')
        ttk.Button(action_frame, text="Добавить",
                   command=self.add_month, width=12).pack(side='right')

    def on_frame_configure(self, event=None):
        """Обновление скроллрегиона при изменении размера фрейма"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_labor_field(self):
        """Добавляет поля для ввода трудозатрат по участку"""
        # Проверяем ограничение в 12 строк
        if len(self.labor_entries) >= 12:
            messagebox.showwarning("Предупреждение", "Можно добавить не более 12 участков!")
            return

        frame = ttk.Frame(self.labor_container)
        frame.pack(fill='x', pady=2)

        # Участок - ширина как у заголовков
        site_entry = ttk.Entry(frame, width=25, font=('Arial', 10), justify='left')
        site_entry.pack(side='left', padx=(0, 10))

        # Трудозатраты - ширина как у заголовков
        labor_entry = ttk.Entry(frame, width=30, font=('Arial', 10), justify='left')
        labor_entry.pack(side='left', padx=(0, 10))

        # Кнопка удаления строки (скрываем для первой строки)
        remove_btn = ttk.Button(frame, text="×", width=4,
                                command=lambda f=frame, se=site_entry, le=labor_entry: self.remove_labor_field(f, se,
                                                                                                               le))
        remove_btn.pack(side='right', padx=(10, 0))

        self.labor_entries.append((site_entry, labor_entry, remove_btn))

        # Скрываем кнопку удаления если это первая строка
        if len(self.labor_entries) == 1:
            remove_btn.pack_forget()

        # Отключаем кнопку добавления если достигли лимита
        if len(self.labor_entries) >= 30:
            self.add_button.config(state='disabled')

        # Обновляем скроллрегион
        self.dialog.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def remove_labor_field(self, frame, site_entry, labor_entry):
        """Удаляет поле ввода трудозатрат"""
        # Находим запись в списке
        entry_to_remove = None
        for entry in self.labor_entries:
            if entry[0] == site_entry and entry[1] == labor_entry:
                entry_to_remove = entry
                break

        if entry_to_remove and len(self.labor_entries) > 1:  # Запрещаем удаление последней строки
            frame.destroy()
            self.labor_entries.remove(entry_to_remove)

            # Включаем кнопку добавления при удалении строки
            if len(self.labor_entries) < 30:
                self.add_button.config(state='normal')

            # Показываем кнопку удаления у первой строки, если осталась только одна строка
            if len(self.labor_entries) == 1:
                self.labor_entries[0][2].pack_forget()

            # Обновляем скроллрегион
            self.dialog.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_month(self):
        """Добавляет новый месяц"""
        try:
            month = int(self.month_entry.get())
            resources = float(self.resources_entry.get())

            # ПРОВЕРКИ
            if month < 1 or month > 12:
                messagebox.showerror("Ошибка", "Месяц должен быть в диапазоне от 1 до 12!")
                return

            if resources <= 0:
                messagebox.showerror("Ошибка", "Ресурсы должны быть положительными!")
                return

            # Проверяем, существует ли уже месяц
            if month in self.app.df_b['Месяц'].values:
                messagebox.showerror("Ошибка", f"Месяц {month} уже существует!")
                return

            # Добавляем в таблицу ресурсов с явным указанием типов
            new_resources = pd.DataFrame({
                'Месяц': [int(month)],  # Явно преобразуем в int
                'Ресурсы (часы)': [float(resources)]  # Явно преобразуем в float
            })
            self.app.df_b = pd.concat([self.app.df_b, new_resources], ignore_index=True)

            # Добавляем трудозатраты с явным указанием типов
            for site_entry, labor_entry, _ in self.labor_entries:
                if site_entry.get() and labor_entry.get():
                    site = int(site_entry.get())
                    labor = float(labor_entry.get())

                    # ПРОВЕРКА УЧАСТКА
                    if site <= 0:
                        messagebox.showerror("Ошибка", "Номер участка должен быть положительным!")
                        return

                    # ПРОВЕРКА ТРУДОЗАТРАТ
                    if labor < 0:
                        messagebox.showerror("Ошибка", "Трудозатраты не могут быть отрицательными!")
                        return

                    new_labor = pd.DataFrame({
                        'Участок': [int(site)],  # Явно преобразуем в int
                        'Месяц': [int(month)],  # Явно преобразуем в int
                        'Трудозатраты (ч/га)': [float(labor)]  # Явно преобразуем в float
                    })
                    self.app.df_a = pd.concat([self.app.df_a, new_labor], ignore_index=True)

            sites = [int(s) for s in self.app.df_bj['Участок'].unique()]  # Преобразуем участки

            # ДОБАВЛЯЕМ ТРУДОЗАТРАТЫ "Не указано" для всех участков, которые не были указаны
            specified_sites = [int(site_entry.get()) for site_entry, labor_entry, _ in self.labor_entries
                               if site_entry.get() and labor_entry.get()]

            for site in sites:
                if site not in specified_sites:
                    new_labor = pd.DataFrame({
                        'Участок': [int(site)],  # Явно преобразуем в int
                        'Месяц': [int(month)],  # Явно преобразуем в int
                        'Трудозатраты (ч/га)': ["Не указано"]  # Вместо числа - строка
                    })
                    self.app.df_a = pd.concat([self.app.df_a, new_labor], ignore_index=True)

            # Добавляем доходы как "Не указано" для всех участков
            for site in sites:
                new_income = pd.DataFrame({
                    'Участок': [int(site)],  # Явно преобразуем в int
                    'Месяц': [int(month)],  # Явно преобразуем в int
                    'Доход (тыс. руб./га)': ["Не указано"]  # Вместо числа - строка
                })
                self.app.df_c = pd.concat([self.app.df_c, new_income], ignore_index=True)

            if self.app.save_data():
                self.app.refresh_data()
                self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Ошибка", "Проверьте правильность введенных данных! Все поля должны содержать числа.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ForestHarvestingApp(root)
    root.mainloop()