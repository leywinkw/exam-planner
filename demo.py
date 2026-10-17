"""Opens the planner with sample data (own temp folder, your real data is not touched).

Used to take screenshots for the presentation:
    python3 demo.py calendar   # month calendar with a selected day
    python3 demo.py gantt      # Gantt chart tab
    python3 demo.py dialog     # "several topics" dialog
    python3 demo.py error      # error message for a wrong date
"""
import shutil
import sys
import tempfile
import tkinter as tk
from datetime import date, timedelta
from pathlib import Path

from planner.models import CONTROL
from planner.scheduler import Planner
from planner.storage import Storage
from ui.app import App
from ui.dialogs import MultiTopicDialog

STATES = ("calendar", "gantt", "dialog", "error")


def sample_planner(today):
    planner = Planner()
    planner.add_exam("Математика", today + timedelta(days=16), today)
    control = planner.add_exam("Физика", today + timedelta(days=7), today, kind=CONTROL)
    planner.add_exam("Программирование на Python", today + timedelta(days=21), today)
    for name in ("Пределы", "Производные", "Интегралы", "Ряды"):
        planner.add_topic("Математика", name, "авто")
    for name in ("Кинематика", "Законы Ньютона", "Оптика"):
        planner.add_topic(control.name, name, "авто")
    for name in ("Основы Python", "Коллекции", "ООП", "Обработка ошибок"):
        planner.add_topic("Программирование на Python", name, "авто")
    planner.set_status("Математика", "Пределы", "done")
    return planner


def find_notebook(widget):
    for child in widget.winfo_children():
        if child.winfo_class() == "TNotebook":
            return child
        found = find_notebook(child)
        if found:
            return found


def main():
    state = sys.argv[1] if len(sys.argv) > 1 else "calendar"
    if state not in STATES:
        sys.exit(f"Use one of: {', '.join(STATES)}")
    today = date.today()
    folder = Path(tempfile.mkdtemp(prefix="exam_planner_demo_"))
    storage = Storage(folder)
    storage.save(sample_planner(today))

    root = tk.Tk()
    root.title("Планировщик подготовки к экзаменам")
    root.geometry("1240x820+40+40")
    app = App(root, storage)

    def prepare():
        if state == "calendar":
            app.select_day(today + timedelta(days=2))
        elif state == "gantt":
            find_notebook(root).select(1)
        elif state == "dialog":
            event = "Программирование на Python"
            app.topic_exam.set(event)
            app.update_dropdowns()
            dialog = MultiTopicDialog(root, event, ["Основы Python"])
            for _name, var in dialog.vars[:3]:
                var.set(True)
            dialog.extra.insert(0, "Работа с файлами")
        elif state == "error":
            app.exam_name.set("Химия")
            app.exam_date.insert(0, "32.13.2026")
            app.add_exam()

    root.after(500, prepare)
    root.mainloop()
    shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
