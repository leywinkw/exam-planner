import re
from datetime import date, datetime

from planner.errors import ValidationError

DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")  # какие форматы даты можно вводить
MIN_DIFFICULTY, MAX_DIFFICULTY = 1, 5  # сложность от 1 до 5

TODO, DONE = "todo", "done"  # статус темы, в плане или выполнена
EXAM, CONTROL = "exam", "control"  # тип события, экзамен или контрольная
# префикс для контрольной, чтобы её название не совпало с экзаменом по тому же предмету
CONTROL_PREFIX = "Контрольная · "


def next_date(day, month=None, today=None):
    # ближайшая будущая дата с таким числом (и месяцем, если он есть), если такой даты нет, вернёт None
    # сегодняшняя дата не подходит, нужна строго позже
    today = today or date.today()
    # идём по месяцам (или по годам, если месяц задан), пока не найдём подходящую дату
    for step in range(0, 96):
        if month is None:
            index = today.year * 12 + (today.month - 1) + step
            year, current = index // 12, index % 12 + 1
        else:
            year, current = today.year + step // 12, month
            if step % 12:
                continue  # если задан месяц, шагаем по годам
        try:
            candidate = date(year, current, day)
        except ValueError:
            continue  # такой даты нет (31 апреля, 29 февраля), идём дальше
        if candidate > today:
            return candidate
    return None


def parse_date(text, today=None):
    # принимает ДД.ММ.ГГГГ или ГГГГ-ММ-ДД, можно коротко, «25» или «25.11», тогда берём ближайшую будущую дату
    # если не подошло, будет ValidationError
    text = str(text).strip()
    # пробуем форматы по очереди, strptime кидает ValueError, если не подходит
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    # короткий ввод, только число или число с месяцем
    short = re.fullmatch(r"(\d{1,2})(?:[./-](\d{1,2}))?", text)
    if short:
        day = int(short.group(1))
        month = int(short.group(2)) if short.group(2) else None
        found = next_date(day, month, today) if 1 <= day <= 31 and (month is None or 1 <= month <= 12) else None
        if found:
            return found
    raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ")


def parse_difficulty(value):
    # превращает ввод в число от 1 до 5, иначе ValidationError
    try:
        number = int(str(value).strip())
    except ValueError:
        # from None прячет лишнюю техническую ошибку, пользователю нужен только понятный текст
        raise ValidationError("Сложность должна быть целым числом от 1 до 5") from None
    if not MIN_DIFFICULTY <= number <= MAX_DIFFICULTY:
        raise ValidationError("Сложность должна быть от 1 до 5")
    return number


def clean_name(value, what):
    # убирает пробелы по краям, пустое название нельзя
    name = "" if value is None else str(value).strip()
    if not name:
        raise ValidationError(f"Укажите {what}")
    return name


class Exam:
    # экзамен или контрольная, у каждого своя дата и свои темы

    def __init__(self, name, exam_date, kind=EXAM):
        # данные проверяем сразу при создании
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
    # тема, часов на неё столько же, какова сложность

    def __init__(self, exam, name, difficulty, status=TODO, planned_day=None):
        self.exam = clean_name(exam, "экзамен")
        self.name = clean_name(name, "название темы")
        self.difficulty = parse_difficulty(difficulty)
        if status not in (TODO, DONE):
            raise ValidationError("Некорректный статус темы")
        self.status = status
        self.planned_day = planned_day  # первый день в плане, по нему находим пропущенные темы

    @property
    def hours(self):
        # сложность 1-5 это 1-5 часов
        return self.difficulty

    @property
    def key(self):
        # ключ темы, пара из события и названия, по нему тема лежит в словаре
        return (self.exam, self.name)

    def __repr__(self):
        return f"Topic({self.exam!r}, {self.name!r}, {self.difficulty}, {self.status})"
