import yaml
import os
import re
import sys
import glob
import random
import json
import requests
import threading
import webbrowser
from PIL import Image as PILImage
from PIL import ImageTk
from tkinter import *
from tkinter import messagebox, ttk
import tkinter as tk


class ReagentCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.current_version = "1.45215"
        self.update_messages = [
            "Доступно обновление на GitHub! ⬆️",
            "Обновись! Новые фичи ждут! 🚀",
            "Обновления не сделают тебе больно 😇",
            "Твоя версия устарела! 🕒",
            "Новая версия уже вышла! 🎉",
            "Не пропусти важные изменения! 🔔",
            "Новая версия — как экзотермическая реакция! 🔥",
            "Обнови свой реактив! 🧪",
            "Требуется катализатор обновления! ⚗️",
            "Не будь инертным газом! 💨",
            "Пофикшены баги, добавлены котики 🐈",
            "git pull origin main! 🌿",
            "Собрано с любовью и кофеином ☕",
            "Нет багов — нет проблем 🐞",
            "Выбери красную таблетку обновлений 🔴",
            "Этот апдейт одобрил Рик Санчеz! 🔬",
            "sudo apt-get upgrade ⚙️",
            "404 - Версия не найдена ❌",
            "Доктор, я обновил TARDIS! 🕰️",
            "Теперь с поддержкой ⑨⑨⑨⑨⑨⑨⑨⑨⑨⑨ 🦋",
            "Пора на орбитальный апдейт! 🛰️",
            "Чё каво, апдейт есть? 👀",
            "Это не баг, а фича! 🪲",
            "Аманда, у тебя фрезон убежал! 🥶",
            "А если серьёзно, я скучаю по Эмгыр де Шнайдер 🐱"
        ]
        self.root.title(f"SS14 Химический калькулятор by i_love_Megumin v{self.current_version}")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'img/icon.ico'
        self.root.iconbitmap(icon_path)
        self.root.geometry("900x620")
        self.root.configure(bg="#2e2e2e")
        self.recipe_categories = {
            'medicine': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/medicine.yml',
            'chemicals': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/chemicals.yml',
            'pyrotechnic': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/pyrotechnic.yml',
            'drinks': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/a5444e854b78c6cc09a653f550c82c9a72f26e68/Resources/Prototypes/Recipes/Reactions/drinks.yml',
            'ss220 medicine': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/9fad48b5ffce66ea9fa00e3b7a1f29658dba6657/Resources/Prototypes/SS220/Recipes/Reactions/medicine.yml',
            'ss220 drinks': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/a5444e854b78c6cc09a653f550c82c9a72f26e68/Resources/Prototypes/SS220/Recipes/Reactions/drinks.yml'
        }
        self.translation_files = {
            'medicine': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/medicine.ftl',
            'chemicals': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/chemicals.ftl',
            'pyrotechnic': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/pyrotechnic.ftl',
            'biological': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/biological.ftl',
            'botany': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/botany.ftl',
            'cleaning': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/cleaning.ftl',
            'elements': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/elements.ftl',
            'fun': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/fun.ftl',
            'gases': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/gases.ftl',
            'narcotics': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/narcotics.ftl',
            'toxins': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/toxins.ftl',
            'alcohol': 'https://raw.githubusercontent.com/space-syndicate/space-station-14/c5fffb0b73c7f5c11e41b3996a41a2722c978ab4/Resources/Locale/ru-RU/reagents/meta/consumable/drink/alcohol.ftl',
            'drinks': 'https://raw.githubusercontent.com/space-syndicate/space-station-14/c5fffb0b73c7f5c11e41b3996a41a2722c978ab4/Resources/Locale/ru-RU/reagents/meta/consumable/drink/drinks.ftl',
            'juice': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/consumable/drink/juice.ftl',
            'soda': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/consumable/drink/soda.ftl',
            'ingredients': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/consumable/food/ingredients.ftl',
            'ss220 drinks': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/ss220/reagents/meta/drinks.ftl',
            'condiments': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/reagents/meta/consumable/food/condiments.ftl',
            'ss220 medicine': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/fa0479912413b71c64d7fec4373fdd0b5bbcec90/Resources/Locale/ru-RU/ss220/reagents/meta/medicine.ftl',
        }
        self.search_var = tk.StringVar()
        self.search_results = []
        self.gif_frames = []
        self.current_gif_frame = 0
        self.animation_job = None
        self.resize_in_progress = False
        self.frame_delay = 150
        self.recipes = []
        self.recipe_dict = {}
        self.overlay_opacity = 0.95
        self.language = 'ru'
        self.depth_colors = [
            "#FFFFFF", "#4EC9B0", "#569CD6",
            "#B5CEA8", "#CE9178", "#C586C0"
        ]
        self.COLOR_NAMES = {
            "Белый": "#FFFFFF",
            "Бирюзовый": "#4EC9B0",
            "Голубой": "#569CD6",
            "Оливковый": "#B5CEA8",
            "Коралловый": "#CE9178",
            "Лаванда": "#C586C0",
            "Лосось": "#FFA07A",
            "Мята": "#98FB98",
            "Сирень": "#DDA0DD",
            "Золото": "#FFD700",
            "Небо": "#87CEEB",
            "Розовый": "#FF69B4",
            "Бежевый": "#F5F5DC",
            "Кремовый": "#FFFDD0",
            "Серый": "#D3D3D3",
            "Светло синий": "#AEC6CF",
            "Светло зелёный": "#77DD77",
            "Светло лиловый": "#CDA4DE"
        }
        self.color_vars = []
        self.color_previews = []
        self.custom_colors = self.depth_colors.copy()
        self.custom_recipe_links = {}
        self.custom_translation_links = {}
        self.load_images()
        self.setup_styles()
        self.load_settings()
        self.create_widgets()
        self.setup_directories()
        self.load_translations()
        self.load_recipes()
        self.setup_clipboard_handlers()
        self.overlay_window = None
        self.overlay_content = None
        self.progress_visible = None
        self.settings_win = None
        self.check_for_updates_async()


    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.',
                        background="#2e2e2e",
                        foreground="white",
                        fieldbackground="#4f4f4f",
                        bordercolor="#2e2e2e",
                        focuscolor=[])
        style.configure("Custom.TLabelframe",
                        background="#2e2e2e",
                        foreground="white",
                        borderwidth=0,
                        relief='flat')
        style.configure("Custom.TLabelframe.Label",
                        background="#2e2e2e",
                        foreground="white")
        style.configure('Red.TButton',
                        background="#d9534f",
                        foreground="white",
                        font=("Arial", 12),
                        borderwidth=0)
        style.map('Red.TButton',
                        background=[('active', '#c9302c'), ('!active', '#d9534f')])
        style.configure('TCombobox',
                        background="#454545",
                        foreground="white",
                        fieldbackground="#4f4f4f",
                        selectbackground="#5e5e5e",
                        selectforeground="white",
                        bordercolor="#454545",
                        arrowcolor="white",
                        arrowsize=12,
                        padding=5)
        style.map('TCombobox',
                        fieldbackground=[('readonly', '#4f4f4f')],
                        selectbackground=[('readonly', '#4f4f4f')],
                        selectforeground=[('readonly', 'white')],
                        background=[('active', '#5e5e5e')],
                        bordercolor=[('active', '#6e6e6e'), ('focus', '#1e7e34')])
        style.configure("Custom.Treeview",
                        background="#3c3c3c",
                        foreground="white",
                        fieldbackground="#3c3c3c",
                        borderwidth=0)
        style.configure("Custom.Treeview.Heading",
                        background="#454545",
                        foreground="white",
                        relief="flat",
                        font=('Arial', 10, 'bold'))
        style.map("Custom.Treeview.Heading",
                        background=[('active', '#5e5e5e')],
                        foreground=[('active', 'white')])
        style.map("Custom.Treeview",
                        background=[('selected', '#1e7e34')])
        style.configure("Custom.TButton",
                        background="#454545",
                        foreground="white",
                        bordercolor="#454545")
        style.map("Custom.TButton",
                        background=[('active', '#5e5e5e')])
        style.configure("Custom.Toplevel",
                        background="#2e2e2e")


    def load_translations(self):
        self.translations = {}
        for filename in os.listdir('translations'):
            if filename.endswith('.ftl'):
                try:
                    with open(os.path.join('translations', filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                        entries = re.findall(
                            r'^reagent-name-([\w-]+)\s*=\s*(.+)$',
                            content,
                            re.MULTILINE
                        )
                        for eng_name, translation in entries:
                            normalized_id = eng_name.replace('-', '').lower()

                            translation = translation.strip().strip('"')
                            if translation:
                                translation = translation[0].upper() + translation[1:]

                            self.translations[normalized_id] = translation

                    print(f"Загружено переводов из {filename}: {len(entries)}")
                except Exception as e:
                    print(f"Ошибка загрузки перевода {filename}: {str(e)}")


    def start_resize(self, event, side):
        self.overlay_window._resize_data = {
            'side': side,
            'start_x': event.x_root,
            'start_y': event.y_root,
            'start_w': self.overlay_window.winfo_width(),
            'start_h': self.overlay_window.winfo_height(),
            'start_x_pos': self.overlay_window.winfo_x(),
            'start_y_pos': self.overlay_window.winfo_y()
        }


    def on_resize(self, event, side):
        if not hasattr(self.overlay_window, '_resize_data'):
            return

        data = self.overlay_window._resize_data
        dx = event.x_root - data['start_x']
        dy = event.y_root - data['start_y']

        x = data['start_x_pos']
        y = data['start_y_pos']
        width = data['start_w']
        height = data['start_h']

        if 'n' in side:
            height -= dy
            y += dy
            height = max(height, self.overlay_window.minsize()[1])
            y = min(y, data['start_y_pos'] + data['start_h'] - self.overlay_window.minsize()[1])
        if 's' in side:
            height += dy
            height = max(height, self.overlay_window.minsize()[1])
        if 'w' in side:
            width -= dx
            x += dx
            width = max(width, self.overlay_window.minsize()[0])
            x = min(x, data['start_x_pos'] + data['start_w'] - self.overlay_window.minsize()[0])
        if 'e' in side:
            width += dx
            width = max(width, self.overlay_window.minsize()[0])

        if side in ('nw', 'ne', 'sw', 'se'):
            if 'n' in side:
                height = data['start_h'] - dy
                y = data['start_y_pos'] + dy
            if 's' in side:
                height = data['start_h'] + dy
            if 'w' in side:
                width = data['start_w'] - dx
                x = data['start_x_pos'] + dx
            if 'e' in side:
                width = data['start_w'] + dx

        self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")


    def toggle_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            self.overlay_window = None
            self.overlay_btn.config(text="🖥️ Показать оверлей")
        else:
            self.create_overlay_window()
            self.overlay_btn.config(text="🖥️ Скрыть оверлей")


    def on_search_keyrelease(self, event):
        if event.keysym in ('Return', 'Up', 'Down', 'Left', 'Right'):
            return
        search_term = self.search_var.get().lower()
        if not search_term:
            self.search_entry['values'] = []
            return

        results = []
        for recipe in self.recipes:
            normalized_id = recipe['id'].lower().replace(' ', '')
            translated = self.translations.get(normalized_id, recipe['id']).lower()

            if search_term in translated or search_term in recipe['id'].lower():
                results.append({
                    'translated': self.translations.get(normalized_id, recipe['id']),
                    'id': recipe['id'],
                    'category': recipe['category']
                })

        max_results = 15
        displayed_results = [f"{res['translated']} ({res['category']})" for res in results[:max_results]]
        self.search_entry['values'] = displayed_results
        self.search_results = results[:max_results]


    def on_search_select(self, event):
        if not self.search_results:
            return

        index = self.search_entry.current()
        if index == -1:
            return

        selected = self.search_results[index]
        self.category_var.set(selected['category'])
        self.update_recipes_list()

        translated_names = [self.recipe_map.get(name) for name in self.recipe_combobox['values']]
        try:
            idx = translated_names.index(selected['id'])
            self.recipe_var.set(self.recipe_combobox['values'][idx])
        except ValueError:
            return

        self.root.after(100, self.calculate_reactants)


    def on_search_enter(self, event):
        search_term = self.search_var.get().strip().lower()
        if not search_term:
            return

        best_match = self.get_best_match(search_term)
        if best_match:
            self.category_var.set(best_match['category'])
            self.update_recipes_list()

            translated_names = self.recipe_combobox['values']
            target_name = self.translations.get(
                best_match['id'].lower().replace(' ', ''),
                best_match['id']
            )

            if target_name in translated_names:
                self.recipe_var.set(target_name)
                self.calculate_reactants()
            else:
                if translated_names:
                    self.recipe_var.set(translated_names[0])
                    self.calculate_reactants()


    def get_best_match(self, search_term):
        best_score = -1
        best_match = None
        for recipe in self.recipes:
            normalized_id = recipe['id'].lower().replace(' ', '')
            translated = self.translations.get(normalized_id, recipe['id']).lower()

            score = 0
            if search_term in translated:
                score += 2
            if search_term in recipe['id'].lower():
                score += 1
            if translated.startswith(search_term):
                score += 1

            if score > best_score:
                best_score = score
                best_match = recipe

        return best_match


    def create_overlay_window(self):
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.wm_attributes("-topmost", True)
        self.overlay_window.configure(bg='#2e2e2e')
        self.overlay_window.overrideredirect(True)
        self.overlay_window.geometry("300x400+100+100")
        self.overlay_window.minsize(200, 150)
        self.overlay_window.wm_attributes("-alpha", self.overlay_opacity)

        main_frame = tk.Frame(self.overlay_window, bg='#2e2e2e')
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(main_frame, bg='#454545', height=30)
        title_bar.pack(fill=tk.X)

        title_label = tk.Label(title_bar, text="Рецепт поверх окон", bg='#454545', fg='white')
        title_label.pack(side=tk.LEFT, padx=10)

        close_btn = tk.Button(title_bar, text="×", command=self.toggle_overlay,
                            bg='#ff4444', fg='white', bd=0, padx=10)
        close_btn.pack(side=tk.RIGHT)

        self.overlay_content = tk.Text(main_frame, wrap=tk.WORD, font=("Courier New", 10),
                                     bg="#3c3c3c", fg="white", padx=10, pady=10)
        self.overlay_content.pack(fill=tk.BOTH, expand=True)

        self.setup_resize_zones(main_frame)

        title_bar.bind("<ButtonPress-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)
        title_label.bind("<ButtonPress-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.on_move)

        self.update_overlay_content()


    def setup_resize_zones(self, parent):
        resize_size = 2
        bg_color = '#2e2e2e'

        resize_frames = {
            'n': tk.Frame(parent, bg=bg_color, height=resize_size, cursor='sb_v_double_arrow',
                          borderwidth=0, highlightthickness=0),
            's': tk.Frame(parent, bg=bg_color, height=resize_size, cursor='sb_v_double_arrow',
                          borderwidth=0, highlightthickness=0),
            'e': tk.Frame(parent, bg=bg_color, width=resize_size, cursor='sb_h_double_arrow',
                          borderwidth=0, highlightthickness=0),
            'w': tk.Frame(parent, bg=bg_color, width=resize_size, cursor='sb_h_double_arrow',
                          borderwidth=0, highlightthickness=0),
            'nw': tk.Frame(parent, bg=bg_color, width=resize_size * 2, height=resize_size * 2,
                           cursor='size_nw_se', borderwidth=0, highlightthickness=0),
            'ne': tk.Frame(parent, bg=bg_color, width=resize_size * 2, height=resize_size * 2,
                           cursor='size_ne_sw', borderwidth=0, highlightthickness=0),
            'sw': tk.Frame(parent, bg=bg_color, width=resize_size * 2, height=resize_size * 2,
                           cursor='size_ne_sw', borderwidth=0, highlightthickness=0),
            'se': tk.Frame(parent, bg=bg_color, width=resize_size * 2, height=resize_size * 2,
                           cursor='size_nw_se', borderwidth=0, highlightthickness=0)
        }

        resize_frames['n'].place(relx=0, rely=0, relwidth=1)
        resize_frames['s'].place(relx=0, rely=1, relwidth=1, anchor='sw')
        resize_frames['e'].place(relx=1, rely=0, relheight=1, anchor='ne')
        resize_frames['w'].place(relx=0, rely=0, relheight=1)

        resize_frames['nw'].place(relx=0, rely=0)
        resize_frames['ne'].place(relx=1, rely=0, anchor='ne')
        resize_frames['sw'].place(relx=0, rely=1, anchor='sw')
        resize_frames['se'].place(relx=1, rely=1, anchor='se')

        for side, frame in resize_frames.items():
            frame.bind("<ButtonPress-1>", lambda e, s=side: self.start_resize(e, s))
            frame.bind("<B1-Motion>", lambda e, s=side: self.on_resize(e, s))


    def create_corner_grip(self, parent, corner, size):
        cursors = {
            "nw": "size_nw_se",
            "ne": "size_ne_sw",
            "sw": "size_ne_sw",
            "se": "size_nw_se"
        }
        frame = tk.Frame(parent, bg='#2e2e2e', width=size, height=size,
                         cursor=cursors[corner], borderwidth=0, highlightthickness=0)

        if corner == "nw":
            frame.place(relx=0.0, rely=0.0, anchor=tk.NW)
        elif corner == "ne":
            frame.place(relx=1.0, rely=0.0, anchor=tk.NE)
        elif corner == "sw":
            frame.place(relx=0.0, rely=1.0, anchor=tk.SW)
        elif corner == "se":
            frame.place(relx=1.0, rely=1.0, anchor=tk.SE)

        frame.bind("<Button-1>", lambda e, c=corner: self.start_resize(e, c))
        frame.bind("<B1-Motion>", lambda e, c=corner: self.on_resize(e, c))


    def start_move(self, event):
        self.overlay_window._offset_x = event.x
        self.overlay_window._offset_y = event.y


    def on_move(self, event):
        x = self.overlay_window.winfo_x() + (event.x - self.overlay_window._offset_x)
        y = self.overlay_window.winfo_y() + (event.y - self.overlay_window._offset_y)
        self.overlay_window.geometry(f"+{x}+{y}")


    def update_overlay_content(self):
        if not self.overlay_window or not self.overlay_content:
            return

        main_content = self.result_text.get("1.0", tk.END)
        self.overlay_content.delete("1.0", tk.END)
        self.overlay_content.insert(tk.END, main_content)

        for tag in self.result_text.tag_names():
            self.overlay_content.tag_config(tag, foreground=self.result_text.tag_cget(tag, "foreground"))
            ranges = self.result_text.tag_ranges(tag)
            for i in range(0, len(ranges), 2):
                start = ranges[i]
                end = ranges[i+1]
                self.overlay_content.tag_add(tag, start, end)


    def setup_directories(self, upd = False):
        ood = False
        if not os.path.exists('recipes'):
            os.makedirs('recipes')
            ood = True
        if not os.path.exists('translations'):
            os.makedirs('translations')
            ood = True
        if ood and not upd:
            self.update_data_async()


    def load_images(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        try:
            gif_files = glob.glob(os.path.join(base_path, 'img', '[0-9]*.gif'))
            if not gif_files:
                raise FileNotFoundError("No GIF files found")

            selected_gif = random.choice(gif_files)
            print(f"Loading GIF: {selected_gif}")

            self.original_gif = PILImage.open(selected_gif)

            self.prepare_gif_frames(self.original_gif.size)
            self.current_gif_frame = 0
            self.animation_job = None

            total_frames = self.original_gif.n_frames
            frame_indices = range(0, total_frames, 2 if total_frames > 30 else 1)

        except Exception as e:
            print(f"Ошибка загрузки аватара: {str(e)}")
            self.gif_frames = []

        try:
            discord_path = os.path.join(base_path, 'img', 'discord.png')
            self.discord_image = ImageTk.PhotoImage(PILImage.open(discord_path).resize((40, 40)))
        except Exception as e:
            print(f"Ошибка загрузки Discord: {str(e)}")
            self.discord_image = None


    def animate_gif(self):
        if not self.gif_frames or self.resize_in_progress:
            return

        self.current_gif_frame = (self.current_gif_frame + 1) % len(self.gif_frames)
        try:
            self.avatar_label.configure(image=self.gif_frames[self.current_gif_frame])
        except tk.TclError:
            return

        self.animation_job = self.root.after(self.frame_delay, self.animate_gif)


    def prepare_gif_frames(self, container_size):
        self.gif_frames = []

        orig_width, orig_height = self.original_gif.size
        ratio = min(container_size[0] / orig_width, container_size[1] / orig_height)
        new_size = (int(orig_width * ratio), int(orig_height * ratio))

        for frame in range(self.original_gif.n_frames):
            self.original_gif.seek(frame)
            frame_img = self.original_gif.copy()

            frame_img = frame_img.resize(new_size, PILImage.Resampling.LANCZOS)

            canvas = PILImage.new('RGBA', container_size, (0, 0, 0, 0))
            position = (
                (container_size[0] - new_size[0]) // 2,
                (container_size[1] - new_size[1]) // 2
            )
            canvas.paste(frame_img, position)

            self.gif_frames.append(ImageTk.PhotoImage(canvas))


    def update_avatar_animation(self):
        if not self.gif_frames:
            return

        self.current_gif_frame = (self.current_gif_frame + 1) % len(self.gif_frames)
        if hasattr(self, 'avatar_label') and self.avatar_label.winfo_exists():
            try:
                self.avatar_label.configure(image=self.gif_frames[self.current_gif_frame])
            except tk.TclError:
                pass

        delay = self.original_gif.info.get('duration', 100)
        self.animation_job = self.root.after(delay, self.update_avatar_animation)


    def load_recipes(self):
        self.recipes = []
        self.recipe_dict = {}

        for filename in os.listdir('recipes'):
            if filename.endswith('.yml'):
                try:
                    with open(os.path.join('recipes', filename), 'r', encoding='utf-8') as f:
                        recipes = yaml.load(f, Loader=self.custom_yaml_loader)
                        if recipes:
                            category = filename.replace('.yml', '')
                            for recipe in self.filter_recipes(recipes):
                                recipe_id = recipe.get('id', '')
                                if recipe_id.endswith("Drink"):
                                    recipe['id'] = recipe_id[:-len("Drink")]
                                recipe['category'] = category
                                self.recipes.append(recipe)
                    print(f'{filename} загружен!')
                except Exception as e:
                    print(f"Ошибка загрузки {filename}: {e}")

        self.recipe_dict = {recipe['id']: recipe for recipe in self.recipes}
        self.recipes.sort(key=lambda x: x['id'].lower())


    def filter_recipes(self, raw_data):
        for entry in raw_data:
            if isinstance(entry, dict) and entry.get("type") == "reaction" and "id" in entry and "reactants" in entry:
                yield entry


    def custom_yaml_loader(self, stream):
        class CustomLoader(yaml.SafeLoader):
            def handle_tag(self, tag, node):
                if tag.startswith('!type:'):
                    return self.construct_mapping(node)
                return super().handle_tag(tag, node)

        def construct_typed_effect(loader, node):
            if isinstance(node, yaml.MappingNode):
                return loader.construct_mapping(node)
            return loader.construct_scalar(node)

        CustomLoader.add_multi_constructor('!type:', lambda loader, tag_suffix, node: {
            'type': tag_suffix,
            **loader.construct_mapping(node)
        } if isinstance(node, yaml.MappingNode) else {'type': tag_suffix})

        CustomLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            lambda loader, node: loader.construct_mapping(node)
        )

        return CustomLoader(stream)


    def safe_resize(self, event):
        if not hasattr(self, 'avatar_container'):
            return

        if self.resize_in_progress:
            return

        self.resize_in_progress = True

        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

        container_width = self.avatar_container.winfo_width()
        container_height = self.avatar_container.winfo_height()

        if container_width <= 0 or container_height <= 0:
            return

        square_size = max(container_width, container_height)

        if square_size != getattr(self, 'current_canvas_size', 0):
            self.current_canvas_size = square_size
            self.prepare_gif_frames((square_size, square_size))
            self.current_gif_frame = 0

            if self.gif_frames:
                try:
                    self.avatar_label.configure(image=self.gif_frames[0])
                except tk.TclError:
                    pass


    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#2e2e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        left_panel = tk.Frame(main_frame, bg="#2e2e2e")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        search_frame = tk.Frame(left_panel, bg="#2e2e2e")
        search_frame.pack(fill=tk.X, pady=5)

        tk.Label(search_frame,
                text="Поиск",
                font=("Arial", 13),
                fg="white",
                bg="#2e2e2e").pack(anchor=tk.W)

        self.search_entry = ttk.Combobox(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 13),
            values=[],
            state="normal",
            foreground="white",
        )
        self.search_entry.pack(fill=tk.X)
        self.search_entry.bind("<KeyRelease>", self.on_search_keyrelease)
        self.search_entry.bind("<<ComboboxSelected>>", self.on_search_select)
        self.search_entry.bind("<Return>", self.on_search_enter)
        self.search_entry['values'] = []

        self.category_var = tk.StringVar()
        category_frame = tk.Frame(left_panel, bg="#2e2e2e")
        category_frame.pack(fill=tk.X, pady=5)

        bottom_frame = tk.Frame(self.root, bg="#2e2e2e", height=40)
        bottom_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        bottom_frame.pack_propagate(False)

        left_bottom = tk.Frame(bottom_frame, bg="#2e2e2e")
        left_bottom.pack(side=tk.LEFT)

        right_buttons = tk.Frame(bottom_frame, bg="#2e2e2e")
        right_buttons.pack(side=tk.RIGHT)

        self.overlay_btn = tk.Button(
            right_buttons,
            text="🖥️ Показать оверлей",
            command=self.toggle_overlay,
            bg="#454545",
            fg="white",
            font=("Arial", 10)
        )
        self.overlay_btn.pack(side=tk.LEFT, padx=2)

        github_btn = tk.Button(
            right_buttons,
            text="GitHub",
            command=lambda: webbrowser.open("https://github.com/R-R0S/ss14-calc"),
            bg="#333333",
            fg="white",
            font=("Arial", 10)
        )
        github_btn.pack(side=tk.LEFT, padx=5)

        self.settings_btn = tk.Button(
            right_buttons,
            text="⚙️",
            command=self.create_settings_window,
            bg="#333333",
            fg="white",
            font=("Arial", 10))
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(category_frame,
                text="Категория",
                font=("Arial", 13),
                fg="white",
                bg="#2e2e2e").pack(anchor=tk.W)

        self.category_combobox = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=list(self.recipe_categories.keys()),
            state="readonly",
            font=("Arial", 13))
        self.category_combobox.pack(fill=tk.X, pady=5)
        self.category_combobox.bind("<<ComboboxSelected>>", self.update_recipes_list)

        self.recipe_var = tk.StringVar()
        recipe_frame = tk.Frame(left_panel, bg="#2e2e2e")
        recipe_frame.pack(fill=tk.X, pady=5)

        tk.Label(recipe_frame,
                text="Рецепт",
                font=("Arial", 13),
                fg="white",
                bg="#2e2e2e").pack(anchor=tk.W)

        self.recipe_combobox = ttk.Combobox(
            recipe_frame,
            textvariable=self.recipe_var,
            state="readonly",
            font=("Arial", 13))
        self.recipe_combobox.pack(fill=tk.X, pady=5)

        amount_frame = tk.Frame(left_panel, bg="#2e2e2e")
        amount_frame.pack(fill=tk.X, pady=5)

        tk.Label(amount_frame,
                 text="Количество",
                 font=("Arial", 13),
                 fg="white",
                 bg="#2e2e2e").pack(anchor=tk.W)

        self.amount_entry = tk.Entry(
            amount_frame,
            font=("Arial", 13),
            bg="#4f4f4f",
            fg="white"
        )
        self.amount_entry.pack(fill=tk.X, pady=5)
        self.amount_entry.insert(0, "90")

        button_frame = tk.Frame(left_panel, bg="#2e2e2e")
        button_frame.pack(fill=tk.X, pady=10)

        self.calculate_btn = tk.Button(
            button_frame,
            text="Рассчитать",
            command=self.calculate_reactants,
            bg="#1e7e34",
            fg="white",
            font=("Arial", 12)
        )
        self.calculate_btn.pack(side=tk.LEFT, padx=5)

        self.update_btn = tk.Button(
            button_frame,
            text="Обновить данные",
            command=self.update_data_async,
            bg="#0067a1",
            fg="white",
            font=("Arial", 12)
        )
        self.update_btn.pack(side=tk.RIGHT, padx=5)

        self.avatar_container = tk.Frame(
            left_panel,
            bg="#2e2e2e",
            width=0,
            height=0
        )
        self.avatar_container.pack_propagate(False)
        self.avatar_container.pack(fill=tk.BOTH, expand=True, pady=5)

        if hasattr(self, 'gif_frames') and self.gif_frames:
            self.avatar_label = tk.Label(
                self.avatar_container,
                image=self.gif_frames[0],
                bg="#2e2e2e"
            )
            self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")
            self.animate_gif()

        self.avatar_container.bind("<Configure>", self.safe_resize)

        if self.gif_frames:
            self.avatar_label = tk.Label(
                self.avatar_container,
                image=self.gif_frames[0],
                bg="#2e2e2e"
            )
            self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")
            self.update_avatar_animation()

        discord_frame = tk.Frame(left_bottom, bg="#2e2e2e")
        discord_frame.pack(side=tk.LEFT, padx=5)

        if hasattr(self, 'discord_image') and self.discord_image:
            discord_btn = tk.Label(
                discord_frame,
                image=self.discord_image,
                bg="#2e2e2e",
                cursor="hand2"
            )
            discord_btn.pack(side=tk.LEFT)
            discord_btn.bind("<Button-1>", lambda e: webbrowser.open("https://discord.com/users/317692089355862016"))

        tk.Label(
            discord_frame,
            text=f"©FelinidsPower,\n «Надежда» - 3025г.",
            fg="white",
            bg="#2e2e2e",
            font=("Arial Black", 9)
        ).pack(side=tk.LEFT, padx=5)

        right_panel = tk.Frame(main_frame, bg="#2e2e2e")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.result_text = tk.Text(
            right_panel,
            wrap=tk.WORD,
            font=("Courier New", 11),
            bg="#3c3c3c",
            fg="white",
            padx=15,
            pady=15
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.progress_frame = tk.Frame(right_panel, bg="#2e2e2e", height=30)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = tk.Label(
            self.progress_frame,
            text="",
            bg="#2e2e2e",
            fg="white",
            font=("Arial", 9)
        )
        self.status_label.pack(fill=tk.X, padx=5)


        for i, color in enumerate(self.depth_colors):
            self.result_text.tag_config(f"depth{i}", foreground=color)


    def update_recipes_list(self, event=None):
        current_search = self.search_var.get()
        order = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz"
        mapping = str.maketrans({ch: chr(1000 + i) for i, ch in enumerate(order)})
        selected_category = self.category_var.get()
        if not selected_category:
            return

        filtered_recipes = [r for r in self.recipes if r['category'] == selected_category]

        translated_names = []
        self.recipe_map = {}
        for recipe in filtered_recipes:
            normalized_id = recipe['id'].lower().replace(' ', '')
            translated = self.translations.get(normalized_id, recipe['id'])
            translated_names.append(translated)
            self.recipe_map[translated] = recipe['id']

        translated_names.sort(key=lambda s: s.lower().translate(mapping))
        self.recipe_combobox['values'] = translated_names
        if translated_names:
            self.recipe_var.set(translated_names[0])
        else:
            self.recipe_var.set('')
        self.search_var.set(current_search)


    def update_data_async(self):
        self.update_btn.config(state=tk.DISABLED)
        self.progress_frame.pack(fill=tk.X, pady=5)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Подготовка к обновлению...")
        threading.Thread(target=self.update_data).start()


    def hide_progress(self):
        self.progress_frame.pack_forget()
        self.progress_bar['value'] = 0
        self.status_label.config(text="")


    def update_data(self):
        try:
            total_files = len(self.recipe_categories) + len(self.translation_files) + len(self.custom_recipe_links) + len(self.custom_translation_links)
            self.setup_directories(upd=True)

            self.root.after(0, self.progress_bar.configure, {'maximum': total_files})
            self.root.after(0, self.status_label.config, {'text': "Загрузка рецептов..."})

            for i, (category, url) in enumerate(self.recipe_categories.items()):
                print(f'{category}: {url}')
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f'recipes/{category}.yml', 'w', encoding='utf-8') as f:
                        f.write(response.text)

                self.root.after(0, self.progress_bar.step, 1)
                self.root.after(0, self.status_label.config,
                                {'text': f"Загружено рецептов: {i + 1}/{len(self.recipe_categories)}"})

            self.root.after(0, self.status_label.config, {'text': "Загрузка переводов..."})
            for i, (name, url) in enumerate(self.translation_files.items()):
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f'translations/{name}.ftl', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                self.root.after(0, self.progress_bar.step, 1)
                self.root.after(0, self.status_label.config,
                                {'text': f"Загружено переводов: {i + 1}/{len(self.translation_files)}"})

            self.root.after(0, self.status_label.config, {'text': "Обновление завершено!"})
            self.root.after(2000, self.hide_progress)
            self.root.after(0, messagebox.showinfo, "Обновление", "Данные успешно обновлены!")
            self.load_translations()
            self.load_recipes()
            self.update_recipes_list()

        except Exception as e:
            self.root.after(0, self.status_label.config, {'text': f"Ошибка: {str(e)}"})
            self.root.after(0, messagebox.showerror, "Ошибка", f"Ошибка при обновлении: {str(e)}")
            self.root.after(5000, self.hide_progress)
        finally:
            self.root.after(0, self.update_btn.config, {'state': tk.NORMAL})


    def calculate_reactants(self):
        selected_translation = self.recipe_var.get()
        scroll_position = self.result_text.yview()
        self.result_text.delete(1.0, tk.END)
        self.result_text.yview_moveto(scroll_position[0])
        if not selected_translation:
            messagebox.showwarning("Ошибка", "Выберите рецепт")
            return

        recipe_id = self.recipe_map.get(selected_translation)
        if not recipe_id:
            messagebox.showerror("Ошибка", "Неверный выбор рецепта")
            return

        if not recipe_id or recipe_id not in self.recipe_dict:
            messagebox.showerror("Ошибка", "Рецепт не найден")
            return

        try:
            amount = float(self.amount_entry.get() or 90)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректное количество")
            return

        self.result_text.delete(1.0, tk.END)
        self.resolve_reactants(
            recipe_id=recipe_id,
            amount_needed=amount,
            text_widget=self.result_text
        )

        self.update_overlay_content()


    def resolve_reactants(self, recipe_id, amount_needed, depth=0,
                          target_product=None, include_header=True,
                          visited=None, text_widget=None):

        color_index = depth % len(self.depth_colors)
        current_color_tag = f"depth{color_index}"

        if not self.result_text.tag_cget(current_color_tag, "foreground"):
            self.result_text.tag_config(
                current_color_tag,
                foreground=self.depth_colors[color_index]
            )


        def format_amount(value):
            return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else str(int(value))

        if visited is None:
            visited = set()

        current_color_tag = f"depth{depth}"
        self.result_text.tag_config(
            f"depth{depth}",
            foreground=self.depth_colors[depth % len(self.depth_colors)]
        )
        recipe = self.recipe_dict.get(recipe_id)

        if not recipe:
            text_widget.insert(tk.END,
                               f"{'  ' * depth}Ошибка: Рецепт {recipe_id} не найден\n", current_color_tag)
            return

        products = recipe.get("products", {})
        reactants = recipe.get("reactants", {})
        effects = recipe.get("effects", [])
        mixer_categories = recipe.get("requiredMixerCategories", [])

        is_electrolysis = 'Electrolysis' in mixer_categories
        is_centrifuge = 'Centrifuge' in mixer_categories
        is_Shake = 'Shake' in mixer_categories
        is_Stir = 'Stir' in mixer_categories
        is_instant = len(effects) > 0 and len(products) == 0

        target_product = target_product or next(iter(products.keys()), None) if products else None
        product_amount = products.get(target_product, 0) if target_product else 0
        multiplier = amount_needed / product_amount if product_amount and not is_electrolysis and not is_instant else 0

        if is_centrifuge and reactants:
            first_reactant = next(iter(reactants.values()))
            base_amount = first_reactant.get('amount', 0)
            multiplier = amount_needed / base_amount if base_amount else 0
        elif is_electrolysis and reactants:
            first_reactant = next(iter(reactants.values()))
            base_amount = first_reactant.get('amount', 0)
            multiplier = amount_needed / base_amount if base_amount else 0
        elif is_instant:
            multiplier = amount_needed

        normalized_id = recipe_id.lower().replace(' ', '')
        translated_name = self.translations.get(normalized_id, recipe_id)
        if include_header:
            header = f"{'  ' * depth}{format_amount(amount_needed)} {translated_name}"

            if is_electrolysis:
                header += " [ЭЛЕКТРОЛИЗ]"
            elif is_centrifuge:
                header += " [ЦЕНТРИФУГА]"
            elif is_instant:
                header += " [МГНОВЕННАЯ РЕАКЦИЯ]"
            elif is_Shake:
                header += " [ВЗБОЛТАТЬ]"
            elif is_Stir:
                header += " [ПЕРЕМЕШАТЬ]"

            if "minTemp" in recipe:
                header += f"(мин. темп:{recipe['minTemp']}K)"

            header += ":" if reactants else ""
            text_widget.insert(tk.END, header + "\n", current_color_tag)

        for reactant, info in reactants.items():
            required_amount = info["amount"]
            is_catalyst = info.get("catalyst", False)
            final_amount = required_amount * (multiplier if not is_catalyst else 1)
            normalized_reactant = reactant.lower().replace(' ', '').replace('-', '')
            translated_name = self.translations.get(normalized_reactant, reactant)

            line = f"{'  ' * (depth + 1)}{format_amount(final_amount)} {translated_name}"
            if reactant in self.recipe_dict and not is_catalyst:
                component_recipe = self.recipe_dict[reactant]
                if "minTemp" in component_recipe:
                    line += f" [р](мин. темп:{component_recipe['minTemp']}K)"
                else:
                    line += " [р]"
            if is_catalyst:
                line += " (катализатор)"
            text_widget.insert(tk.END, line + "\n", current_color_tag)

            if reactant in self.recipe_dict and not is_catalyst and reactant not in visited:
                new_visited = visited.copy()
                new_visited.add(reactant)
                self.resolve_reactants(
                    recipe_id=reactant,
                    amount_needed=final_amount,
                    depth=depth + 1,
                    target_product=reactant,
                    include_header=False,
                    visited=new_visited,
                    text_widget=text_widget
                )

        if is_electrolysis:
            products_text = []
            for product, amount in products.items():
                product_amount = amount * multiplier
                normalized_product = product.lower().replace(' ', '').replace('-', '')
                translated_product = self.translations.get(normalized_product, product)
                products_text.append(f"{format_amount(product_amount)} {translated_product}")

            if products_text:
                text_widget.insert(tk.END,
                                   f"{'  ' * (depth + 1)}Продукты электролиза: {' + '.join(products_text)}\n", current_color_tag)


        if is_centrifuge:
            products_text = []
            for product, amount in products.items():
                product_amount = amount * multiplier
                normalized_product = product.lower().replace(' ', '').replace('-', '')
                translated_product = self.translations.get(normalized_product, product)
                products_text.append(f"{format_amount(product_amount)} {translated_product}")

            if products_text:
                text_widget.insert(tk.END,
                                   f"{'  ' * (depth + 1)}Продукты центрифуги: {' + '.join(products_text)}\n", current_color_tag)

        elif is_instant:
            effects_text = []
            for effect in effects:
                if isinstance(effect, dict):
                    effect_type = effect.get('type', '').split(':')[-1]
                    details = []

                    if effect_type == 'CreateGas':
                        details.append(f"Создает газ: {effect.get('gas', 'Неизвестно')}")
                    elif effect_type == 'PopupMessage':
                        details.append(f"Сообщение: {', '.join(effect.get('messages', []))}")
                    elif effect_type == 'EmpReactionEffect':
                        details.append(f"ЭМИ радиус: {effect.get('maxRange', 0)}м")

                    if details:
                        effects_text.append(f"{effect_type} ({'; '.join(details)})")
                    else:
                        effects_text.append(effect_type)
                else:
                    effects_text.append(str(effect))

            if effects_text:
                text_widget.insert(tk.END,
                                   f"{'  ' * (depth + 1)}Эффекты: {' | '.join(effects_text)}\n",
                                   current_color_tag)


    def compare_versions(self, v1, v2):
        try:
            v1 = [int(part) for part in v1.split('.')]
            v2 = [int(part) for part in v2.split('.')]
        except ValueError:
            return 0

        for p1, p2 in zip(v1, v2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0 if len(v1) == len(v2) else 1 if len(v1) > len(v2) else -1


    def check_for_updates(self):
        try:
            api_url = "https://api.github.com/repos/R-R0S/ss14-calc/releases/latest"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')

                if self.compare_versions(latest_version, self.current_version) > 0:
                    self.add_update_notification()
                    self.root.after(0, self.show_update_dialog, release_data['html_url'])
        except Exception as e:
            print(f"Ошибка проверки обновлений: {str(e)}")


    def show_update_dialog(self, release_url):
        if messagebox.askyesno(
                "Доступно обновление",
                f"Обнаружена новая версия!\n\nХотите перейти на страницу релиза?",
                icon='question'
        ):
            webbrowser.open(release_url)


    def add_update_notification(self):
        base_title = f"SS14 Химический калькулятор by i_love_Megumin v{self.current_version}"
        random_message = random.choice(self.update_messages)
        new_title = f"{base_title} | {random_message}"
        self.root.after(0, self.root.title, new_title)


    def check_for_updates_async(self):
        threading.Thread(target=self.check_for_updates, daemon=True).start()


    def create_settings_window(self):
        if self.settings_win and self.settings_win.winfo_exists():
            return

        self.settings_btn.config(state=tk.DISABLED)
        self.settings_win = tk.Toplevel(self.root)
        self.settings_win.geometry("500x400")
        self.settings_win.title("Настройки")
        self.settings_win.configure(bg="#2e2e2e")
        self.settings_win.protocol("WM_DELETE_WINDOW", self.close_settings)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#2e2e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#454545", foreground="white", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#1e7e34")])

        notebook = ttk.Notebook(self.settings_win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        general_frame = tk.Frame(notebook, bg="#2e2e2e")
        self.create_general_tab(general_frame)
        notebook.add(general_frame, text="Основные")

        links_frame = tk.Frame(notebook, bg="#2e2e2e")
        self.create_links_tab(links_frame)
        notebook.add(links_frame, text="Ссылки")

        about_frame = tk.Frame(notebook, bg="#2e2e2e")
        self.create_about_tab(about_frame)
        notebook.add(about_frame, text="О приложении")


    def update_opacity_display(self, value):
        opacity = float(value) / 100
        self.overlay_opacity = opacity
        self.opacity_label.config(text=f"Прозрачность оверлея - {int(opacity * 100)}%")

        if self.overlay_window:
            self.overlay_window.wm_attributes("-alpha", opacity)


    def create_general_tab(self, parent):
        style = ttk.Style()
        style.configure("Custom.Horizontal.TScale",
                        background="#2e2e2e",
                        troughcolor="#454545",
                        bordercolor="#454545",
                        lightcolor="#454545",
                        darkcolor="#454545",
                        sliderthickness=15,
                        sliderlength=30,
                        gripcount=0)

        style.map("Custom.Horizontal.TScale",
                  slidercolor=[('active', '#1e7e34'), ('!active', '#5e5e5e')])

        opacity_frame = ttk.Frame(parent)
        opacity_frame.pack(fill=tk.X, pady=15, padx=10)

        self.opacity_label = ttk.Label(
            opacity_frame,
            text=f"Прозрачность оверлея - {int(self.overlay_opacity * 100)}%",
            font=('Arial', 10),
            background="#2e2e2e",
            foreground="white"
        )
        self.opacity_label.pack(anchor=tk.W, pady=(0, 5))

        self.opacity_slider = ttk.Scale(
            opacity_frame,
            from_=30,
            to=100,
            value=self.overlay_opacity * 100,
            command=self.update_opacity_display,
            style="Custom.Horizontal.TScale",
            orient=tk.HORIZONTAL
        )
        self.opacity_slider.pack(fill=tk.X)


        lang_frame = tk.Frame(parent, bg="#2e2e2e")
        lang_frame.pack(fill=tk.X, pady=5, padx=10)

        tk.Label(lang_frame, text="Язык интерфейса:", bg="#2e2e2e", fg="white").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value=self.language)
        ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=[('ru', 'Русский')],
            state="readonly"
        ).pack(side=tk.LEFT)
        self.lang_var.trace_add("write", self.update_language)

        color_frame = ttk.LabelFrame(parent,
                                     text="Цвета уровней рекурсии",
                                     style="Custom.TLabelframe")
        color_frame.pack(fill=tk.BOTH, pady=10, padx=5, expand=True)

        self.color_vars = []
        self.color_previews = []
        color_names = list(self.COLOR_NAMES.keys())

        for col in [0, 1]:
            column_frame = ttk.Frame(color_frame)
            column_frame.grid(row=0, column=col, padx=10, sticky='nsew')

            for i in range(3):
                idx = col * 3 + i
                if idx >= 6:
                    break

                row = ttk.Frame(column_frame)
                row.pack(fill=tk.X, pady=2)

                hex_color = self.depth_colors[idx]
                color_preview = tk.Canvas(row, width=20, height=20,
                                          bg=hex_color,
                                          highlightthickness=0)
                color_preview.pack(side=tk.LEFT, padx=(0, 5))
                self.color_previews.append(color_preview)

                default_name = self.get_color_name(hex_color)
                color_var = tk.StringVar(value=default_name)
                color_var.trace_add("write", lambda *a, i=idx: self.update_color(i))

                cb = ttk.Combobox(
                    row,
                    textvariable=color_var,
                    values=color_names,
                    state="readonly",
                    width=14,
                    style="Custom.TCombobox"
                )
                cb.pack(side=tk.LEFT)
                self.color_vars.append(color_var)


    def get_color_name(self, hex_code):
        for name, code in self.COLOR_NAMES.items():
            if code == hex_code:
                return name
        return "белый"


    def update_color(self, index):
        color_name = self.color_vars[index].get()
        hex_color = self.COLOR_NAMES[color_name]
        self.depth_colors[index] = hex_color
        self.color_previews[index].config(bg=hex_color)
        self.result_text.tag_config(f"depth{index}", foreground=hex_color)
        self.update_overlay_content()
        if self.recipe_var.get():
            self.calculate_reactants()


    def get_color_palette(self):
        return [
            "#FFFFFF", "#4EC9B0", "#569CD6",
            "#B5CEA8", "#CE9178", "#C586C0",
            "#FFA07A", "#98FB98", "#DDA0DD",
            "#FFD700", "#87CEEB", "#FF69B4"
        ]


    def close_settings(self):
            self.save_settings()
            if self.settings_win:
                self.settings_win.destroy()
            self.settings_btn.config(state=tk.NORMAL)
            self.settings_win = None


    def create_links_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        recipes_frame = ttk.Frame(notebook)
        self.create_links_table(recipes_frame, is_recipe=True)
        notebook.add(recipes_frame, text="Пользовательские рецепты")

        translations_frame = ttk.Frame(notebook)
        self.create_links_table(translations_frame, is_recipe=False)
        notebook.add(translations_frame, text="Пользовательские переводы")


    def create_links_table(self, parent, is_recipe):
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("Название", "Ссылка")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        tree.heading("Название", text="Название")
        tree.heading("Ссылка", text="Ссылка")
        tree.column("Название", width=150, anchor=tk.W)
        tree.column("Ссылка", width=400, anchor=tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        data = self.custom_recipe_links if is_recipe else self.custom_translation_links
        for name, url in data.items():
            tree.insert("", tk.END, values=(name, url))

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Button(btn_frame,
                   text="Добавить",
                   style="Custom.TButton",
                   command=lambda: self.edit_link(tree, is_recipe, False)
                   ).pack(side=tk.LEFT, padx=2)

        ttk.Button(btn_frame,
                   text="Редактировать",
                   style="Custom.TButton",
                   command=lambda: self.edit_link(tree, is_recipe, True)
                   ).pack(side=tk.LEFT, padx=2)

        ttk.Button(btn_frame,
                   text="Удалить",
                   style="Custom.TButton",
                   command=lambda: self.delete_link(tree, is_recipe)
                   ).pack(side=tk.LEFT, padx=2)

        if is_recipe:
            self.recipe_tree = tree
        else:
            self.translation_tree = tree


    def setup_clipboard_handlers(self):
        def handle_paste(event):
            try:
                widget = event.widget
                if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
                    clipboard_text = self.root.clipboard_get()
                    if clipboard_text:
                        widget.insert(tk.INSERT, clipboard_text)
            except tk.TclError:
                pass


    def edit_link(self, tree, is_recipe, is_edit=False):
        item = tree.selection() if is_edit else None
        current_values = tree.item(item, "values") if item else ("", "")

        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование ссылки" if is_edit else "Добавление ссылки")
        dialog.configure(bg="#2e2e2e")
        dialog.geometry("400x180")
        dialog.resizable(False, False)

        style = ttk.Style()
        style.configure("Dialog.TLabel",
                        background="#2e2e2e",
                        foreground="white",
                        font=("Arial", 10))

        style.configure("Dialog.TEntry",
                        fieldbackground="#4f4f4f",
                        foreground="white",
                        insertcolor="white",
                        borderwidth=2,
                        relief="flat")

        style.map("Dialog.TEntry",
                  fieldbackground=[("active", "#5e5e5e")])

        style.configure("Dialog.TButton",
                        background="#454545",
                        foreground="white",
                        width=10,
                        borderwidth=0)

        style.map("Dialog.TButton",
                  background=[("active", "#5e5e5e")])

        main_frame = ttk.Frame(dialog)
        main_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        ttk.Label(main_frame,
                  text="Название:",
                  style="Dialog.TLabel").pack(anchor=tk.W)

        name_entry = ttk.Entry(main_frame,
                               width=40,
                               style="Dialog.TEntry")
        name_entry.insert(0, current_values[0])
        name_entry.pack(pady=5)

        ttk.Label(main_frame,
                  text="Ссылка:",
                  style="Dialog.TLabel").pack(anchor=tk.W)

        url_entry = ttk.Entry(main_frame,
                              width=40,
                              style="Dialog.TEntry")
        url_entry.insert(0, current_values[1])
        url_entry.pack(pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        def save_changes():
            new_name = name_entry.get().strip()
            new_url = url_entry.get().strip()
            if not new_name or not new_url:
                messagebox.showerror("Ошибка", "Название и ссылка не могут быть пустыми")
                return
            if not new_url.startswith(('http://', 'https://')):
                messagebox.showerror("Ошибка", "Ссылка должна начинаться с http:// или https://")
                return

            if item:
                tree.item(item, values=(new_name, new_url))
            else:
                tree.insert("", tk.END, values=(new_name, new_url))

            if is_recipe:
                self.custom_recipe_links[new_name] = new_url
                self.recipe_categories[new_name] = new_url
            else:
                self.custom_translation_links[new_name] = new_url
                self.translation_files[new_name] = new_url

            self.save_settings()
            dialog.destroy()

        ttk.Button(btn_frame,
                   text="Сохранить",
                   style="Dialog.TButton",
                   command=save_changes).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame,
                   text="Отмена",
                   style="Dialog.TButton",
                   command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Destroy>", lambda e: self.settings_btn.config(state=tk.NORMAL))

    def delete_link(self, tree, is_recipe):
        selected_item = tree.selection()
        if selected_item:
            name = tree.item(selected_item, "values")[0]
            tree.delete(selected_item)

            if is_recipe:
                if name in self.custom_recipe_links:
                    del self.custom_recipe_links[name]
                if name in self.recipe_categories:
                    del self.recipe_categories[name]
                self.category_combobox['values'] = list(self.recipe_categories.keys())
            else:
                if name in self.custom_translation_links:
                    del self.custom_translation_links[name]
                if name in self.translation_files:
                    del self.translation_files[name]

            self.save_settings()
            self.load_recipes()
            self.update_recipes_list()


    def update_categories(self, is_recipe, name, url):
        if is_recipe:
            self.recipe_categories[name] = url
        else:
            self.translation_files[name] = url


    def update_overlay_opacity(self, value):
        self.overlay_opacity = value
        if self.overlay_window:
            self.overlay_window.wm_attributes("-alpha", value)


    def update_language(self, *args):
        self.language = self.lang_var.get()
        # Мэйби когда-то позже


    def save_settings(self):
        self.custom_recipe_links = {self.recipe_tree.item(item)['values'][0]: self.recipe_tree.item(item)['values'][1]
                                    for item in self.recipe_tree.get_children()}

        self.custom_translation_links = {
            self.translation_tree.item(item)['values'][0]: self.translation_tree.item(item)['values'][1]
            for item in self.translation_tree.get_children()}

        hex_colors = [self.COLOR_NAMES[var.get()] for var in self.color_vars]

        settings = {
            'opacity': self.overlay_opacity,
            'language': self.language,
            'depth_colors': hex_colors,
            'custom_recipes': self.custom_recipe_links,
            'custom_translations': self.custom_translation_links
        }

        try:
            with open('settings.cfg', 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {str(e)}")

        self.recipe_categories = {
            **self.recipe_categories,
            **self.custom_recipe_links
        }
        self.category_combobox['values'] = list(self.recipe_categories.keys())
        self.load_recipes()
        self.load_translations()
        self.update_recipes_list()


    def load_settings(self):
        try:
            with open('settings.cfg', 'r') as f:
                settings = json.load(f)
                self.overlay_opacity = settings.get('opacity', 0.95)
                self.language = settings.get('language', 'ru')
                if 'depth_colors' in settings:
                    self.depth_colors = []
                    self.depth_colors = [
                        self.COLOR_NAMES.get(color, color)
                        for color in settings['depth_colors']
                    ]
                    self.depth_colors = self.depth_colors[:6]
                    print(f'цвета {self.depth_colors} - загруженны!')
                    for i, color in enumerate(self.depth_colors):
                        if i < len(self.color_vars):
                            color_name = self.get_color_name(color)
                            self.color_vars[i].set(color_name)

                self.custom_recipe_links = settings.get('custom_recipes', {})
                self.custom_translation_links = settings.get('custom_translations', {})

                self.recipe_categories.update(self.custom_recipe_links)
                self.translation_files.update(self.custom_translation_links)
        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить настройки: {str(e)}")
            self.depth_colors = list(self.COLOR_NAMES.values())[:6]


    def reset_settings(self):
        if messagebox.askyesno("Сброс настроек",
                               "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?"):
            try:
                if os.path.exists('settings.cfg'):
                    os.remove('settings.cfg')

                self.overlay_opacity = 0.95
                self.language = 'ru'
                self.depth_colors = [
                    "#FFFFFF", "#4EC9B0", "#569CD6",
                    "#B5CEA8", "#CE9178", "#C586C0"
                ]
                self.custom_recipe_links = {}
                self.custom_translation_links = {}

                if self.settings_win and self.settings_win.winfo_exists():
                    self.settings_win.destroy()
                    self.settings_btn.config(state=tk.NORMAL)
                    self.settings_win = None

                for i in range(len(self.depth_colors)):
                    self.result_text.tag_config(
                        f"depth{i}",
                        foreground=self.depth_colors[i]
                    )

                if self.recipe_var.get():
                    self.calculate_reactants()

                messagebox.showinfo("Сброс настроек", "Настройки успешно сброшены!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сбросить настройки: {str(e)}")


    def create_about_tab(self, parent):
        main_frame = tk.Frame(parent, bg="#2e2e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        info_text = f"""SS14 Химический калькулятор
    Версия: {self.current_version}
    Автор: i_love_Megumin aka R-R0S

Вы можете добавить свои собственные рецепты,
достаточно положить файл.yml с рецептом в папку recipes
или добавить ссылку на файл рецептов, например с GitHub
проекта, на котором вы играете. Аналогично с переводами.

Если вы добавили рецепты, не забудьте обновить данные !

Если вы сталкнулись с проблемой -
попробуйте сбросить настройки и перезапустить приложение!"""

        info_label = tk.Label(
            main_frame,
            text=info_text,
            bg="#2e2e2e",
            fg="white",
            font=("Arial", 11),
            justify=tk.LEFT
        )
        info_label.pack(pady=10, anchor=tk.W)

        reset_btn = ttk.Button(
            main_frame,
            text="Сбросить все настройки",
            command=self.reset_settings,
            style='Red.TButton',
        )
        reset_btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReagentCalculatorApp(root)
    root.mainloop()