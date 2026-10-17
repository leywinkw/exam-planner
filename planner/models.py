from datetime import date, datetime

from planner.errors import ValidationError

DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")  # допустимые форматы даты при вводе
MIN_DIFFICULTY, MAX_DIFFICULTY = 1, 5  # сложность темы: от 1 до 5

TODO, DONE = "todo", "done"  # статус темы: в плане / выполнена
EXAM, CONTROL = "exam", "control"  # тип события
# у контрольной название получает этот префикс, чтобы не совпасть с экзаменом по тому же предмету
CONTROL_PREFIX = "Контрольная · "


def parse_date(text):
    """Принимает дату ДД.ММ.ГГГГ или ГГГГ-ММ-ДД, иначе выбрасывает ValidationError."""
    text = str(text).strip()
    # пробуем форматы по очереди: strptime выбрасывает ValueError, если строка не подходит
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ")


def parse_difficulty(value):
    """Превращает ввод в число от 1 до 5; не число или выход за границы дают ValidationError."""
    try:
        number = int(str(value).strip())
    except ValueError:
        # from None прячет технический ValueError: пользователю нужен только понятный текст
        raise ValidationError("Сложность должна быть целым числом от 1 до 5") from None
    if not MIN_DIFFICULTY <= number <= MAX_DIFFICULTY:
        raise ValidationError("Сложность должна быть от 1 до 5")
    return number


def clean_name(value, what):
    """Убирает пробелы по краям; пустое название (и None) недопустимо."""
    name = "" if value is None else str(value).strip()
    if not name:
        raise ValidationError(f"Укажите {what}")
    return name


class Exam:
    """Экзамен или контрольная (поле kind): у обоих есть дата и свои темы."""

    def __init__(self, name, exam_date, kind=EXAM):
        # данные проверяются прямо при создании: некорректный Exam создать нельзя
        self.name = clean_name(name, "название экзамена")
        if kind not in (EXAM, CONTROL):
            raise ValidationError("Некорректный тип события")
        self.kind = kind
        if not isinstance(exam_date, date):
            raise ValidationError("Некорректная дата экзамена")
        self.date = exam_date

    def __repr__(self):
        return f"Exam({self.name!r}, {self.date.isoformat()}, {self.kind})"


class Topic:
    """Тема для изучения; часов на неё нужно столько же, какова сложность."""

    def __init__(self, exam, name, difficulty, status=TODO, planned_day=None):
        self.exam = clean_name(exam, "экзамен")
        self.name = clean_name(name, "название темы")
        self.difficulty = parse_difficulty(difficulty)
        if status not in (TODO, DONE):
            raise ValidationError("Некорректный статус темы")
        self.status = status
        self.planned_day = planned_day  # первый день, на который тему поставили в план; по нему находим пропущенные темы

    @property
    def hours(self):
        # сложность 1-5 одновременно означает 1-5 часов
        return self.difficulty

    @property
    def key(self):
        # ключ темы: пара (событие, название); по ней тема лежит в словаре Planner.topics
        return (self.exam, self.name)

    def __repr__(self):
        return f"Topic({self.exam!r}, {self.name!r}, {self.difficulty}, {self.status})"
