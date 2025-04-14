import yaml
import os
import requests
import threading
from tkinter import *
from tkinter import messagebox, font


class ReagentCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reagent Calculator")
        self.root.geometry("800x500")  # Увеличил окно
        self.root.configure(bg="#2e2e2e")  # Тёмный фон
        self.recipes = []  # Список рецептов, будет обновляться после загрузки
        self.recipe_dict = {}  # Словарь рецептов для быстрого поиска по id

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
            "Phenol": "Фенол",
            "Lacerinol": "Лацеринол",
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
        }

        # Инициализация переменной для выпадающего меню
        self.recipe_var = StringVar(self.root)

        # Загрузка и обновление данных
        self.load_recipes()

        # Создание интерфейса
        self.create_widgets()

    def load_recipes(self):
        """Загружает рецепты, обрабатывая YAML файл."""
        try:
            # Проверка существует ли локальный файл с рецептами
            if os.path.exists("recipes.yml"):
                with open("recipes.yml", "r", encoding="utf-8") as f:
                    self.recipes = list(self.filter_recipes(yaml.load(f, Loader=self.custom_yaml_loader)))
                    self.recipe_dict = {recipe['id']: recipe for recipe in self.recipes if 'id' in recipe}
        except Exception as e:
            print(f"Ошибка при загрузке рецептов: {e}")
            messagebox.showerror("Ошибка", "Не удалось загрузить рецепты.")
            self.recipes = []
            self.recipe_dict = {}

    def filter_recipes(self, raw_data):
        """Фильтрует только нужные рецепты."""
        for entry in raw_data:
            if isinstance(entry, dict) and entry.get("type") == "reaction" and "id" in entry and "reactants" in entry:
                yield entry

    def custom_yaml_loader(self, stream):
        """Функция для загрузки YAML с поддержкой пользовательских тегов."""
        class IgnoreUnknownTagsLoader(yaml.SafeLoader):
            pass

        def ignore_unknown_tag(loader, tag_suffix, node):
            if isinstance(node, yaml.ScalarNode):
                return loader.construct_scalar(node)
            elif isinstance(node, yaml.SequenceNode):
                return loader.construct_sequence(node)
            elif isinstance(node, yaml.MappingNode):
                return loader.construct_mapping(node)
            return None

        IgnoreUnknownTagsLoader.add_multi_constructor('!type', ignore_unknown_tag)
        IgnoreUnknownTagsLoader.add_multi_constructor('!', ignore_unknown_tag)

        return IgnoreUnknownTagsLoader(stream)


    def create_widgets(self):
        """Создает виджеты для интерфейса."""
        # Левый контейнер
        left_frame = Frame(self.root, bg="#2e2e2e")
        left_frame.pack(side=LEFT, padx=20, pady=20, fill=Y)

        # Название рецепта
        self.recipe_label = Label(left_frame, text="Выберите рецепт", font=("Arial", 14), fg="white", bg="#2e2e2e")
        self.recipe_label.pack(pady=10)

        # Проверка на наличие рецептов и создание выпадающего списка
        if self.recipes:
            self.recipe_var.set("Выберите рецепт")  # начальное значение

            # Переводим рецепты перед выводом
            translated_recipes = [self.translations.get(recipe['id'], recipe['id']) for recipe in self.recipes]

            self.recipe_dropdown = OptionMenu(left_frame, self.recipe_var, *translated_recipes)
            self.recipe_dropdown.config(bg="#4f4f4f", fg="white", font=("Arial", 12))
            self.recipe_dropdown.pack(pady=10, fill=X)
        else:
            self.recipe_dropdown = Label(left_frame, text="Нет доступных рецептов", font=("Arial", 12), fg="white", bg="#2e2e2e")
            self.recipe_dropdown.pack(pady=20)

        # Ввод количества
        self.amount_label = Label(left_frame, text="Количество продукта (по умолчанию 90)", font=("Arial", 12), fg="white", bg="#2e2e2e")
        self.amount_label.pack(pady=10)

        # Поле ввода количества
        self.amount_entry = Entry(left_frame, font=("Arial", 12), bg="#4f4f4f", fg="white")
        self.amount_entry.pack(pady=10)

        self.calculate_button = Button(left_frame, text="Рассчитать", command=self.calculate_reactants, bg="#1e7e34", fg="white", font=("Arial", 12))
        self.calculate_button.pack(pady=10)

        self.update_button = Button(left_frame, text="Обновить рецепты", command=self.update_data_async, bg="#0067a1", fg="white", font=("Arial", 12))
        self.update_button.pack(pady=10)

        # Правый контейнер для вывода
        right_frame = Frame(self.root, bg="#2e2e2e")
        right_frame.pack(side=RIGHT, padx=20, pady=20, fill=BOTH, expand=True)

        self.result_label = Label(right_frame, text="Результаты:", font=("Arial", 14), fg="white", bg="#2e2e2e")
        self.result_label.pack(pady=10)

        self.result_text = Text(right_frame, height=20, width=50, wrap=WORD, font=("Courier", 12), bg="#3c3c3c", fg="white", padx=10, pady=10)
        self.result_text.pack(pady=10, fill=BOTH, expand=True)

    def calculate_reactants(self):
        """Вычисляет количество реагентов на основе выбранного рецепта с учетом составных реагентов."""
        selected_recipe_translated = self.recipe_var.get()
        if selected_recipe_translated == "Выберите рецепт":
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите рецепт.")
            return

        # Ищем оригинальный id рецепта
        selected_recipe = None
        for recipe in self.recipes:
            translated_name = self.translations.get(recipe['id'], recipe['id'])
            if translated_name == selected_recipe_translated:
                selected_recipe = recipe
                break

        if selected_recipe:
            product_name = list(selected_recipe.get('products', {}).keys())[0]
            product_amount_str = self.amount_entry.get()

            # Если поле пустое, использовать значение по умолчанию (90 единиц вещества)
            if not product_amount_str:
                product_amount = 90
            else:
                try:
                    product_amount = int(product_amount_str)
                except ValueError:
                    messagebox.showwarning("Предупреждение", "Введите корректное количество!")
                    return

            result_str = self.resolve_reactants(selected_recipe['id'], product_amount, target_product=selected_recipe['id'])

            self.result_text.delete(1.0, END)
            self.result_text.insert(END, result_str)

        else:
            messagebox.showerror("Ошибка", "Не удалось найти рецепт.")

    def resolve_reactants(self, recipe_id, amount_needed, depth=0, target_product=None, include_header=True,
                          visited=None):
        """Рекурсивно определяет состав реагентов, компактно и с пометками для вложенных рецептов."""

        def format_amount(value):
            """Форматирует количество: удаляет лишние нули, если они не нужны."""
            return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else str(int(value))

        if visited is None:
            visited = set()

        recipe = self.recipe_dict.get(recipe_id)
        if not recipe:
            return f"{' ' * (depth * 2)}Ошибка: Рецепт {recipe_id} не найден.\n"

        products = recipe.get("products", {})
        reactants = recipe.get("reactants", {})

        if target_product is None:
            target_product = max(products, key=products.get, default=None)

        if not target_product or target_product not in products:
            return f"{' ' * (depth * 2)}Ошибка: Продукт {target_product} не найден в рецепте {recipe_id}.\n"

        product_amount = products[target_product]
        multiplier = amount_needed / product_amount

        translated_product = self.translations.get(target_product, target_product)
        has_reactants = bool(reactants)

        result_str = ""

        # Добавляем заголовок продукта, если требуется
        if include_header:
            suffix = " [р]" if has_reactants else ""
            header_line = f"{' ' * (depth * 2)}{format_amount(amount_needed)} {translated_product}{suffix}"
            if "minTemp" in recipe:
                header_line += f" (мин. температура: {recipe['minTemp']}K)"
            header_line += ":\n" if has_reactants else "\n"
            result_str += header_line

        # Обработка реагентов
        for reactant, info in reactants.items():
            required_amount = info["amount"]
            is_catalyst = info.get("catalyst", False)
            final_amount = required_amount if is_catalyst else required_amount * multiplier

            translated_name = self.translations.get(reactant, reactant)
            catalyst_note = " (катализатор)" if is_catalyst else ""
            is_nested = reactant in self.recipe_dict and not is_catalyst
            suffix = " [р]" if is_nested else ""

            # Определяем отступ для текущего реагента
            line_indent = (depth + 1) * 2 if include_header else depth * 2
            line = f"{' ' * line_indent}{format_amount(final_amount)} {translated_name}{suffix}{catalyst_note}\n"
            result_str += line

            # Если реагент вложенный и не посещён, обрабатываем его рецепт
            if is_nested and reactant not in visited:
                visited.add(reactant)
                # Рекурсивно получаем состав реагентов без заголовка
                reactants_str = self.resolve_reactants(
                    recipe_id=reactant,
                    amount_needed=final_amount,
                    depth=depth + 1,
                    target_product=reactant,
                    include_header=False,
                    visited=visited
                )
                result_str += reactants_str

        return result_str

    def update_data_async(self):
        """Обновление данных асинхронно с GitHub."""
        update_thread = threading.Thread(target=self.update_data)
        update_thread.start()

    def update_data(self):
        """Загружает новые данные рецептов с GitHub и сохраняет в файл."""
        try:
            url = "https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/c107ced0a8a8090cd0e1b32f68b79cc7ca431420/Resources/Prototypes/Recipes/Reactions/medicine.yml"
            response = requests.get(url)
            if response.status_code == 200:
                with open("recipes.yml", "w", encoding="utf-8") as f:
                    f.write(response.text)
                messagebox.showinfo("Обновление", "Рецепты успешно обновлены.")
                # Используем безопасную загрузку YAML
                self.load_recipes()
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить новые рецепты.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при обновлении данных: {e}")


if __name__ == "__main__":
    root = Tk()
    app = ReagentCalculatorApp(root)
    root.mainloop()
