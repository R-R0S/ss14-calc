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
            "Dexalin": "Дексалин",
            "Dermaline": "Дермалин",
            "Hyronalin": "Гидролин",
            "DexalinPlus": "Дексалин Плюс",
            # Добавьте переводы для названий рецептов
            "Recipe1": "Рецепт 1",
            "Recipe2": "Рецепт 2",
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

            result_str = self.resolve_reactants(selected_recipe['id'], product_amount)

            self.result_text.delete(1.0, END)
            self.result_text.insert(END, result_str)

        else:
            messagebox.showerror("Ошибка", "Не удалось найти рецепт.")

    def resolve_reactants(self, recipe_id, amount_needed, depth=0):
        """Рекурсивно решает, какие реагенты нужны для производства продукта, с учетом составных реагентов."""
        recipe = self.recipe_dict.get(recipe_id)
        if not recipe:
            return "Ошибка: Рецепт не найден."

        reactants = recipe.get("reactants", {})
        products = recipe.get("products", {})
        if not products:
            return f"Ошибка: Нет продуктов в рецепте {recipe_id}."

        product_name = list(products.keys())[0]
        product_amount = products[product_name]
        multiplier = amount_needed / product_amount

        result_str = f"{'  ' * depth}{amount_needed:.2f} {product_name} (Рецепт {recipe_id}):\n"

        for reactant, info in reactants.items():
            required_amount = info["amount"]
            is_catalyst = info.get("catalyst", False)
            final_amount = required_amount if is_catalyst else required_amount * multiplier

            result_str += f"{'  ' * (depth + 1)}{reactant}: {final_amount:.2f}" + (" (катализатор)" if is_catalyst else "") + "\n"

            # Рекурсивно проходим, если реагент является составным
            if reactant in self.recipe_dict and not is_catalyst:
                result_str += self.resolve_reactants(reactant, final_amount, depth + 2)

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
