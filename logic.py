"""Data handling and recipe calculation for the SS14 chemical calculator.

Every function receives the application window (``app``) as its first
argument, but only touches its plain Python state (recipe dictionaries,
colours, ...) or emits its signals, so worker threads may call them safely.
"""
import json
import os
import random
import re
import shutil
from urllib.parse import urlsplit

import requests
import yaml

from data import BUILTIN_PRESETS, DEFAULT_DEPTH_COLORS

RECIPE_FOLDER = 'recipes'
TRANSLATION_FOLDER = 'translations'
PRESETS_FOLDER = 'presets'
PRESET_FILE = 'preset.cfg'

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
    mapping = getattr(app, 'recipe_file_categories', {})

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

        stem = filename[:-len('.yml')]
        category = mapping.get(stem, stem)
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
    # Configured labels first (several files may share one label), then the
    # labels that only exist as local files.
    ordered = []
    for stem in app.recipe_categories:
        label = mapping.get(stem, stem)
        if label not in ordered:
            ordered.append(label)
    app.available_categories = ordered + [
        category for category in available if category not in ordered
    ]


def local_files(folder, suffix):
    """Return the base names of the downloaded files present in *folder*."""
    try:
        names = os.listdir(folder)
    except OSError:
        return set()
    return {name[:-len(suffix)] for name in names if name.endswith(suffix)}


def preset_path(name):
    """Folder holding the files and the settings of preset *name*."""
    return os.path.join(PRESETS_FOLDER, name)


def preset_file_counts(name):
    """Return ``(recipes, translations)`` link counts of preset *name*.

    A preset holds links only; the files are downloaded like any other.
    A category may carry a list of links, and every one of them counts.
    """
    try:
        content = read_preset(name)
    except (OSError, ValueError):
        return 0, 0
    if not content:
        return 0, 0
    recipes = sum(1 for value in content['custom_recipes'].values()
                  for _ in _source_urls(value))
    return recipes, len(content['custom_translations'])


def read_preset(name):
    """Return the preset's links: ``{category: url}`` and a URL list.

    Old presets stored file names as keys with the labels held apart;
    they are converted on the fly.  A preset without a settings file
    holds no links at all; an unreadable file raises, so the caller can
    leave the current data alone.
    """
    path = os.path.join(preset_path(name), PRESET_FILE)
    try:
        with open(path, encoding='utf-8') as handle:
            content = json.load(handle)
    except FileNotFoundError:
        content = {}
    if not isinstance(content, dict):
        raise ValueError(f'{path}: ожидается словарь настроек')
    translations = content.get('custom_translations')
    if isinstance(translations, dict):
        # старый формат: ключи — имена файлов, категории — отдельным полем
        labels = content.get('recipe_file_categories') or {}
        recipes = {labels.get(stem, stem): url
                   for stem, url in (content.get('custom_recipes') or {}).items()}
        return {'custom_recipes': recipes,
                'custom_translations': list(translations.values())}
    return {
        'custom_recipes': dict(content.get('custom_recipes') or {}),
        'custom_translations': list(translations or []),
    }


def write_preset(name, content):
    """Store preset *name*'s links (a preset holds no files)."""
    folder = preset_path(name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, PRESET_FILE), 'w', encoding='utf-8') as handle:
        json.dump({
            'custom_recipes': dict(content['custom_recipes']),
            'custom_translations': list(content['custom_translations']),
        }, handle, indent=2)


def preset_content(recipe_links, translation_links, labels):
    """Convert the local sources into the preset format.

    The categories come from the stored labels; sources sharing one
    category are saved as a list of links.  The files themselves do not
    belong to a preset — their names are recreated on load.
    """
    recipes = {}
    for stem, url in recipe_links.items():
        recipes.setdefault(labels.get(stem, stem), []).append(url)
    return {
        'custom_recipes': {category: urls[0] if len(urls) == 1 else urls
                           for category, urls in recipes.items()},
        'custom_translations': list(translation_links.values()),
    }


def preset_links(content):
    """Convert preset content into local sources.

    Returns ``(recipe_links, translation_links, labels)``; every file
    stem is freshly suffixed, exactly like when adding a link.
    """
    recipe_links, labels = recipe_links_and_labels(content['custom_recipes'])
    return recipe_links, links_from_urls(content['custom_translations']), labels


def clear_data_files():
    """Delete every downloaded recipe and translation file."""
    for folder, suffix in ((RECIPE_FOLDER, '.yml'), (TRANSLATION_FOLDER, '.ftl')):
        _clear_files(folder, suffix)


def delete_preset(name):
    """Drop the preset folder with all of its files."""
    shutil.rmtree(preset_path(name), ignore_errors=True)


def rename_preset(old, new):
    """Move the preset folder to a new name."""
    os.rename(preset_path(old), preset_path(new))


def ensure_preset_folders(app):
    """Create presets/ and one folder per listed preset with its content."""
    os.makedirs(PRESETS_FOLDER, exist_ok=True)
    for name in app.presets:
        if not name or name in ('.', '..') \
                or any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name):
            continue
        folder = preset_path(name)
        if os.path.isdir(folder):
            continue
        content = BUILTIN_PRESETS.get(name)
        if name in BUILTIN_PRESETS and content is None:
            content = preset_content(app.base_recipe_categories,
                                     app.base_translation_files,
                                     app.base_recipe_labels)
        try:
            os.makedirs(folder, exist_ok=True)
            if content:
                write_preset(name, content)
        except OSError as exc:
            print(f'Не удалось создать пресет {name}: {exc}')


def _folder_files(folder, suffix):
    """Sorted file names of *folder* ending with *suffix*."""
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    return sorted(name for name in names if name.endswith(suffix))


def _clear_files(folder, suffix):
    """Delete every *suffix* file of *folder*."""
    for file_name in _folder_files(folder, suffix):
        try:
            os.remove(os.path.join(folder, file_name))
        except OSError as exc:
            print(f'Не удалось удалить {folder}/{file_name}: {exc}')


def file_stem_from_url(url):
    """Return the file stem suggested by the path of *url*."""
    stem = os.path.splitext(os.path.basename(urlsplit(url).path))[0]
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', stem)


def _random_hex():
    return ''.join(random.choices('0123456789abcdef', k=5))


def fresh_file_stem(base, taken):
    """Return a new *base* stem carrying a random hex suffix.

    Every newly created file gets its own suffix, so a name can never be
    mistaken for a category label or clash with a future file.
    """
    while True:
        candidate = f'{base}-{_random_hex()}'
        if candidate not in taken:
            return candidate


def links_from_urls(urls):
    """Map every URL to its own suffixed file stem (the name comes from the URL)."""
    links = {}
    taken = set()
    for url in urls:
        base = file_stem_from_url(url) or 'file'
        stem = fresh_file_stem(base, taken)
        links[stem] = url
        taken.add(stem)
    return links


def _source_urls(value):
    """Yield every URL of an authoring source value.

    A source is either a single URL or a list/tuple of them; anything
    else is reported instead of silently dropped.
    """
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, str):
                yield item
            else:
                print(f'Пропущена некорректная ссылка: {item!r}')
    else:
        print(f'Пропущена некорректная ссылка: {value!r}')


def recipe_links_and_labels(base):
    """Map every ``{category: url(s)}`` source to its own suffixed file.

    Returns ``(links, categories)``: file stem -> url and file stem ->
    category label.  A category may hold several links, given as a list;
    the file name comes from the URL only, so it stays free of the
    category name.  A repeated URL is reported on the console: it would
    fetch the very same file twice.
    """
    links, categories, taken = {}, {}, set()
    owners = {}
    for label, value in base.items():
        for url in _source_urls(value):
            base_name = file_stem_from_url(url) or 'file'
            stem = fresh_file_stem(base_name, taken)
            links[stem] = url
            categories[stem] = label
            taken.add(stem)
            if url in owners:
                print(f'Предупреждение: одна и та же ссылка в категориях '
                      f'«{owners[url]}» и «{label}» — файл скачается дважды: {url}')
            else:
                owners[url] = label
    return links, categories


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
