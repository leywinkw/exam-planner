import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from planner.calview import EXAM_COLOR, MONTHS, WEEKDAYS, load_color, month_weeks, shift_month
from planner.errors import PlannerError
from planner.models import DONE, TODO, parse_date
from planner.storage import Storage
from ui.gantt import GanttChart
from ui.widgets import HintEntry

BG = "#ffffff"
PANEL = "#f8fafc"
TEXT = "#0f172a"
MUTED = "#64748b"
ACCENT = "#2563eb"
STATUS_TEXT = {TODO: "в плане", DONE: "готово"}


class App(ttk.Frame):
    def __init__(self, root, storage=None):
        super().__init__(root, padding=12)
        self.root = root
        self.storage = storage or Storage("data")
        self.planner, warnings = self.storage.load()
        self.today = date.today()
        self.year, self.month = self.today.year, self.today.month
        self.selected_day = self.today
        self.topic_ids = {}
        self.exam_ids = {}

        self._style()
        self._build()
        self.pack(fill="both", expand=True)
        self.refresh()
        if warnings:
            messagebox.showwarning("Данные", "\n".join(warnings))

    # --- layout --------------------------------------------------------
    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=("Helvetica", 12))
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG)
        style.configure("Muted.TLabel", foreground=MUTED, font=("Helvetica", 11))
        style.configure("H.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("TButton", padding=(10, 5))
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])
        style.configure("Treeview", rowheight=26, background=BG, fieldbackground=BG)
        style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))
        self.root.configure(bg=BG)

    def _build(self):
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(0, 16))
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)
        self._build_exams(left)
        self._build_topics(left)
        self._build_settings(left)
        self.status = ttk.Label(right, style="Muted.TLabel", wraplength=560, justify="left")
        self.status.pack(side="bottom", anchor="w", pady=(8, 0))
        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True)
        calendar_tab = ttk.Frame(tabs, padding=(0, 8))
        gantt_tab = ttk.Frame(tabs, padding=(0, 8))
        tabs.add(calendar_tab, text="Календарь нагрузки")
        tabs.add(gantt_tab, text="Диаграмма Ганта")
        self.gantt = GanttChart(gantt_tab)
        self.gantt.pack(fill="both", expand=True)
        self._build_calendar(calendar_tab)

    def _build_exams(self, parent):
        ttk.Label(parent, text="Экзамены", style="H.TLabel").pack(anchor="w")
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        self.exam_name = HintEntry(row, "Название экзамена", width=18)
        self.exam_name.pack(side="left")
        self.exam_date = HintEntry(row, "ДД.ММ.ГГГГ", width=11)
        self.exam_date.pack(side="left", padx=6)
        ttk.Button(row, text="Добавить", style="Accent.TButton",
                   command=self.add_exam).pack(side="left")
        self.exam_tree = ttk.Treeview(parent, columns=("date",), height=4, selectmode="browse")
        self.exam_tree.heading("#0", text="Экзамен")
        self.exam_tree.heading("date", text="Дата")
        self.exam_tree.column("#0", width=190)
        self.exam_tree.column("date", width=100, anchor="center")
        self.exam_tree.pack(fill="x", pady=4)
        ttk.Button(parent, text="Удалить экзамен", command=self.remove_exam).pack(anchor="e")

    def _build_topics(self, parent):
        ttk.Label(parent, text="Темы", style="H.TLabel").pack(anchor="w", pady=(14, 0))
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        self.topic_exam = ttk.Combobox(row, state="readonly", width=14)
        self.topic_exam.pack(side="left")
        self.topic_name = HintEntry(row, "Название темы", width=18)
        self.topic_name.pack(side="left", padx=6)
        row2 = ttk.Frame(parent)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Сложность (1-5):").pack(side="left")
        self.topic_diff = ttk.Spinbox(row2, from_=1, to=5, width=3)
        self.topic_diff.set(3)
        self.topic_diff.pack(side="left", padx=6)
        ttk.Button(row2, text="Добавить тему", style="Accent.TButton",
                   command=self.add_topic).pack(side="right")
        self.topic_tree = ttk.Treeview(parent, columns=("exam", "diff", "status"), height=7,
                                       selectmode="browse")
        for col, text, width in (("#0", "Тема", 120), ("exam", "Экзамен", 90),
                                 ("diff", "Сл.", 40), ("status", "Статус", 70)):
            self.topic_tree.heading(col, text=text)
            self.topic_tree.column(col, width=width, anchor="w" if col in ("#0", "exam") else "center")
        self.topic_tree.pack(fill="x", pady=4)
        buttons = ttk.Frame(parent)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Готово", command=lambda: self.mark(DONE)).pack(side="left")
        ttk.Button(buttons, text="Не сделано", command=lambda: self.mark(TODO)).pack(side="left", padx=6)
        ttk.Button(buttons, text="Удалить", command=self.remove_topic).pack(side="right")

    def _build_settings(self, parent):
        ttk.Label(parent, text="План", style="H.TLabel").pack(anchor="w", pady=(14, 0))
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Часов в день:").pack(side="left")
        self.limit = ttk.Spinbox(row, from_=1, to=16, width=3, command=self.set_limit)
        self.limit.pack(side="left", padx=6)
        self.limit.bind("<Return>", lambda _e: self.set_limit())
        self.limit.bind("<FocusOut>", lambda _e: self.set_limit())
        ttk.Button(row, text="Перепланировать", style="Accent.TButton",
                   command=self.replan).pack(side="right")

    def _build_calendar(self, parent):
        head = ttk.Frame(parent)
        head.pack(fill="x")
        ttk.Button(head, text="◀", width=3, command=lambda: self.change_month(-1)).pack(side="left")
        self.month_label = ttk.Label(head, style="H.TLabel", anchor="center")
        self.month_label.pack(side="left", expand=True, fill="x")
        ttk.Button(head, text="▶", width=3, command=lambda: self.change_month(1)).pack(side="left")

        self.grid_frame = tk.Frame(parent, bg=BG)
        self.grid_frame.pack(fill="both", expand=True, pady=8)
        for col in range(7):
            self.grid_frame.columnconfigure(col, weight=1, uniform="day")

        legend = ttk.Frame(parent)
        legend.pack(fill="x")
        for color, text in (("#f1f5f9", "свободно"), ("#bbf7d0", "до 50%"),
                            ("#fde68a", "до 80%"), ("#fdba74", "лимит"), (EXAM_COLOR, "экзамен")):
            tk.Label(legend, bg=color, width=2, relief="flat").pack(side="left")
            ttk.Label(legend, text=text, style="Muted.TLabel").pack(side="left", padx=(4, 12))

        self.day_title = ttk.Label(parent, style="H.TLabel")
        self.day_title.pack(anchor="w", pady=(10, 2))
        self.day_list = tk.Listbox(parent, height=6, bd=0, highlightthickness=1,
                                   highlightbackground="#e2e8f0", font=("Helvetica", 12),
                                   activestyle="none")
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

    def _changed(self, replanned=False):
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
            self.planner.add_exam(self.exam_name.get(), parse_date(self.exam_date.get()), date.today())
            self.exam_name.delete(0, "end")
            self.exam_date.delete(0, "end")
        if self._run(go):
            self._changed()

    def remove_exam(self):
        name = self.exam_ids.get(self._selected(self.exam_tree))
        if name is None:
            return messagebox.showinfo("Экзамены", "Выберите экзамен в списке")
        if messagebox.askyesno("Удалить", f"Удалить экзамен «{name}» и его темы?"):
            if self._run(lambda: self.planner.remove_exam(name)):
                self._changed()

    def add_topic(self):
        def go():
            self.planner.add_topic(self.topic_exam.get(), self.topic_name.get(), self.topic_diff.get())
            self.topic_name.delete(0, "end")
        if self._run(go):
            self._changed()

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

    def replan(self):
        moved, at_risk = self.planner.replan(date.today())
        self.at_risk = at_risk
        self._changed(replanned=True)
        lines = []
        if moved:
            lines.append("Перенесено вперёд: " + ", ".join(t.name for t in moved))
        if at_risk:
            lines.append("Не помещаются до экзамена: " + ", ".join(t.name for t in at_risk))
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
        if not hasattr(self, "at_risk"):
            self.at_risk = self.planner.build_plan(self.today)
        exams = sorted(self.planner.exams.values(), key=lambda e: e.date)
        self.exam_tree.delete(*self.exam_tree.get_children())
        self.exam_ids = {}
        for exam in exams:
            iid = self.exam_tree.insert("", "end", text=exam.name,
                                        values=(exam.date.strftime("%d.%m.%Y"),))
            self.exam_ids[iid] = exam.name
        self.topic_exam["values"] = [e.name for e in exams]
        if exams and self.topic_exam.get() not in self.topic_exam["values"]:
            self.topic_exam.set(exams[0].name)
        if not exams:
            self.topic_exam.set("")
        self.topic_tree.delete(*self.topic_tree.get_children())
        self.topic_ids = {}
        for topic in self.planner.topics.values():
            iid = self.topic_tree.insert("", "end", text=topic.name, values=(
                topic.exam, topic.difficulty, STATUS_TEXT[topic.status]))
            self.topic_ids[iid] = topic.key
        self.limit.set(self.planner.daily_limit)
        self.draw_calendar()
        self.draw_day()
        self.gantt.draw(self.planner, self.at_risk, self.today)
        if self.at_risk:
            self.status.configure(foreground="#b91c1c", text="Не помещаются до экзамена: " + ", ".join(
                f"{t.name} ({t.exam})" for t in self.at_risk))
        else:
            self.status.configure(foreground=MUTED, text="Все темы помещаются в план." if self.planner.topics
                                  else "Добавьте экзамен и темы, план построится сам.")

    def draw_calendar(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.month_label.configure(text=f"{MONTHS[self.month - 1]} {self.year}")
        for col, name in enumerate(WEEKDAYS):
            ttk.Label(self.grid_frame, text=name, style="Muted.TLabel", anchor="center").grid(
                row=0, column=col, sticky="ew")
        exam_days = {e.date for e in self.planner.exams.values()}
        for row, week in enumerate(month_weeks(self.year, self.month), start=1):
            for col, number in enumerate(week):
                if not number:
                    continue
                day = date(self.year, self.month, number)
                hours = self.planner.day_load(day)
                color = EXAM_COLOR if day in exam_days else load_color(hours, self.planner.daily_limit)
                text = f"{number}\n{hours} ч" if hours else f"{number}\n "
                cell = tk.Label(self.grid_frame, text=text, bg=color, fg=TEXT, height=3,
                                font=("Helvetica", 12, "bold" if day == self.today else "normal"),
                                bd=2, relief="solid" if day == self.selected_day else "flat",
                                cursor="hand2", highlightthickness=0)
                cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
                cell.bind("<Button-1>", lambda _e, d=day: self.select_day(d))

    def draw_day(self):
        day = self.selected_day
        self.day_title.configure(text=f"{day.strftime('%d.%m.%Y')} · {self.planner.day_load(day)} ч")
        self.day_list.delete(0, "end")
        for exam in self.planner.exams.values():
            if exam.date == day:
                self.day_list.insert("end", f"ЭКЗАМЕН: {exam.name}")
        for exam, topic, hours in self.planner.plan.get(day, []):
            self.day_list.insert("end", f"{topic} — {exam}, {hours} ч")
        if not self.day_list.size():
            self.day_list.insert("end", "На этот день ничего не запланировано")
