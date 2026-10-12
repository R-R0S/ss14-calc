#!/usr/bin/env python3
"""SS14 chemical recipe calculator — Qt (PySide6) port of the Tk application.

The window itself lives here: state, settings, search, calculation and the
worker threads.  Widgets are built by :mod:`ui`, data work is done by
:mod:`logic` and the constants by :mod:`data`.
"""
import json
import os
import random
import re
import shutil
import sys
import threading
import webbrowser
from html import escape

import requests
from PySide6 import QtCore, QtGui, QtWidgets

from data import (APP_TITLE, BASE_RECIPE_CATEGORIES, BASE_TRANSLATION_FILES,
                  COLOR_NAMES, DEFAULT_DEPTH_COLORS, UPDATE_MESSAGES, color_name)
import logic
import ui

SETTINGS_FILE = 'settings.cfg'
GITHUB_RELEASE_API = 'https://api.github.com/repos/R-R0S/ss14-calc/releases/latest'
DEFAULT_OPACITY = 0.95
DEFAULT_LANGUAGE = 'ru'
MAX_SEARCH_RESULTS = 15
_HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')
# The search popup shows ``translated (category)``; Enter has to match by name.
_TRAILING_CATEGORY = re.compile(r'\s*\([^()]*\)\s*$')


class ReagentCalculatorQt(QtWidgets.QMainWindow):
    """Main window: search, calculation, overlay and settings."""

    # Emitted by the worker threads, handled by the slots below.
    progress_changed = QtCore.Signal(int)
    data_update_finished = QtCore.Signal(object)
    update_available = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.current_version = '2.0'

        self.base_recipe_categories = dict(BASE_RECIPE_CATEGORIES)
        self.base_translation_files = dict(BASE_TRANSLATION_FILES)
        self.COLOR_NAMES = dict(COLOR_NAMES)

        # configured sources (name -> url) and data loaded from disk
        self.recipe_categories = {}
        self.translation_files = {}
        self.custom_recipe_links = {}
        self.custom_translation_links = {}
        self.available_categories = []
        self.recipes = []
        self.recipe_dict = {}
        self.recipe_map = {}
        self.translations = {}

        # settings
        self.overlay_opacity = DEFAULT_OPACITY
        self.language = DEFAULT_LANGUAGE
        self.depth_colors = list(DEFAULT_DEPTH_COLORS)

        # overlay and settings dialog state
        self.overlay_window = None
        self.overlay_content = None
        self.opacity_slider = None
        self.opacity_label = None
        self.language_combo = None
        self.color_combos = []
        self.color_previews = []
        self.avatar_movie = None

        logic.setup_dirs(self)
        self.load_settings()
        logic.load_translations(self)
        logic.load_recipes(self)
        ui.init_ui(self)

        self.progress_changed.connect(self._show_progress)
        self.data_update_finished.connect(self._finish_data_update)
        self.update_available.connect(self._announce_update)
        self.check_for_updates_async()

    # ------------------------------------------------------------------ data

    def reload_data(self):
        """Re-read the local files and refresh the category list."""
        logic.load_translations(self)
        logic.load_recipes(self)
        self.refresh_categories()

    def refresh_categories(self):
        """Rebuild the category box, keeping the selection when possible."""
        current = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(self.available_categories)
        index = self.category_combo.findText(current)
        if index < 0 and self.category_combo.count():
            index = 0
        self.category_combo.setCurrentIndex(index)
        self.category_combo.blockSignals(False)
        self.update_recipes_list()

    def update_recipes_list(self, *_args):
        """Fill the recipe box with the selected category, sorted as in Tk."""
        category = self.category_combo.currentText()
        names = []
        self.recipe_map = {}
        if category:
            for recipe in self.recipes:
                if recipe['category'] != category:
                    continue
                translated = self.translations.get(recipe['id'].lower().replace(' ', ''), recipe['id'])
                names.append(translated)
                self.recipe_map[translated] = recipe['id']
            names.sort(key=logic.recipe_sort_key)

        selected = self.recipe_combo.currentText()
        self.recipe_combo.blockSignals(True)
        self.recipe_combo.clear()
        self.recipe_combo.addItems(names)
        if selected in names:
            self.recipe_combo.setCurrentText(selected)
        self.recipe_combo.blockSignals(False)

    # ---------------------------------------------------------------- search

    def on_search(self, text):
        """Remember the typed text and refresh the popup on the next loop pass.

        The refresh is deliberately deferred: picking a suggestion inserts its
        text into the line edit first and emits ``activated`` afterwards, so
        rebuilding the completer model inside the ``textChanged`` handler would
        invalidate the index the completer is about to hand over and the recipe
        would never be selected.
        """
        self.search_query = text.strip()
        self.search_delay.start()

    def refresh_search_suggestions(self):
        """Fill the search popup with the first recipes matching ``search_query``."""
        term = self.search_query.lower()
        model = QtGui.QStandardItemModel()
        if term:
            for recipe in self.recipes:
                translated = self.translations.get(recipe['id'].lower().replace(' ', ''), recipe['id'])
                if term not in translated.lower() and term not in recipe['id'].lower():
                    continue
                item = QtGui.QStandardItem(f'{translated} ({recipe["category"]})')
                item.setData(self._recipe_record(recipe), QtCore.Qt.UserRole)
                model.appendRow(item)
                if model.rowCount() >= MAX_SEARCH_RESULTS:
                    break
        self.search_completer.setModel(model)
        self.search_model = model
        self.search_completer.setCompletionPrefix(self.search_query)

    def _search_term(self):
        """The typed text without the ``(category)`` suffix the popup adds."""
        return _TRAILING_CATEGORY.sub('', self.search_edit.text()).strip().lower()

    def _recipe_record(self, recipe):
        """Bundle everything the UI needs in order to select *recipe*."""
        return {
            'id': recipe['id'],
            'category': recipe.get('category', ''),
            'translated': self.translations.get(recipe['id'].lower().replace(' ', ''), recipe['id']),
        }

    def on_search_suggestion(self, index):
        """A suggestion from the search popup was picked."""
        record = index.data(QtCore.Qt.UserRole)
        if isinstance(record, dict):
            self._select_recipe(record)
        else:  # the model was rebuilt before the index arrived: search by text
            self.on_search_enter()

    def on_search_enter(self):
        """Enter picks the best match and calculates it, like in the Tk app."""
        term = self._search_term()
        if not term:
            return
        best = logic.get_best_match(self, term)
        if best:
            self._select_recipe(self._recipe_record(best), fallback_to_first=True)

    def _select_recipe(self, record, fallback_to_first=False):
        """Show *record* in the category/recipe boxes and calculate it."""
        category_index = self.category_combo.findText(record['category'])
        if category_index < 0:
            return
        if category_index != self.category_combo.currentIndex():
            self.category_combo.setCurrentIndex(category_index)  # refills the recipe box

        position = self.recipe_combo.findText(record['translated'])
        if position < 0:
            if not fallback_to_first or not self.recipe_combo.count():
                return
            position = 0
        self.recipe_combo.setCurrentIndex(position)
        self.calculate_reactants()

    # ---------------------------------------------------------- calculation

    def calculate_reactants(self):
        """Render the selected recipe together with all of its reactants."""
        selected = self.recipe_combo.currentText()
        if not selected:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите рецепт')
            return
        recipe_id = self.recipe_map.get(selected)
        if not recipe_id or recipe_id not in self.recipe_dict:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', 'Рецепт не найден')
            return
        try:
            amount = float(self.amount_entry.text() or 90)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', 'Некорректное количество')
            return

        scrollbar = self.result_text.verticalScrollBar()
        scroll_position = scrollbar.value()
        lines = logic.resolve_reactants(self, recipe_id=recipe_id, amount_needed=amount)
        # ``white-space: pre-wrap`` keeps the per depth indentation (HTML would
        # collapse it) while still wrapping long lines, like the Tk text widget.
        html = ''.join(
            f'<div style="color: {colour}; font-family: monospace; white-space: pre-wrap;">'
            f'{escape(text)}</div>\n'
            for text, colour in lines
        )
        self.result_text.setHtml(html)
        scrollbar.setValue(scroll_position)
        ui.update_overlay_content(self)

    # --------------------------------------------------------------- overlay

    def toggle_overlay(self):
        """Show or hide the overlay window."""
        if self.overlay_window is not None and self.overlay_window.isVisible():
            self.overlay_window.hide()
            self.overlay_btn.setText('Показать оверлей')
            return
        if self.overlay_window is None:
            ui.create_overlay_window(self)
        self.overlay_window.show()
        self.overlay_window.raise_()
        ui.update_overlay_content(self)
        self.overlay_btn.setText('Скрыть оверлей')

    def update_overlay_opacity(self, value):
        """Apply a new overlay opacity (0.3 … 1.0)."""
        self.overlay_opacity = float(value)
        if self.opacity_label is not None:
            self.opacity_label.setText(f'Прозрачность оверлея - {round(self.overlay_opacity * 100)}%')
        if self.overlay_window is not None:
            ui.apply_overlay_opacity(self.overlay_window, self.overlay_opacity)

    def update_color(self, level):
        """Apply a newly selected colour for a recursion depth."""
        if level >= len(self.color_combos):
            return
        hex_color = self.COLOR_NAMES.get(self.color_combos[level].currentText())
        if hex_color is None:
            return
        self.depth_colors[level] = hex_color
        if level < len(self.color_previews):
            self.color_previews[level].setStyleSheet(
                f'background-color: {hex_color}; border: 1px solid #777777;')
        if self.result_text.toPlainText():
            self.calculate_reactants()

    # ------------------------------------------------------------- settings

    def create_settings_window(self):
        ui.create_settings_window(self)

    def reload_links_table(self):
        ui.reload_links_table(self)

    def edit_link(self, is_edit=False):
        ui.edit_link(self, is_edit=is_edit)

    def delete_link(self):
        ui.delete_link(self)

    def save_settings(self):
        """Write the current settings to disk, in the format Tk used."""
        settings = {
            'opacity': self.overlay_opacity,
            'language': self.language,
            'depth_colors': list(self.depth_colors),
            'custom_recipes': dict(self.custom_recipe_links),
            'custom_translations': dict(self.custom_translation_links),
        }
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as handle:
                json.dump(settings, handle, indent=2)
        except OSError as exc:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить настройки: {exc}')

    def load_settings(self):
        """Read settings.cfg, falling back to the bundled defaults."""
        try:
            with open(SETTINGS_FILE, encoding='utf-8') as handle:
                settings = json.load(handle)
        except FileNotFoundError:
            settings = None
        except (OSError, ValueError) as exc:
            print(f'Ошибка загрузки настроек: {exc}')
            settings = None

        if isinstance(settings, dict):
            self.overlay_opacity = _read_opacity(settings.get('opacity'))
            self.language = settings.get('language', DEFAULT_LANGUAGE)
            self.depth_colors = _read_colors(settings.get('depth_colors'))
            self.custom_recipe_links = settings.get('custom_recipes') or dict(self.base_recipe_categories)
            self.custom_translation_links = settings.get('custom_translations') \
                or dict(self.base_translation_files)
        else:
            self.custom_recipe_links = dict(self.base_recipe_categories)
            self.custom_translation_links = dict(self.base_translation_files)

        self.recipe_categories.update(self.custom_recipe_links)
        self.translation_files.update(self.custom_translation_links)

    def reset_settings(self):
        """Restore every default and drop all downloaded data."""
        answer = QtWidgets.QMessageBox.question(
            self,
            'Сброс настроек',
            'Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?')
        if answer != QtWidgets.QMessageBox.Yes:
            return

        try:
            if os.path.exists(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)
            shutil.rmtree(logic.RECIPE_FOLDER, ignore_errors=True)
            shutil.rmtree(logic.TRANSLATION_FOLDER, ignore_errors=True)
            logic.setup_dirs(self)

            self.overlay_opacity = DEFAULT_OPACITY
            self.language = DEFAULT_LANGUAGE
            self.depth_colors = list(DEFAULT_DEPTH_COLORS)
            self.custom_recipe_links = dict(self.base_recipe_categories)
            self.custom_translation_links = dict(self.base_translation_files)
            self.recipe_categories = dict(self.custom_recipe_links)
            self.translation_files = dict(self.custom_translation_links)

            self.reload_data()
            self._sync_settings_widgets()
            if self.overlay_window is not None:
                ui.apply_overlay_opacity(self.overlay_window, self.overlay_opacity)
        except OSError as exc:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Не удалось сбросить настройки: {exc}')
            return

        QtWidgets.QMessageBox.information(
            self,
            'Сброс настроек',
            'Настройки успешно сброшены!\n'
            'Нажмите «Обновить данные», чтобы загрузить рецепты заново.')

    def _sync_settings_widgets(self):
        """Push freshly reset values into an open settings dialog."""
        if self.opacity_slider is not None:
            self.opacity_slider.setValue(round(self.overlay_opacity * 100))
        if self.opacity_label is not None:
            self.opacity_label.setText(f'Прозрачность оверлея - {round(self.overlay_opacity * 100)}%')
        if self.language_combo is not None:
            index = self.language_combo.findData(self.language)
            self.language_combo.setCurrentIndex(index if index >= 0 else 0)
        for level, combo in enumerate(self.color_combos):
            combo.blockSignals(True)
            combo.setCurrentText(color_name(self.depth_colors[level]) or combo.itemText(0))
            combo.blockSignals(False)
        for level, preview in enumerate(self.color_previews):
            preview.setStyleSheet(
                f'background-color: {self.depth_colors[level]}; border: 1px solid #777777;')

    # -------------------------------------------------------- updating data

    def update_data_async(self):
        """Download every configured recipe and translation."""
        self.progress_bar.setRange(0, len(logic.update_queue(self)))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('Загружено %v из %m')
        self.progress_bar.setVisible(True)
        self.update_btn.setEnabled(False)
        threading.Thread(target=logic.update_data, args=(self,), daemon=True).start()

    @QtCore.Slot(int)
    def _show_progress(self, value):
        self.progress_bar.setValue(value)

    @QtCore.Slot(object)
    def _finish_data_update(self, report):
        """React to a finished download: reload everything and report."""
        self.progress_bar.setVisible(False)
        self.update_btn.setEnabled(True)
        self.reload_data()

        failures = []
        if report.get('recipes'):
            failures.append('Рецепты:\n- ' + '\n- '.join(report['recipes']))
        if report.get('translations'):
            failures.append('Переводы:\n- ' + '\n- '.join(report['translations']))
        if failures:
            QtWidgets.QMessageBox.warning(
                self, 'Обновление', 'Не удалось загрузить:\n\n' + '\n\n'.join(failures))
        else:
            QtWidgets.QMessageBox.information(self, 'Обновление', 'Данные успешно обновлены!')

    # -------------------------------------------------------- update checker

    def check_for_updates_async(self):
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        """Ask GitHub for the newest release (worker thread, no UI calls)."""
        try:
            response = requests.get(GITHUB_RELEASE_API, timeout=10)
        except Exception as exc:
            print(f'Ошибка проверки обновлений: {exc}')
            return
        if response.status_code != 200:
            return
        try:
            release = response.json()
            latest_version = release['tag_name'].lstrip('v')
            release_url = release['html_url']
        except (ValueError, KeyError, TypeError) as exc:
            print(f'Ошибка проверки обновлений: {exc}')
            return
        if self.compare_versions(latest_version, self.current_version) > 0:
            self.update_available.emit(release_url)

    @QtCore.Slot(str)
    def _announce_update(self, release_url):
        self.setWindowTitle(f'{APP_TITLE} v{self.current_version} | {random.choice(UPDATE_MESSAGES)}')
        answer = QtWidgets.QMessageBox.question(
            self,
            'Доступно обновление',
            'Обнаружена новая версия!\n\nХотите перейти на страницу релиза?')
        if answer == QtWidgets.QMessageBox.Yes:
            webbrowser.open(release_url)

    @staticmethod
    def compare_versions(v1, v2):
        """Compare two dotted version strings: 1 when v1 is newer."""
        try:
            parts1 = [int(part) for part in v1.split('.')]
            parts2 = [int(part) for part in v2.split('.')]
        except ValueError:
            return 0
        for part1, part2 in zip(parts1, parts2):
            if part1 > part2:
                return 1
            if part1 < part2:
                return -1
        return 0 if len(parts1) == len(parts2) else (1 if len(parts1) > len(parts2) else -1)

    # --------------------------------------------------------------- window

    def closeEvent(self, event):
        if self.overlay_window is not None:
            self.overlay_window.hide()
        super().closeEvent(event)


def _read_opacity(value):
    try:
        return min(max(float(value), 0.3), 1.0)
    except (TypeError, ValueError):
        return DEFAULT_OPACITY


def _read_colors(values):
    """Return the six depth colours, padded with defaults when necessary."""
    valid = [value for value in (values or []) if isinstance(value, str) and _HEX_COLOR.match(value)]
    return (valid + list(DEFAULT_DEPTH_COLORS))[:6]


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QtGui.QIcon(ui.icon_path()))
    window = ReagentCalculatorQt()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
