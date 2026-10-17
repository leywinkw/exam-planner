"""Рисует скриншоты самого исходного кода для презентации и сохраняет их в docs/screens/.

    python3 code_screens.py

Каждая картинка - настоящее окно с подсвеченным кодом из файлов проекта; снимает его сама
программа (см. screenshots.py). Номера строк настоящие. Только macOS.
"""
import re
import sys
import time
import tkinter as tk
from pathlib import Path

from screenshots import front_window_number, save_window_png

ROOT = Path(__file__).parent
OUT = ROOT / "docs" / "screens"

# имя картинки -> куски кода. Кусок: (файл, строка начала, строка конца) или просто строка текста.
# Начало и конец ищутся по тексту, а не по номерам, чтобы картинки не ломались при правках кода.
# Если конец не указан (None), берётся весь блок def/class; если нет и начала, то весь файл.
IMAGES = {
    "code_errors_left.png": [
        ("planner/errors.py", None, None),
        ("planner/models.py", "def parse_difficulty", None),
    ],
    "code_errors_right.png": [
        ("ui/app.py", "def _run", None),
        ("planner/storage.py", "# любая проблема с файлами", "return Planner(), warnings"),
    ],
    "code_dicts_left.png": [
        ("planner/scheduler.py", "def build_plan", "def build_plan"),
        "        ...",
        ("planner/scheduler.py", "plan = {}  # итог", "blocked = "),
    ],
    "code_dicts_right.png": [
        ("planner/estimator.py", "# словарь 1", '"физик"'),
        "    ...",
        "}",
        ("planner/estimator.py", "def estimate_difficulty", None),
    ],
    "code_oop_left.png": [
        ("planner/models.py", "class Exam", "self.date = exam_date"),
        ("planner/models.py", "class Topic", "self.status = status"),
    ],
    "code_oop_right.png": [
        ("planner/scheduler.py", "class Planner", "self.set_max_chunk(max_chunk)"),
        ("planner/scheduler.py", "def add_exam", 'raise ValidationError("Такое событие уже есть")'),
    ],
}

BG, GUTTER_BG, FG = "#1e1e2e", "#181825", "#cdd6f4"
COLORS = {"keyword": "#cba6f7", "string": "#a6e3a1", "comment": "#6c7086", "number": "#fab387",
          "defname": "#89b4fa", "file": "#89dceb", "gutter": "#6c7086", "builtin": "#f9e2af"}
KEYWORDS = {"def", "class", "return", "if", "elif", "else", "for", "while", "in", "not", "and", "or", "try",
            "except", "raise", "from", "import", "with", "as", "None", "True", "False", "is", "continue",
            "break", "lambda", "pass", "self"}
BUILTINS = {"str", "int", "dict", "list", "set", "min", "max", "sum", "isinstance", "sorted", "len"}
# комментарий | строка | число | слово
TOKEN = re.compile(r'(?P<comment>#.*)|(?P<string>[rfbRFB]*("""|\'\'\'|"|\')(?:.*?)\3)|(?P<number>\b\d+\b)'
                   r'|(?P<word>[A-Za-zА-Яа-я_][\wА-Яа-я_]*)')


def indent_of(line):
    return len(line) - len(line.lstrip())


def cut(name, start, end):
    """Возвращает [(номер строки, текст)] куска файла: по маркерам или блоком def/class."""
    lines = (ROOT / name).read_text(encoding="utf-8").splitlines()
    if start is None:
        return list(enumerate(lines, start=1))
    first = next(i for i, line in enumerate(lines) if start in line)
    if end is not None:
        last = next(i for i in range(first, len(lines)) if end in lines[i])
    else:
        last = first
        for i in range(first + 1, len(lines)):
            if lines[i].strip() and indent_of(lines[i]) <= indent_of(lines[first]):
                break
            last = i
        while not lines[last].strip():  # пустые строки в конце блока не нужны
            last -= 1
    return [(n + 1, lines[n]) for n in range(first, last + 1)]


def build_rows(pieces):
    """Склеивает куски в строки картинки: (номер или None, текст, вид)."""
    rows, last_file = [], None
    for piece in pieces:
        if isinstance(piece, str):
            rows.append((None, piece, "code"))
            continue
        name, start, end = piece
        if name != last_file:
            if rows:
                rows.append((None, "", "code"))  # пустая строка между файлами
            rows.append((None, f"# {name}", "file"))
        rows += [(n, text, "code") for n, text in cut(name, start, end)]
        last_file = name
    return rows


def highlight(widget, row, text, state):
    """Раскрашивает одну строку; state["doc"] - открыт ли многострочный docstring."""
    quotes = text.count('"""')
    if state["doc"]:
        widget.tag_add("string", f"{row}.0", f"{row}.end")
        if quotes % 2:
            state["doc"] = False
        return
    if quotes % 2:  # docstring начинается в этой строке и продолжается ниже
        start = text.index('"""')
        widget.tag_add("string", f"{row}.{start}", f"{row}.end")
        state["doc"] = True
        text = text[:start]
    previous = ""
    for match in TOKEN.finditer(text):
        kind, word, tag = match.lastgroup, match.group(0), None
        if kind in ("comment", "string", "number"):
            tag = kind
        elif kind == "word":
            if word in KEYWORDS:
                tag = "keyword"
            elif previous in ("def", "class"):
                tag = "defname"
            elif word in BUILTINS:
                tag = "builtin"
            previous = word
        if tag:
            widget.tag_add(tag, f"{row}.{match.start()}", f"{row}.{match.end()}")
        if kind != "word":
            previous = ""


def render(master, name, pieces):
    rows = build_rows(pieces)
    width = max(len(text) for _, text, _ in rows) + 2

    window = tk.Toplevel(master)
    window.title(", ".join(dict.fromkeys(p[0] for p in pieces if not isinstance(p, str))))
    window.configure(bg=BG)
    window.geometry("+60+60")
    font = ("Menlo", 15)
    gutter = tk.Text(window, width=4, height=len(rows), bg=GUTTER_BG, fg=COLORS["gutter"], font=font, bd=0,
                     highlightthickness=0, padx=10, pady=14, takefocus=0, cursor="arrow")
    code = tk.Text(window, width=width, height=len(rows), bg=BG, fg=FG, font=font, bd=0, highlightthickness=0,
                   padx=14, pady=14, wrap="none", takefocus=0, cursor="arrow", insertwidth=0)
    gutter.pack(side="left", fill="y")
    code.pack(side="left")
    for tag, color in COLORS.items():
        code.tag_configure(tag, foreground=color)
    code.tag_configure("file", foreground=COLORS["file"], font=("Menlo", 15, "bold"))
    state = {"doc": False}
    for row, (number, text, kind) in enumerate(rows, start=1):
        newline = "\n" if row < len(rows) else ""
        code.insert("end", text + newline)
        gutter.insert("end", (str(number) if number else "").rjust(3) + newline)
        if kind == "file":
            code.tag_add("file", f"{row}.0", f"{row}.end")
        else:
            highlight(code, row, text, state)
    code.configure(state="disabled")
    gutter.configure(state="disabled")

    window.lift()
    window.focus_force()
    master.update()
    time.sleep(1.0)  # даём окну отрисоваться, иначе снимок получится пустым
    master.update()
    time.sleep(0.3)
    ok = save_window_png(front_window_number(prefer_key=True), OUT / name)
    print(("saved  " if ok else "FAILED ") + name, f"({len(rows)} строк, {width} символов в ширину)")
    window.destroy()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    master = tk.Tk()
    master.withdraw()  # один скрытый корень; каждая картинка - отдельное окно поверх него
    for name, pieces in IMAGES.items():
        render(master, name, pieces)
    master.destroy()


if __name__ == "__main__":
    if sys.platform != "darwin":
        sys.exit("code_screens.py работает только на macOS")
    main()
