import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from planner.calview import (CONTROL_COLOR, EXAM_COLOR, MONTHS, WEEKDAYS, load_color,
                             month_weeks, shift_month)
from planner.catalog import subjects, topics_for
from planner.errors import PlannerError
from planner.models import CONTROL, CONTROL_PREFIX, DONE, EXAM, TODO, parse_date
from planner.storage import Storage
from ui import theme
from ui.dialogs import MultiTopicDialog
from ui.gantt import GanttChart
from ui.theme import ACCENT, CARD, MUTED, TEXT, font
from ui.widgets import HintCombobox, HintEntry

STATUS_TEXT = {TODO: "в плане", DONE: "готово"}
KIND_LABELS = {"Экзамен": EXAM, "Контрольная": CONTROL}


def short(name):
    """Event name for narrow columns."""
    return name.replace(CONTROL_PREFIX, "КР · ")


def plural_days(n):
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} день"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} дня"
    return f"{n} дней"


def card(parent, **pack):
    """White panel with a thin border; returns the inner frame to put widgets in."""
    outer = tk.Frame(parent, bg=CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    outer.pack(**pack)
    inner = ttk.Frame(outer, padding=16)
    inner.pack(fill="both", expand=True)
    return outer, inner


class App(ttk.Frame):
    def __init__(self, root, storage=None):
        super().__init__(root, style="Page.TFrame")
        self.root = root
        self.storage = storage or Storage("data")
        self.planner, warnings = self.storage.load()
        self.today = date.today()
        self.year, self.month = self.today.year, self.today.month
        self.selected_day = self.today
        self.topic_ids = {}
        self.exam_ids = {}
        self.note = ""
        self.at_risk = self.planner.build_plan(self.today)

        theme.apply_style(self.root)
        self._build()
        self.pack(fill="both", expand=True)
        self.refresh()
        if warnings:
            messagebox.showwarning("Данные", "\n".join(warnings))

    # --- layout --------------------------------------------------------
    def _build(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(24, 14))
        header.pack(fill="x")
        ttk.Label(header, text="Планировщик экзаменов", style="Title.TLabel").pack(side="left")
        self.summary = ttk.Label(header, style="Sub.TLabel")
        self.summary.pack(side="right")

        body = ttk.Frame(self, style="Page.TFrame", padding=16)
        body.pack(fill="both", expand=True)
        _, left = card(body, side="left", fill="y", padx=(0, 16))
        _, right = card(body, side="left", fill="both", expand=True)
        self._build_exams(left)
        self._build_topics(left)

        self.status = ttk.Label(right, style="Status.TLabel", wraplength=640, justify="left")
        self.status.pack(side="bottom", anchor="w", pady=(10, 0))
        self._build_settings(right)
        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True)
        calendar_tab = ttk.Frame(tabs, padding=(0, 12))
        gantt_tab = ttk.Frame(tabs, padding=(0, 12))
        tabs.add(calendar_tab, text="Календарь нагрузки")
        tabs.add(gantt_tab, text="Диаграмма Ганта")
        self.gantt = GanttChart(gantt_tab)
        self.gantt.pack(fill="both", expand=True)
        self._build_calendar(calendar_tab)

    def _build_exams(self, parent):
        ttk.Label(parent, text="ЧТО СДАЁМ", style="Section.TLabel").pack(anchor="w")
        self.exam_name = HintCombobox(parent, "Выберите или введите предмет")
        self.exam_name.pack(fill="x", pady=(6, 6))
        row = ttk.Frame(parent)
        row.pack(fill="x")
        self.exam_date = HintEntry(row, "ДД.ММ.ГГГГ", width=11)
        self.exam_date.pack(side="left")
        self.exam_kind = ttk.Combobox(row, state="readonly", width=12, values=list(KIND_LABELS))
        self.exam_kind.set("Экзамен")
        self.exam_kind.pack(side="left", padx=8)
        ttk.Button(row, text="Добавить", style="Accent.TButton",
                   command=self.add_exam).pack(side="right")
        self.exam_tree = ttk.Treeview(parent, columns=("date", "left"), height=4, selectmode="browse")
        for col, text, width, anchor in (("#0", "Событие", 170, "w"), ("date", "Дата", 86, "center"),
                                         ("left", "Осталось", 80, "center")):
            self.exam_tree.heading(col, text=text)
            self.exam_tree.column(col, width=width, anchor=anchor)
        self.exam_tree.pack(fill="x", pady=(10, 6))
        ttk.Button(parent, text="Удалить выбранное", style="Danger.TButton",
                   command=self.remove_exam).pack(anchor="e")

    def _build_topics(self, parent):
        ttk.Label(parent, text="ТЕМЫ", style="Section.TLabel").pack(anchor="w", pady=(18, 0))
        self.topic_exam = ttk.Combobox(parent, state="readonly")
        self.topic_exam.pack(fill="x", pady=(6, 6))
        self.topic_exam.bind("<<ComboboxSelected>>", lambda _e: self.update_dropdowns())
        self.topic_name = HintCombobox(parent, "Выберите или введите тему")
        self.topic_name.pack(fill="x")
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(6, 0))
        ttk.Label(row, text="Сложность").pack(side="left")
        self.topic_diff = ttk.Combobox(row, state="readonly", width=6,
                                       values=["авто", "1", "2", "3", "4", "5"])
        self.topic_diff.set("авто")
        self.topic_diff.pack(side="left", padx=8)
        ttk.Button(row, text="Несколько…", command=self.add_many).pack(side="right")
        ttk.Button(row, text="Добавить", style="Accent.TButton",
                   command=self.add_topic).pack(side="right", padx=(0, 6))

        self.topic_tree = ttk.Treeview(parent, columns=("exam", "diff", "status"), height=6,
                                       selectmode="browse")
        for col, text, width in (("#0", "Тема", 150), ("exam", "Событие", 100),
                                 ("diff", "Сл.", 36), ("status", "Статус", 66)):
            self.topic_tree.heading(col, text=text)
            self.topic_tree.column(col, width=width,
                                   anchor="w" if col in ("#0", "exam") else "center")
        self.topic_tree.pack(fill="x", pady=(10, 6))
        buttons = ttk.Frame(parent)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Готово", command=lambda: self.mark(DONE)).pack(side="left")
        ttk.Button(buttons, text="Не сделано", command=lambda: self.mark(TODO)).pack(side="left", padx=6)
        ttk.Button(buttons, text="Удалить", style="Danger.TButton",
                   command=self.remove_topic).pack(side="right")
        ttk.Button(parent, text="Применить выбранную сложность к теме",
                   command=self.change_difficulty).pack(fill="x", pady=(6, 0))

    def _build_settings(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Label(bar, text="ПЛАН", style="Section.TLabel").pack(side="left", padx=(0, 14))
        ttk.Label(bar, text="Часов в день").pack(side="left")
        self.limit = ttk.Spinbox(bar, from_=1, to=16, width=4, command=self.set_limit)
        self.limit.pack(side="left", padx=(6, 18))
        ttk.Label(bar, text="Часов на тему в день").pack(side="left")
        self.chunk = ttk.Spinbox(bar, from_=1, to=8, width=4, command=self.set_chunk)
        self.chunk.pack(side="left", padx=6)
        for spin, action in ((self.limit, self.set_limit), (self.chunk, self.set_chunk)):
            spin.bind("<Return>", lambda _e, a=action: a())
            spin.bind("<FocusOut>", lambda _e, a=action: a())
        ttk.Button(bar, text="Перепланировать", style="Accent.TButton",
                   command=self.replan).pack(side="right")

    def _build_calendar(self, parent):
        head = ttk.Frame(parent)
        head.pack(fill="x")
        ttk.Button(head, text="◀", width=3, command=lambda: self.change_month(-1)).pack(side="left")
        self.month_label = ttk.Label(head, style="H.TLabel", anchor="center")
        self.month_label.pack(side="left", expand=True, fill="x")
        ttk.Button(head, text="▶", width=3, command=lambda: self.change_month(1)).pack(side="left")

        self.grid_frame = tk.Frame(parent, bg=CARD)
        self.grid_frame.pack(fill="both", expand=True, pady=10)
        for col in range(7):
            self.grid_frame.columnconfigure(col, weight=1, uniform="day")

        legend = ttk.Frame(parent)
        legend.pack(fill="x")
        for color, text in (("#f1f5f9", "свободно"), ("#bbf7d0", "до 50%"), ("#fde68a", "до 80%"),
                            ("#fdba74", "лимит"), (EXAM_COLOR, "экзамен"), (CONTROL_COLOR, "контрольная")):
            tk.Label(legend, bg=color, width=2, highlightbackground=theme.BORDER,
                     highlightthickness=1).pack(side="left")
            ttk.Label(legend, text=text, style="Muted.TLabel").pack(side="left", padx=(5, 14))

        self.day_title = ttk.Label(parent, style="H.TLabel")
        self.day_title.pack(anchor="w", pady=(14, 4))
        self.day_list = tk.Listbox(parent, height=5, bd=0, highlightthickness=1,
                                   highlightbackground=theme.BORDER, font=font(12),
                                   activestyle="none", bg="white", fg=TEXT,
                                   selectbackground=theme.ACCENT_SOFT,
                                   selectforeground=TEXT)
        self.day_list.pack(fill="x")

    # --- actions -------------------------------------------------------
    def _run(self, action):
        """Run an action; show planner errors in a dialog instead of crashing."""
        try:
            action()
        except PlannerError as error:
            messagebox.showerror("Ошибка", str(error))
            return False
        return True

    def _changed(self, replanned=False, note=""):
        self.note = note
        self.today = date.today()
        if not replanned:
            self.at_risk = self.planner.build_plan(self.today)
        try:
            self.storage.save(self.planner)
        except PlannerError as error:
            messagebox.showerror("Ошибка", str(error))
        self.refresh()

    def add_exam(self):
        def go():
            kind = KIND_LABELS[self.exam_kind.get()]
            self.planner.add_exam(self.exam_name.get(), parse_date(self.exam_date.get()),
                                  date.today(), kind)
            self.exam_name.delete(0, "end")
            self.exam_date.delete(0, "end")
        if self._run(go):
            self._changed(note="Теперь добавьте темы: выберите событие ниже и тему из списка.")

    def remove_exam(self):
        name = self.exam_ids.get(self._selected(self.exam_tree))
        if name is None:
            return messagebox.showinfo("События", "Выберите экзамен или контрольную в списке")
        if messagebox.askyesno("Удалить", f"Удалить «{short(name)}» и его темы?"):
            if self._run(lambda: self.planner.remove_exam(name)):
                self._changed()

    def add_topic(self):
        added = []

        def go():
            added.append(self.planner.add_topic(
                self.topic_exam.get(), self.topic_name.get(), self.topic_diff.get()))
            self.topic_name.delete(0, "end")
        if self._run(go):
            topic = added[0]
            how = "определена автоматически" if self.topic_diff.get() == "авто" else "задана"
            self._changed(note=f"«{topic.name}»: сложность {topic.difficulty} {how} "
                               f"({topic.hours} ч). Её можно поменять кнопкой под списком тем.")

    def add_many(self):
        event = self.topic_exam.get()
        if not event:
            return messagebox.showinfo("Темы", "Сначала добавьте экзамен или контрольную")
        taken = [t.name for t in self.planner.topics.values() if t.exam == event]
        dialog = MultiTopicDialog(self.root, event, taken)
        self.root.wait_window(dialog)
        errors, count = [], 0
        for name in dialog.result:
            try:
                self.planner.add_topic(event, name, self.topic_diff.get())
                count += 1
            except PlannerError as error:
                errors.append(f"{name}: {error}")
        if errors:
            messagebox.showerror("Не все темы добавлены", "\n".join(errors))
        if count:
            self._changed(note=f"Добавлено тем: {count}.")

    def update_dropdowns(self):
        """Fill the dropdown lists: subjects not added yet, typical topics of the chosen event."""
        self.exam_name["values"] = subjects(taken=self.planner.exams)
        taken = [t.name for t in self.planner.topics.values() if t.exam == self.topic_exam.get()]
        self.topic_name["values"] = topics_for(self.topic_exam.get(), taken)

    def change_difficulty(self):
        key = self._selected_topic()
        if key and self._run(lambda: self.planner.set_difficulty(*key, self.topic_diff.get())):
            topic = self.planner.topics[key]
            self._changed(note=f"«{topic.name}»: сложность {topic.difficulty} ({topic.hours} ч).")

    def _selected_topic(self):
        key = self.topic_ids.get(self._selected(self.topic_tree))
        if key is None:
            messagebox.showinfo("Темы", "Выберите тему в списке")
        return key

    def mark(self, status):
        key = self._selected_topic()
        if key and self._run(lambda: self.planner.set_status(*key, status)):
            self._changed()

    def remove_topic(self):
        key = self._selected_topic()
        if key and self._run(lambda: self.planner.remove_topic(*key)):
            self._changed()

    def set_limit(self):
        if self.limit.get() == str(self.planner.daily_limit):
            return
        if self._run(lambda: self.planner.set_daily_limit(self.limit.get())):
            self._changed()
        else:
            self.limit.set(self.planner.daily_limit)

    def set_chunk(self):
        if self.chunk.get() == str(self.planner.max_chunk):
            return
        if self._run(lambda: self.planner.set_max_chunk(self.chunk.get())):
            self._changed()
        else:
            self.chunk.set(self.planner.max_chunk)

    def replan(self):
        moved, at_risk = self.planner.replan(date.today())
        self.at_risk = at_risk
        self._changed(replanned=True)
        lines = []
        if moved:
            lines.append("Перенесено вперёд: " + ", ".join(t.name for t in moved))
        if at_risk:
            lines.append("Не помещаются до срока: " + ", ".join(t.name for t in at_risk))
        messagebox.showinfo("Перепланирование", "\n".join(lines) or "План актуален, переносить нечего.")

    def change_month(self, delta):
        self.year, self.month = shift_month(self.year, self.month, delta)
        self.draw_calendar()

    def select_day(self, day):
        self.selected_day = day
        self.draw_calendar()
        self.draw_day()

    # --- drawing -------------------------------------------------------
    @staticmethod
    def _selected(tree):
        selection = tree.selection()
        return selection[0] if selection else None

    def refresh(self):
        events = sorted(self.planner.exams.values(), key=lambda e: e.date)
        self.exam_tree.delete(*self.exam_tree.get_children())
        self.exam_ids = {}
        for event in events:
            left = (event.date - self.today).days
            iid = self.exam_tree.insert("", "end", text=short(event.name), values=(
                event.date.strftime("%d.%m.%Y"), plural_days(left) if left >= 0 else "прошло"))
            self.exam_ids[iid] = event.name
        self.topic_exam["values"] = [e.name for e in events]
        if events and self.topic_exam.get() not in self.topic_exam["values"]:
            self.topic_exam.set(events[0].name)
        if not events:
            self.topic_exam.set("")
        self.topic_tree.delete(*self.topic_tree.get_children())
        self.topic_ids = {}
        for topic in self.planner.topics.values():
            iid = self.topic_tree.insert("", "end", text=topic.name, values=(
                short(topic.exam), topic.difficulty, STATUS_TEXT[topic.status]))
            self.topic_ids[iid] = topic.key
        self.limit.set(self.planner.daily_limit)
        self.chunk.set(self.planner.max_chunk)
        self.update_dropdowns()
        self.draw_calendar()
        self.draw_day()
        self.gantt.draw(self.planner, self.at_risk, self.today)
        self._draw_status(events)

    def _draw_status(self, events):
        upcoming = [e for e in events if e.date > self.today]
        if upcoming:
            nearest = upcoming[0]
            self.summary.configure(text=f"Ближайшее: {short(nearest.name)} — через "
                                        f"{plural_days((nearest.date - self.today).days)}")
        else:
            self.summary.configure(text="Добавьте первый экзамен слева")
        if self.at_risk:
            color = theme.DANGER
            text = "Не помещаются до срока: " + ", ".join(
                f"{t.name} ({short(t.exam)})" for t in self.at_risk)
        else:
            color = MUTED
            text = ("Все темы помещаются в план." if self.planner.topics
                    else "Добавьте экзамен или контрольную и темы — план построится сам.")
        if self.note:
            text = f"{self.note}\n{text}"
        self.status.configure(foreground=color, text=text)

    def draw_calendar(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.month_label.configure(text=f"{MONTHS[self.month - 1]} {self.year}")
        for col, name in enumerate(WEEKDAYS):
            ttk.Label(self.grid_frame, text=name, style="Muted.TLabel", anchor="center").grid(
                row=0, column=col, sticky="ew", pady=(0, 4))
        marks = {e.date: e.kind for e in self.planner.exams.values()}
        for row, week in enumerate(month_weeks(self.year, self.month), start=1):
            for col, number in enumerate(week):
                if not number:
                    continue
                self._draw_cell(row, col, date(self.year, self.month, number), marks)

    def _draw_cell(self, row, col, day, marks):
        hours = self.planner.day_load(day)
        kind = marks.get(day)
        if kind == EXAM:
            color, caption = EXAM_COLOR, "экзамен"
        elif kind == CONTROL:
            color, caption = CONTROL_COLOR, "контрольная"
        else:
            color = load_color(hours, self.planner.daily_limit)
            caption = f"{hours} ч" if hours else " "
        border = color
        if day == self.selected_day:
            border = TEXT
        elif day == self.today:
            border = ACCENT
        cell = tk.Label(self.grid_frame, text=f"{day.day}\n{caption}", bg=color, fg=TEXT, height=3,
                        font=font(12, "bold" if day == self.today else "normal"),
                        cursor="hand2", highlightthickness=2, highlightbackground=border,
                        highlightcolor=border)
        cell.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        cell.bind("<Button-1>", lambda _e, d=day: self.select_day(d))

    def draw_day(self):
        day = self.selected_day
        self.day_title.configure(text=f"{day.strftime('%d.%m.%Y')} · {self.planner.day_load(day)} ч")
        self.day_list.delete(0, "end")
        for event in self.planner.exams.values():
            if event.date == day:
                label = "КОНТРОЛЬНАЯ" if event.kind == CONTROL else "ЭКЗАМЕН"
                self.day_list.insert("end", f"{label}: {event.name.replace(CONTROL_PREFIX, '')}")
        for exam, topic, hours in self.planner.plan.get(day, []):
            self.day_list.insert("end", f"{topic} — {short(exam)}, {hours} ч")
        if not self.day_list.size():
            self.day_list.insert("end", "На этот день ничего не запланировано")
