import yaml
import os
import requests
import threading
from tkinter import *
from tkinter import messagebox, ttk
import tkinter as tk


class ReagentCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reagent Calculator")
        self.root.geometry("1000x600")
        self.root.configure(bg="#2e2e2e")

        # Конфигурация категорий
        self.recipe_categories = {
            'medicine': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/medicine.yml',
            'chemicals': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/chemicals.yml',
            'pyrotechnic': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/pyrotechnic.yml'
        }

        self.recipes = []
        self.recipe_dict = {}
        # Словарь для перевода
        self.translations = {
            "Dylovene": "Диловен",
            "TableSalt": "Столовая Соль",
            "SpaceDrugs": "Космический мираж",
            "Lexorin": "Лексорин",
            "Mannitol": "Маннитол",
            "Vestine": "Вестин",
            "Lipozine": "Липозин",
            "Mercury": "Ртуть",
            "Impedrezene": "Импедрезен",
            "HeartbreakerToxin": "Токсин Хартбрейкер",
            "MindbreakerToxin": "Токсин Майндбрейкер",
            "ZombieBlood": "Кровь зомби",
            "AmbuzolPlus": "Амбузол Плюс",
            "Ambuzol": "Абузол",
            "Blood": "Кровь",
            "Phalanximine": "Фалангимин",
            "Fersilicite": "Силицид железа",
            "Leporazine": "Лепоразин",
            "Copper": "Медь",
            "Silicon": "Кремний",
            "Ammonia": "Аммиак",
            "TranexamicAcid": "Транексамовая кислота",
            "Nitrogen": "Азот",
            "SulfuricAcid": "Серная кислота",
            "Potassium": "Калий",
            "Ethylredoxrazine": "Этилредоксразин",
            "Oxygen": "Кислород",
            "Iron": "Железо",
            "Radium": "Радий",
            "Carbon": "Углерод",
            "Chlorine": "Хлор",
            "Bruizine": "Бруизин",
            "Phenol": "Фенол",
            "Lacerinol": "Лацеринол",
            "BicarLacerinol": "BicarLacerinol Razorium",
            "BicarPuncturase": "BicarPuncturase Razorium",
            "BicarBruizine": "BicarBruizine Razorium",
            "Puncturase": "Пунктураз",
            "Acetone": "Ацетон",
            "Hydroxide": "Гидроксид",
            "Cryptobiolin": "Криптобиолин",
            "Sugar": "Сахар",
            "Saline": "физ. раствор",
            "Ipecac": "Ипекак",
            "Epinephrine": "Эпинефрин",
            "Benzene": "Бензол",
            "UnstableMutagen": "Нестабильный мутаген",
            "Bicaridine": "Бикаридин",
            "Cryoxadone": "Криоксадон",
            "Doxarubixadone": "Доксарубиксадон",
            "Inaprovaline": "Инапровалин",
            "Water": "Вода",
            "Arithrazine": "Аритразин",
            "Kelotane": "Келотан",
            "Phosphorus": "Фосфор",
            "Hydrogen": "Водород",
            "Plasma": "Плазма",
            "Dexalin": "Дексалин",
            "Dermaline": "Дермалин",
            "Hyronalin": "Хироналин",
            "DexalinPlus": "Дексалин Плюс",
            "Ultravasculine": "Ультраваскулин",
            "Ethanol": "Этанол",
            "Synaptizine": "Синаптизин",
            "Histamine": "Гистамин",
            "Lithium": "Литий",
            "Tricordrazine": "Трикордразин",
            "Oculine": "Окулин",
            "Siderlac": "Сидерлак",
            "Aloe": "Алоэ",
            "Stellibinin": "Стеллибинин",
            "Cognizine": "Когнизин",
            "CarpoToxin": "Карпотоксин",
            "Sigynate": "Сигинат",
            "SodiumCarbonate": "Карбонат натрия",
            "SodiumHydroxide": "Гидроксид натрия",
            "Diphenhydramine": "Дифенгидрамин",
            "Diethylamine": "Диэтиламин",
            "Oil": "Масло",
            "Pyrazine": "Пиразин",
            "Insuzine": "Инсузин",
            "Opporozidone": "Оппорозидон",
            "Necrosol": "Некрозол",
            "Omnizine": "Омнизин",
            "Psicodine": "Псикодин",
            "Lipolicide": "Липолицид",
            "Ephedrine": "Эфедрин",
            "Happiness": "Счастье",
            "Laughter": "Смех",
            "PotassiumIodide": "Иодид калия",
            "Haloperidol": "Галоперидол",
            "Aloxadone": "Алоксадон",
        }

        self.setup_directories()
        self.load_recipes()
        self.create_widgets()

    def setup_directories(self):
        if not os.path.exists('recipes'):
            os.makedirs('recipes')

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
        class IgnoreUnknownTagsLoader(yaml.SafeLoader):
            pass

        def ignore_unknown_tag(loader, tag_suffix, node):
            return None

        IgnoreUnknownTagsLoader.add_multi_constructor('!type', ignore_unknown_tag)
        IgnoreUnknownTagsLoader.add_multi_constructor('!', ignore_unknown_tag)
        return IgnoreUnknownTagsLoader(stream)

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#2e2e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель
        left_panel = tk.Frame(main_frame, bg="#2e2e2e")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Выбор категории
        self.category_var = tk.StringVar()
        category_frame = tk.Frame(left_panel, bg="#2e2e2e")
        category_frame.pack(fill=tk.X, pady=5)

        tk.Label(category_frame,
                text="Выберите категорию:",
                font=("Arial", 12),
                fg="white",
                bg="#2e2e2e").pack(anchor=tk.W)

        self.category_combobox = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=list(self.recipe_categories.keys()),
            state="readonly",
            font=("Arial", 11))
        self.category_combobox.pack(fill=tk.X, pady=5)
        self.category_combobox.bind("<<ComboboxSelected>>", self.update_recipes_list)

        # Выбор рецепта
        self.recipe_var = tk.StringVar()
        recipe_frame = tk.Frame(left_panel, bg="#2e2e2e")
        recipe_frame.pack(fill=tk.X, pady=5)

        tk.Label(recipe_frame,
                text="Выберите рецепт:",
                font=("Arial", 12),
                fg="white",
                bg="#2e2e2e").pack(anchor=tk.W)

        self.recipe_combobox = ttk.Combobox(
            recipe_frame,
            textvariable=self.recipe_var,
            state="readonly",
            font=("Arial", 11))
        self.recipe_combobox.pack(fill=tk.X, pady=5)

        # Ввод количества
        amount_frame = tk.Frame(left_panel, bg="#2e2e2e")
        amount_frame.pack(fill=tk.X, pady=5)

        tk.Label(amount_frame,
                 text="Количество продукта:",
                 font=("Arial", 12),
                 fg="white",
                 bg="#2e2e2e").pack(anchor=tk.W)

        self.amount_entry = tk.Entry(
            amount_frame,
            font=("Arial", 12),
            bg="#4f4f4f",
            fg="white"
        )
        self.amount_entry.pack(fill=tk.X, pady=5)
        self.amount_entry.insert(0, "90")

        # Кнопки
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

        # Правая панель с результатами
        right_panel = tk.Frame(main_frame, bg="#2e2e2e")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

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

        # Настройка цветов для уровней
        self.depth_colors = [
            "#FFFFFF", "#4EC9B0", "#569CD6",
            "#B5CEA8", "#CE9178", "#C586C0"
        ]
        for i, color in enumerate(self.depth_colors):
            self.result_text.tag_config(f"depth{i}", foreground=color)

    def update_recipes_list(self, event=None):
        selected_category = self.category_var.get()
        if not selected_category:
            return

        # Фильтруем рецепты по выбранной категории
        filtered_recipes = [r for r in self.recipes if r['category'] == selected_category]

        # Получаем переведенные названия
        translated_names = []
        self.recipe_map = {}
        for recipe in filtered_recipes:
            translated = self.translations.get(recipe['id'], recipe['id'])
            translated_names.append(translated)
            self.recipe_map[translated] = recipe['id']

        # Обновляем список рецептов
        self.recipe_combobox['values'] = translated_names
        if translated_names:
            self.recipe_var.set(translated_names[0])
        else:
            self.recipe_var.set('')
            messagebox.showinfo("Информация", "В выбранной категории нет рецептов")

    def update_data_async(self):
        threading.Thread(target=self.update_data).start()

    def update_data(self):
        try:
            # Скачиваем все категории
            for category, url in self.recipe_categories.items():
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f'recipes/{category}.yml', 'w', encoding='utf-8') as f:
                        f.write(response.text)

            # Перезагружаем рецепты
            self.load_recipes()
            self.update_recipes_list()
            messagebox.showinfo("Обновление", "Данные успешно обновлены!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")

    def calculate_reactants(self):
        selected_translation = self.recipe_var.get()
        if not selected_translation:
            messagebox.showwarning("Ошибка", "Выберите рецепт")
            return

        # Получаем оригинальный ID рецепта
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

    def resolve_reactants(self, recipe_id, amount_needed, depth=0,
                          target_product=None, include_header=True,
                          visited=None, text_widget=None):
        # Исправленная версия функции
        def format_amount(value):
            return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else str(int(value))

        if visited is None:
            visited = set()

        current_color_tag = f"depth{min(depth, len(self.depth_colors) - 1)}"
        recipe = self.recipe_dict.get(recipe_id)

        if not recipe:
            text_widget.insert(tk.END,
                               f"{'  ' * depth}Ошибка: Рецепт {recipe_id} не найден\n",
                               current_color_tag)
            return

        products = recipe.get("products", {})
        reactants = recipe.get("reactants", {})

        target_product = target_product or next(iter(products.keys()), None)
        if not target_product or target_product not in products:
            text_widget.insert(tk.END,
                               f"{'  ' * depth}Ошибка: Продукт не найден\n",
                               current_color_tag)
            return

        product_amount = products[target_product]
        multiplier = amount_needed / product_amount
        translated_product = self.translations.get(target_product, target_product)

        if include_header:
            header = f"{'  ' * depth}{format_amount(amount_needed)} {translated_product}"
            if "minTemp" in recipe:
                header += f" (мин. температура: {recipe['minTemp']}K)"
            header += ":\n" if reactants else "\n"
            text_widget.insert(tk.END, header, current_color_tag)

        for reactant, info in reactants.items():
            required_amount = info["amount"]
            is_catalyst = info.get("catalyst", False)
            final_amount = required_amount * (multiplier if not is_catalyst else 1)
            translated_name = self.translations.get(reactant, reactant)

            line = f"{'  ' * (depth + 1)}{format_amount(final_amount)} {translated_name}"
            if reactant in self.recipe_dict and not is_catalyst:
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


if __name__ == "__main__":
    root = tk.Tk()
    app = ReagentCalculatorApp(root)
    root.mainloop()