from datetime import date, timedelta

import pytest

from planner.errors import ValidationError
from planner.models import DONE, parse_date, parse_difficulty
from planner.scheduler import REVISION, Planner
from planner.storage import Storage

TODAY = date(2026, 10, 1)


def make_planner():
    p = Planner(daily_limit=4)
    p.add_exam("Math", TODAY + timedelta(days=10), today=TODAY)
    p.add_exam("Physics", TODAY + timedelta(days=14), today=TODAY)
    for name, d in [("Limits", 5), ("Series", 3), ("Matrices", 2)]:
        p.add_topic("Math", name, d)
    for name, d in [("Optics", 4), ("Waves", 2), ("Heat", 1)]:
        p.add_topic("Physics", name, d)
    return p


# --- проверка ввода -----------------------------------------------------------
@pytest.mark.parametrize("text", ["", "abc", "32.01.2026", "2026/01/01"])
def test_bad_dates_rejected(text):
    with pytest.raises(ValidationError):
        parse_date(text)


def test_both_date_formats():
    assert parse_date("05.11.2026") == parse_date("2026-11-05") == date(2026, 11, 5)


@pytest.mark.parametrize("value", ["0", "6", "x", "", "-1", "2.5"])
def test_bad_difficulty_rejected(value):
    with pytest.raises(ValidationError):
        parse_difficulty(value)


def test_exam_validation():
    p = Planner()
    with pytest.raises(ValidationError):
        p.add_exam("  ", TODAY + timedelta(days=3), today=TODAY)
    with pytest.raises(ValidationError):
        p.add_exam("Old", TODAY - timedelta(days=1), today=TODAY)
    p.add_exam("A", TODAY + timedelta(days=3), today=TODAY)
    with pytest.raises(ValidationError):
        p.add_exam("A", TODAY + timedelta(days=4), today=TODAY)


def test_topic_needs_exam_and_is_unique():
    p = make_planner()
    with pytest.raises(ValidationError):
        p.add_topic("Chemistry", "x", 3)
    with pytest.raises(ValidationError):
        p.add_topic("Math", "Limits", 3)


def test_bad_daily_limit():
    for value in ("0", "17", "abc", None):
        with pytest.raises(ValidationError):
            Planner().set_daily_limit(value)


def test_remove_exam_removes_topics():
    p = make_planner()
    p.remove_exam("Math")
    assert all(t.exam != "Math" for t in p.topics.values())


# --- построение плана -------------------------------------------------------------
def test_daily_limit_never_exceeded():
    p = make_planner()
    p.build_plan(TODAY)
    assert p.plan
    assert all(p.day_load(day) <= p.daily_limit for day in p.plan)


def test_all_topics_scheduled_before_exam():
    p = make_planner()
    assert p.build_plan(TODAY) == []
    for exam in p.exams.values():
        hours = {}
        for day, items in p.plan.items():
            for e, topic, h in items:
                if e == exam.name and topic != REVISION:
                    assert day < exam.date - timedelta(days=1)
                    hours[topic] = hours.get(topic, 0) + h
        expected = {t.name: t.hours for t in p.topics.values() if t.exam == exam.name}
        assert hours == expected


def test_day_before_exam_is_revision_only():
    p = make_planner()
    p.build_plan(TODAY)
    for exam in p.exams.values():
        eve = p.plan[exam.date - timedelta(days=1)]
        assert any(topic == REVISION and e == exam.name for e, topic, _ in eve)
        assert all(e != exam.name or topic == REVISION for e, topic, _ in eve)


def test_nothing_on_or_after_exam_day():
    p = make_planner()
    p.build_plan(TODAY)
    last = max(e.date for e in p.exams.values())
    assert all(day < last for day in p.plan)


def test_hardest_topic_first():
    p = make_planner()
    p.build_plan(TODAY)
    first_day = p.plan[TODAY]
    assert first_day[0][:2] == ("Math", "Limits")


def test_not_enough_days_reports_risk():
    p = Planner(daily_limit=2)
    p.add_exam("E", TODAY + timedelta(days=3), today=TODAY)
    p.add_topic("E", "Big", 5)
    risk = p.build_plan(TODAY)
    assert [t.name for t in risk] == ["Big"]
    assert all(p.day_load(day) <= 2 for day in p.plan)


def test_exam_tomorrow_only_revision():
    p = Planner()
    p.add_exam("E", TODAY + timedelta(days=1), today=TODAY)
    p.add_topic("E", "T", 2)
    risk = p.build_plan(TODAY)
    assert [t.name for t in risk] == ["T"]
    assert list(p.plan) == [TODAY]


def test_done_topics_not_planned():
    p = make_planner()
    for t in list(p.topics.values()):
        p.set_status(t.exam, t.name, DONE)
    p.build_plan(TODAY)
    assert all(topic == REVISION for items in p.plan.values() for _, topic, _ in items)


def test_empty_planner():
    p = Planner()
    assert p.build_plan(TODAY) == []
    assert p.plan == {}


# --- пересчёт плана ---------------------------------------------------------------
def test_replan_moves_missed_topic_forward():
    p = make_planner()
    p.build_plan(TODAY)
    later = TODAY + timedelta(days=2)
    moved, risk = p.replan(later)
    names = {t.name for t in moved}
    assert "Limits" in names
    assert risk == []
    assert all(day >= later for day in p.plan)
    assert any(topic == "Limits" for items in p.plan.values() for _, topic, _ in items)


def test_replan_ignores_done_topics():
    p = make_planner()
    p.build_plan(TODAY)
    p.set_status("Math", "Limits", DONE)
    moved, _ = p.replan(TODAY + timedelta(days=2))
    assert "Limits" not in {t.name for t in moved}


def test_replan_warns_when_late():
    p = Planner(daily_limit=4)
    p.add_exam("E", TODAY + timedelta(days=5), today=TODAY)
    p.add_topic("E", "A", 5)
    p.add_topic("E", "B", 5)
    assert p.build_plan(TODAY) == []
    _, risk = p.replan(TODAY + timedelta(days=3))
    assert {t.name for t in risk} == {"A", "B"}


# --- хранение данных --------------------------------------------------------------
def test_csv_roundtrip(tmp_path):
    p = make_planner()
    p.set_status("Math", "Series", DONE)
    p.set_daily_limit(6)
    Storage(tmp_path).save(p)
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert warnings == []
    assert loaded.daily_limit == 6
    assert set(loaded.exams) == {"Math", "Physics"}
    assert loaded.topics[("Math", "Series")].status == DONE
    assert loaded.plan


def test_missing_files_give_empty_planner(tmp_path):
    loaded, warnings = Storage(tmp_path / "nope").load(TODAY)
    assert loaded.exams == {} and warnings == []


@pytest.mark.parametrize("content", [
    "garbage without header\n1,2,3\n",
    "name,date\nMath,not-a-date\n",
    "name,date\n,2030-01-01\n",
])
def test_corrupt_exams_file(tmp_path, content):
    (tmp_path / "exams.csv").write_text(content, encoding="utf-8")
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert loaded.exams == {} and len(warnings) == 1


def test_corrupt_topics_file(tmp_path):
    (tmp_path / "exams.csv").write_text("name,date\nMath,2030-01-01\n", encoding="utf-8")
    (tmp_path / "topics.csv").write_text("exam,name,difficulty,status\nMath,T,9,todo\n", encoding="utf-8")
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert loaded.exams == {} and len(warnings) == 1


def test_binary_file_does_not_crash(tmp_path):
    (tmp_path / "exams.csv").write_bytes(b"\xff\xfe\x00\x01")
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert loaded.exams == {} and len(warnings) == 1


# --- исправления по замечаниям ревью -----------------------------------------------------------
def test_close_exams_keep_revision_day_clean():
    p = Planner(daily_limit=4)
    p.add_exam("B", TODAY + timedelta(days=5), today=TODAY)
    p.add_exam("A", TODAY + timedelta(days=9), today=TODAY)
    for name in ("a1", "a2", "a3"):
        p.add_topic("A", name, 5)
    p.add_topic("B", "b1", 2)
    p.build_plan(TODAY)
    for exam in p.exams.values():
        eve = p.plan[exam.date - timedelta(days=1)]
        assert all(topic == REVISION for _, topic, _ in eve)
        assert exam.date not in p.plan


def test_none_name_rejected():
    from planner.models import Topic
    with pytest.raises(ValidationError):
        Topic("E", None, 3)


def test_replan_after_restart(tmp_path):
    p = make_planner()
    p.build_plan(TODAY)
    Storage(tmp_path).save(p)
    loaded, _ = Storage(tmp_path).load(TODAY)
    moved, risk = loaded.replan(TODAY + timedelta(days=3))
    assert "Limits" in {t.name for t in moved}
    assert risk == []


def test_corrupt_files_are_backed_up(tmp_path):
    (tmp_path / "exams.csv").write_text("name,date\nMath,oops\n", encoding="utf-8")
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert loaded.exams == {}
    assert (tmp_path / "exams.csv.bak").exists() and not (tmp_path / "exams.csv").exists()
    assert ".bak" in warnings[0]


def test_bom_and_duplicates_and_missing_cells(tmp_path):
    (tmp_path / "exams.csv").write_text("﻿name,date\nMath,2030-01-01\n", encoding="utf-8")
    loaded, warnings = Storage(tmp_path).load(TODAY)
    assert "Math" in loaded.exams and warnings == []
    (tmp_path / "topics.csv").write_text(
        "exam,name,difficulty,status,planned_day\nMath,T,2,todo,\nMath,T,3,todo,\n", encoding="utf-8")
    assert len(Storage(tmp_path).load(TODAY)[1]) == 1
    (tmp_path / "exams.csv").write_text("name,date\nMath\n", encoding="utf-8")
    assert len(Storage(tmp_path).load(TODAY)[1]) == 1


def test_month_shift_is_clamped():
    from planner.calview import shift_month
    assert shift_month(9999, 12, 1) == (9999, 12)
    assert shift_month(1, 1, -1) == (1, 1)


# --- короткий ввод даты ---------------------------------------------------
def test_short_date_day_only():
    from planner.models import parse_date
    today = date(2026, 10, 17)
    assert parse_date("25", today) == date(2026, 10, 25)   # число ещё впереди в этом месяце
    assert parse_date("5", today) == date(2026, 11, 5)     # число уже прошло: следующий месяц
    assert parse_date("17", today) == date(2026, 11, 17)   # сегодня не подходит, нужна будущая дата


def test_short_date_skips_months_without_that_day():
    from planner.models import parse_date
    assert parse_date("31", date(2026, 4, 10)) == date(2026, 5, 31)   # в апреле 30 дней
    assert parse_date("30", date(2026, 1, 31)) == date(2026, 3, 30)   # в феврале нет 30-го


def test_short_date_day_and_month():
    from planner.models import parse_date
    today = date(2026, 10, 17)
    assert parse_date("25.11", today) == date(2026, 11, 25)
    assert parse_date("5.3", today) == date(2027, 3, 5)               # в этом году март уже был
    assert parse_date("29.02", today) == date(2028, 2, 29)            # ближайший високосный год


@pytest.mark.parametrize("text", ["0", "32", "31.02", "15.13", "1.2.3.4", "25,11"])
def test_short_date_bad_values(text):
    from planner.models import parse_date
    with pytest.raises(ValidationError):
        parse_date(text, date(2026, 10, 17))


def test_full_date_unchanged_by_short_rules():
    from planner.models import parse_date
    assert parse_date("05.11.2026", date(2026, 10, 17)) == date(2026, 11, 5)
    assert parse_date("2026-11-05") == date(2026, 11, 5)
