import tkinter as tk
from tkinter import ttk

from planner.catalog import topics_for
from ui import theme


class MultiTopicDialog(tk.Toplevel):
    """Pick several typical topics (and type your own) for one exam or control work."""

    def __init__(self, parent, event_name, taken):
        super().__init__(parent)
        self.title("Несколько тем")
        self.configure(bg=theme.CARD, padx=20, pady=16)
        self.resizable(False, False)
        self.result = []
        self.vars = []

        ttk.Label(self, text="Темы для", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(self, text=event_name, style="H.TLabel").pack(anchor="w", pady=(0, 8))

        options = topics_for(event_name, taken)
        if options:
            box = ttk.Frame(self)
            box.pack(fill="x")
            for index, name in enumerate(options):
                var = tk.BooleanVar(value=False)
                self.vars.append((name, var))
                tk.Checkbutton(box, text=name, variable=var, bg=theme.CARD, anchor="w",
                               activebackground=theme.CARD, font=theme.font(12),
                               highlightthickness=0).grid(row=index // 2, column=index % 2,
                                                          sticky="w", padx=(0, 18), pady=1)
        else:
            ttk.Label(self, text="Для этого названия нет готового списка — впишите темы ниже.",
                      style="Muted.TLabel").pack(anchor="w")

        ttk.Label(self, text="Свои темы через запятую", style="Muted.TLabel").pack(anchor="w", pady=(12, 2))
        self.extra = ttk.Entry(self, width=48)
        self.extra.pack(fill="x")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(16, 0))
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Добавить", style="Accent.TButton",
                   command=self.confirm).pack(side="right", padx=8)

        self.transient(parent)
        self.grab_set()
        self.extra.focus_set()

    def confirm(self):
        names = [name for name, var in self.vars if var.get()]
        names += [part.strip() for part in self.extra.get().split(",") if part.strip()]
        self.result = list(dict.fromkeys(names))  # no duplicates, order kept
        self.destroy()
