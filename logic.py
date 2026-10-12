"""Data handling and recipe calculation for the SS14 chemical calculator.

Every function receives the application window (``app``) as its first
argument, but only touches its plain Python state (recipe dictionaries,
colours, ...) or emits its signals, so worker threads may call them safely.
"""
import os
import re

import requests
import yaml

from data import DEFAULT_DEPTH_COLORS

RECIPE_FOLDER = 'recipes'
TRANSLATION_FOLDER = 'translations'

# The original Tk version ordered recipes with a Russian first collation.
_SORT_ORDER = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz'
_SORT_TABLE = str.maketrans({char: chr(1000 + index) for index, char in enumerate(_SORT_ORDER)})


def recipe_sort_key(name):
    """Sort key placing Russian names before Latin ones, as in the Tk app."""
    return name.lower().translate(_SORT_TABLE)


def setup_dirs(app):
    """Create the data folders the application reads its files from."""
    for folder in (RECIPE_FOLDER, TRANSLATION_FOLDER):
        os.makedirs(folder, exist_ok=True)


def custom_yaml_loader(stream):
    """YAML loader that understands the ``!type:`` tags used by SS14."""

    class CustomLoader(yaml.SafeLoader):
        pass

    def multi_constructor(loader, tag_suffix, node):
        if isinstance(node, yaml.MappingNode):
            return {'type': tag_suffix, **loader.construct_mapping(node)}
        return {'type': tag_suffix}

    CustomLoader.add_multi_constructor('!type:', multi_constructor)
    CustomLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: loader.construct_mapping(node),
    )
    return CustomLoader(stream)


def filter_recipes(raw_data):
    """Yield only the reaction entries that describe a usable recipe."""
    for entry in raw_data:
        if isinstance(entry, dict) and entry.get('type') == 'reaction' and 'id' in entry and 'reactants' in entry:
            yield entry


def format_amount(value):
    """Render a reagent amount the way the Tk version did (``45``, ``22.5``)."""
    rounded = f"{value:.2f}"
    if '.' not in rounded:
        return str(int(value))
    return rounded.rstrip('0').rstrip('.')


def get_best_match(app, search_term):
    """Return the recipe that matches *search_term* best (used by Enter)."""
    best_score = -1
    best_match = None
    term = search_term.lower()
    for recipe in app.recipes:
        normalized_id = recipe['id'].lower().replace(' ', '')
        translated = app.translations.get(normalized_id, recipe['id']).lower()

        score = 0
        if term in translated:
            score += 2
        if term in recipe['id'].lower():
            score += 1
        if translated.startswith(term):
            score += 1

        if score > best_score:
            best_score = score
            best_match = recipe

    return best_match


def load_translations(app):
    """Read every ``.ftl`` file of the translations folder into memory."""
    app.translations = {}
    for filename in sorted(os.listdir(TRANSLATION_FOLDER)):
        if not filename.endswith('.ftl'):
            continue
        try:
            with open(os.path.join(TRANSLATION_FOLDER, filename), encoding='utf-8') as handle:
                content = handle.read()
        except OSError as exc:
            print(f'Ошибка загрузки перевода {filename}: {exc}')
            continue

        entries = re.findall(r'^reagent-name-([\w-]+)\s*=\s*(.+)$', content, re.MULTILINE)
        for reagent, translation in entries:
            translation = translation.strip().strip('"')
            if not translation:
                continue
            key = reagent.replace('-', '').lower()
            app.translations[key] = translation[0].upper() + translation[1:]


def load_recipes(app):
    """Read every ``.yml`` file of the recipes folder into memory."""
    app.recipes = []
    available = []

    for filename in sorted(os.listdir(RECIPE_FOLDER)):
        if not filename.endswith('.yml'):
            continue
        try:
            with open(os.path.join(RECIPE_FOLDER, filename), encoding='utf-8') as handle:
                data = yaml.load(handle, Loader=custom_yaml_loader)
        except Exception as exc:
            print(f'Ошибка загрузки {filename}: {exc}')
            continue
        if not data:
            continue

        category = filename[:-len('.yml')]
        if category not in available:
            available.append(category)
        for recipe in filter_recipes(data):
            recipe_id = recipe.get('id', '')
            if recipe_id.endswith('Drink'):
                recipe['id'] = recipe_id[:-len('Drink')]
            recipe['category'] = category
            app.recipes.append(recipe)

    app.recipe_dict = {recipe['id']: recipe for recipe in app.recipes}
    app.recipes.sort(key=lambda recipe: recipe['id'].lower())
    # Configured sources first, then categories that only exist as local files.
    app.available_categories = list(app.recipe_categories) + [
        category for category in available if category not in app.recipe_categories
    ]


def update_queue(app):
    """Return ``(destination, url, group)`` for every remote source."""
    queue = []
    for sources, folder, suffix, group in (
        (app.recipe_categories, RECIPE_FOLDER, '.yml', 'recipes'),
        (app.translation_files, TRANSLATION_FOLDER, '.ftl', 'translations'),
    ):
        for name, url in sources.items():
            if isinstance(url, str) and url.startswith(('http://', 'https://')):
                queue.append((os.path.join(folder, f'{name}{suffix}'), url, group))
    return queue


def _download(url, destination):
    """Save *url* into *destination*; return an error message or ``None``."""
    try:
        response = requests.get(url, timeout=15)
    except Exception as exc:
        return str(exc)
    if response.status_code != 200:
        return f'статус {response.status_code}'
    try:
        with open(destination, 'w', encoding='utf-8') as handle:
            handle.write(response.text)
    except OSError as exc:
        return f'не удалось записать файл ({exc})'
    return None


def update_data(app):
    """Download all configured recipes and translations (worker thread).

    Progress is reported through ``app.progress_changed`` and the outcome
    through ``app.data_update_finished``; both are queued across threads.
    """
    report = {'recipes': [], 'translations': []}
    queue = update_queue(app)
    try:
        for step, (destination, url, group) in enumerate(queue, start=1):
            error = _download(url, destination)
            if error:
                report[group].append(f'{os.path.basename(destination)}: {error}')
            app.progress_changed.emit(step)
    except Exception as exc:  # never leave the button disabled
        report['translations'].append(f'неожиданная ошибка: {exc}')
    finally:
        app.data_update_finished.emit(report)


def resolve_reactants(app, recipe_id, amount_needed, depth=0,
                      target_product=None, include_header=True, visited=None):
    """Yield ``(text, colour)`` lines for *recipe_id* and all of its reactants.

    The reaction tree is walked depth first, so the caller only has to render
    the yielded lines in order to reproduce the original output.
    """
    if visited is None:
        visited = set()

    palette = app.depth_colors or DEFAULT_DEPTH_COLORS
    colour = palette[depth % len(palette)]

    recipe = app.recipe_dict.get(recipe_id)
    if recipe is None:
        yield f"{'  ' * depth}Ошибка: Рецепт {recipe_id} не найден", colour
        return

    products = recipe.get('products', {})
    reactants = recipe.get('reactants', {})
    effects = recipe.get('effects', [])
    mixer_categories = recipe.get('requiredMixerCategories', [])

    is_electrolysis = 'Electrolysis' in mixer_categories
    is_centrifuge = 'Centrifuge' in mixer_categories
    is_shake = 'Shake' in mixer_categories
    is_stir = 'Stir' in mixer_categories
    is_instant = bool(effects) and not products

    if target_product is None and products:
        target_product = next(iter(products))
    product_amount = products.get(target_product, 0) if target_product else 0
    multiplier = amount_needed / product_amount if product_amount and not is_electrolysis and not is_instant else 0

    if (is_centrifuge or is_electrolysis) and reactants:
        base_amount = next(iter(reactants.values())).get('amount', 0)
        multiplier = amount_needed / base_amount if base_amount else 0
    elif is_instant:
        multiplier = amount_needed

    if include_header:
        normalized_id = recipe_id.lower().replace(' ', '')
        header = f"{'  ' * depth}{format_amount(amount_needed)} {app.translations.get(normalized_id, recipe_id)}"
        if is_electrolysis:
            header += ' [ЭЛЕКТРОЛИЗ]'
        elif is_centrifuge:
            header += ' [ЦЕНТРИФУГА]'
        elif is_instant:
            header += ' [МГНОВЕННАЯ РЕАКЦИЯ]'
        elif is_shake:
            header += ' [ВЗБОЛТАТЬ]'
        elif is_stir:
            header += ' [ПЕРЕМЕШАТЬ]'
        if 'minTemp' in recipe:
            header += f"(мин. темп:{recipe['minTemp']}K)"
        if reactants:
            header += ':'
        yield header, colour

    for reactant, info in reactants.items():
        is_catalyst = info.get('catalyst', False)
        final_amount = info.get('amount', 0) * (multiplier if not is_catalyst else 1)
        normalized_reactant = reactant.lower().replace(' ', '').replace('-', '')
        line = f"{'  ' * (depth + 1)}{format_amount(final_amount)} {app.translations.get(normalized_reactant, reactant)}"

        if reactant in app.recipe_dict:
            component_recipe = app.recipe_dict[reactant]
            if 'minTemp' in component_recipe:
                line += f" [р](мин. темп:{component_recipe['minTemp']}K)"
            else:
                line += ' [р]'
        if is_catalyst:
            line += ' (катализатор)'
        yield line, colour

        if reactant in app.recipe_dict and reactant not in visited:
            yield from resolve_reactants(
                app,
                recipe_id=reactant,
                amount_needed=final_amount,
                depth=depth + 1,
                target_product=reactant,
                include_header=False,
                visited={*visited, reactant},
            )

    def product_lines(title):
        parts = []
        for product, amount in products.items():
            normalized_product = product.lower().replace(' ', '').replace('-', '')
            parts.append(f"{format_amount(amount * multiplier)} {app.translations.get(normalized_product, product)}")
        if parts:
            yield f"{'  ' * (depth + 1)}{title}: {' + '.join(parts)}", colour

    def effect_lines():
        effects_text = []
        for effect in effects:
            if not isinstance(effect, dict):
                effects_text.append(str(effect))
                continue
            effect_type = effect.get('type', '').split(':')[-1]
            details = []
            if effect_type == 'CreateGas':
                details.append(f"Создает газ: {effect.get('gas', 'Неизвестно')}")
            elif effect_type == 'PopupMessage':
                details.append(f"Сообщение: {', '.join(effect.get('messages', []))}")
            elif effect_type == 'EmpReactionEffect':
                details.append(f"ЭМИ радиус: {effect.get('maxRange', 0)}м")
            effects_text.append(f"{effect_type} ({'; '.join(details)})" if details else effect_type)
        if effects_text:
            yield f"{'  ' * (depth + 1)}Эффекты: {' | '.join(effects_text)}", colour

    if is_electrolysis and products:
        yield from product_lines('Продукты электролиза')

    if is_centrifuge and products:
        yield from product_lines('Продукты центрифуги')
    elif is_instant and effects:
        yield from effect_lines()
