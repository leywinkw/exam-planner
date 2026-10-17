import math
import tkinter as tk
from datetime import timedelta
from tkinter import ttk

from planner.models import CONTROL
from planner.ganttview import DONE_ROW, REVISION_BAR, RISK_ROW, TODO_BAR, gantt_rows

LABEL_W = 300
ROW_H = 30
HEAD_H = 68
BAR_COLORS = {TODO_BAR: "#818cf8", REVISION_BAR: "#c4b5fd"}
EXAM_LINE = "#ef4444"
CONTROL_LINE = "#8b5cf6"
TODAY_LINE = "#4f46e5"
WEEKEND = "#f1f5f9"
GRID = "#e2e8f0"
TEXT = "#0f172a"
MUTED = "#94a3b8"
RISK = "#b91c1c"


class GanttChart(ttk.Frame):
    """Диаграмма Ганта на tk.Canvas: строка на каждую тему, по горизонтали дни."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        xbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        ybar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
        xbar.pack(side="bottom", fill="x")
        ybar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.data = None
        self.canvas.bind("<Configure>", lambda _e: self.redraw())

    def draw(self, planner, at_risk, today):
        self.data = (planner, at_risk, today)
        self.redraw()

    def redraw(self):
        """Рисует диаграмму заново: сетка дней, полоски тем, линии событий и линия «сегодня»."""
        canvas = self.canvas
        canvas.delete("all")
        if self.data is None:
            return
        planner, at_risk, today = self.data
        rows = gantt_rows(planner, at_risk)
        exams = sorted(planner.exams.values(), key=lambda e: e.date)
        if not rows or not exams:
            canvas.create_text(20, 30, anchor="w", fill=MUTED, font=("Helvetica", 12),
                               text="Добавьте экзамены и темы — здесь появится диаграмма Ганта.")
            canvas.configure(scrollregion=(0, 0, 1, 1))
            return

        first, last = today, exams[-1].date
        days = (last - first).days + 1
        width = max(canvas.winfo_width(), 400)
        day_w = max(16, (width - LABEL_W - 30) / days)
        step = max(1, math.ceil(46 / day_w))  # подпись даты не на каждый день, чтобы подписи не налезали друг на друга

        def x_of(day):
            # x-координата начала дня на оси времени
            return LABEL_W + (day - first).days * day_w

        height = HEAD_H + len(rows) * ROW_H + 10
        for i in range(days):
            day = first + timedelta(days=i)
            x = x_of(day)
            if day.weekday() >= 5:
                canvas.create_rectangle(x, HEAD_H, x + day_w, height, fill=WEEKEND, outline="")
            canvas.create_line(x, HEAD_H - 6, x, height, fill=GRID)
            if i % step == 0:
                canvas.create_text(x + 2, HEAD_H - 11, anchor="w", fill=MUTED,
                                   font=("Helvetica", 10), text=day.strftime("%d.%m"))

        for index, row in enumerate(rows):
            top = HEAD_H + index * ROW_H
            canvas.create_line(0, top, LABEL_W + days * day_w, top, fill=GRID)
            kind = row["kind"]
            color = RISK if kind == RISK_ROW else (MUTED if kind == DONE_ROW else TEXT)
            label = f'{row["name"]} · {row["exam"]}'
            label = label.replace("Контрольная · ", "КР · ")
            if len(label) > 30:
                label = label[:29] + "…"
            canvas.create_text(8, top + ROW_H / 2, anchor="w", fill=color,
                               font=("Helvetica", 11), text=label)
            if row["start"] is not None:
                x1, x2 = x_of(row["start"]) + 2, x_of(row["end"]) + day_w - 2
                canvas.create_rectangle(x1, top + 5, x2, top + ROW_H - 5,
                                        fill=BAR_COLORS[kind], outline="")
            else:
                note = "не помещается до экзамена" if kind == RISK_ROW else "готово"
                canvas.create_text(x_of(first) + 6, top + ROW_H / 2, anchor="w", fill=color,
                                   font=("Helvetica", 10, "italic"), text=note)

        for index, exam in enumerate(exams):
            x = x_of(exam.date) + day_w / 2
            line = CONTROL_LINE if exam.kind == CONTROL else EXAM_LINE
            canvas.create_line(x, 16, x, height, fill=line, width=2)
            # подписи событий в два яруса, чтобы названия соседних событий не накладывались
            canvas.create_text(x - 4, 16 + (index % 2) * 14, anchor="ne", fill=line,
                               font=("Helvetica", 10, "bold"),
                               text=exam.name.replace("Контрольная · ", "КР · "))
        x = x_of(today) + day_w / 2
        canvas.create_line(x, HEAD_H - 4, x, height, fill=TODAY_LINE, width=2, dash=(4, 3))
        canvas.create_text(x + 4, 1, anchor="nw", fill=TODAY_LINE,
                           font=("Helvetica", 10, "bold"), text="сегодня")
        canvas.create_line(LABEL_W, 0, LABEL_W, height, fill=GRID)
        canvas.configure(scrollregion=(0, 0, LABEL_W + days * day_w + 20, height))
