import yaml
import os
import re
import sys
import random
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
        self.current_version = "0.33104"
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
        self.root.geometry("1000x650")
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


        self.recipes = []
        self.recipe_dict = {}
        self.load_images()
        self.create_widgets()
        self.setup_directories()
        self.load_translations()
        self.load_recipes()

        self.overlay_window = None
        self.overlay_content = None
        self.progress_visible = None

        self.check_for_updates_async()
        # self.debug_add_update_notification()

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

    def create_overlay_window(self):
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.wm_attributes("-topmost", True)
        self.overlay_window.configure(bg='#2e2e2e')
        self.overlay_window.overrideredirect(True)
        self.overlay_window.geometry("400x300+100+100")
        self.overlay_window.minsize(200, 150)
        self.overlay_window.wm_attributes("-alpha", 0.95)

        # Главный контейнер
        main_frame = tk.Frame(self.overlay_window, bg='#2e2e2e')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок окна
        title_bar = tk.Frame(main_frame, bg='#454545', height=30)
        title_bar.pack(fill=tk.X)

        # Текст заголовка
        title_label = tk.Label(title_bar, text="Рецепт поверх окон", bg='#454545', fg='white')
        title_label.pack(side=tk.LEFT, padx=10)

        # Кнопка закрытия
        close_btn = tk.Button(title_bar, text="×", command=self.toggle_overlay,
                            bg='#ff4444', fg='white', bd=0, padx=10)
        close_btn.pack(side=tk.RIGHT)

        # Контент оверлея
        self.overlay_content = tk.Text(main_frame, wrap=tk.WORD, font=("Courier New", 10),
                                     bg="#3c3c3c", fg="white", padx=10, pady=10)
        self.overlay_content.pack(fill=tk.BOTH, expand=True)

        # Зоны ресайза
        self.setup_resize_zones(main_frame)

        # Привязки для перемещения окна
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
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        try:
            avatar_path = os.path.join(base_path, 'img', 'avatar.png')
            self.avatar_image = ImageTk.PhotoImage(PILImage.open(avatar_path).resize((80, 80)))
        except Exception as e:
            print(f"Ошибка загрузки аватара: {str(e)}")
            self.avatar_image = None

        try:
            discord_path = os.path.join(base_path, 'img', 'discord.png')
            self.discord_image = ImageTk.PhotoImage(PILImage.open(discord_path).resize((40, 40)))
        except Exception as e:
            print(f"Ошибка загрузки Discord: {str(e)}")
            self.discord_image = None


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


    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#2e2e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        left_panel = tk.Frame(main_frame, bg="#2e2e2e")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)

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

        decorative_btn = tk.Button(
            right_buttons,
            text="⚙️",
            bg="#333333",
            fg="white",
            font=("Arial", 10),
            state=tk.DISABLED
        )
        decorative_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(category_frame,
                text="Выберите категорию:",
                font=("Arial", 14),
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
                text="Выберите рецепт:",
                font=("Arial", 14),
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
                 text="Количество продукта:",
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
        )
        self.avatar_container.pack(fill=tk.BOTH, expand=True, pady=5)

        if hasattr(self, 'avatar_image') and self.avatar_image:
            self.avatar_label = tk.Label(
                self.avatar_container,
                image=self.avatar_image,
                bg="#2e2e2e"
            )
            self.avatar_label.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

            def safe_resize(event):
                w = event.width
                h = event.height
                if w <= 0 or h <= 0:
                    return

                size = min(w, h)
                if size != self.current_avatar_size:
                    self.current_avatar_size = size
                    if getattr(sys, 'frozen', False):
                        avatar_path = os.path.join(sys._MEIPASS, 'img', 'avatar.png')
                    else:
                        avatar_path = 'img/avatar.png'
                    img = PILImage.open(avatar_path)
                    img.thumbnail((size, size), PILImage.Resampling.LANCZOS)
                    self.avatar_image = ImageTk.PhotoImage(img)
                    self.avatar_label.configure(image=self.avatar_image)

            self.current_avatar_size = 0
            self.avatar_container.bind("<Configure>", safe_resize)

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

        self.depth_colors = [
            "#FFFFFF", "#4EC9B0", "#569CD6",
            "#B5CEA8", "#CE9178", "#C586C0"
        ]
        for i, color in enumerate(self.depth_colors):
            self.result_text.tag_config(f"depth{i}", foreground=color)

    def update_recipes_list(self, event=None):
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
            total_files = len(self.recipe_categories) + len(self.translation_files)
            self.setup_directories(upd=True)

            self.root.after(0, self.progress_bar.configure, {'maximum': total_files})
            self.root.after(0, self.status_label.config, {'text': "Загрузка рецептов..."})

            for i, (category, url) in enumerate(self.recipe_categories.items()):
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
        def format_amount(value):
            return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else str(int(value))

        if visited is None:
            visited = set()

        current_color_tag = f"depth{min(depth, len(self.depth_colors) - 1)}"
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

    # def debug_add_update_notification(self):
    #     base_title = f"SS14 Химический калькулятор by i_love_Megumin v{self.current_version}"
    #     random_message = self.update_messages[24]
    #     new_title = f"{base_title} | {random_message}"
    #     self.root.after(0, self.root.title, new_title)

    def check_for_updates_async(self):
        threading.Thread(target=self.check_for_updates, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReagentCalculatorApp(root)
    root.mainloop()