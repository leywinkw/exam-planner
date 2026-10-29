import re
from datetime import date, datetime

from planner.errors import ValidationError

DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")  # допустимые форматы даты при вводе
MIN_DIFFICULTY, MAX_DIFFICULTY = 1, 5  # сложность темы: от 1 до 5

TODO, DONE = "todo", "done"  # статус темы: в плане / выполнена
EXAM, CONTROL = "exam", "control"  # тип события
# у контрольной название получает этот префикс, чтобы не совпасть с экзаменом по тому же предмету
CONTROL_PREFIX = "Контрольная · "


def next_date(day, month=None, today=None):
    """Ближайшая будущая дата с таким числом (и месяцем, если он указан); None, если такой даты нет.

    Дата считается ближайшей, если она строго позже сегодняшней: «25» в день 25-го даст 25-е следующего месяца.
    """
    today = today or date.today()
    # перебираем месяцы (или годы, если месяц указан) вперёд, пока не найдём существующую дату в будущем
    for step in range(0, 96):
        if month is None:
            index = today.year * 12 + (today.month - 1) + step
            year, current = index // 12, index % 12 + 1
        else:
            year, current = today.year + step // 12, month
            if step % 12:
                continue  # для «день.месяц» шагаем по годам
        try:
            candidate = date(year, current, day)
        except ValueError:
            continue  # такого числа в этом месяце нет (31 апреля, 29 февраля), идём дальше
        if candidate > today:
            return candidate
    return None


def parse_date(text, today=None):
    """Принимает дату ДД.ММ.ГГГГ или ГГГГ-ММ-ДД; можно короче: «25» или «25.11» (берётся ближайшая будущая).

    Иначе выбрасывает ValidationError.
    """
    text = str(text).strip()
    # пробуем форматы по очереди: strptime выбрасывает ValueError, если строка не подходит
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    # короткий ввод: только число или число и месяц, без года
    short = re.fullmatch(r"(\d{1,2})(?:[./-](\d{1,2}))?", text)
    if short:
        day = int(short.group(1))
        month = int(short.group(2)) if short.group(2) else None
        found = next_date(day, month, today) if 1 <= day <= 31 and (month is None or 1 <= month <= 12) else None
        if found:
            return found
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
