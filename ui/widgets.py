from tkinter import ttk

HINT_COLOR = "#94a3b8"
TEXT_COLOR = "#0f172a"
# клавиши, которые при показанной подсказке ничего не делают (иначе они съели бы текст подсказки)
EDIT_KEYS = {"BackSpace", "Delete", "Left", "Right", "Home", "End", "Up", "Down"}


class _HintMixin:
    """Серая подсказка внутри пустого поля.

    Подсказка видна, пока в поле ничего нет, даже когда оно выбрано: курсор стоит в самом её начале,
    а первая же введённая буква заменяет подсказку. Пока подсказка показана, get() возвращает "",
    поэтому остальной код никогда не видит её текст.
    """

    def _init_hint(self, hint):
        self.hint = hint
        self._showing = False
        self.bind("<FocusIn>", lambda _e: self._to_start())
        self.bind("<FocusOut>", lambda _e: self._show())
        self.bind("<ButtonRelease-1>", lambda _e: self._to_start(), add="+")
        self.bind("<Key>", self._on_key)
        self.bind("<<Paste>>", lambda _e: self._hide(), add="+")
        self._show()

    def _to_start(self):
        """Пока показана подсказка, курсор всегда в начале поля и ничего не выделено."""
        if self._showing:
            self.selection_clear()
            self.icursor(0)
            self.after_idle(lambda: self.icursor(0) if self._showing else None)

    def _on_key(self, event):
        if not self._showing:
            return None
        if event.keysym in EDIT_KEYS:
            return "break"  # подсказку нельзя стирать и двигать по ней курсор
        typing = event.char and event.char.isprintable() and not event.state & 0x0C  # без Ctrl и Command
        if typing:
            self._hide()  # убираем подсказку, а сама буква вставится стандартной обработкой
        return None

    def _show(self):
        if not self._showing and not super().get():
            super().insert(0, self.hint)
            self.configure(foreground=HINT_COLOR)
            self._showing = True
            self._to_start()

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
        self._show()  # поле опустело: снова подсказка (и при выбранном поле тоже)

    def insert(self, index, text):
        self._hide()
        super().insert(index, text)


class HintEntry(_HintMixin, ttk.Entry):
    def __init__(self, parent, hint, **options):
        super().__init__(parent, **options)
        self._init_hint(hint)


class HintCombobox(_HintMixin, ttk.Combobox):
    """Выпадающий список с подсказкой: можно выбрать готовое значение или ввести своё."""

    def __init__(self, parent, hint, **options):
        super().__init__(parent, **options)
        self._init_hint(hint)
        self.bind("<<ComboboxSelected>>", lambda _e: self._picked(), add="+")

    def _picked(self):
        # список записал значение в поле: теперь это настоящий текст, а не подсказка
        if self._showing:
            self._showing = False
        self.configure(foreground=TEXT_COLOR)
        self.selection_clear()

    def set(self, value):
        self._showing = False
        self.configure(foreground=TEXT_COLOR)
        super().set(value)
