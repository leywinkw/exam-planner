import calendar

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
          "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# (верхняя граница нагрузки как доля от дневного лимита, цвет клетки)
LOAD_COLORS = [(0, "#f1f5f9"), (0.5, "#bbf7d0"), (0.8, "#fde68a"), (1.0, "#fdba74")]
EXAM_COLOR = "#fca5a5"  # клетка дня экзамена
CONTROL_COLOR = "#c4b5fd"  # клетка дня контрольной


def month_weeks(year, month):
    """Недели месяца: списки по 7 чисел (0 - клетка вне месяца)."""
    return calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)


def shift_month(year, month, delta):
    """Сдвигает месяц на delta (можно отрицательное) с переходом через границу года."""
    # считаем месяцы подряд от нулевого года, потом разбираем обратно на год и месяц
    index = year * 12 + (month - 1) + delta
    new_year = index // 12
    if not 1 <= new_year <= 9999:  # datetime.date работает только с годами 1-9999, дальше не листаем
        return year, month
    return new_year, index % 12 + 1


def load_color(hours, limit):
    """Цвет клетки дня: от серого (свободно) до оранжевого (дошли до лимита часов)."""
    share = hours / limit if limit else 0
    for bound, color in LOAD_COLORS:
        if share <= bound:
            return color
    return LOAD_COLORS[-1][1]
