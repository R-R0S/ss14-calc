#!/usr/bin/env bash
#
# Запуск калькулятора SS14 на Linux.
#
#   1. Проверяет, установлен ли python (несовпадение версии — предупреждение,
#      но не остановка).
#   2. Проверяет файлы приложения и окружение .venv рядом с ними: окружение
#      создаётся, зависимости ставятся из requirements.txt.
#   3. Активирует окружение в этом же окне и запускает калькулятор.
#
# Данные (settings.cfg, recipes/, translations/) создаются в папке скрипта,
# поэтому запускать его можно из любого каталога.

set -u

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR" || exit 1

MIN_PY='3.10'
VENV_DIR="$APP_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
REQ="$APP_DIR/requirements.txt"

note() { printf '%s\n' "$*"; }
warn() { printf 'Внимание: %s\n' "$*"; }
fail() { printf 'Ошибка: %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- 1. python
PYTHON=''
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

PYVER=''
if [ -n "$PYTHON" ]; then
    PYVER="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    note "Найден Python $PYVER"
    if ! "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info[:2] < (3, 10))'; then
        warn "приложению нужен Python $MIN_PY и новее (проверено на 3.12 и 3.14)."
        warn "Запуск не блокирую: если окружение .venv уже есть, оно продолжит работать."
    fi
else
    warn "python3 не найден в PATH."
fi

# ------------------------------------------------- 2. файлы приложения
missing=''
for file in main.py ui.py logic.py data.py requirements.txt; do
    [ -f "$APP_DIR/$file" ] || missing="$missing $file"
done
if [ -n "$missing" ]; then
    warn "не найдены файлы приложения:$missing"
    note "Похоже, папка приложения неполная. Восстановите её через git:"
    if git -C "$APP_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        note "    git -C \"$APP_DIR\" checkout -- ."
    else
        note "    git clone https://github.com/R-R0S/ss14-calc.git ss14-calc"
        note "    cd ss14-calc && ./run.sh"
    fi
    fail "запуск прерван"
fi

# ------------------------------------------------------- 3. окружение .venv
if [ ! -x "$VENV_PY" ]; then
    [ -n "$PYTHON" ] || fail "нет окружения .venv и нет python для его создания"
    note "Окружение .venv не найдено — создаю (Python $PYVER)…"
    "$PYTHON" -m venv "$VENV_DIR" || fail "не удалось создать окружение .venv"
fi

# Возвращает 0, если все пакеты из requirements.txt стоят в нужных версиях;
# иначе печатает список проблем и возвращает 1.
deps_missing() {
    "$VENV_PY" - "$REQ" <<'PY'
import sys
from importlib import metadata

try:
    lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
except OSError:
    sys.exit(0)  # requirements.txt нет — сверять не с чем

broken = []
for line in lines:
    line = line.strip()
    if not line or line.startswith('#') or '==' not in line:
        continue
    name, want = (part.strip() for part in line.split('==', 1))
    try:
        have = metadata.version(name)
    except metadata.PackageNotFoundError:
        broken.append(f'{line} — не установлен')
        continue
    if have != want:
        broken.append(f'{line} — установлен {have}')
print('\n'.join(broken))
sys.exit(1 if broken else 0)
PY
}

if deps_missing; then
    note "Зависимости в порядке."
else
    note "Ставлю зависимости из requirements.txt…"
    "$VENV_PY" -m pip install -r "$REQ" || fail "не удалось установить зависимости"
fi

# --------------------------------------------------------------- 4. запуск
note "Запускаю калькулятор (выход — Ctrl+C в этом терминале)…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate" || fail "не удалось активировать окружение"
# Внутри activate зашит абсолютный путь окружения: если папку проекта
# переехали или переименовали, PATH ведёт мимо .venv и `python` оказывается
# системным. Такой activate обходим, запуская интерпретатор напрямую.
if [ "$(command -v python 2>/dev/null)" != "$VENV_DIR/bin/python" ]; then
    warn "activate указывает на другое расположение окружения — запускаю через $VENV_PY"
    exec "$VENV_PY" "$APP_DIR/main.py"
fi
exec python "$APP_DIR/main.py"
