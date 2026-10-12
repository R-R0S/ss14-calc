"""End-to-end interaction tests for the Qt calculator.

Run with ``python test/test_app.py`` (add ``QT_QPA_PLATFORM=offscreen`` on a
machine without a display).  Every check happens in a scratch directory, so
the local ``settings.cfg``, ``recipes/`` and ``translations/`` are never
touched: the data folders are copied first and the working directory is
switched to the copy.
"""
import json
import os
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
from data import DEFAULT_DEPTH_COLORS  # noqa: E402

FAILURES = []
MODAL_LOG = []


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
    state['timer'].stop()


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
    win.category_combo.setCurrentIndex(win.category_combo.findText('Botany'))
    app.processEvents()
    names = [win.recipe_combo.itemText(i) for i in range(win.recipe_combo.count())]
    index = next((i for i, name in enumerate(names) if 'обаст' in name), None)
    check(index is not None, 'the catalyst test recipe is present in Botany')
    if index is not None:
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
    built_tabs.append(ui._build_links_tab(win))
    check(win.links_table.rowCount() == len(win.custom_recipe_links),
          'link table lists the configured recipes')
    win.links_mode_combo.setCurrentIndex(1)
    check(win.links_table.rowCount() == len(win.custom_translation_links),
          'switching the mode shows translations')
    win.links_mode_combo.setCurrentIndex(0)

    # invalid sources are rejected
    sweeper = start_modal_sweeper(app)
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.links_table.rowCount() == len(win.custom_recipe_links),
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
    sweeper = start_modal_sweeper(app, action=fill_good)
    ui.edit_link(win, is_edit=False)
    app.processEvents()
    stop_sweeper(sweeper)
    check(win.links_table.rowCount() == before + 1, 'a valid source is added to the table')
    check(win.custom_recipe_links.get('тестовый источник') == 'https://example.com/test.yml',
          'a valid source is stored in the settings')
    check(win.recipe_categories.get('тестовый источник') == 'https://example.com/test.yml',
          'a valid source becomes an update source')

    # deleting it again
    win.links_table.selectRow(win.links_table.rowCount() - 1)
    ui.delete_link(win)
    check('тестовый источник' not in win.custom_recipe_links, 'sources can be deleted')
    check('тестовый источник' not in win.recipe_categories, 'deletion updates the sources')

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
    check(set(saved) == {'opacity', 'language', 'depth_colors', 'custom_recipes',
                         'custom_translations'}, 'settings.cfg keeps the Tk format')
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
    check(os.path.isdir('recipes') and os.path.isdir('translations'), 'data folders exist again')
    check(win.category_combo.count() == len(win.base_recipe_categories),
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


def make_workdir():
    """Copy the downloaded data into a scratch directory and move into it."""
    workdir = tempfile.mkdtemp(prefix='ss14-calc-test-')
    for folder in ('recipes', 'translations'):
        source = os.path.join(REPO_ROOT, folder)
        target = os.path.join(workdir, folder)
        if os.path.isdir(source):
            shutil.copytree(source, target)
        else:
            os.makedirs(target)
    if not os.listdir(os.path.join(workdir, 'recipes')):
        print('No recipes next to the sources: start the application once and press '
              '«Обновить данные» before running the tests.')
    os.chdir(workdir)
    return workdir


def run_suite():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    win = app_main.ReagentCalculatorQt()
    win.show()
    app.processEvents()

    steps = (test_startup, test_search, test_calculation, test_overlay, test_settings,
             test_update_flow, test_reset, test_close)
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
        return run_suite()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
