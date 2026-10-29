from tkinter import ttk

HINT_COLOR = "#94a3b8"
TEXT_COLOR = "#0f172a"
# клавиши, которые не работают пока показана подсказка, иначе они бы стирали её
EDIT_KEYS = {"BackSpace", "Delete", "Left", "Right", "Home", "End", "Up", "Down"}


class _HintMixin:
    # серая подсказка внутри пустого поля
    # пока она показана, get() возвращает пустую строку, остальной код её не видит
    # курсор стоит в начале, первая набранная буква заменяет подсказку

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
        # пока подсказка видна, курсор в начале и ничего не выделено
        if self._showing:
            self.selection_clear()
            self.icursor(0)
            self.after_idle(lambda: self.icursor(0) if self._showing else None)

    def _on_key(self, event):
        if not self._showing:
            return None
        if event.keysym in EDIT_KEYS:
            return "break"  # подсказку нельзя стереть и по ней нельзя двигать курсор
        typing = event.char and event.char.isprintable() and not event.state & 0x0C  # без Ctrl и Command
        if typing:
            self._hide()  # убираем подсказку, буква вставится сама
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
        self._show()  # поле пустое, снова показываем подсказку

    def insert(self, index, text):
        self._hide()
        super().insert(index, text)


class HintEntry(_HintMixin, ttk.Entry):
    def __init__(self, parent, hint, **options):
        super().__init__(parent, **options)
        self._init_hint(hint)


class HintCombobox(_HintMixin, ttk.Combobox):
    # список с подсказкой, можно выбрать значение или ввести своё

    def __init__(self, parent, hint, **options):
        super().__init__(parent, **options)
        self._init_hint(hint)
        self.bind("<<ComboboxSelected>>", lambda _e: self._picked(), add="+")

    def _picked(self):
        # список вставил значение, теперь это обычный текст
        if self._showing:
            self._showing = False
        self.configure(foreground=TEXT_COLOR)
        self.selection_clear()

    def set(self, value):
        self._showing = False
        self.configure(foreground=TEXT_COLOR)
        super().set(value)
