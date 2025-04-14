import yaml
import os
import sys
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
        self.root.title("SS14 Химический калькулятор by i_love_Megumin")
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
            'ss220 medicine': 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/9fad48b5ffce66ea9fa00e3b7a1f29658dba6657/Resources/Prototypes/SS220/Recipes/Reactions/medicine.yml'
        }

        self.recipes = []
        self.recipe_dict = {}
        self.translations = {
            "medicine": "Медикоменты",
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
            "Ambuzol": "Амбузол",
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
            "BicarLacerinol": "BicarLacerinol",
            "BicarPuncturase": "BicarPuncturase",
            "BicarBruizine": "BicarBruizine",
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
            "CelluloseBreakdown": "Расщепление Целлюлозы",
            "Cellulose": "Целлюлозные волокна",
            "WeldingFuel": "Сварочное топливо",
            "FoamingAgent": "Пенообразующий элемент",
            "PolytrinicAcid": "Политриновая кислота",
            "FluorosulfuricAcid": "Фторсерная кислота",
            "Fluorine": "Фтор",
            "PotassiumExplosion": "Взрыв калия",
            "Smoke": "Дым или пенна",
            "Fluorosurfactant": "Фторсурфактант",
            "IronMetalFoam": "Металлическая пена",
            "AluminiumMetalFoam": "Алюминевая пена",
            "Aluminium": "Алюминий",
            "UraniumEmpExplosion": "Взрыв урана",
            "Uranium": "Уран",
            "Flash": "Вспышка",
            "TableSaltBreakdown": "Расщепление соли",
            "Thermite": "Термит",
            "Desoxyephedrine": "Дезоксиэфедрин",
            "Iodine": "Йод",
            "Stimulants": "Стимулятор",
            "SpaceGlue": "Космический клей",
            "MuteToxin": "Токсин Немоты",
            "ChloralHydrate": "Хлоралгидрат",
            "Pax": "Пакс",
            "Charcoal": "Уголь",
            "Ash": "Пепел",
            "NorepinephricAcid": "Норэпинефриновая кислота",
            "Ethyloxyephedrine": "Этилоксиэфедрин",
            "Diphenylmethylamine": "Дифенилметиламин",
            "Coffee": "Кофе",
            "SodiumPolyacrylate": "Полиакрилат натрия",
            "Nocturine": "Ноктюрин",
            "Tazinide": "Тазинид",
            "Licoxide": "Ликоксид",
            "Foam": "Пена",
            "Sulfur": "Сера",
            "Sodium": "Натрий",
            "ChlorineTrifluoride": "Трифторид хлора",
            "Napalm": "Напалм",
            "Phlogiston": "Флогистон",
            "WeldingFuelBreakdown": "Разложение топлива",
            "Fomepizole": "Фомепизол",
            "Harai": "Харай",
            "Cerebrin": "Церебрин",
        }

        self.setup_directories()
        self.load_recipes()
        self.load_images()
        self.create_widgets()

    def setup_directories(self):
        if not os.path.exists('recipes'):
            os.makedirs('recipes')

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
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_panel = tk.Frame(main_frame, bg="#2e2e2e")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.category_var = tk.StringVar()
        category_frame = tk.Frame(left_panel, bg="#2e2e2e")
        category_frame.pack(fill=tk.X, pady=5)

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

        self.avatar_container = tk.Frame(left_panel,
                                         bg="#2e2e2e",
                                         height=300)
        self.avatar_container.pack(fill=tk.X, pady=5)
        self.avatar_container.pack_propagate(False)

        if hasattr(self, 'avatar_image') and self.avatar_image:
            self.avatar_label = tk.Label(self.avatar_container,
                                         image=self.avatar_image,
                                         bg="#2e2e2e")
            self.avatar_label.pack(fill=tk.BOTH, expand=True)

            def safe_resize(event):
                w = self.avatar_container.winfo_width() + 25
                h = self.avatar_container.winfo_height() + 25
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

        discord_frame = tk.Frame(left_panel,
                                 bg="#2e2e2e",
                                 height=40)
        discord_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        discord_frame.pack_propagate(False)

        if hasattr(self, 'discord_image') and self.discord_image:
            discord_btn = tk.Label(discord_frame,
                                   image=self.discord_image,
                                   bg="#2e2e2e",
                                   cursor="hand2")
            discord_btn.pack(side=tk.LEFT, padx=5)
            discord_btn.bind("<Button-1>", lambda e: webbrowser.open("https://discord.com/users/317692089355862016"))

        tk.Label(discord_frame,
                 text=f"©FelinidsPower,\n «Надежда» - 3025г.",
                 fg="white",
                 bg="#2e2e2e",
                 font=("Arial Black", 9)).pack(side=tk.LEFT, padx=5)

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

        filtered_recipes = [r for r in self.recipes if r['category'] == selected_category]

        translated_names = []
        self.recipe_map = {}
        for recipe in filtered_recipes:
            translated = self.translations.get(recipe['id'], recipe['id'])
            translated_names.append(translated)
            self.recipe_map[translated] = recipe['id']

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
            for category, url in self.recipe_categories.items():
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f'recipes/{category}.yml', 'w', encoding='utf-8') as f:
                        f.write(response.text)

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
        is_centrifuge = 'Centrifuge' in mixer_categories  # Новая проверка
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

        translated_name = self.translations.get(recipe_id, recipe_id)
        if include_header:
            header = f"{'  ' * depth}{format_amount(amount_needed)} {translated_name}"

            if is_electrolysis:
                header += " [ЭЛЕКТРОЛИЗ]"
            elif is_centrifuge:
                header += " [ЦЕНТРИФУГА]"
            elif is_instant:
                header += " [МГНОВЕННАЯ РЕАКЦИЯ]"

            if "minTemp" in recipe:
                header += f" (мин. температура: {recipe['minTemp']}K)"

            header += ":" if reactants else ""
            text_widget.insert(tk.END, header + "\n", current_color_tag)

        for reactant, info in reactants.items():
            required_amount = info["amount"]
            is_catalyst = info.get("catalyst", False)
            final_amount = required_amount * (multiplier if not is_catalyst else 1)
            translated_name = self.translations.get(reactant, reactant)

            line = f"{'  ' * (depth + 1)}{format_amount(final_amount)} {translated_name}"
            if reactant in self.recipe_dict and not is_catalyst:
                component_recipe = self.recipe_dict[reactant]
                if "minTemp" in component_recipe:
                    line += f" [р] (мин. температура: {component_recipe['minTemp']}K)"
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
                translated_product = self.translations.get(product, product)
                products_text.append(f"{format_amount(product_amount)} {translated_product}")

        if is_centrifuge:
            products_text = []
            for product, amount in products.items():
                product_amount = amount * multiplier
                translated_product = self.translations.get(product, product)
                products_text.append(f"{format_amount(product_amount)} {translated_product}")

            if products_text:
                text_widget.insert(tk.END,
                                   f"{'  ' * (depth + 1)}Продукты электролиза: {' + '.join(products_text)}\n", current_color_tag)

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


if __name__ == "__main__":
    root = tk.Tk()
    app = ReagentCalculatorApp(root)
    root.mainloop()