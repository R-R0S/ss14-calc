"""Dump the rendered calculation for every test fixture recipe.

A regression helper: take a snapshot before a change, another one after it
and diff the two.

    python test/snapshot_calculation.py > /tmp/after.txt
    diff /tmp/before.txt /tmp/after.txt

The script runs on the committed test fixtures (``test/fixtures``) inside a
scratch directory, so the local ``settings.cfg``, ``recipes/`` and
``translations/`` are never touched and the dump stays the same no matter
what data the application has downloaded.
"""
import os
import shutil
import sys
import tempfile

from PySide6 import QtWidgets, QtCore

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import main as app_main  # noqa: E402

FIXTURES = os.path.join(REPO_ROOT, 'test', 'fixtures')
AMOUNTS = ('90', '1')


def make_workdir():
    """Copy the test fixtures into a scratch directory and move into it."""
    workdir = tempfile.mkdtemp(prefix='ss14-calc-snapshot-')
    for folder in ('recipes', 'translations'):
        shutil.copytree(os.path.join(FIXTURES, folder), os.path.join(workdir, folder))
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
    for recipe_id in recipe_ids:
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
