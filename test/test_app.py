"""End-to-end interaction tests for the Qt calculator.

Run with ``python test/test_app.py`` (add ``QT_QPA_PLATFORM=offscreen`` on a
machine without a display).  Every check happens in a scratch directory, so
the local ``settings.cfg``, ``recipes/`` and ``translations/`` are never
touched: the data folders are copied first and the working directory is
switched to the copy.
"""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import traceback

from PySide6 import QtWidgets, QtCore, QtGui, QtTest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import main as app_main  # noqa: E402
import logic  # noqa: E402
import ui  # noqa: E402
from data import (BASE_RECIPE_CATEGORIES, BASE_TRANSLATION_URLS,
                  BUILTIN_PRESETS, DEFAULT_DEPTH_COLORS)  # noqa: E402

FAILURES = []
MODAL_LOG = []

# QCompleter's popup view has no C++ parent, so Shiboken treats it as owned
# by the Python wrapper and deletes the C++ view with the wrapper, while
# QCompleter still points at it.  The wrappers obtained below are kept for
# the whole run.
POPUP_REFS = []


def check(condition, message):
    if condition:
        print(f'  ok   {message}')
    else:
        print(f'  FAIL {message}')
        FAILURES.append(message)


def mouse(widget, kind, global_pos, buttons=QtCore.Qt.MouseButton.NoButton,
          button=QtCore.Qt.MouseButton.NoButton):
    local = QtCore.QPointF(global_pos - widget.mapToGlobal(QtCore.QPoint(0, 0)))
    event = QtGui.QMouseEvent(kind, local, global_pos, button, buttons,
                              QtCore.Qt.KeyboardModifier.NoModifier)
    QtWidgets.QApplication.sendEvent(widget, event)


def drag(app, widget, delta):
    """Press on the centre of *widget*, move by *delta*, release."""
    centre = widget.mapToGlobal(QtCore.QPoint(0, 0)) + QtCore.QPoint(widget.width() // 2,
                                                                     widget.height() // 2)
    target = centre + QtCore.QPoint(*delta)
    mouse(widget, QtCore.QEvent.Type.MouseButtonPress, centre,
          QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.LeftButton)
    mouse(widget, QtCore.QEvent.Type.MouseMove, target,
          QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.NoButton)
    mouse(widget, QtCore.QEvent.Type.MouseButtonRelease, target,
          QtCore.Qt.MouseButton.NoButton, QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()


def render_alpha(widget, point):
    """Paint *widget* into an ARGB image and return the alpha at *point*."""
    image = QtGui.QImage(widget.size(), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(image)
    widget.render(painter, QtCore.QPoint(0, 0))
    painter.end()
    return image.pixelColor(point).alpha()


def background_alpha(widget):
    """Alpha of the painted window background (the text area is transparent)."""
    return render_alpha(widget, QtCore.QPoint(6, widget.height() - 6))


def border_alpha(widget):
    """Alpha of the one pixel border on the left edge."""
    return render_alpha(widget, QtCore.QPoint(0, widget.height() // 2))


def text_alpha(widget):
    """Strongest alpha inside the overlay text area.

    Glyph pixels are painted by the text widget itself, so they must stay
    fully opaque no matter which background alpha the window uses.
    """
    content = widget.content
    image = QtGui.QImage(content.size(), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(image)
    content.render(painter, QtCore.QPoint(0, 0))
    painter.end()
    best = 0
    for y in range(0, image.height(), 2):
        for x in range(0, image.width(), 2):
            best = max(best, image.pixel(x, y) >> 24)
    return best


def start_modal_sweeper(app, action=None, answer=None):
    """Run *action(modal)* (or click *answer*) as soon as a modal pops up.

    Detection happens from a timer, but the reaction is deferred by one event
    loop pass: a ``QTimer`` never re-enters its own handler, so any modal the
    reaction itself opens would deadlock the loop otherwise.
    """
    state = {'done': False, 'seen': set()}

    def handle(modal):
        if not modal.isVisible():
            return
        if isinstance(modal, QtWidgets.QMessageBox):
            state['done'] = True
            for button in modal.buttons():
                if answer and answer.lower() in button.text().replace('&', '').lower():
                    button.click()
                    return
            modal.reject()
        elif isinstance(modal, QtWidgets.QDialog):
            if action is not None:
                action(modal)  # may raise further modals of its own
            state['done'] = True
            modal.accept()

    def sweep():
        modal = app.activeModalWidget()
        if modal is None or modal in state['seen']:
            return
        state['seen'].add(modal)
        if isinstance(modal, QtWidgets.QMessageBox):
            MODAL_LOG.append(f'{modal.windowTitle()}: {modal.text()}')
        else:
            MODAL_LOG.append(modal.windowTitle())
        QtCore.QTimer.singleShot(0, lambda current=modal: handle(current))

    timer = QtCore.QTimer()
    timer.timeout.connect(sweep)
    timer.start(20)
    state['timer'] = timer
    return state


def stop_sweeper(state):
    """Drop the sweeper, whether or not it found its menu."""
    timer = state.timer if isinstance(state, PopupSweeper) else state['timer']
    timer.stop()


class PopupSweeper(QtCore.QObject):
    """Click the action labelled *label* as soon as a menu pops up.

    A ``QMenu`` is a popup, not a modal, so ``activeModalWidget`` never sees
    it; the click is deferred by one loop pass for the same reason as with a
    modal.  The menu is hidden afterwards: the actions are checkable, and
    triggering one of those toggles it without closing the popup, which would
    leave ``QMenu.exec`` running forever.

    The menu is caught from a timer instead of an event filter: by the time
    ``exec`` has entered its own nested loop, a timer is the only thing that
    still ticks, and ``activePopupWidget`` names the menu exactly while it
    lives.  A ``QMenu`` may appear without ever being a popup of the app, so
    the timer also looks at the visible top level widgets.
    """

    def __init__(self, app, label):
        super().__init__(app)
        self._app = app
        self._label = label
        self._fired = False
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._sweep)
        self.timer.start(20)

    def _sweep(self):
        if self._fired:
            return
        menu = self._app.activePopupWidget()
        if not isinstance(menu, QtWidgets.QMenu):
            for widget in self._app.topLevelWidgets():
                if (isinstance(widget, QtWidgets.QMenu) and widget.isVisible()
                        and widget not in (self._app.activeWindow(),)):
                    menu = widget
                    break
        if not isinstance(menu, QtWidgets.QMenu):
            return
        for action in menu.actions():
            if action.text() != self._label:
                continue
            self._fired = True
            # The recalculation may raise a dialog of its own, so it runs on
            # the next loop pass, not inside the menu's own nested loop.
            QtCore.QTimer.singleShot(0, lambda m=menu, a=action: (
                a.trigger(), m.hide()))
            return


def start_popup_sweeper(app, label):
    """Install a :class:`PopupSweeper` that clicks *label* in the next menu."""
    return PopupSweeper(app, label)


# --------------------------------------------------------------- test steps

def test_startup(app, win):
    print('startup')
    check(win.category_combo.count() > 0, 'category box is filled')
    check(win.recipe_combo.count() > 0, 'recipe box is filled for the first category')
    check(win.amount_entry.text() == '90', 'amount defaults to 90')
    check(win.overlay_btn.text() == 'Показать оверлей', 'overlay button starts as hidden')
    check(len(win.available_categories) >= len(win.recipe_categories),
          'local categories are listed too')
    check(all(isinstance(url, str) for url in win.recipe_categories.values()),
          'recipe sources are urls/paths, not recipe lists')
    check(win.avatar_movie is not None and win.avatar_movie.state() == QtGui.QMovie.Running,
          'avatar gif is running and referenced')
    check(not os.path.exists('recipes') or os.listdir('recipes'), 'recipe files are loaded')


def test_data_py(app, win):
    print('data.py links')

    def good_url(url, suffix):
        return (isinstance(url, str)
                and url.startswith(('http://', 'https://'))
                and url.endswith(suffix))

    def source_urls(value):
        if isinstance(value, str):
            return (value,)
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return ()

    check(all(isinstance(name, str) and name.strip() for name in BASE_RECIPE_CATEGORIES),
          'every recipe source has a name')
    bad = [name for name, value in BASE_RECIPE_CATEGORIES.items()
           if not all(good_url(url, '.yml') for url in source_urls(value))]
    check(not bad, f'every recipe link is an http(s) .yml URL {bad}')
    check(all(good_url(url, '.ftl') for url in BASE_TRANSLATION_URLS),
          'every translation link is an http(s) .ftl URL')

    for name, content in BUILTIN_PRESETS.items():
        check(bool(name) and name not in ('.', '..')
              and not any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name),
              f'the built-in preset name is usable {name!r}')
        if content is None:
            continue
        if not isinstance(content, dict):
            check(False, f'the {name} preset is a dict or None')
            continue
        check(set(content) <= {'custom_recipes', 'custom_translations'},
              f'the {name} preset holds only links')
        recipes = content.get('custom_recipes') or {}
        translations = content.get('custom_translations') or ()
        check(isinstance(recipes, dict)
              and all(isinstance(category, str) and category.strip()
                      and all(good_url(url, '.yml') for url in source_urls(value))
                      for category, value in recipes.items()),
              f'the {name} recipe links are categories to .yml URLs')
        check(isinstance(translations, (list, tuple))
              and all(good_url(url, '.ftl') for url in translations),
              f'the {name} translation links are a list of .ftl URLs')

    # a category may hold several links; every one becomes its own file
    links, cats = logic.recipe_links_and_labels({
        'Медикаменты': ('https://example.com/main/medicine.yml',
                        'https://example.com/ss220/medicine.yml'),
        'Химикаты': 'https://example.com/chemicals.yml',
    })
    check(len(links) == 3 and set(cats.values()) == {'Медикаменты', 'Химикаты'},
          'a category may hold several links')

    # a repeated link is reported instead of silently doubling the file
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        logic.recipe_links_and_labels({
            'Медикаменты': 'https://example.com/medicine.yml',
            'Запасные': 'https://example.com/medicine.yml',
        })
    check('Предупреждение' in buffer.getvalue(),
          'a repeated link is reported on the console')

    # sources sharing a category are saved back as a list
    grouped = logic.preset_content(
        {'a1': 'https://example.com/main/medicine.yml',
         'a2': 'https://example.com/ss220/medicine.yml'},
        {'b1': 'https://example.com/x.ftl'},
        {'a1': 'Медикаменты', 'a2': 'Медикаменты'})
    check(grouped['custom_recipes'] == {
        'Медикаменты': ['https://example.com/main/medicine.yml',
                        'https://example.com/ss220/medicine.yml']},
        'sources sharing a category are saved as a list')


def test_search(app, win):
    print('search')
    check(hasattr(logic, 'get_best_match'), 'logic.get_best_match exists')
    win.search_edit.setText('дифен')
    app.processEvents()
    check(win.search_model.rowCount() > 0, 'suggestions are collected while typing')
    completion = win.search_completer.completionModel()
    record = completion.index(0, 0).data(QtCore.Qt.UserRole)
    check(isinstance(record, dict) and 'translated' in record,
          'suggestion carries the recipe record')

    # A real click on the popup: Qt fills the line edit first and emits
    # ``activated`` afterwards, so the model has to survive that.
    expected = record['translated']
    win.recipe_combo.setCurrentIndex(-1)
    win.search_completer.complete()
    app.processEvents()
    popup = win.search_completer.popup()
    QtTest.QTest.mouseClick(popup.viewport(), QtCore.Qt.MouseButton.LeftButton,
                            QtCore.Qt.KeyboardModifier.NoModifier,
                            popup.visualRect(completion.index(0, 0)).center())
    app.processEvents()
    check(win.recipe_combo.currentText() == expected,
          f'a click on a suggestion opens the recipe ({win.recipe_combo.currentText()})')
    check(win.result_text.toPlainText() != '', 'a clicked suggestion is calculated')

    # Enter on the popup item
    win.search_edit.setText('')
    win.recipe_combo.setCurrentIndex(-1)
    win.search_edit.setText('дифен')
    app.processEvents()
    win.search_completer.complete()
    app.processEvents()
    popup.setCurrentIndex(completion.index(0, 0))
    QtTest.QTest.keyClick(popup, QtCore.Qt.Key_Return)
    app.processEvents()
    check(win.recipe_combo.currentText() == expected,
          f'Enter on the popup opens the recipe ({win.recipe_combo.currentText()})')

    # Enter on the text the popup has just filled in, which carries the
    # "(category)" suffix
    win.search_edit.setText('Дифенгидрамин (medicine)')
    app.processEvents()
    win.on_search_enter()
    check(win.recipe_combo.currentText() == expected,
          'Enter still matches the completed text')

    win.search_edit.setText('')
    win.recipe_combo.setCurrentIndex(-1)
    win.search_edit.setText('дифен')
    app.processEvents()
    win.on_search_enter()
    check(win.recipe_combo.currentIndex() >= 0, 'Enter selects the best match')
    check(win.result_text.toPlainText() != '', 'Enter calculates it')

    # The Tk app scores every recipe for an unknown term and keeps the best,
    # so a nonsense query falls back to the first recipe instead of failing.
    win.search_edit.setText('ёлка-палка-морковка')
    MODAL_LOG.clear()
    sweeper = start_modal_sweeper(app)
    win.on_search_enter()
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.result_text.toPlainText() != '', 'a nonsense query still calculates')
    check(not MODAL_LOG, 'a nonsense query raises no error')


def popup_dominant_color(widget, step=4):
    """Most frequent rendered colour of *widget* as an (r, g, b) tuple."""
    image = widget.grab().toImage()
    counts = {}
    for y in range(0, image.height(), step):
        for x in range(0, image.width(), step):
            color = image.pixelColor(x, y)
            key = (color.red(), color.green(), color.blue())
            counts[key] = counts.get(key, 0) + 1
    return max(counts, key=counts.get)


def popup_frame_is_dark(widget):
    """True when no near-white pixel sits in the outermost popup rows."""
    image = widget.grab().toImage()
    edge = []
    for offset in range(3):
        edge += [image.pixelColor(x, offset) for x in range(image.width())]
        edge += [image.pixelColor(offset, y) for y in range(image.height())]
    return all(min(color.red(), color.green(), color.blue()) < 200 for color in edge)


def test_popup_styles(app, win):
    """Every popup paints its own dark background, not the system theme."""
    print('popup styles')

    win.category_combo.showPopup()
    app.processEvents()
    combo_popup = win.category_combo.view().window()
    check(min(popup_dominant_color(combo_popup)) < 100, 'combo popup list is dark')
    check(popup_frame_is_dark(combo_popup), 'combo popup frame is dark')
    win.category_combo.hidePopup()

    win.search_edit.setText('дифен')
    app.processEvents()
    # grab() renders the popup view even while it is hidden, so the suite
    # never has to show a real completer popup.
    completer_popup = win.search_completer.popup()
    check(min(popup_dominant_color(completer_popup)) < 100, 'search popup list is dark')
    check(popup_frame_is_dark(completer_popup), 'search popup frame is dark')
    POPUP_REFS.append(completer_popup)

    # The recipe choice menu from on_result_link(): grab() paints it hidden.
    menu = QtWidgets.QMenu(win)
    for label in ('Первый вариант', 'Второй вариант'):
        menu.addAction(label).setCheckable(True)
    check(min(popup_dominant_color(menu)) < 100, 'recipe choice menu is dark')
    check(popup_frame_is_dark(menu), 'recipe choice menu frame is dark')


def test_calculation(app, win):
    print('calculation')
    win.category_combo.setCurrentIndex(win.category_combo.findText('medicine'))
    app.processEvents()
    names = [win.recipe_combo.itemText(i) for i in range(win.recipe_combo.count())]
    check(names == sorted(names, key=logic.recipe_sort_key),
          'recipes are sorted with the Russian collation')
    win.recipe_combo.setCurrentIndex(0)
    before = win.result_text.toPlainText()
    win.amount_entry.setText('abc')
    sweeper = start_modal_sweeper(app)
    win.calculate_reactants()
    app.processEvents()
    stop_sweeper(sweeper)
    check('Некорректное количество' in ''.join(MODAL_LOG), 'bad amount is rejected')
    check(win.result_text.toPlainText() == before, 'a bad amount changes no result')

    win.amount_entry.setText('90')
    win.calculate_reactants()
    text = win.result_text.toPlainText()
    check('90' in text and '\n' in text, 'result contains indented reactant lines')
    html = win.result_text.toHtml()
    check('monospace' in html, 'result uses a monospace font')
    indents = {len(line) - len(line.lstrip(' ')) for line in text.splitlines()}
    check(0 in indents and max(indents) >= 2,
          f'every recursion depth gets its own indentation {sorted(indents)}')

    scrollbar = win.result_text.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())
    win.calculate_reactants()
    check(scrollbar.value() == scrollbar.maximum(), 'scroll position survives a recalculation')

    # Катализатор: пометка, тег [р] и развёрнутая собственная рецептура.
    index = win.recipe_combo.findText('Дифенгидрамин')
    check(index >= 0, 'the catalyst test recipe is present in medicine')
    if index >= 0:
        win.recipe_combo.setCurrentIndex(index)
        win.amount_entry.setText('10')
        win.calculate_reactants()
        text = win.result_text.toPlainText()
        lines = text.splitlines()
        catalyst = next((line for line in lines if 'Серная кислота' in line), '')
        check('(катализатор)' in catalyst,
              f'the catalyst line is marked ({catalyst.strip()})')
        check(catalyst.count('(катализатор)') == 1,
              f'the catalyst marker is not duplicated ({catalyst.strip()})')
        check('[р]' in catalyst,
              f'a catalyst with a recipe gets the [р] tag ({catalyst.strip()})')
        depth = (len(catalyst) - len(catalyst.lstrip(' '))) // 2
        nested = [line for line in lines
                  if (len(line) - len(line.lstrip(' '))) // 2 > depth]
        check(len(nested) >= 3 and any('Сера' in line for line in nested),
              f'the catalyst recipe is expanded below its line ({len(nested)} lines)')


def test_reagent_recipe_choice(app, win):
    print('reagent recipe choice')
    win.category_combo.setCurrentIndex(win.category_combo.findText('medicine'))
    app.processEvents()
    index = win.recipe_combo.findText('Гамма-препарат')
    check(index >= 0, 'the gamma recipe is present in medicine')
    if index < 0:
        return
    win.recipe_combo.setCurrentIndex(index)
    win.amount_entry.setText('90')
    win.calculate_reactants()

    # Дифенгидрамин теперь имеет два рецепта: имя становится ссылкой, но
    # обычный текст результата остаётся прежним.
    check('reagent:Diphenhydramine' in win.result_text.toHtml(),
          'the reagent with two recipes carries a link')
    check('text-decoration: underline' not in win.result_text.toHtml(),
          'no reactant name is underlined in the result')
    text = win.result_text.toPlainText()
    check('Дифенгидрамин' in text and '[р]' in text,
          'the linked reagent keeps its name and the [р] tag')
    check('Сера' in text, 'the default recipe is expanded by default')

    choices = dict(logic.recipe_choices(win, 'Diphenhydramine'))
    check(set(choices) == {'Diphenhydramine', 'DiphenhydramineFromEthanol'},
          f'both recipes are offered ({sorted(choices)})')
    check(choices['Diphenhydramine'] == 'Дифенгидрамин',
          f'the labels read like the recipe headers ({choices})')

    win.choose_reagent_recipe('Diphenhydramine', 'DiphenhydramineFromEthanol')
    text = win.result_text.toPlainText()
    check('720' in text and 'Сера' not in text,
          'the alternative recipe drives the tree (720 Этанол, no sulfur)')
    check(win.session_choices == {'Diphenhydramine': 'DiphenhydramineFromEthanol'},
          'the choice is remembered for this tree')

    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check('reagent_recipe_overrides' not in saved,
          'a recipe replacement is not written to settings.cfg')

    # Выбор рецепта по умолчанию убирает запомненную замену целиком.
    win.choose_reagent_recipe('Diphenhydramine', 'Diphenhydramine')
    check(win.session_choices == {}, 'the default recipe clears the choice')
    check('Сера' in win.result_text.toPlainText(), 'the default recipe is back')

    # The root line of a recipe with alternatives carries its own link.
    index = win.recipe_combo.findText('Дифенгидрамин')
    check(index >= 0, 'the ambiguous recipe is directly selectable')
    win.recipe_combo.setCurrentIndex(index)
    win.amount_entry.setText('90')
    win.calculate_reactants()
    check('root:Diphenhydramine' in win.result_text.toHtml(),
          'the root line carries the recipe link')
    check('90 Дифенгидрамин' in win.result_text.toPlainText(),
          'the root line still reads as the header')

    # A pick in the root menu: remembered, recalculated, box untouched.
    sweeper = start_popup_sweeper(app, 'Альтернативный рецепт: DiphenhydramineFromEthanol')
    win.result_text.anchorClicked.emit(QtCore.QUrl('root:Diphenhydramine'))
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.session_choices == {'Diphenhydramine': 'DiphenhydramineFromEthanol'},
          'the root menu remembers the alternative recipe')
    text = win.result_text.toPlainText()
    check('720' in text and 'Сера' not in text,
          'the root line shows the chosen recipe')
    check(win.recipe_combo.currentText() == 'Дифенгидрамин',
          'the recipe box keeps its own selection')

    # An explicit pick in the recipe box supersedes the root override.
    win.recipe_combo.setCurrentIndex(win.recipe_combo.findText('DiphenhydramineFromEthanol'))
    app.processEvents()
    check(win.session_choices == {},
          'an explicit pick in the recipe box drops the root choice')
    win.calculate_reactants()
    check('Сера' not in win.result_text.toPlainText(),
          'the box variant is calculated as the root')

    # Back to the state the following tests expect.
    win.choose_reagent_recipe('Diphenhydramine', 'Diphenhydramine')
    win.recipe_combo.setCurrentIndex(win.recipe_combo.findText('Гамма-препарат'))
    win.calculate_reactants()
    check(win.session_choices == {}, 'the default state is restored')


def test_hidden_recipes(app, win):
    print('hidden recipes')
    win.category_combo.setCurrentIndex(win.category_combo.findText('chemicals'))
    app.processEvents()
    index = win.recipe_combo.findText('Светящаяся смесь')
    check(index >= 0, 'the decomposition fixture is present in chemicals')
    if index < 0:
        return
    win.recipe_combo.setCurrentIndex(index)
    win.amount_entry.setText('90')
    win.calculate_reactants()

    # Центрифуга и электролиз по умолчанию скрыты: строки реактантов есть,
    # но [р] и развёртывания нет.
    html = win.result_text.toHtml()
    text = win.result_text.toPlainText()
    check('Радиевый порошок' in text and 'Радиевая соль' in text,
          'the hidden reagents are still listed')
    check('[р]' not in text and 'Сера' not in text,
          'a decomposition expands nothing by default')
    check('reagent:RadiumPowder' in html and 'reagent:RadiumSalt' in html,
          'the hidden reagents stay clickable')
    # Qt переносит декорацию ссылки в span внутри якоря.
    anchor = re.search(
        r'<a href="reagent:RadiumPowder"><span style="([^"]*)"', html)
    check(anchor is not None and 'underline' not in anchor.group(1),
          'a reagent with one recipe is clickable but not underlined')

    # Меню скрытого по умолчанию разложения предлагает его показать.
    sweeper = start_popup_sweeper(app, 'Показать рецепт')
    win.result_text.anchorClicked.emit(QtCore.QUrl('reagent:RadiumPowder'))
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.session_choices == {'RadiumPowder': 'RadiumPowder'},
          'the show action remembers the decomposition for this tree')
    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check('reagent_recipe_overrides' not in saved,
          'a shown decomposition is not written to settings.cfg')
    text = win.result_text.toPlainText()
    check('Кислород' in text and 'Продукты центрифуги' in text,
          'the shown recipe expands')

    # Показанный рецепт меню предлагает скрыть снова.
    sweeper = start_popup_sweeper(app, 'Скрыть рецепт')
    win.result_text.anchorClicked.emit(QtCore.QUrl('reagent:RadiumPowder'))
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.hidden_recipes == {'RadiumPowder'},
          'the hide action hides the reagent recipe')
    text = win.result_text.toPlainText()
    check('Радиевый порошок' in text and 'Кислород' not in text,
          'the hidden reagent line stays while its recipe disappears')

    # Скрытый по умолчанию электролиз показывается так же.
    sweeper = start_popup_sweeper(app, 'Показать рецепт')
    win.result_text.anchorClicked.emit(QtCore.QUrl('reagent:RadiumSalt'))
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.session_choices.get('RadiumSalt') == 'RadiumSalt',
          'the electrolysis recipe is picked through the menu')
    check('Сера' in win.result_text.toPlainText(),
          'the picked decomposition expands')

    # Выбор собственного рецепта разложения из меню его развивает.
    win.choose_reagent_recipe('RadiumPowder', 'RadiumPowder')
    check('Кислород' in win.result_text.toPlainText(),
          'a recipe pick expands the recipe')
    text = win.result_text.toPlainText()
    check('Продукты центрифуги' in text,
          'the centrifuge recipe runs when chosen explicitly')
    check('Радиевая соль [р]' in text,
          'its reactant carries the [р] tag again')

    # Легаси-ключ на разложение в конфиге игнорируется и вычищается.
    win.session_choices.clear()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        legacy = json.load(handle)
    legacy['reagent_recipe_overrides'] = {'RadiumPowder': 'RadiumPowder'}
    with open(app_main.SETTINGS_FILE, 'w', encoding='utf-8') as handle:
        json.dump(legacy, handle)
    win.load_settings()
    win.calculate_reactants()
    check('Кислород' not in win.result_text.toPlainText(),
          'a legacy decomposition entry in the config expands nothing')
    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check('reagent_recipe_overrides' not in saved,
          'the legacy config key is dropped on save')

    win.hidden_recipes.clear()
    win.session_choices.clear()
    win.save_settings()
    win.calculate_reactants()

    # Скрытие живёт до смены рецепта и не пишется в настройки.
    win.choose_reagent_recipe('RadiumSalt', 'RadiumSalt')
    check('Сера' in win.result_text.toPlainText(),
          'the electrolysis recipe is expanded again')
    win.hidden_recipes.add('RadiumSalt')
    win.calculate_reactants()
    check('Сера' not in win.result_text.toPlainText(),
          'the hidden reagent loses its recipe once more')

    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check('hidden_recipes' not in saved,
          'the hidden recipes are not written to settings.cfg')

    index = win.recipe_combo.findText('Сталь')
    win.recipe_combo.setCurrentIndex(index)
    win.calculate_reactants()
    check(win.hidden_recipes == set(),
          'another recipe in the box starts with nothing hidden')
    check(win.session_choices == {},
          'another recipe in the box starts with no shown decomposition')

    index = win.recipe_combo.findText('Светящаяся смесь')
    win.recipe_combo.setCurrentIndex(index)
    win.calculate_reactants()
    check(win.hidden_recipes == set() and 'Сера' not in win.result_text.toPlainText(),
          'coming back restores the unexpanded default tree')

    # Back to the state the following tests expect.
    win.category_combo.setCurrentIndex(win.category_combo.findText('medicine'))
    app.processEvents()
    index = win.recipe_combo.findText('Гамма-препарат')
    check(index >= 0, 'the overlay recipe is present in medicine')
    win.recipe_combo.setCurrentIndex(index)
    win.amount_entry.setText('90')
    win.calculate_reactants()


def test_byproducts(app, win):
    print('byproducts')

    win.category_combo.setCurrentIndex(win.category_combo.findText('chemicals'))
    app.processEvents()
    index = win.recipe_combo.findText('Крошковая панель')
    check(index >= 0, 'the byproduct fixture is present in chemicals')
    if index < 0:
        return
    win.recipe_combo.setCurrentIndex(index)
    win.amount_entry.setText('10')
    win.calculate_reactants()

    # Grit — добавочный: строка есть и кликабельна, но не развёрнута,
    # в отличие от Steel, у которого есть собственный рецепт.
    html = win.result_text.toHtml()
    text = win.result_text.toPlainText()
    check('Крошка' in text, 'the byproduct reagent is listed')
    check('reagent:Grit' in html, 'the byproduct stays clickable')
    check('Крошка [р]' not in text and 'Алюминий' not in text,
          'a byproduct expands nothing by default')
    check('Сталь [р]' in text and 'Углерод' in text,
          'a reagent with its own recipe still expands')

    # Меню скрытого по умолчанию добавочного предлагает его показать.
    sweeper = start_popup_sweeper(app, 'Показать рецепт')
    win.result_text.anchorClicked.emit(QtCore.QUrl('reagent:Grit'))
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.session_choices == {'Grit': 'SolventMix'},
          'the show action remembers the byproduct recipe for this tree')
    check('Крошка [р]' in win.result_text.toPlainText()
          and 'Алюминий' in win.result_text.toPlainText(),
          'the shown byproduct recipe expands')

    # Выбор рецептуры добавочного продукта сессионный и не сохраняется.
    win.choose_reagent_recipe('Grit', 'SolventMix')
    check(win.session_choices == {'Grit': 'SolventMix'},
          'a byproduct pick stays in the session choices')
    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check('reagent_recipe_overrides' not in saved,
          'a byproduct pick is not written to settings.cfg')

    # Легаси-ключ на добавочный продукт в конфиге игнорируется и вычищается.
    win.session_choices.clear()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        legacy = json.load(handle)
    legacy['reagent_recipe_overrides'] = {'Grit': 'SolventMix'}
    with open(app_main.SETTINGS_FILE, 'w', encoding='utf-8') as handle:
        json.dump(legacy, handle)
    win.load_settings()
    win.calculate_reactants()
    check('Алюминий' not in win.result_text.toPlainText(),
          'a legacy byproduct entry in the config expands nothing')
    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check('reagent_recipe_overrides' not in saved,
          'the legacy config key is dropped on save')

    # Смена рецепта возвращает всё к умолчанию.
    index = win.recipe_combo.findText('Сталь')
    win.recipe_combo.setCurrentIndex(index)
    win.calculate_reactants()
    check(win.session_choices == {} and win.hidden_recipes == set(),
          'another recipe in the box starts with no session choices')

    # Back to the state the following tests expect.
    win.category_combo.setCurrentIndex(win.category_combo.findText('medicine'))
    app.processEvents()
    index = win.recipe_combo.findText('Гамма-препарат')
    check(index >= 0, 'the overlay recipe is still present in medicine')
    win.recipe_combo.setCurrentIndex(index)
    win.amount_entry.setText('90')
    win.calculate_reactants()


def test_overlay(app, win):
    print('overlay')
    win.calculate_reactants()
    win.toggle_overlay()
    app.processEvents()
    overlay = win.overlay_window
    check(overlay is not None and overlay.isVisible(), 'overlay shows')
    check(win.overlay_btn.text() == 'Скрыть оверлей', 'button follows the overlay')
    check(overlay.windowFlags() & QtCore.Qt.WindowStaysOnTopHint, 'overlay stays on top')
    check(overlay.windowFlags() & QtCore.Qt.FramelessWindowHint, 'overlay is frameless')
    check(overlay.minimumSize() == QtCore.QSize(200, 150), 'minimum size matches the Tk app')
    check(overlay.content.toPlainText() == win.result_text.toPlainText(),
          'overlay mirrors the current result')

    # Оверлей показывает те же ссылки и offers the same recipe choice.
    check(isinstance(overlay.content, QtWidgets.QTextBrowser),
          'the overlay content is a link-aware text browser')
    check('reagent:Diphenhydramine' in overlay.content.toHtml(),
          'the overlay carries the recipe links')
    check('text-decoration: underline' not in overlay.content.toHtml(),
          'the overlay does not underline its links')
    sweeper = start_popup_sweeper(app, 'Альтернативный рецепт: DiphenhydramineFromEthanol')
    overlay.content.anchorClicked.emit(QtCore.QUrl('reagent:Diphenhydramine'))
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.session_choices == {'Diphenhydramine': 'DiphenhydramineFromEthanol'},
          'a click in the overlay picks the alternative recipe')
    check('720' in overlay.content.toPlainText(),
          'the overlay shows the newly chosen recipe')
    # Убрать выбор, чтобы остальные тесты видели состояние по умолчанию.
    win.choose_reagent_recipe('Diphenhydramine', 'Diphenhydramine')
    check(win.session_choices == {}, 'the overlay choice is cleared again')
    # the window background carries the alpha on every platform
    check(background_alpha(overlay) == round(win.overlay_opacity * 255),
          'the overlay paints its background')
    handles = {c.objectName()[len(ui.HANDLE_PREFIX):]: c
               for c in overlay.findChildren(QtWidgets.QWidget)
               if c.objectName().startswith(ui.HANDLE_PREFIX)}
    check(set(handles) == {'nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'},
          'eight resize zones exist')

    def rect():
        g = overlay.geometry()
        return (g.x(), g.y(), g.width(), g.height())

    expected = {
        'nw': (130, 120, 270, 380),
        'n': (100, 120, 300, 380),
        'ne': (100, 120, 330, 380),
        'e': (100, 100, 330, 400),
        'se': (100, 100, 330, 420),
        's': (100, 100, 300, 420),
        'sw': (130, 100, 270, 420),
        'w': (130, 100, 270, 400),
    }
    for side in ('nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'):
        overlay.setGeometry(100, 100, 300, 400)
        app.processEvents()
        handles[side].setGeometry(handles[side].geometry())  # keep positions in sync
        overlay._position_handles()
        drag(app, handles[side], (30, 20))
        check(rect() == expected[side], f'{side} edge resize follows the cursor {rect()}')

    # minimum size keeps the opposite corner anchored
    overlay.setGeometry(100, 100, 300, 400)
    app.processEvents()
    overlay._position_handles()
    drag(app, handles['n'], (0, 500))
    check(rect() == (100, 350, 300, 150), f'minimum height is clamped {rect()}')

    overlay.setGeometry(100, 100, 300, 400)
    app.processEvents()
    overlay._position_handles()
    drag(app, handles['w'], (500, 0))
    check(rect() == (200, 100, 200, 400), f'minimum width is clamped {rect()}')

    overlay.setGeometry(100, 100, 300, 400)
    app.processEvents()
    overlay._position_handles()
    drag(app, handles['se'], (-500, -500))
    check(rect() == (100, 100, 200, 150), f'corner respects both minimums {rect()}')

    # the resize zones follow the borders after a resize
    overlay.setGeometry(0, 0, 500, 600)
    app.processEvents()
    se = handles['se'].geometry()
    check((se.x(), se.y()) == (500 - 14, 600 - 14), f'corner zone follows the border {se}')

    # dragging the title bar moves the window
    overlay.setGeometry(100, 100, 300, 400)
    app.processEvents()
    bar = overlay.title_bar
    start = bar.mapToGlobal(QtCore.QPoint(0, 0)) + QtCore.QPoint(40, 10)
    mouse(bar, QtCore.QEvent.Type.MouseButtonPress, start,
          QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.LeftButton)
    mouse(bar, QtCore.QEvent.Type.MouseMove, start + QtCore.QPoint(45, 25),
          QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.NoButton)
    mouse(bar, QtCore.QEvent.Type.MouseButtonRelease, start + QtCore.QPoint(45, 25),
          QtCore.Qt.MouseButton.NoButton, QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    check(rect() == (145, 125, 300, 400), f'title bar drag moves the window {rect()}')

    # the opacity only changes the painted background; the text stays opaque
    win.update_overlay_opacity(0.4)
    check(win.overlay_opacity == 0.4, 'opacity value is stored')
    check(overlay._background_alpha == 102, 'opacity reaches the overlay background')
    check(background_alpha(overlay) == 102, 'the painted background follows the opacity')
    check(overlay.windowOpacity() == 1.0, 'the window itself never turns translucent')
    check(text_alpha(overlay) == 255, 'recipe text is opaque at 40% background')
    overlay.set_background_alpha(0)
    check(border_alpha(overlay) == 45, 'border alpha is untouched by the background')
    check(text_alpha(overlay) == 255, 'recipe text is opaque on a transparent background')
    win.update_overlay_opacity(1.0)

    overlay.closed.emit()
    app.processEvents()
    check(not overlay.isVisible(), 'close button hides the overlay')
    check(win.overlay_btn.text() == 'Показать оверлей', 'button text is restored')
    win.toggle_overlay()
    app.processEvents()
    check(overlay.isVisible(), 'overlay shows again')
    win.toggle_overlay()


def test_settings(app, win):
    print('settings')
    # The tabs are parentless until a dialog adopts them, so this step holds
    # them alive in a local list (a bare call would let Python delete them).
    built_tabs = [ui._build_general_tab(win)]
    check(win.opacity_slider is not None, 'opacity slider exists')
    win.opacity_slider.setValue(55)
    check(abs(win.overlay_opacity - 0.55) < 1e-9, 'slider drives the overlay opacity')
    check('55%' in win.opacity_label.text(), 'opacity label shows the value')
    check(len(win.color_combos) == 6 and len(win.color_previews) == 6, 'six colours with previews')

    win.color_combos[2].setCurrentText('Золото')
    check(win.depth_colors[2] == '#FFD700', 'colour combo updates depth colours')
    check('#FFD700' in win.color_previews[2].styleSheet(), 'preview follows the colour')
    # Блок выше переключает категорию для своих проверок, поэтому перед
    # перекраской результата выбираем рецепт заново.
    win.category_combo.setCurrentIndex(win.category_combo.findText('medicine'))
    app.processEvents()
    win.recipe_combo.setCurrentIndex(0)
    win.amount_entry.setText('90')
    win.calculate_reactants()
    check('#ffd700' in win.result_text.toHtml().lower(), 'the new colour is used right away')

    win.language_combo.setCurrentIndex(0)
    check(win.language == 'ru', 'language selection is stored')

    # links tab wiring
    # A downloaded file that no source points at still has to be visible.
    phantom = os.path.join(logic.RECIPE_FOLDER, 'phantom.yml')
    with open(phantom, 'w', encoding='utf-8') as handle:
        handle.write('- type: reaction\n  id: Phantom\n  reactants:\n'
                     '    Water:\n      amount: 1\n  products:\n    Water: 1\n')
    built_tabs.append(ui._build_links_tab(win))

    def row_by_name(name):
        for row in range(win.links_table.rowCount()):
            item = win.links_table.item(row, 0)
            if item.text() == name or item.data(QtCore.Qt.UserRole) == name:
                return row
        return -1

    def headers():
        return [win.links_table.horizontalHeaderItem(column).text()
                for column in range(win.links_table.columnCount())]

    check(headers() == ['Категория', 'Ссылка', 'Файл'], 'recipes table has a category column')
    check(win.links_recipe_btn.isChecked() and not win.links_translation_btn.isChecked(),
          'recipes mode is on by default')

    downloaded = logic.local_files(logic.RECIPE_FOLDER, '.yml')
    expected = len(win.custom_recipe_links) + len(downloaded - set(win.custom_recipe_links))
    check(win.links_table.rowCount() == expected,
          'link table lists the sources and the local files')
    row = row_by_name('medicine')
    check(row >= 0 and win.links_table.item(row, 2).text() == 'medicine.yml',
          'a downloaded source shows its file name')
    row = row_by_name('phantom')
    check(row >= 0 and win.links_table.item(row, 1).text() == ''
          and win.links_table.item(row, 2).text() == 'phantom.yml',
          'a local file without a source is listed')
    check(not (win.links_table.item(row, 2).flags() & QtCore.Qt.ItemIsEditable),
          'the file cell is read-only')
    check(not (win.links_table.item(row, 1).flags() & QtCore.Qt.ItemIsEditable),
          'the link cell is read-only')

    # Categories change only through the edit dialog, with validation.
    chemicals_row = row_by_name('chemicals')
    pyro_row = row_by_name('pyrotechnic')
    check(not (win.links_table.item(chemicals_row, 0).flags() & QtCore.Qt.ItemIsEditable),
          'the category cell is read-only')

    def fill_category(label):
        def fill(dialog):
            edits = dialog.findChildren(QtWidgets.QLineEdit)
            edits[0].setText(label)
            for button in dialog.findChildren(QtWidgets.QPushButton):
                if button.text() == 'Сохранить':
                    button.click()
        return fill

    def edit_category(row, label):
        win.links_table.selectRow(row)
        sweeper = start_modal_sweeper(app, action=fill_category(label))
        ui.edit_link(win, is_edit=True)
        app.processEvents()
        stop_sweeper(sweeper)

    def category_names():
        return [win.category_combo.itemText(index)
                for index in range(win.category_combo.count())]

    edit_category(chemicals_row, '')
    check(win.links_table.item(chemicals_row, 0).text() == 'chemicals',
          'an empty category is rejected')

    edit_category(chemicals_row, 'плохое/имя')
    check(not win.recipe_file_categories, 'a category with bad characters is rejected')

    edit_category(chemicals_row, 'Химия')
    check(win.recipe_file_categories.get('chemicals') == 'Химия', 'the new category is stored')
    check('Химия' in category_names(), 'the category box picks up the new label')
    grouped = [recipe for recipe in win.recipes if recipe['category'] == 'Химия']
    check(grouped and 'chemicals' not in category_names(),
          'recipes move to the new category')

    extra = [recipe for recipe in win.recipes if recipe['category'] == 'pyrotechnic']
    check(extra, 'pyrotechnic recipes exist before the merge')
    edit_category(pyro_row, 'Химия')
    merged = [recipe for recipe in win.recipes if recipe['category'] == 'Химия']
    check(len(merged) == len(grouped) + len(extra), 'two files merge into one category')

    edit_category(chemicals_row, 'chemicals')
    edit_category(pyro_row, 'pyrotechnic')
    check(not win.recipe_file_categories, 'restoring the labels drops the mapping')
    check('chemicals' in category_names(), 'the original category is back')

    # Translations: links only, the file name comes from the link.
    win.links_translation_btn.click()
    check(headers() == ['Ссылка', 'Файл'], 'translations table has no category column')
    check(not win.links_recipe_btn.isChecked() and win.links_translation_btn.isChecked(),
          'the mode buttons follow the table')
    downloaded = logic.local_files(logic.TRANSLATION_FOLDER, '.ftl')
    expected = len(win.custom_translation_links) + len(downloaded - set(win.custom_translation_links))
    check(win.links_table.rowCount() == expected,
          'switching the mode shows translations')

    def fill_translation(url):
        def fill(dialog):
            edits = dialog.findChildren(QtWidgets.QLineEdit)
            check(len(edits) == 1, 'the translation form only asks for a link')
            edits[0].setText(url)
            for button in dialog.findChildren(QtWidgets.QPushButton):
                if button.text() == 'Сохранить':
                    button.click()
        return fill

    translation_links = dict(win.custom_translation_links)
    sweeper = start_modal_sweeper(app, action=fill_translation('https://example.com/path/тестовый.ftl'))
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    added = set(win.custom_translation_links) - set(translation_links)
    stem = added.pop() if len(added) == 1 else ''
    check(re.fullmatch(r'тестовый-[0-9a-f]{5}', stem) is not None,
          f'the translation file is named after the link with a suffix ({stem})')
    check(win.custom_translation_links.get(stem) == 'https://example.com/path/тестовый.ftl',
          'the link is stored under the file name')

    sweeper = start_modal_sweeper(app, action=fill_translation('https://example.com/other/тестовый.ftl'))
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    later = set(win.custom_translation_links) - set(translation_links)
    check(len(later) == 2, 'a second link gets its own file')
    second = (later - {stem}).pop()
    check(re.fullmatch(r'тестовый-[0-9a-f]{5}', second) is not None and second != stem,
          'every new file carries its own suffix')

    for old in later:
        win.links_table.selectRow(row_by_name(old))
        ui.delete_link(win)
    check(win.custom_translation_links == translation_links, 'translation rows can be deleted')
    win.links_recipe_btn.click()

    # invalid sources are rejected
    before = win.links_table.rowCount()
    sweeper = start_modal_sweeper(app)
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.links_table.rowCount() == before,
          'an empty link form is rejected')

    def fill_bad(dialog):
        edits = dialog.findChildren(QtWidgets.QLineEdit)
        edits[0].setText('плохое/имя')
        edits[1].setText('ftp://example.com/x.yml')
        for button in dialog.findChildren(QtWidgets.QPushButton):
            if button.text() == 'Сохранить':
                button.click()

    sweeper = start_modal_sweeper(app, action=fill_bad)
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    check('плохое/имя' not in win.custom_recipe_links, 'an invalid file name is rejected')

    def fill_good(dialog):
        edits = dialog.findChildren(QtWidgets.QLineEdit)
        edits[0].setText('тестовый источник')
        edits[1].setText('https://example.com/test.yml')
        for button in dialog.findChildren(QtWidgets.QPushButton):
            if button.text() == 'Сохранить':
                button.click()

    before = win.links_table.rowCount()
    recipe_links = dict(win.custom_recipe_links)
    sweeper = start_modal_sweeper(app, action=fill_good)
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.links_table.rowCount() == before + 1, 'a valid source is added to the table')
    added = set(win.custom_recipe_links) - set(recipe_links)
    stem = added.pop() if len(added) == 1 else ''
    check(re.fullmatch(r'test-[0-9a-f]{5}', stem) is not None,
          f'the file is named after the link with a suffix ({stem})')
    check(win.custom_recipe_links.get(stem) == 'https://example.com/test.yml',
          'the link is stored under the file name')
    check(win.recipe_categories.get(stem) == 'https://example.com/test.yml',
          'a valid source becomes an update source')
    check(win.recipe_file_categories.get(stem) == 'тестовый источник',
          'the settings map the file name to the category')
    row = row_by_name(stem)
    check(row >= 0 and win.links_table.item(row, 0).text() == 'тестовый источник'
          and win.links_table.item(row, 2).text() == f'{stem}.yml (не загружен)',
          'a source without a downloaded file is marked')

    # deleting it again
    win.links_table.selectRow(row)
    ui.delete_link(win)
    check(stem not in win.custom_recipe_links, 'sources can be deleted')
    check(stem not in win.recipe_categories, 'deletion updates the sources')
    check(stem not in win.recipe_file_categories, 'deletion drops the category mapping')
    check(row_by_name(stem) < 0, 'a deleted row leaves the table')

    # A second "medicine" source becomes its own file with the same category.
    def fill_medicine(dialog):
        edits = dialog.findChildren(QtWidgets.QLineEdit)
        edits[0].setText('medicine')
        edits[1].setText('https://example.com/medicine-copy.yml')
        for button in dialog.findChildren(QtWidgets.QPushButton):
            if button.text() == 'Сохранить':
                button.click()

    recipe_links = dict(win.custom_recipe_links)
    sweeper = start_modal_sweeper(app, action=fill_medicine)
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    added = set(win.custom_recipe_links) - set(recipe_links)
    check(len(added) == 1, 'a duplicate category is added as its own file')
    stem = added.pop()
    check(re.fullmatch(r'medicine-copy-[0-9a-f]{5}', stem) is not None,
          f'every new file is named after its link ({stem})')
    row = row_by_name(stem)
    check(row >= 0 and win.links_table.item(row, 0).text() == 'medicine'
          and win.links_table.item(row, 2).text().startswith(f'{stem}.yml'),
          'the file column shows the suffixed name while the category stays clean')
    win.links_table.selectRow(row)
    ui.delete_link(win)
    check(stem not in win.recipe_file_categories, 'deleting the row drops its category')

    os.remove(phantom)
    win.reload_links_table()

    built_tabs.append(ui._build_about_tab(win))
    about = built_tabs[-1]
    labels = about.findChildren(QtWidgets.QLabel)
    check(any('i_love_Megumin' in label.text() for label in labels), 'about tab carries the info text')
    check(any(button.text() == 'Сбросить все настройки'
              for button in about.findChildren(QtWidgets.QPushButton)), 'about tab has the reset button')
    check(all(tab is not None for tab in built_tabs), 'all three settings tabs were built')

    # the dialog itself opens and closes, saving the settings on the way out
    win.save_settings()
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check(set(saved) == {'config_version', 'opacity', 'language', 'depth_colors',
                         'custom_recipes', 'custom_translations',
                         'recipe_file_categories', 'presets'},
          'settings.cfg keeps the Tk format plus the version, the labels and the presets')
    check('reagent_recipe_overrides' not in saved,
          'recipe replacements are never written')
    check(saved['config_version'] == 1, 'the config carries its format version')
    check(saved['depth_colors'] == win.depth_colors, 'colours are written to disk')

    reads = []
    original_load = logic.load_recipes

    def spy_load(app):
        reads.append(1)
        return original_load(app)

    logic.load_recipes = spy_load
    sweeper = start_modal_sweeper(app)
    win.create_settings_window()
    app.processEvents()
    stop_sweeper(sweeper)
    logic.load_recipes = original_load
    check('Настройки' in MODAL_LOG, 'the settings dialog opens')
    check(not reads, 'closing the settings dialog does not re-read the data')


def test_update_flow(app, win):
    print('update flow')
    original_download = logic._download
    downloaded = []

    def fake_ok(url, destination):
        downloaded.append(destination)
        return None

    logic._download = fake_ok
    sweeper = start_modal_sweeper(app)
    win.update_data_async()
    check(not win.update_btn.isEnabled(), 'the button is disabled while updating')
    check(win.progress_bar.isVisible(), 'progress bar shown')
    deadline = QtCore.QDeadlineTimer(15000)
    while not sweeper['done'] and not deadline.hasExpired():
        app.processEvents()
        QtCore.QThread.msleep(10)
    stop_sweeper(sweeper)
    check(any('Данные успешно обновлены' in title for title in MODAL_LOG),
          f'success is reported {MODAL_LOG[-3:]}')
    check(win.update_btn.isEnabled(), 'the button is enabled again')
    check(not win.progress_bar.isVisible(), 'progress bar is hidden again')
    check(len(downloaded) == len(logic.update_queue(win)), 'every source is downloaded')
    check(win.category_combo.count() > 0, 'categories are refreshed after the update')

    def fake_fail(url, destination):
        return 'нет сети'

    logic._download = fake_fail
    MODAL_LOG.clear()
    sweeper = start_modal_sweeper(app)
    win.update_data_async()
    deadline = QtCore.QDeadlineTimer(15000)
    while not sweeper['done'] and not deadline.hasExpired():
        app.processEvents()
        QtCore.QThread.msleep(10)
    stop_sweeper(sweeper)
    check(any('Не удалось загрузить' in title for title in MODAL_LOG),
          'failures are reported to the user')
    check(win.update_btn.isEnabled(), 'the button is enabled after a failure')
    logic._download = original_download


def test_presets(app, win):
    print('presets')
    check(win.presets == ['Default', 'Corvax', 'SS220 Exodus', 'SS220 Main'],
          'the built-in presets are seeded into the list')
    with open(app_main.SETTINGS_FILE, encoding='utf-8') as handle:
        saved = json.load(handle)
    check(saved.get('presets') == win.presets, 'the preset list is written to settings.cfg')
    check(os.path.isdir(os.path.join('presets', 'Default')),
          'every built-in preset gets its folder')
    default = logic.read_preset('Default')
    check(default['custom_recipes']
          == logic.preset_content(win.base_recipe_categories,
                                  win.base_translation_files,
                                  win.base_recipe_labels)['custom_recipes'],
          'the Default preset holds the factory links by category')
    check(default['custom_translations'] == list(win.base_translation_files.values()),
          'the Default preset holds the factory translation links')
    for name in ('Corvax', 'SS220 Exodus', 'SS220 Main'):
        content = logic.read_preset(name)
        own = json.loads(json.dumps(BUILTIN_PRESETS[name] or {}))
        check(content['custom_recipes'] == dict(own.get('custom_recipes') or {})
              and content['custom_translations'] == list(own.get('custom_translations') or ()),
              f'the {name} preset carries its own links from data.py')
    main_recipes, main_translations = logic.preset_file_counts('SS220 Main')
    expected_main = sum(len(value) if isinstance(value, (list, tuple)) else 1
                        for value in BUILTIN_PRESETS['SS220 Main']['custom_recipes'].values())
    check(main_recipes == expected_main
          and main_translations == len(BUILTIN_PRESETS['SS220 Main']['custom_translations']),
          'a preset of pure links counts them')

    # an old-style preset (file names as keys) is converted on read
    os.makedirs(logic.preset_path('Старый формат'), exist_ok=True)
    with open(os.path.join(logic.preset_path('Старый формат'), logic.PRESET_FILE),
              'w', encoding='utf-8') as handle:
        json.dump({'custom_recipes': {'a-1': 'https://example.com/x.yml'},
                   'custom_translations': {'b-1': 'https://example.com/y.ftl'},
                   'recipe_file_categories': {'a-1': 'Химия'}}, handle)
    check(logic.read_preset('Старый формат') == {
        'custom_recipes': {'Химия': 'https://example.com/x.yml'},
        'custom_translations': ['https://example.com/y.ftl']},
        'an old preset is converted on read')
    logic.delete_preset('Старый формат')

    ui.set_links_mode(win, 'Пресеты')
    headers = [win.links_table.horizontalHeaderItem(column).text()
               for column in range(win.links_table.columnCount())]
    check(headers == ['Название', 'Рецептов', 'Переводов'], 'the preset table has its columns')
    check(win.links_table.rowCount() == len(win.presets), 'every preset gets a row')
    check(win.links_table.item(0, 0).text() == 'Default', 'the presets keep their order')
    check(not win.preset_load_btn.isHidden() and win.links_add_btn.isHidden(),
          'the preset buttons replace the source buttons')

    def preset_row(name):
        for row in range(win.links_table.rowCount()):
            if win.links_table.item(row, 0).text() == name:
                return row
        return -1

    def fill_name(dialog, name):
        edits = dialog.findChildren(QtWidgets.QLineEdit)
        edits[0].setText(name)
        for button in dialog.findChildren(QtWidgets.QPushButton):
            if button.text() == 'Сохранить':
                button.click()

    # saving the current data as a new preset
    recipe_links = dict(win.custom_recipe_links)
    translation_links = dict(win.custom_translation_links)
    labels = dict(win.recipe_file_categories)
    sweeper = start_modal_sweeper(
        app, action=lambda dialog: fill_name(dialog, 'Тестовый пресет'))
    ui.save_preset_as(win)
    app.processEvents()
    stop_sweeper(sweeper)
    check('Тестовый пресет' in win.presets, 'a new preset joins the list')
    content = logic.read_preset('Тестовый пресет')
    check(content == logic.preset_content(recipe_links, translation_links, labels),
          'the preset stores the links by category')
    recipes, translations = logic.preset_file_counts('Тестовый пресет')
    check(recipes == len(recipe_links) and translations == len(translation_links),
          'the preset counts its links')

    # an existing name asks before it is overwritten
    MODAL_LOG.clear()
    sweeper = start_modal_sweeper(
        app, action=lambda dialog: fill_name(dialog, 'Тестовый пресет'), answer='no')
    ui.save_preset_as(win)
    app.processEvents()
    stop_sweeper(sweeper)
    check(any('Перезаписать' in title for title in MODAL_LOG),
          'saving under an existing name asks for confirmation')
    check(win.presets.count('Тестовый пресет') == 1, 'a declined overwrite changes nothing')

    sweeper = start_modal_sweeper(
        app, action=lambda dialog: fill_name(dialog, 'Тестовый пресет'), answer='yes')
    ui.save_preset_as(win)
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.presets.count('Тестовый пресет') == 1, 'an accepted overwrite keeps one entry')

    # loading a preset backs the current data up and re-downloads the files
    ui.set_links_mode(win, 'Рецепты')
    stem = next(iter(win.custom_recipe_links))
    for row in range(win.links_table.rowCount()):
        if win.links_table.item(row, 0).data(QtCore.Qt.UserRole) == stem:
            win.links_table.selectRow(row)
            break
    ui.delete_link(win)
    check(stem not in win.custom_recipe_links, 'a source is dropped before the load')
    pre_links = dict(win.custom_recipe_links)
    pre_translations = dict(win.custom_translation_links)
    pre_labels = dict(win.recipe_file_categories)

    def load_and_wait(row_name):
        """Answer the load question and wait for its update to finish."""
        win.links_table.selectRow(preset_row(row_name))
        MODAL_LOG.clear()
        sweeper = start_modal_sweeper(app, answer='yes')
        ui.load_preset(win)
        deadline = QtCore.QDeadlineTimer(15000)
        while not any('Данные успешно обновлены' in title for title in MODAL_LOG) \
                and not deadline.hasExpired():
            app.processEvents()
            QtCore.QThread.msleep(10)
        stop_sweeper(sweeper)
        return any('Данные успешно обновлены' in title for title in MODAL_LOG)

    original_download = logic._download
    logic._download = lambda url, destination: None
    ui.set_links_mode(win, 'Пресеты')
    check(load_and_wait('Тестовый пресет'),
          'loading the preset ends with the standard update')
    check(set(win.custom_recipe_links.values()) == set(recipe_links.values()),
          'the preset restores the saved links')
    check(set(win.recipe_file_categories.values())
          == {labels.get(stem, stem) for stem in recipe_links},
          'the restored links carry their categories')
    check(not logic.local_files('recipes', '.yml')
          and not logic.local_files('translations', '.ftl'),
          'the old files are dropped before the download')
    check('backup' in win.presets, 'the current data is backed up before the load')
    backup = logic.read_preset('backup')
    check(backup == logic.preset_content(pre_links, pre_translations, pre_labels),
          'the backup holds the state from before the load')
    check(preset_row('backup') >= 0, 'the backup preset shows up in the table')

    # loading the backup itself must not rewrite it
    check(load_and_wait('backup'), 'the backup loads through the same update')
    check(set(win.custom_recipe_links.values()) == set(pre_links.values()),
          'the backup restores its own state')
    check(win.presets.count('backup') == 1, 'loading the backup does not recreate it')
    logic._download = original_download

    # renaming
    win.links_table.selectRow(preset_row('Тестовый пресет'))
    sweeper = start_modal_sweeper(
        app, action=lambda dialog: fill_name(dialog, 'Переименованный'))
    ui.rename_preset(win)
    app.processEvents()
    stop_sweeper(sweeper)
    check('Переименованный' in win.presets and 'Тестовый пресет' not in win.presets,
          'the preset is renamed in the list')
    check(os.path.isdir(os.path.join('presets', 'Переименованный'))
          and not os.path.exists(os.path.join('presets', 'Тестовый пресет')),
          'the preset folder follows the new name')

    # an invalid name is rejected
    sweeper = start_modal_sweeper(
        app, action=lambda dialog: fill_name(dialog, 'плохое/имя'))
    ui.save_preset_as(win)
    app.processEvents()
    stop_sweeper(sweeper)
    check(all(name != 'плохое/имя' for name in win.presets),
          'an invalid preset name is rejected')

    # deleting
    win.links_table.selectRow(preset_row('Переименованный'))
    sweeper = start_modal_sweeper(app, answer='yes')
    ui.delete_preset(win)
    app.processEvents()
    stop_sweeper(sweeper)
    check('Переименованный' not in win.presets, 'a preset leaves the list')
    check(not os.path.exists(os.path.join('presets', 'Переименованный')),
          'the preset folder is deleted')

    ui.set_links_mode(win, 'Рецепты')


def test_reset(app, win):
    print('reset (destructive, runs last)')
    win.depth_colors[0] = '#FF0000'
    win.save_settings()
    MODAL_LOG.clear()
    sweeper = start_modal_sweeper(app, answer='да')
    win.reset_settings()
    app.processEvents()
    stop_sweeper(sweeper)
    check(any('Сброс настроек' in title for title in MODAL_LOG), 'reset asks for confirmation')
    # the confirm button is labelled Yes in English
    MODAL_LOG.clear()
    sweeper = start_modal_sweeper(app, answer='yes')
    win.reset_settings()
    app.processEvents()
    stop_sweeper(sweeper)

    check(win.depth_colors == DEFAULT_DEPTH_COLORS, 'colours are back to the defaults')
    check(win.overlay_opacity == app_main.DEFAULT_OPACITY, 'opacity is back to the default')
    check(win.custom_recipe_links == win.base_recipe_categories, 'links are back to the defaults')
    check(win.recipe_file_categories == win.base_recipe_labels,
          'the category labels are back to the defaults')
    check(win.presets == list(BUILTIN_PRESETS), 'the preset list is back to the built-ins')
    check(not os.path.exists(os.path.join('presets', 'backup')),
          'the preset folders are recreated from scratch')
    check(logic.read_preset('Default')['custom_recipes']
          == logic.preset_content(win.base_recipe_categories,
                                  win.base_translation_files,
                                  win.base_recipe_labels)['custom_recipes'],
          'the Default preset holds the factory links again')
    check(os.path.isdir('recipes') and os.path.isdir('translations'), 'data folders exist again')
    check(win.category_combo.count() == len(set(win.base_recipe_labels.values())),
          'the category box shows the default sources')
    check(win.recipe_combo.count() == 0, 'no recipes remain after the reset')


def test_close(app, win):
    print('close')
    win.toggle_overlay()
    app.processEvents()
    win.close()
    app.processEvents()
    check(win.overlay_window is None or not win.overlay_window.isVisible(),
          'closing the window hides the overlay')


FIXTURES = os.path.join(REPO_ROOT, 'test', 'fixtures')


def make_workdir():
    """Copy the test fixtures into a scratch directory and move into it.

    The suite never touches the downloaded data: it runs on the committed
    fixture recipes/translations, so a user updating or resetting the local
    data cannot break the tests.
    """
    workdir = tempfile.mkdtemp(prefix='ss14-calc-test-')
    for folder in ('recipes', 'translations'):
        shutil.copytree(os.path.join(FIXTURES, folder), os.path.join(workdir, folder))
    shutil.copy(os.path.join(FIXTURES, 'settings.cfg'), workdir)
    os.chdir(workdir)
    return workdir


def run_suite():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    win = app_main.ReagentCalculatorQt()
    win.show()
    app.processEvents()

    steps = (test_startup, test_data_py, test_search, test_popup_styles,
             test_calculation, test_reagent_recipe_choice, test_hidden_recipes,
             test_byproducts, test_overlay,
             test_settings, test_update_flow, test_presets, test_reset, test_close)
    for step in steps:
        try:
            step(app, win)
        except Exception:
            traceback.print_exc()
            FAILURES.append(f'{step.__name__} raised')

    print()
    if FAILURES:
        print(f'FAILURES ({len(FAILURES)}):')
        for failure in FAILURES:
            print(' -', failure)
        return 1
    print('ALL TESTS PASSED')
    return 0


def main():
    original_cwd = os.getcwd()
    workdir = make_workdir()
    try:
        code = run_suite()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(workdir, ignore_errors=True)
    # The interpreter shutdown races inside PySide6/Qt when the suite has
    # rendered popup widgets (the crash is in Qt's own destruction order,
    # not in the application code), so the process stops right here and
    # that teardown is skipped entirely.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


if __name__ == '__main__':
    main()
