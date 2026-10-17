from datetime import date, datetime

from planner.errors import ValidationError

DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")
MIN_DIFFICULTY, MAX_DIFFICULTY = 1, 5

TODO, DONE = "todo", "done"


def parse_date(text):
    """Accept DD.MM.YYYY or YYYY-MM-DD, raise ValidationError otherwise."""
    text = str(text).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ")


def parse_difficulty(value):
    try:
        number = int(str(value).strip())
    except ValueError:
        raise ValidationError("Сложность должна быть целым числом от 1 до 5") from None
    if not MIN_DIFFICULTY <= number <= MAX_DIFFICULTY:
        raise ValidationError("Сложность должна быть от 1 до 5")
    return number


def clean_name(value, what):
    name = "" if value is None else str(value).strip()
    if not name:
        raise ValidationError(f"Укажите {what}")
    return name


class Exam:
    def __init__(self, name, exam_date):
        self.name = clean_name(name, "название экзамена")
        if not isinstance(exam_date, date):
            raise ValidationError("Некорректная дата экзамена")
        self.date = exam_date

    def __repr__(self):
        return f"Exam({self.name!r}, {self.date.isoformat()})"


class Topic:
    """A study topic; hours needed equal its difficulty."""

    def __init__(self, exam, name, difficulty, status=TODO, planned_day=None):
        self.exam = clean_name(exam, "экзамен")
        self.name = clean_name(name, "название темы")
        self.difficulty = parse_difficulty(difficulty)
        if status not in (TODO, DONE):
            raise ValidationError("Некорректный статус темы")
        self.status = status
        self.planned_day = planned_day  # first day it was planned; used to detect missed topics

    @property
    def hours(self):
        return self.difficulty

    @property
    def key(self):
        return (self.exam, self.name)

    def __repr__(self):
        return f"Topic({self.exam!r}, {self.name!r}, {self.difficulty}, {self.status})"
