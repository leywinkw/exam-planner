from datetime import date, timedelta

import pytest

from planner.errors import ValidationError
from planner.models import CONTROL, CONTROL_PREFIX
from planner.scheduler import REVISION, Planner
from planner.storage import Storage

TODAY = date(2026, 10, 1)


def study_days(planner, name=None):
    """Дни, на которые стоят занятия (без повторения), и часы по дням."""
    return {day: sum(h for _, t, h in items if t != REVISION and (name is None or t == name))
            for day, items in sorted(planner.plan.items())
            if any(t != REVISION and (name is None or t == name) for _, t, _ in items)}


def test_topic_is_spread_over_the_whole_period():
    p = Planner(daily_limit=6, max_chunk=2)
    p.add_exam("E", TODAY + timedelta(days=10), TODAY)
    p.add_topic("E", "Big", 5)
    assert p.build_plan(TODAY) == []
    days = study_days(p, "Big")
    assert sum(days.values()) == 5 and max(days.values()) <= 2
    assert len(days) >= 4  # не в одни и те же первые дни
    assert (max(days) - min(days)).days >= 6  # растянуто почти на весь срок до повторения


def test_few_hours_are_not_dumped_into_the_first_day():
    """Три часа за 10 дней до контрольной: по часу через несколько дней, а не 3 часа сразу."""
    p = Planner(daily_limit=4)
    c = p.add_exam("Физика", TODAY + timedelta(days=10), TODAY, kind=CONTROL)
    for name in ("a", "b", "c"):
        p.add_topic(c.name, name, 1)
    assert p.build_plan(TODAY) == []
    days = study_days(p)
    assert len(days) == 3 and all(h == 1 for h in days.values())
    assert (max(days) - min(days)).days >= 6
    assert min(days) <= TODAY + timedelta(days=2)  # и начинается без долгого ожидания


def test_hours_are_spread_evenly_one_per_day():
    p = Planner(daily_limit=4, max_chunk=2)
    p.add_exam("E", TODAY + timedelta(days=10), TODAY)  # учебные дни: сегодня ... +8, всего 9
    for name in ("a", "b", "c"):
        p.add_topic("E", name, 3)
    assert p.build_plan(TODAY) == []
    days = study_days(p)
    assert len(days) == 9 and set(days.values()) == {1}  # 9 часов на 9 дней: ровно по часу


def test_max_chunk_one_hour():
    p = Planner(daily_limit=4, max_chunk=1)
    p.add_exam("E", TODAY + timedelta(days=10), TODAY)
    p.add_topic("E", "T", 3)
    p.build_plan(TODAY)
    days = study_days(p, "T")
    assert len(days) == 3 and set(days.values()) == {1}


def test_leftover_hours_fill_free_days():
    """Если из-за лимита на тему часть часов не встала, они уходят в свободные дни, а не в «не успеваем»."""
    p = Planner(daily_limit=4, max_chunk=2)
    p.add_exam("E", TODAY + timedelta(days=5), TODAY)
    p.add_topic("E", "A", 5)
    p.add_topic("E", "B", 5)
    assert p.build_plan(TODAY) == []
    assert all(p.day_load(day) <= 4 for day in p.plan)


def test_chunk_never_exceeds_limits():
    p = Planner(daily_limit=3, max_chunk=2)
    p.add_exam("E", TODAY + timedelta(days=12), TODAY)
    for name, d in (("a", 5), ("b", 4), ("c", 3)):
        p.add_topic("E", name, d)
    p.build_plan(TODAY)
    for day, items in p.plan.items():
        assert p.day_load(day) <= 3
        assert all(h <= 2 for _, t, h in items if t != REVISION)


@pytest.mark.parametrize("value", ["0", "9", "x", None])
def test_bad_max_chunk(value):
    with pytest.raises(ValidationError):
        Planner().set_max_chunk(value)


def test_control_work_with_several_topics():
    p = Planner()
    control = p.add_exam("Математика", TODAY + timedelta(days=4), TODAY, kind=CONTROL)
    assert control.name == CONTROL_PREFIX + "Математика" and control.kind == CONTROL
    exam = p.add_exam("Математика", TODAY + timedelta(days=12), TODAY)
    assert exam.name == "Математика"
    for name in ("Пределы", "Производные", "Интегралы"):
        p.add_topic(control.name, name, "авто")
    assert p.build_plan(TODAY)  # 15 h do not fit into 3 study days: some topics are at risk
    eve = p.plan[TODAY + timedelta(days=3)]
    assert eve == [(control.name, REVISION, 1)]  # control revision is 1 hour
    assert all(day < control.date for day, items in p.plan.items()
               if any(e == control.name for e, _, _ in items))


def test_control_uses_its_own_deadline_over_topics_of_exam():
    p = Planner(daily_limit=4)
    c = p.add_exam("Физика", TODAY + timedelta(days=3), TODAY, kind=CONTROL)
    p.add_topic(c.name, "Кинематика", 4)
    risk = p.build_plan(TODAY)  # only 2 study days (today, +1) before revision day
    assert risk == []
    assert max(day for day, items in p.plan.items()
               if any(t == "Кинематика" for _, t, _ in items)) <= TODAY + timedelta(days=1)


def test_csv_keeps_kind_and_chunk(tmp_path):
    p = Planner(max_chunk=1)
    c = p.add_exam("Химия", TODAY + timedelta(days=5), TODAY, kind=CONTROL)
    p.add_topic(c.name, "Растворы", 2)
    Storage(tmp_path).save(p)
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert warnings == [] and loaded.max_chunk == 1
    assert loaded.exams[c.name].kind == CONTROL


def test_old_exams_file_without_kind_loads(tmp_path):
    (tmp_path / "exams.csv").write_text("name,date\nMath,2030-01-01\n", encoding="utf-8")
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert warnings == [] and loaded.exams["Math"].kind == "exam"
