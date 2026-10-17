"""Console input/output examples of the planner core (no window). Run: python3 examples/io_demo.py

A fixed "today" (01.10.2026) makes the output reproducible.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from planner.errors import PlannerError
from planner.models import CONTROL, parse_date
from planner.scheduler import Planner
from planner.storage import Storage

TODAY = date(2026, 10, 1)


def show(title, action):
    """Run action, print the result or the user-facing error message."""
    try:
        result = action()
        print(f"[ОК]     {title} -> {result}")
    except PlannerError as error:
        print(f"[ОШИБКА] {title} -> {error}")


def fmt(day):
    return day.strftime("%d.%m")


print("== 1. Ввод экзаменов ==")
p = Planner()
show("Экзамен 'Математика', 11.10.2026", lambda: p.add_exam("Математика", parse_date("11.10.2026"), TODAY).name)
show("Экзамен '' (пустое название)", lambda: p.add_exam("", parse_date("11.10.2026"), TODAY))
show("Экзамен 'Физика', дата '32.13.2026'", lambda: p.add_exam("Физика", parse_date("32.13.2026"), TODAY))
show("Экзамен 'Физика', дата 20.09.2026 (прошла)", lambda: p.add_exam("Физика", parse_date("20.09.2026"), TODAY))
show("Экзамен 'Математика' повторно", lambda: p.add_exam("Математика", parse_date("12.10.2026"), TODAY))
show("Контрольная 'Физика', 06.10.2026", lambda: p.add_exam("Физика", parse_date("06.10.2026"), TODAY, kind=CONTROL).name)

print("\n== 2. Ввод тем и автоподбор сложности ==")
ctl = "Контрольная · Физика"
show("Тема 'Введение в анализ', сложность 'авто'", lambda: p.add_topic("Математика", "Введение в анализ", "авто").difficulty)
show("Тема 'Интегралы', сложность 'авто'", lambda: p.add_topic("Математика", "Интегралы", "авто").difficulty)
show("Тема 'Ряды', сложность 9", lambda: p.add_topic("Математика", "Ряды", "9"))
show("Тема 'Ряды', сложность 'abc'", lambda: p.add_topic("Математика", "Ряды", "abc"))
show("Тема 'Ряды', сложность 3", lambda: p.add_topic("Математика", "Ряды", "3").difficulty)
show("Тема 'Кинематика' для контрольной, 'авто'", lambda: p.add_topic(ctl, "Кинематика", "авто").difficulty)
show("Тема 'Оптика' для контрольной, 'авто'", lambda: p.add_topic(ctl, "Оптика", "авто").difficulty)
show("Тема для несуществующего экзамена", lambda: p.add_topic("Химия", "Растворы", "авто"))
show("Лимит часов в день = 0", lambda: p.set_daily_limit("0"))

print("\n== 3. Построение плана (лимит 4 ч/день, не более 2 ч одной темы в день) ==")
risk = p.build_plan(TODAY)
for day in sorted(p.plan):
    items = ", ".join(f"{t} ({h} ч)" if t != "Повторение" else f"Повторение · {e.replace('Контрольная · ', 'КР ')} ({h} ч)"
                      for e, t, h in p.plan[day])
    print(f"{fmt(day)}  {p.day_load(day)} ч: {items}")
print("Не помещаются:", [t.name for t in risk] or "нет")

print("\n== 4. Отстал: перепланирование через 3 дня ==")
p.set_status("Математика", "Интегралы", "done")
moved, risk = p.replan(TODAY + timedelta(days=3))
print("Перенесено вперёд:", [t.name for t in moved])
print("Не помещаются до срока:", [t.name for t in risk] or "нет")

print("\n== 5. Файлы данных ==")
with tempfile.TemporaryDirectory() as folder:
    Storage(folder).save(p)
    print("Сохранено:", sorted(os.listdir(folder)))
    with open(os.path.join(folder, "exams.csv"), encoding="utf-8") as file:
        print(file.read().strip())
    with open(os.path.join(folder, "exams.csv"), "w", encoding="utf-8") as file:
        file.write("name,date\nМатематика,не-дата\n")
    loaded, warnings = Storage(folder).load(TODAY)
    print("Повреждённый файл -> экзаменов:", len(loaded.exams))
    print("Сообщение:", warnings[0])
    print("Копия сохранена:", "exams.csv.bak" in os.listdir(folder))
