from planner.calview import load_color, month_weeks, shift_month


def test_month_weeks_shape():
    weeks = month_weeks(2026, 10)
    assert all(len(w) == 7 for w in weeks)
    days = [d for w in weeks for d in w if d]
    assert days == list(range(1, 32))
    assert weeks[0][3] == 1  # 1 Oct 2026 is a Thursday


def test_shift_month_wraps_year():
    assert shift_month(2026, 12, 1) == (2027, 1)
    assert shift_month(2026, 1, -1) == (2025, 12)
    assert shift_month(2026, 5, 0) == (2026, 5)


def test_load_color_grows_with_load():
    colors = [load_color(h, 4) for h in (0, 1, 3, 4)]
    assert len(set(colors)) == 4
    assert load_color(0, 0) == load_color(0, 4)
