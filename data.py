# Centralized static data/constants for the Qt application
APP_TITLE = 'SS14 Химический калькулятор by i_love_Megumin'

# Корни репозиториев
_WIZARDS = 'https://raw.githubusercontent.com/space-wizards/space-station-14/refs/heads/master/Resources'
_CORVAX = 'https://raw.githubusercontent.com/space-syndicate/space-station-14/refs/heads/master/Resources'
_SS220 = 'https://raw.githubusercontent.com/SerbiaStrong-220/space-station-14/refs/heads/master/Resources'
_MONOLITH = 'https://raw.githubusercontent.com/SerbiaStrong-220/Monolith/refs/heads/master/Resources'

# Рецепты ванильной игры — Default.
BASE_RECIPE_CATEGORIES = {
    'Медикаменты': f'{_WIZARDS}/Prototypes/Recipes/Reactions/medicine.yml',
    'Химикаты': (
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/chemicals.yml',
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/cleaning.yml',
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/fun.yml',
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/pyrotechnic.yml',
    ),
    'Ботаника': f'{_WIZARDS}/Prototypes/Recipes/Reactions/botany.yml',
    'Напитки': f'{_WIZARDS}/Prototypes/Recipes/Reactions/drinks.yml',
    'Еда': f'{_WIZARDS}/Prototypes/Recipes/Reactions/food.yml',
    'Остальное': (
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/biological.yml',
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/gas.yml',
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/single_reagent.yml',
        f'{_WIZARDS}/Prototypes/Recipes/Reactions/soap.yml',
    ),
}

# Переводы для базовых рецептов — русская локаль Corvax.
BASE_TRANSLATION_URLS = (
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/biological.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/botany.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/chemicals.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/cleaning.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/elements.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/fun.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/gases.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/medicine.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/narcotics.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/pyrotechnic.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/toxins.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/drink/alcohol.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/drink/drinks.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/drink/juice.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/drink/soda.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/food/condiments.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/food/food.ftl',
    f'{_CORVAX}/Locale/ru-RU/reagents/meta/consumable/food/ingredients.ftl',
)

# Встроенные пресеты: имя -> своё содержимое. При первом запуске (когда в
# settings.cfg ещё нет ключа presets) имена записываются в конфиг, а папки
# presets/<Имя>/ создаются с этими данными; дальше пресеты живут как
# обычные пользовательские (заполнить/переименовать/удалить через вкладку
# «Данные»). Пресет — только ссылки, файлы скачиваются общим механизмом:
#   custom_recipes     — категория -> ссылка (или список ссылок) на .yml
#                        (имя файла считается из пути ссылки и получает
#                        суффикс); повторять ключ категории нельзя —
#                        Python молча оставит последний, используйте список;
#   custom_translations — список ссылок на .ftl (имя файла то же правило).
# None у имени означает заводские ссылки приложения (как у свежей
# установки).
BUILTIN_PRESETS = {
    'Default': None,
    'Corvax': {
        'custom_recipes': {
            'Медикаменты': f'{_CORVAX}/Prototypes/Recipes/Reactions/medicine.yml',
            'Химикаты': (
                f'{_CORVAX}/Prototypes/Recipes/Reactions/chemicals.yml',
                f'{_CORVAX}/Prototypes/Recipes/Reactions/cleaning.yml',
                f'{_CORVAX}/Prototypes/Recipes/Reactions/fun.yml',
                f'{_CORVAX}/Prototypes/Recipes/Reactions/pyrotechnic.yml',
            ),
            'Ботаника': f'{_CORVAX}/Prototypes/Recipes/Reactions/botany.yml',
            'Напитки': (
                f'{_CORVAX}/Prototypes/Recipes/Reactions/drinks.yml',
                f'{_CORVAX}/Prototypes/Corvax/Recipes/Reactions/drinks.yml',
            ),
            'Еда': f'{_CORVAX}/Prototypes/Recipes/Reactions/food.yml',
            'Остальное': (
                f'{_CORVAX}/Prototypes/Recipes/Reactions/soap.yml',
                f'{_CORVAX}/Prototypes/Recipes/Reactions/biological.yml',
                f'{_CORVAX}/Prototypes/Recipes/Reactions/gas.yml',
                f'{_CORVAX}/Prototypes/Recipes/Reactions/single_reagent.yml',
                ),
        },
        'custom_translations': BASE_TRANSLATION_URLS,
    },
    'SS220 Exodus': {
        'custom_recipes': {
            'Медикаменты': (
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/medicine.yml',
                f'{_MONOLITH}/Prototypes/_Exodus/Recipes/Reactions/medicine.yml',
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/medicine.yml',
                f'{_MONOLITH}/Prototypes/_NF/Recipes/Reactions/medicine.yml',
                f'{_MONOLITH}/Prototypes/_Exodus/Virology/chemistry.yml',
            ),
            'Химикаты': (
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/chemicals.yml',
                f'{_MONOLITH}/Prototypes/_NF/Recipes/Reactions/chemicals.yml',
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/pyrotechnic.yml',
                f'{_MONOLITH}/Prototypes/_NF/Recipes/Reactions/pyrotechnic.yml',
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/cleaning.yml',
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/fun.yml',
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/economy.yml',
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/fentanyl.yml',
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/pyrotechnics.yml',
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/synthesis.yml',
            ),
            'Ботаника': f'{_MONOLITH}/Prototypes/Recipes/Reactions/botany.yml',
            'Напитки': (
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/drinks.yml',
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/drinks.yml',
                f'{_MONOLITH}/Prototypes/_NF/Recipes/Reactions/drinks.yml',
            ),
            'Еда': f'{_MONOLITH}/Prototypes/Recipes/Reactions/food.yml',
            'Остальное': (
                f'{_MONOLITH}/Prototypes/_Mono/Recipes/Reactions/technological.yml',
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/biological.yml',
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/gas.yml',
                f'{_MONOLITH}/Prototypes/Recipes/Reactions/single_reagent.yml',
            ),
        },
        'custom_translations': (
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/biological.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/botany.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/chemicals.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/cleaning.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/elements.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/fun.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/gases.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/medicine.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/narcotics.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/pyrotechnic.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/toxins.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/drink/alcohol.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/drink/drinks.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/drink/juice.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/drink/soda.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/food/condiments.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/food/food.ftl',
            f'{_MONOLITH}/Locale/ru-RU/reagents/meta/consumable/food/ingredients.ftl',
            f'{_MONOLITH}/Locale/ru-RU/Goobstation/reagents/meta/medicine.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_DV/reagents/meta/consumable/food/condiments.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Exodus/reagents/medicine.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Mono/reagents/medicine.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Mono/reagents/narcotics.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Mono/reagents/technological.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Mono/reagents/meta/consumable/drink/drinks.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/biological.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/chemicals.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/medicine.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/narcotics.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/consumable/drink/drinks.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/consumable/food/food.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_NF/reagents/meta/consumable/food/ingredients.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Exodus/virology/virology.ftl',
            f'{_MONOLITH}/Locale/ru-RU/_Exodus/virology/integration.ftl',
        ),
    },
    'SS220 Main': {
        'custom_recipes': {
            'Медикаменты': (
                f'{_SS220}/Prototypes/Recipes/Reactions/medicine.yml',
                f'{_SS220}/Prototypes/SS220/Recipes/Reactions/medicine.yml',
            ),
            'Химикаты': (
                f'{_SS220}/Prototypes/Recipes/Reactions/fun.yml',
                f'{_SS220}/Prototypes/SS220/Recipes/Reactions/fun.yml',
                f'{_SS220}/Prototypes/Recipes/Reactions/chemicals.yml',
                f'{_SS220}/Prototypes/Recipes/Reactions/cleaning.yml',
                f'{_SS220}/Prototypes/Recipes/Reactions/pyrotechnic.yml',
                f'{_SS220}/Prototypes/SS220/Recipes/Reactions/nacrotics.yml',
            ),
            'Ботаника': f'{_SS220}/Prototypes/Recipes/Reactions/botany.yml',
            'Напитки': (
                f'{_SS220}/Prototypes/Recipes/Reactions/drinks.yml',
                f'{_SS220}/Prototypes/SS220/Recipes/Reactions/drinks.yml',
            ),
            'Еда': (
                f'{_SS220}/Prototypes/Recipes/Reactions/food.yml',
                f'{_SS220}/Prototypes/SS220/Recipes/Reactions/food.yml',
            ),
            'Остальное': (
                f'{_SS220}/Prototypes/Recipes/Reactions/soap.yml',
                f'{_SS220}/Prototypes/Recipes/Reactions/biological.yml',
                f'{_SS220}/Prototypes/Recipes/Reactions/gas.yml',
                f'{_SS220}/Prototypes/Recipes/Reactions/single_reagent.yml',
            ),
        },
        'custom_translations': (
            f'{_SS220}/Locale/ru-RU/reagents/meta/biological.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/botany.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/chemicals.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/cleaning.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/elements.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/fun.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/gases.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/medicine.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/narcotics.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/pyrotechnic.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/toxins.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/drink/alcohol.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/drink/drinks.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/drink/juice.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/drink/soda.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/food/condiments.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/food/food.ftl',
            f'{_SS220}/Locale/ru-RU/reagents/meta/consumable/food/ingredients.ftl',
            f'{_SS220}/Locale/ru-RU-220/reagents/meta/medicine.ftl',
        ),
    },
}

COLOR_NAMES = {
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

DEFAULT_DEPTH_COLORS = [
    "#FFFFFF", "#4EC9B0", "#569CD6",
    "#B5CEA8", "#CE9178", "#C586C0"
]


def color_name(hex_code):
    """Return the human readable name of *hex_code* or ``None`` when unknown."""
    wanted = (hex_code or '').upper()
    for name, code in COLOR_NAMES.items():
        if code.upper() == wanted:
            return name
    return None


# Текст вкладки «О приложении». Поля {} заполняет ui.py при сборке вкладки,
# чтобы версия приложения подставлялась из app.current_version.
ABOUT_INFO = (
    "SS14 Химический калькулятор\n"
    "Версия: {version}\n"
    "Автор: i_love_Megumin aka R-R0S\n"
    "\n"
    "Вы можете добавить свои собственные рецепты,\n"
    "достаточно положить файл .yml с рецептом в папку recipes\n"
    "или добавить ссылку на файл рецептов, например с GitHub\n"
    "проекта, на котором вы играете. Аналогично с переводами.\n"
    "\n"
    "Если вы добавили рецепты, не забудьте обновить данные!\n"
    "\n"
    "Если вы столкнулись с проблемой —\n"
    "попробуйте сбросить настройки и перезапустить приложение!"
)

UPDATE_MESSAGES = [
            "Доступно обновление на GitHub! ⬆️",
            "Обновись! Новые фичи ждут! 🚀",
            "Обновления не сделают тебе больно 😇",
            "Твоя версия устарела! 🕒",
            "Новая версия уже вышла! 🎉",
            "Не пропусти важные изменения! 🔔",
            "Новая версия — как экзотермическая реакция! 🔥",
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
            "Пора на орбитальный апдейт! 🛰️",
            "Чё каво, апдейт есть? 👀",
            "Это не баг, а фича! 🪲",
            "Аманда, у тебя фрезон убежал! 🥶",
            "А если серьёзно, я скучаю по Эмгыр де Шнайдер 🐱"
]
