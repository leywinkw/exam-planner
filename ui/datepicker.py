import tkinter as tk
from datetime import date

from planner.calview import MONTHS, WEEKDAYS, month_weeks, shift_month
from ui import theme


class DatePicker(tk.Toplevel):
    # маленький календарь под полем даты, нажимаешь на число и оно вставляется в поле
    # выбрать можно только будущие дни
    # закрывается после выбора, по клику в другом месте или по Esc

    def __init__(self, entry, on_pick, start=None):
        super().__init__(entry)
        self.entry, self.on_pick = entry, on_pick
        start = start or date.today()
        self.year, self.month = start.year, start.month
        self.overrideredirect(True)  # окно без рамки
        self.configure(bg=theme.BORDER)
        self.attributes("-topmost", True)
        body = tk.Frame(self, bg=theme.CARD, padx=10, pady=8)
        body.pack(padx=1, pady=1)

        head = tk.Frame(body, bg=theme.CARD)
        head.pack(fill="x")
        self._arrow(head, "◀", -1).pack(side="left")
        self.title = tk.Label(head, bg=theme.CARD, fg=theme.TEXT, font=theme.font(13, "bold"), width=14)
        self.title.pack(side="left", expand=True)
        self._arrow(head, "▶", 1).pack(side="left")
        self.grid_frame = tk.Frame(body, bg=theme.CARD)
        self.grid_frame.pack(pady=(6, 0))
        self.draw()

        self.update_idletasks()
        self.geometry(f"+{entry.winfo_rootx()}+{entry.winfo_rooty() + entry.winfo_height() + 4}")
        self.lift()
        # клик в другом месте окна закрывает календарь
        self._outside_id = entry.winfo_toplevel().bind("<Button-1>", self._outside, add="+")

    def _arrow(self, parent, text, delta):
        label = tk.Label(parent, text=text, bg=theme.CARD, fg=theme.ACCENT, font=theme.font(13), cursor="hand2", padx=6)
        label.bind("<Button-1>", lambda _e: self.shift(delta))
        return label

    def shift(self, delta):
        self.year, self.month = shift_month(self.year, self.month, delta)
        self.draw()

    def draw(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.title.configure(text=f"{MONTHS[self.month - 1]} {self.year}")
        for col, name in enumerate(WEEKDAYS):
            tk.Label(self.grid_frame, text=name, bg=theme.CARD, fg=theme.MUTED, font=theme.font(11), width=3).grid(row=0, column=col)
        today = date.today()
        for row, week in enumerate(month_weeks(self.year, self.month), start=1):
            for col, number in enumerate(week):
                if not number:
                    continue
                self._day_cell(row, col, date(self.year, self.month, number), today)

    def _day_cell(self, row, col, day, today):
        future = day > today
        cell = tk.Label(self.grid_frame, text=str(day.day), width=3, pady=3, font=theme.font(12, "bold" if day == today else "normal"),
                        bg=theme.CARD, fg=theme.TEXT if future else "#cbd5e1")
        cell.grid(row=row, column=col, padx=1, pady=1)
        if future:  # прошедшие дни и сегодня выбрать нельзя
            cell.configure(cursor="hand2")
            cell.bind("<Enter>", lambda _e: cell.configure(bg=theme.ACCENT_SOFT))
            cell.bind("<Leave>", lambda _e: cell.configure(bg=theme.CARD))
            cell.bind("<Button-1>", lambda _e: self.pick(day))

    def pick(self, day):
        self.on_pick(day)
        self.close()

    def _outside(self, event):
        inside = str(event.widget).startswith(str(self)) or event.widget is self.entry
        if not inside:
            self.close()

    def close(self):
        if self.winfo_exists():
            try:
                self.entry.winfo_toplevel().unbind("<Button-1>", self._outside_id)
            except tk.TclError:
                pass
            self.destroy()
