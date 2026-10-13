"""Qt widgets of the SS14 chemical calculator.

The module contains the main window layout, the frameless overlay window and
the settings dialog.  Functions receive the application window as ``self``/
first argument and only touch widgets and plain state of that window.
"""
import glob
import os
import random
import sys
import webbrowser

from PySide6 import QtCore, QtGui, QtWidgets

from data import ABOUT_INFO, APP_TITLE, COLOR_NAMES, color_name
import logic

GITHUB_URL = 'https://github.com/R-R0S/ss14-calc'
DISCORD_URL = 'https://discord.com/users/317692089355862016'
HANDLE_PREFIX = 'overlay_handle_'

APP_STYLE_SHEET = """
QMainWindow, QDialog { background-color: #2e2e2e; }
QLabel { color: #ffffff; background: transparent; }
QLineEdit, QComboBox {
    background-color: #4f4f4f;
    color: #ffffff;
    border: 1px solid #454545;
    border-radius: 3px;
    padding: 4px;
    selection-background-color: #1e7e34;
    selection-color: #ffffff;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background-color: #4f4f4f;
    color: #ffffff;
    border: 1px solid #454545;
    selection-background-color: #1e7e34;
    selection-color: #ffffff;
}
QTextEdit, QPlainTextEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #454545;
    selection-background-color: #1e7e34;
    selection-color: #ffffff;
}
QTableWidget {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #454545;
    gridline-color: #454545;
    selection-background-color: #1e7e34;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #454545;
    color: #ffffff;
    border: none;
    padding: 4px;
}
QHeaderView { background-color: #454545; }
QTableCornerButton::section { background-color: #454545; border: none; }
QPushButton {
    background-color: #454545;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #5e5e5e; }
QPushButton:pressed { background-color: #1e7e34; }
QPushButton:disabled { background-color: #3c3c3c; color: #909090; }
QPushButton#links_mode_button:checked { background-color: #1e7e34; }
QPushButton#discord_button { background: transparent; padding: 0; }
QPushButton#discord_button:hover { background: rgba(255, 255, 255, 40); border-radius: 4px; }
QProgressBar {
    background-color: #454545;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    text-align: center;
    min-height: 16px;
}
QProgressBar::chunk { background-color: #1e7e34; border-radius: 3px; }
QTabWidget::pane { border: 1px solid #454545; top: -1px; }
QTabBar::tab {
    background-color: #2e2e2e;
    color: #ffffff;
    padding: 6px 14px;
    margin-right: 2px;
}
QTabBar::tab:selected { background-color: #1e7e34; }
QGroupBox {
    color: #ffffff;
    border: 1px solid #454545;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 14px;
}
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QSlider::groove:horizontal { height: 6px; background: #454545; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #1e7e34;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QScrollBar:vertical { background: #2e2e2e; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #5e5e5e; min-height: 24px; border-radius: 6px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; width: 0; }
QScrollBar:horizontal { background: #2e2e2e; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #5e5e5e; min-width: 24px; border-radius: 6px; }
QToolTip {
    background-color: #454545;
    color: #ffffff;
    border: 1px solid #5e5e5e;
    padding: 3px;
}
"""

# The window background itself is painted by OverlayWidget.paintEvent(); this
# sheet only styles its children.
OVERLAY_STYLE = """
#overlay_title {
    background: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 60);
}
QLabel { color: #ffffff; background: transparent; }
QTextEdit#overlay_content {
    background: transparent;
    color: #ffffff;
    border: none;
    selection-background-color: #1e7e34;
    selection-color: #ffffff;
}
QPushButton#overlay_close {
    background-color: #ff4444;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    font-weight: bold;
    padding: 0;
}
QPushButton#overlay_close:hover { background-color: #ff6666; }
"""


def icon_path():
    """Path of the application icon, also valid inside a frozen bundle."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'img', 'icon.ico')


def _platform_name():
    return QtWidgets.QApplication.platformName().lower()


def compositor_owns_geometry():
    """On Wayland clients may not move or resize their own top-level windows,
    so those operations have to be delegated to the window system."""
    return _platform_name().startswith('wayland')


def init_ui(self):
    """Build the main window."""
    application = QtWidgets.QApplication.instance()
    if application is not None and not application.styleSheet():
        application.setStyleSheet(APP_STYLE_SHEET)

    self.setWindowTitle(f'{APP_TITLE} v{self.current_version}')
    self.setWindowIcon(QtGui.QIcon(icon_path()))
    self.resize(900, 620)

    central = QtWidgets.QWidget(self)
    self.setCentralWidget(central)
    main_layout = QtWidgets.QHBoxLayout(central)

    left_v = QtWidgets.QVBoxLayout()
    main_layout.addLayout(left_v, 0)

    left_v.addWidget(QtWidgets.QLabel('Поиск'))
    self.search_edit = QtWidgets.QLineEdit()
    self.search_edit.setPlaceholderText('Название рецепта, например «Лацеринол»')
    left_v.addWidget(self.search_edit)
    _init_search(self)

    left_v.addWidget(QtWidgets.QLabel('Категория'))
    self.category_combo = QtWidgets.QComboBox()
    left_v.addWidget(self.category_combo)
    self.category_combo.currentIndexChanged.connect(self.update_recipes_list)

    left_v.addWidget(QtWidgets.QLabel('Рецепт'))
    self.recipe_combo = QtWidgets.QComboBox()
    left_v.addWidget(self.recipe_combo)

    left_v.addWidget(QtWidgets.QLabel('Количество'))
    self.amount_entry = QtWidgets.QLineEdit()
    self.amount_entry.setText('90')
    self.amount_entry.returnPressed.connect(self.calculate_reactants)
    left_v.addWidget(self.amount_entry)

    btn_row = QtWidgets.QHBoxLayout()
    left_v.addLayout(btn_row)
    self.calculate_btn = QtWidgets.QPushButton('Рассчитать')
    self.calculate_btn.clicked.connect(self.calculate_reactants)
    btn_row.addWidget(self.calculate_btn)

    self.update_btn = QtWidgets.QPushButton('Обновить данные')
    self.update_btn.clicked.connect(self.update_data_async)
    btn_row.addWidget(self.update_btn)

    _init_avatar(self, left_v)
    _init_footer(self, left_v)
    left_v.addStretch()

    right_v = QtWidgets.QVBoxLayout()
    main_layout.addLayout(right_v, 1)

    self.result_text = QtWidgets.QTextEdit()
    self.result_text.setReadOnly(True)
    right_v.addWidget(self.result_text)

    self.progress_bar = QtWidgets.QProgressBar()
    self.progress_bar.setVisible(False)
    right_v.addWidget(self.progress_bar)

    bottom_row = QtWidgets.QHBoxLayout()
    right_v.addLayout(bottom_row)

    self.overlay_btn = QtWidgets.QPushButton('Показать оверлей')
    self.overlay_btn.clicked.connect(self.toggle_overlay)
    bottom_row.addWidget(self.overlay_btn)

    self.settings_btn = QtWidgets.QPushButton('⚙️ Настройки')
    self.settings_btn.clicked.connect(self.create_settings_window)
    bottom_row.addWidget(self.settings_btn)

    github_btn = QtWidgets.QPushButton('GitHub')
    github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
    bottom_row.addWidget(github_btn)

    self.refresh_categories()


def _init_search(self):
    """Suggest recipes while typing, exactly like the Tk combobox did."""
    completer = QtWidgets.QCompleter()
    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    completer.setFilterMode(QtCore.Qt.MatchContains)
    completer.setMaxVisibleItems(15)
    completer.setModel(QtGui.QStandardItemModel())
    completer.activated[QtCore.QModelIndex].connect(self.on_search_suggestion)
    self.search_edit.setCompleter(completer)

    self.search_completer = completer
    self.search_model = completer.model()
    self.search_query = ''

    # The popup model is rebuilt on the next loop pass (see on_search()).
    self.search_delay = QtCore.QTimer()
    self.search_delay.setSingleShot(True)
    self.search_delay.setInterval(0)
    self.search_delay.timeout.connect(self.refresh_search_suggestions)

    self.search_edit.textChanged.connect(self.on_search)
    self.search_edit.returnPressed.connect(self.on_search_enter)


def _init_avatar(self, layout):
    """Show a random GIF from ``img/`` in the left column."""
    label = QtWidgets.QLabel()
    label.setAlignment(QtCore.Qt.AlignCenter)
    label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    layout.addWidget(label)
    self.avatar_label = label

    gifs = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', '[0-9]*.gif'))
    if not gifs:
        return

    movie = QtGui.QMovie(random.choice(gifs))
    if not movie.isValid():
        return
    movie.jumpToFrame(0)
    size = movie.currentPixmap().size()
    if size.width() > 0 and size.height() > 0:
        size.scale(230, 230, QtCore.Qt.KeepAspectRatio)
        movie.setScaledSize(size)
        label.setFixedSize(size)
    label.setMovie(movie)
    movie.start()
    self.avatar_movie = movie  # QLabel keeps only a pointer, not a reference


def _init_footer(self, layout):
    """Discord link and the author's signature line from the Tk version."""
    row = QtWidgets.QHBoxLayout()

    icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'discord.png')
    pixmap = QtGui.QPixmap(icon)
    if not pixmap.isNull():
        button = QtWidgets.QPushButton()
        button.setObjectName('discord_button')
        button.setIcon(QtGui.QIcon(pixmap))
        button.setIconSize(QtCore.QSize(40, 40))
        button.setFixedSize(44, 44)
        button.setToolTip('Написать мне в Discord')
        button.clicked.connect(lambda: webbrowser.open(DISCORD_URL))
        row.addWidget(button)

    caption = QtWidgets.QLabel('© FelinidsPower,\n «Надежда» - 3026г.')
    row.addWidget(caption)
    row.addStretch()
    layout.addLayout(row)


class OverlayWidget(QtWidgets.QWidget):
    """Frameless always-on-top window that shows the current recipe.

    Drag it by its title bar and resize it from any of its eight edges and
    corners.  While the compositor owns the geometry (Wayland) the operation
    is handed over to the window system, everywhere else this widget moves and
    resizes itself, keeping the opposite edge fixed and honouring the minimum
    size.

    The translucent background is painted by :meth:`paintEvent`: Qt skips the
    stylesheet background of a ``WA_TranslucentBackground`` top-level window,
    so an overlay styled that way would stay completely see-through and the
    opacity setting would have nothing to change.
    """

    MIN_WIDTH = 200
    MIN_HEIGHT = 150
    EDGE_WIDTH = 6
    CORNER_WIDTH = 14
    BACKGROUND_RGB = (46, 46, 46)
    BORDER_COLOUR = QtGui.QColor(255, 255, 255, 45)

    _EDGES = {
        'nw': QtCore.Qt.TopEdge | QtCore.Qt.LeftEdge,
        'n': QtCore.Qt.TopEdge,
        'ne': QtCore.Qt.TopEdge | QtCore.Qt.RightEdge,
        'e': QtCore.Qt.RightEdge,
        'se': QtCore.Qt.BottomEdge | QtCore.Qt.RightEdge,
        's': QtCore.Qt.BottomEdge,
        'sw': QtCore.Qt.BottomEdge | QtCore.Qt.LeftEdge,
        'w': QtCore.Qt.LeftEdge,
    }
    _CURSORS = {
        'nw': QtCore.Qt.SizeFDiagCursor,
        'n': QtCore.Qt.SizeVerCursor,
        'ne': QtCore.Qt.SizeBDiagCursor,
        'e': QtCore.Qt.SizeHorCursor,
        'se': QtCore.Qt.SizeFDiagCursor,
        's': QtCore.Qt.SizeVerCursor,
        'sw': QtCore.Qt.SizeBDiagCursor,
        'w': QtCore.Qt.SizeHorCursor,
    }

    closed = QtCore.Signal()

    def __init__(self, parent=None, size=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window
                            | QtCore.Qt.WindowStaysOnTopHint
                            | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self._background_alpha = 255
        self._drag_state = None
        self._resize_state = None
        self._handles = {}
        self._build_content()
        self._build_handles()
        self.resize(size or QtCore.QSize(300, 400))

    # ------------------------------------------------------------ appearance

    def set_background_alpha(self, alpha):
        """Fade the window background (0 … 255) without touching the text."""
        alpha = max(0, min(255, int(alpha)))
        if alpha == self._background_alpha:
            return
        self._background_alpha = alpha
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(),
                         QtGui.QColor(*self.BACKGROUND_RGB, self._background_alpha))
        painter.setPen(self.BORDER_COLOUR)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    # ------------------------------------------------------------------ UI

    def _build_content(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = QtWidgets.QWidget(self)
        self.title_bar.setObjectName('overlay_title')
        self.title_bar.installEventFilter(self)
        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(8, 6, 4, 4)
        title_layout.setSpacing(6)

        title = QtWidgets.QLabel('Рецепт поверх окон', self.title_bar)
        title.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        title_layout.addWidget(title)
        title_layout.addStretch()

        close_button = QtWidgets.QPushButton('×', self.title_bar)
        close_button.setObjectName('overlay_close')
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.closed.emit)
        title_layout.addWidget(close_button)
        layout.addWidget(self.title_bar)

        self.content = QtWidgets.QTextEdit(self)
        self.content.setObjectName('overlay_content')
        self.content.setReadOnly(True)
        layout.addWidget(self.content, 1)

    def _build_handles(self):
        for name, edges in self._EDGES.items():
            handle = QtWidgets.QWidget(self)
            handle.setObjectName(HANDLE_PREFIX + name)
            handle.setCursor(self._CURSORS[name])
            handle.installEventFilter(self)
            self._handles[name] = handle

    def _position_handles(self):
        """Keep the resize zones glued to the window borders."""
        if not self._handles:
            return
        width, height = self.width(), self.height()
        corner, edge = self.CORNER_WIDTH, self.EDGE_WIDTH
        geometries = {
            'nw': (0, 0, corner, corner),
            'n': (corner, 0, width - 2 * corner, edge),
            'ne': (width - corner, 0, corner, corner),
            'e': (width - edge, corner, edge, height - 2 * corner),
            'se': (width - corner, height - corner, corner, corner),
            's': (corner, height - edge, width - 2 * corner, edge),
            'sw': (0, height - corner, corner, corner),
            'w': (0, corner, edge, height - 2 * corner),
        }
        for name, geometry in geometries.items():
            self._handles[name].setGeometry(*geometry)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_handles()

    # ------------------------------------------------- move and resize

    @staticmethod
    def _global_position(event):
        """Global cursor position for both the Qt 6 and the legacy API."""
        if hasattr(event, 'globalPosition'):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def eventFilter(self, watched, event):
        kind = event.type()
        if watched is self.title_bar:
            if kind == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                self._end_interaction()  # leftovers can only come from an interrupted drag
                self._begin_move(event)
                return True
            if kind == QtCore.QEvent.MouseMove and self._drag_state is not None:
                self._update_move(event)
                return True
            if kind == QtCore.QEvent.MouseButtonRelease and self._drag_state is not None:
                self._end_interaction()
                return True
            return False

        name = watched.objectName()
        if name.startswith(HANDLE_PREFIX) and name[len(HANDLE_PREFIX):] in self._EDGES:
            edges = self._EDGES[name[len(HANDLE_PREFIX):]]
            if kind == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                self._end_interaction()
                self._begin_resize(edges, event)
                return True
            if kind == QtCore.QEvent.MouseMove and self._resize_state is not None:
                self._update_resize(event)
                return True
            if kind == QtCore.QEvent.MouseButtonRelease and self._resize_state is not None:
                self._end_interaction()
                return True
        return super().eventFilter(watched, event)

    def _begin_move(self, event):
        handle = self.windowHandle()
        if handle is not None and handle.startSystemMove():
            return  # the window system moves the window from here on
        self._drag_state = {'start': self._global_position(event), 'position': self.pos()}

    def _update_move(self, event):
        offset = self._global_position(event) - self._drag_state['start']
        self.move(self._drag_state['position'] + offset)

    def _begin_resize(self, edges, event):
        if compositor_owns_geometry():
            handle = self.windowHandle()
            if handle is not None and handle.startSystemResize(edges):
                return  # the window system resizes the window from here on
        self._resize_state = {
            'edges': edges,
            'start': self._global_position(event),
            'geometry': self.geometry(),
        }

    def _update_resize(self, event):
        state = self._resize_state
        delta = self._global_position(event) - state['start']
        x, y, width, height = state['geometry'].getRect()

        if state['edges'] & QtCore.Qt.LeftEdge:
            width -= delta.x()
            x += delta.x()
        if state['edges'] & QtCore.Qt.RightEdge:
            width += delta.x()
        if state['edges'] & QtCore.Qt.TopEdge:
            height -= delta.y()
            y += delta.y()
        if state['edges'] & QtCore.Qt.BottomEdge:
            height += delta.y()

        # Clamp to the minimum size while keeping the opposite edge in place.
        if width < self.MIN_WIDTH:
            if state['edges'] & QtCore.Qt.LeftEdge:
                x -= self.MIN_WIDTH - width
            width = self.MIN_WIDTH
        if height < self.MIN_HEIGHT:
            if state['edges'] & QtCore.Qt.TopEdge:
                y -= self.MIN_HEIGHT - height
            height = self.MIN_HEIGHT

        self.setGeometry(x, y, width, height)

    def _end_interaction(self):
        self._drag_state = None
        self._resize_state = None


def apply_overlay_opacity(window, opacity):
    """Paint *window* with the given opacity (0.0 … 1.0).

    Only the background drawn by ``OverlayWidget.paintEvent`` carries the
    alpha, so the recipe text stays fully readable while the game behind the
    overlay shows through. ``setWindowOpacity`` is never used: it would fade
    the text as well and warns on platforms without window alpha.
    """
    alpha = round(min(max(float(opacity), 0.0), 1.0) * 255)
    window.set_background_alpha(alpha)


def create_overlay_window(self):
    """Create the overlay and remember it on the application window."""
    overlay = OverlayWidget()
    overlay.setStyleSheet(OVERLAY_STYLE)
    apply_overlay_opacity(overlay, self.overlay_opacity)
    overlay.closed.connect(self.toggle_overlay)
    overlay.destroyed.connect(lambda *_args: forget_overlay(self))

    self.overlay_window = overlay
    self.overlay_content = overlay.content
    update_overlay_content(self)
    return overlay


def forget_overlay(self):
    """Drop references to an overlay window that no longer exists."""
    self.overlay_window = None
    self.overlay_content = None


def update_overlay_content(self):
    """Mirror the latest calculation result into the overlay."""
    if self.overlay_content is None:
        return
    self.overlay_content.setHtml(self.result_text.toHtml())


def create_settings_window(self):
    """Modal settings dialog with the same tabs as the Tk version."""
    dialog = QtWidgets.QDialog(self)
    dialog.setWindowTitle('Настройки')
    dialog.resize(700, 480)
    layout = QtWidgets.QVBoxLayout(dialog)

    tabs = QtWidgets.QTabWidget()
    layout.addWidget(tabs)
    tabs.addTab(_build_general_tab(self), 'Основные')
    tabs.addTab(_build_links_tab(self), 'Данные')
    tabs.addTab(_build_about_tab(self), 'О приложении')

    dialog.exec()
    # Sources are applied live by edit_link()/delete_link(), so the recipes
    # only have to be re-read after an actual download.
    self.save_settings()


def _build_general_tab(self):
    general = QtWidgets.QWidget()
    column = QtWidgets.QVBoxLayout(general)

    self.opacity_label = QtWidgets.QLabel(f'Прозрачность оверлея - {round(self.overlay_opacity * 100)}%')
    column.addWidget(self.opacity_label)

    slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    slider.setRange(30, 100)
    slider.setValue(round(self.overlay_opacity * 100))
    slider.valueChanged.connect(lambda value: self.update_overlay_opacity(value / 100.0))
    column.addWidget(slider)
    self.opacity_slider = slider

    language_row = QtWidgets.QHBoxLayout()
    language_row.addWidget(QtWidgets.QLabel('Язык интерфейса:'))
    language_combo = QtWidgets.QComboBox()
    language_combo.addItem('Русский', 'ru')
    index = language_combo.findData(self.language)
    language_combo.setCurrentIndex(index if index >= 0 else 0)
    language_combo.currentIndexChanged.connect(
        lambda position: setattr(self, 'language', language_combo.itemData(position)))
    language_row.addWidget(language_combo)
    language_row.addStretch()
    column.addLayout(language_row)
    self.language_combo = language_combo

    colors_group = QtWidgets.QGroupBox('Цвета уровней рекурсии')
    colors_layout = QtWidgets.QGridLayout(colors_group)
    color_names = list(COLOR_NAMES)
    self.color_combos = []
    self.color_previews = []

    for index in range(6):
        hex_color = self.depth_colors[index]
        colors_layout.addWidget(QtWidgets.QLabel(f'Уровень {index + 1}'), index // 3, (index % 3) * 3)

        preview = QtWidgets.QLabel()
        preview.setFixedSize(18, 18)
        preview.setStyleSheet(f'background-color: {hex_color}; border: 1px solid #777777;')
        colors_layout.addWidget(preview, index // 3, (index % 3) * 3 + 1)
        self.color_previews.append(preview)

        combo = QtWidgets.QComboBox()
        combo.addItems(color_names)
        combo.blockSignals(True)
        combo.setCurrentText(color_name(hex_color) or color_names[0])
        combo.blockSignals(False)
        combo.currentTextChanged.connect(lambda _text, level=index: self.update_color(level))
        colors_layout.addWidget(combo, index // 3, (index % 3) * 3 + 2)
        self.color_combos.append(combo)

    column.addWidget(colors_group)
    column.addStretch()
    return general


def _build_links_tab(self):
    links = QtWidgets.QWidget()
    column = QtWidgets.QVBoxLayout(links)

    self.links_mode = 'Рецепты'
    mode_row = QtWidgets.QHBoxLayout()
    self.links_recipe_btn = QtWidgets.QPushButton('Рецепты')
    self.links_translation_btn = QtWidgets.QPushButton('Переводы')
    self.links_preset_btn = QtWidgets.QPushButton('Пресеты')
    for button in (self.links_recipe_btn, self.links_translation_btn, self.links_preset_btn):
        button.setCheckable(True)
        button.setObjectName('links_mode_button')
        mode_row.addWidget(button)
    mode_row.addStretch()
    column.addLayout(mode_row)
    self.links_recipe_btn.setChecked(True)

    self.links_table = QtWidgets.QTableWidget(0, 3)
    self.links_table.setHorizontalHeaderLabels(['Категория', 'Ссылка', 'Файл'])
    header = self.links_table.horizontalHeader()
    header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
    self.links_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    self.links_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    column.addWidget(self.links_table)

    buttons = QtWidgets.QHBoxLayout()
    self.links_add_btn = QtWidgets.QPushButton('Добавить')
    self.links_add_btn.clicked.connect(lambda: self.edit_link(is_edit=False))
    self.links_edit_btn = QtWidgets.QPushButton('Редактировать')
    self.links_edit_btn.clicked.connect(lambda: self.edit_link(is_edit=True))
    self.links_delete_btn = QtWidgets.QPushButton('Удалить')
    self.links_delete_btn.clicked.connect(self.delete_link)
    self.preset_load_btn = QtWidgets.QPushButton('Загрузить')
    self.preset_load_btn.clicked.connect(self.load_preset)
    self.preset_save_btn = QtWidgets.QPushButton('Сохранить как…')
    self.preset_save_btn.clicked.connect(self.save_preset_as)
    self.preset_rename_btn = QtWidgets.QPushButton('Переименовать')
    self.preset_rename_btn.clicked.connect(self.rename_preset)
    self.preset_delete_btn = QtWidgets.QPushButton('Удалить')
    self.preset_delete_btn.clicked.connect(self.delete_preset)
    for button in (self.links_add_btn, self.links_edit_btn, self.links_delete_btn,
                   self.preset_load_btn, self.preset_save_btn,
                   self.preset_rename_btn, self.preset_delete_btn):
        buttons.addWidget(button)
    buttons.addStretch()
    column.addLayout(buttons)

    self.links_recipe_btn.clicked.connect(lambda: set_links_mode(self, 'Рецепты'))
    self.links_translation_btn.clicked.connect(lambda: set_links_mode(self, 'Переводы'))
    self.links_preset_btn.clicked.connect(lambda: set_links_mode(self, 'Пресеты'))
    set_links_mode(self, 'Рецепты')
    return links


def _build_about_tab(self):
    about = QtWidgets.QWidget()
    column = QtWidgets.QVBoxLayout(about)

    info = QtWidgets.QLabel(ABOUT_INFO.format(version=self.current_version))
    info.setTextFormat(QtCore.Qt.PlainText)
    column.addWidget(info)
    column.addStretch()

    reset_button = QtWidgets.QPushButton('Сбросить все настройки')
    reset_button.clicked.connect(self.reset_settings)
    column.addWidget(reset_button)
    return about


def set_links_mode(self, mode):
    """Show recipes, translations or presets in the links table."""
    self.links_mode = mode
    self.links_recipe_btn.setChecked(mode == 'Рецепты')
    self.links_translation_btn.setChecked(mode == 'Переводы')
    self.links_preset_btn.setChecked(mode == 'Пресеты')
    is_presets = mode == 'Пресеты'
    for button in (self.links_add_btn, self.links_edit_btn, self.links_delete_btn):
        button.setVisible(not is_presets)
    for button in (self.preset_load_btn, self.preset_save_btn,
                   self.preset_rename_btn, self.preset_delete_btn):
        button.setVisible(is_presets)
    if is_presets:
        self.links_table.setColumnCount(3)
        self.links_table.setHorizontalHeaderLabels(['Название', 'Рецептов', 'Переводов'])
        reload_presets_table(self)
    elif mode == 'Рецепты':
        self.links_table.setColumnCount(3)
        self.links_table.setHorizontalHeaderLabels(['Категория', 'Ссылка', 'Файл'])
        reload_links_table(self)
    else:
        self.links_table.setColumnCount(2)
        self.links_table.setHorizontalHeaderLabels(['Ссылка', 'Файл'])
        reload_links_table(self)
    _fit_links_columns(self)


def _fit_links_columns(self):
    """Give every column an initial width the user can still drag."""
    if self.links_mode == 'Пресеты':
        widths = (230, 110, 110)
    elif self.links_mode == 'Рецепты':
        widths = (160, 330, 170)
    else:
        widths = (470, 170)
    header = self.links_table.horizontalHeader()
    for index, width in enumerate(widths):
        header.resizeSection(index, width)


def reload_links_table(self):
    """Fill the links table with the sources and the downloaded files.

    Sources keep their configured order; downloaded files that no longer
    belong to a source are listed after them with an empty link.  Every
    cell is read-only: the category and the link change only through the
    dialog and the file name is automatic.
    """
    sources, _live_sources, folder, suffix = _current_links(self)
    downloaded = logic.local_files(folder, suffix)
    is_recipes = self.links_mode == 'Рецепты'
    url_column = 1 if is_recipes else 0
    file_column = url_column + 1

    names = list(sources)
    names += [name for name in sorted(downloaded) if name not in sources]

    self.links_table.setRowCount(0)
    for name in names:
        row = self.links_table.rowCount()
        self.links_table.insertRow(row)

        note = '' if name in downloaded else ' (не загружен)'
        file_item = QtWidgets.QTableWidgetItem(f'{name}{suffix}{note}')
        file_item.setFlags(file_item.flags() & ~QtCore.Qt.ItemIsEditable)

        url_item = QtWidgets.QTableWidgetItem(sources.get(name, ''))
        url_item.setData(QtCore.Qt.UserRole, name)
        url_item.setFlags(url_item.flags() & ~QtCore.Qt.ItemIsEditable)

        if is_recipes:
            label = self.recipe_file_categories.get(name, name)
            category_item = QtWidgets.QTableWidgetItem(label)
            category_item.setData(QtCore.Qt.UserRole, name)
            category_item.setFlags(category_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.links_table.setItem(row, 0, category_item)
        self.links_table.setItem(row, url_column, url_item)
        self.links_table.setItem(row, file_column, file_item)


def _current_links(self):
    """Return ``(saved_links, live_sources, folder, suffix)`` for the mode."""
    if self.links_mode == 'Рецепты':
        return self.custom_recipe_links, self.recipe_categories, 'recipes', '.yml'
    return self.custom_translation_links, self.translation_files, 'translations', '.ftl'


def edit_link(self, is_edit=False):
    """Add a source or change the one selected in the table."""
    is_recipes = self.links_mode == 'Рецепты'
    stem, label, url = '', '', ''
    if is_edit:
        selected = self.links_table.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите запись для редактирования')
            return
        row = selected[0].row()
        stem = self.links_table.item(row, 0).data(QtCore.Qt.UserRole)
        label = self.links_table.item(row, 0).text() if is_recipes else stem
        url = self.links_table.item(row, 1 if is_recipes else 0).text()

    dialog = QtWidgets.QDialog(self)
    dialog.setWindowTitle('Редактирование ссылки' if is_edit else 'Добавление ссылки')
    layout = QtWidgets.QVBoxLayout(dialog)

    label_edit = None
    if is_recipes:
        layout.addWidget(QtWidgets.QLabel('Категория:'))
        label_edit = QtWidgets.QLineEdit(label)
        layout.addWidget(label_edit)
    layout.addWidget(QtWidgets.QLabel('Ссылка:'))
    url_edit = QtWidgets.QLineEdit(url)
    layout.addWidget(url_edit)

    def save():
        nonlocal stem
        new_url = url_edit.text().strip()
        if not new_url.startswith(('http://', 'https://')):
            QtWidgets.QMessageBox.critical(dialog, 'Ошибка', 'Ссылка должна начинаться с http:// или https://')
            return

        new_label = label_edit.text().strip() if is_recipes else ''
        if is_recipes:
            if not new_label:
                QtWidgets.QMessageBox.critical(dialog, 'Ошибка', 'Категория не может быть пустой')
                return
            if any(char in '<>:"/\\|?*' or ord(char) < 32 for char in new_label):
                QtWidgets.QMessageBox.critical(
                    dialog, 'Ошибка',
                    'Категория не может содержать символы, запрещённые в именах файлов')
                return

        saved_links, live_sources, folder, suffix = _current_links(self)
        if not is_edit:
            base = logic.file_stem_from_url(new_url)
            if not base:
                QtWidgets.QMessageBox.critical(
                    dialog, 'Ошибка', 'Не удалось определить имя файла по ссылке')
                return
            taken = set(saved_links) | logic.local_files(folder, suffix)
            stem = logic.fresh_file_stem(base, taken)

        saved_links[stem] = new_url
        live_sources[stem] = new_url
        if is_recipes:
            if new_label == stem:
                self.recipe_file_categories.pop(stem, None)
            else:
                self.recipe_file_categories[stem] = new_label
        reload_links_table(self)
        self.save_settings()
        self.reload_data()
        dialog.accept()

    buttons = QtWidgets.QHBoxLayout()
    save_button = QtWidgets.QPushButton('Сохранить')
    save_button.clicked.connect(save)
    cancel_button = QtWidgets.QPushButton('Отмена')
    cancel_button.clicked.connect(dialog.reject)
    buttons.addWidget(save_button)
    buttons.addWidget(cancel_button)
    layout.addLayout(buttons)

    dialog.exec()


def delete_link(self):
    """Remove the source selected in the table, and its downloaded file."""
    selected = self.links_table.selectedItems()
    if not selected:
        QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите запись для удаления')
        return

    row = selected[0].row()
    stem = self.links_table.item(row, 0).data(QtCore.Qt.UserRole)

    saved_links, live_sources, folder, suffix = _current_links(self)
    saved_links.pop(stem, None)
    live_sources.pop(stem, None)
    self.recipe_file_categories.pop(stem, None)
    try:
        path = os.path.join(folder, f'{stem}{suffix}')
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        print(f'Не удалось удалить {stem}{suffix}: {exc}')

    reload_links_table(self)
    self.save_settings()
    self.reload_data()


def reload_presets_table(self):
    """Fill the table with the preset names in their configured order."""
    self.links_table.setRowCount(0)
    for name in self.presets:
        row = self.links_table.rowCount()
        self.links_table.insertRow(row)

        name_item = QtWidgets.QTableWidgetItem(name)
        name_item.setData(QtCore.Qt.UserRole, name)
        name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.links_table.setItem(row, 0, name_item)

        recipes, translations = logic.preset_file_counts(name)
        for column, count in ((1, recipes), (2, translations)):
            count_item = QtWidgets.QTableWidgetItem(str(count))
            count_item.setTextAlignment(QtCore.Qt.AlignCenter)
            count_item.setFlags(count_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.links_table.setItem(row, column, count_item)


def _selected_preset(self):
    """Name of the preset selected in the table, or ``''``."""
    selected = self.links_table.selectedItems()
    if not selected:
        return ''
    return self.links_table.item(selected[0].row(), 0).data(QtCore.Qt.UserRole)


def _preset_name_error(name):
    """Reason why *name* cannot be a preset name, or ``None``."""
    if not name:
        return 'Имя пресета не может быть пустым'
    if name in ('.', '..') or any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name):
        return 'Имя пресета не может содержать символы, запрещённые в именах файлов'
    return None


def load_preset(self):
    """Replace the local sources with the selected preset, backing the old one up.

    A preset holds links only, so the local files are dropped and fetched
    again by the standard update flow.
    """
    name = _selected_preset(self)
    if not name:
        QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите пресет для загрузки')
        return

    answer = QtWidgets.QMessageBox.question(
        self, 'Загрузка пресета',
        f'Заменить текущие рецепты, переводы и ссылки на пресет «{name}»?\n'
        'Текущие данные будут сохранены в пресет «backup», '
        'файлы будут скачаны заново.')
    if answer != QtWidgets.QMessageBox.Yes:
        return

    if name != 'backup':
        try:
            logic.write_preset('backup', logic.preset_content(
                self.custom_recipe_links, self.custom_translation_links,
                self.recipe_file_categories))
        except OSError as exc:
            QtWidgets.QMessageBox.critical(
                self, 'Ошибка', f'Не удалось сохранить пресет «backup»: {exc}')
            return
        if 'backup' not in self.presets:
            self.presets.append('backup')

    try:
        content = logic.read_preset(name)
    except (OSError, ValueError) as exc:
        QtWidgets.QMessageBox.critical(
            self, 'Ошибка', f'Не удалось прочитать пресет «{name}»: {exc}')
        return

    recipe_links, translation_links, labels = logic.preset_links(content)
    logic.clear_data_files()
    self.custom_recipe_links = recipe_links
    self.custom_translation_links = translation_links
    self.recipe_file_categories = labels
    self.recipe_categories = dict(self.custom_recipe_links)
    self.translation_files = dict(self.custom_translation_links)
    self.save_settings()
    self.reload_data()
    reload_presets_table(self)
    self.update_data_async()


def save_preset_as(self):
    """Store the current sources as a preset of its own."""
    dialog = QtWidgets.QDialog(self)
    dialog.setWindowTitle('Сохранение пресета')
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.addWidget(QtWidgets.QLabel('Название:'))
    name_edit = QtWidgets.QLineEdit()
    layout.addWidget(name_edit)

    def save():
        name = name_edit.text().strip()
        error = _preset_name_error(name)
        if error:
            QtWidgets.QMessageBox.critical(dialog, 'Ошибка', error)
            return
        if name in self.presets:
            answer = QtWidgets.QMessageBox.question(
                dialog, 'Перезапись пресета',
                f'Пресет «{name}» уже существует. Перезаписать его текущими данными?')
            if answer != QtWidgets.QMessageBox.Yes:
                return
        try:
            logic.write_preset(name, logic.preset_content(
                self.custom_recipe_links, self.custom_translation_links,
                self.recipe_file_categories))
        except OSError as exc:
            QtWidgets.QMessageBox.critical(dialog, 'Ошибка', f'Не удалось сохранить пресет: {exc}')
            return
        if name not in self.presets:
            self.presets.append(name)
        self.save_settings()
        reload_presets_table(self)
        dialog.accept()

    buttons = QtWidgets.QHBoxLayout()
    save_button = QtWidgets.QPushButton('Сохранить')
    save_button.clicked.connect(save)
    cancel_button = QtWidgets.QPushButton('Отмена')
    cancel_button.clicked.connect(dialog.reject)
    buttons.addWidget(save_button)
    buttons.addWidget(cancel_button)
    layout.addLayout(buttons)

    dialog.exec()


def rename_preset(self):
    """Give the selected preset a new name."""
    old = _selected_preset(self)
    if not old:
        QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите пресет для переименования')
        return

    dialog = QtWidgets.QDialog(self)
    dialog.setWindowTitle('Переименование пресета')
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.addWidget(QtWidgets.QLabel('Новое название:'))
    name_edit = QtWidgets.QLineEdit(old)
    layout.addWidget(name_edit)

    def save():
        name = name_edit.text().strip()
        error = _preset_name_error(name)
        if error:
            QtWidgets.QMessageBox.critical(dialog, 'Ошибка', error)
            return
        if name == old:
            dialog.accept()
            return
        if name in self.presets:
            QtWidgets.QMessageBox.critical(
                dialog, 'Ошибка', 'Пресет с таким именем уже существует')
            return
        try:
            logic.rename_preset(old, name)
        except OSError as exc:
            QtWidgets.QMessageBox.critical(dialog, 'Ошибка', f'Не удалось переименовать пресет: {exc}')
            return
        self.presets[self.presets.index(old)] = name
        self.save_settings()
        reload_presets_table(self)
        dialog.accept()

    buttons = QtWidgets.QHBoxLayout()
    save_button = QtWidgets.QPushButton('Сохранить')
    save_button.clicked.connect(save)
    cancel_button = QtWidgets.QPushButton('Отмена')
    cancel_button.clicked.connect(dialog.reject)
    buttons.addWidget(save_button)
    buttons.addWidget(cancel_button)
    layout.addLayout(buttons)

    dialog.exec()


def delete_preset(self):
    """Remove the selected preset with all of its files."""
    name = _selected_preset(self)
    if not name:
        QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите пресет для удаления')
        return
    answer = QtWidgets.QMessageBox.question(
        self, 'Удаление пресета', f'Удалить пресет «{name}» со всеми файлами?')
    if answer != QtWidgets.QMessageBox.Yes:
        return
    logic.delete_preset(name)
    self.presets.remove(name)
    self.save_settings()
    reload_presets_table(self)
