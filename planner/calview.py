import calendar

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
          "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# (до какой доли от лимита часов, цвет клетки)
LOAD_COLORS = [(0, "#f1f5f9"), (0.5, "#bbf7d0"), (0.8, "#fde68a"), (1.0, "#fdba74")]
EXAM_COLOR = "#fca5a5"  # цвет дня экзамена
CONTROL_COLOR = "#c4b5fd"  # цвет дня контрольной


def month_weeks(year, month):
    # недели месяца по 7 чисел, 0 значит день не из этого месяца
    return calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)


def shift_month(year, month, delta):
    # двигает месяц вперёд или назад, год меняется сам
    # считаем месяцы подряд, потом делим на год и месяц
    index = year * 12 + (month - 1) + delta
    new_year = index // 12
    if not 1 <= new_year <= 9999:  # date умеет только года от 1 до 9999, дальше не листаем
        return year, month
    return new_year, index % 12 + 1


def load_color(hours, limit):
    # цвет клетки, от серого (пусто) до оранжевого (лимит часов)
    share = hours / limit if limit else 0
    for bound, color in LOAD_COLORS:
        if share <= bound:
            return color
    return LOAD_COLORS[-1][1]
