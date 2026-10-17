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


def test_gantt_rows():
    from datetime import date, timedelta
    from planner.ganttview import DONE_ROW, REVISION_BAR, RISK_ROW, TODO_BAR, gantt_rows
    from planner.scheduler import Planner
    today = date(2026, 10, 1)
    p = Planner(daily_limit=2)
    p.add_exam("E", today + timedelta(days=6), today)
    p.add_topic("E", "Big", 5)
    p.add_topic("E", "Small", 1)
    p.add_topic("E", "Huge", 5)
    p.add_topic("E", "Finished", 1)
    p.set_status("E", "Finished", "done")
    risk = p.build_plan(today)
    rows = gantt_rows(p, risk)
    kinds = {r["name"]: r["kind"] for r in rows}
    assert kinds["Повторение"] == REVISION_BAR
    assert kinds["Finished"] == DONE_ROW
    assert kinds["Big"] == TODO_BAR
    assert RISK_ROW in kinds.values()
    big = next(r for r in rows if r["name"] == "Big")
    assert big["start"] == today and big["end"] <= today + timedelta(days=4)
    assert rows[-1]["start"] is None  # rows without bars go last within the exam


def test_gantt_empty():
    from planner.ganttview import gantt_rows
    from planner.scheduler import Planner
    assert gantt_rows(Planner()) == []
