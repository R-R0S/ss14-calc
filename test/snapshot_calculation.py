"""Dump the rendered calculation for a sample of recipes.

A regression helper: take a snapshot before a change, another one after it
and diff the two.

    python test/snapshot_calculation.py > /tmp/after.txt
    diff /tmp/before.txt /tmp/after.txt

The script runs in a scratch directory holding a copy of the downloaded data,
so the local ``settings.cfg``, ``recipes/`` and ``translations/`` are never
touched.  Like the application itself, it needs recipes: start the app once
and press «Обновить данные».
"""
import os
import shutil
import sys
import tempfile

from PySide6 import QtWidgets, QtCore

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import main as app_main  # noqa: E402

SAMPLE_SIZE = 45
AMOUNTS = ('90', '1')

# Добавляются к выборке в дополнение к равномерной.
FIXED_RECIPES = ('RobustHarvest', 'CreateButter')


def make_workdir():
    """Copy the downloaded data into a scratch directory and move into it."""
    workdir = tempfile.mkdtemp(prefix='ss14-calc-snapshot-')
    for folder in ('recipes', 'translations'):
        source = os.path.join(REPO_ROOT, folder)
        target = os.path.join(workdir, folder)
        if os.path.isdir(source):
            shutil.copytree(source, target)
        else:
            os.makedirs(target)
    os.chdir(workdir)
    return workdir


def reject_modals(app):
    """Close any popup so a message box can never hang the dump."""

    def sweep():
        modal = app.activeModalWidget()
        if modal is not None:
            modal.reject()

    timer = QtCore.QTimer()
    timer.timeout.connect(sweep)
    timer.start(50)
    return timer


def dump(app, win):
    print('CATEGORIES:', win.category_combo.count())
    print('FIRST_CATEGORY:', win.category_combo.currentText())
    print('RECIPE_COUNT_IN_CATEGORY:', win.recipe_combo.count())

    recipe_ids = sorted(win.recipe_dict)
    step = max(1, len(recipe_ids) // SAMPLE_SIZE)
    sample = list(recipe_ids[::step])
    for recipe_id in FIXED_RECIPES:
        if recipe_id in win.recipe_dict and recipe_id not in sample:
            sample.append(recipe_id)
    for recipe_id in sample:
        recipe = win.recipe_dict[recipe_id]
        category = recipe['category']
        index = win.category_combo.findText(category)
        if index < 0:
            print(f'!! category missing: {category}')
            continue
        win.category_combo.setCurrentIndex(index)
        app.processEvents()

        name = win.translations.get(recipe_id.lower().replace(' ', ''), recipe_id)
        position = win.recipe_combo.findText(name)
        if position < 0:
            print(f'!! recipe missing: {category} / {recipe_id}')
            continue
        win.recipe_combo.setCurrentIndex(position)

        for amount in AMOUNTS:
            win.amount_entry.setText(amount)
            win.calculate_reactants()
            app.processEvents()
            print(f'=== {category} | {recipe_id} | {amount} ===')
            print(win.result_text.toPlainText())


def main():
    original_cwd = os.getcwd()
    workdir = make_workdir()
    try:
        app = QtWidgets.QApplication(sys.argv)
        win = app_main.ReagentCalculatorQt()
        win.show()
        app.processEvents()
        timer = reject_modals(app)
        dump(app, win)
        timer.stop()
        win.close()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == '__main__':
    main()
