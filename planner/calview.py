import calendar

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
          "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# (upper bound of load as a share of the daily limit, colour)
LOAD_COLORS = [(0, "#f1f5f9"), (0.5, "#bbf7d0"), (0.8, "#fde68a"), (1.0, "#fdba74")]
EXAM_COLOR = "#fca5a5"
CONTROL_COLOR = "#c4b5fd"


def month_weeks(year, month):
    """Weeks of the month as lists of 7 day numbers (0 = outside the month)."""
    return calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)


def shift_month(year, month, delta):
    index = year * 12 + (month - 1) + delta
    new_year = index // 12
    if not 1 <= new_year <= 9999:  # datetime.date supports only these years
        return year, month
    return new_year, index % 12 + 1


def load_color(hours, limit):
    """Cell colour for a day: grey (free) to orange (at the daily limit)."""
    share = hours / limit if limit else 0
    for bound, color in LOAD_COLORS:
        if share <= bound:
            return color
    return LOAD_COLORS[-1][1]
