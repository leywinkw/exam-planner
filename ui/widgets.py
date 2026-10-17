from tkinter import ttk

HINT_COLOR = "#94a3b8"
TEXT_COLOR = "#0f172a"


class _HintMixin:
    """Shows a grey hint inside the field while it is empty.

    get() returns "" while the hint is shown, so callers never see the hint text.
    """

    def _init_hint(self, hint):
        self.hint = hint
        self._showing = False
        self.bind("<FocusIn>", lambda _e: self._hide())
        self.bind("<FocusOut>", lambda _e: self._show())
        self._show()

    def _show(self):
        if not self._showing and not super().get():
            super().insert(0, self.hint)
            self.configure(foreground=HINT_COLOR)
            self._showing = True

    def _hide(self):
        if self._showing:
            super().delete(0, "end")
            self.configure(foreground=TEXT_COLOR)
            self._showing = False

    def get(self):
        return "" if self._showing else super().get()

    def delete(self, first, last=None):
        self._hide()
        super().delete(first, last)
        if self.focus_get() is not self:
            self._show()

    def insert(self, index, text):
        self._hide()
        super().insert(index, text)


class HintEntry(_HintMixin, ttk.Entry):
    def __init__(self, parent, hint, **options):
        super().__init__(parent, **options)
        self._init_hint(hint)


class HintCombobox(_HintMixin, ttk.Combobox):
    """Editable dropdown: pick a ready value or type your own."""

    def __init__(self, parent, hint, **options):
        super().__init__(parent, **options)
        self._init_hint(hint)
        self.bind("<<ComboboxSelected>>", lambda _e: self._picked(), add="+")

    def _picked(self):
        # the dropdown wrote the value into the field: it is real text now
        if self._showing:
            self._showing = False
        self.configure(foreground=TEXT_COLOR)
        self.selection_clear()

    def set(self, value):
        self._showing = False
        self.configure(foreground=TEXT_COLOR)
        super().set(value)
