import pytest

from planner.errors import ValidationError
from planner.estimator import DEFAULT_DIFFICULTY, estimate_difficulty
from planner.scheduler import Planner
from datetime import date, timedelta

TODAY = date(2026, 10, 1)


def test_subject_base_and_default():
    assert estimate_difficulty("Математика", "Лимиты") == 4
    assert estimate_difficulty("Физкультура", "Бег") == 1
    assert estimate_difficulty("Неизвестный предмет", "Что-то") == DEFAULT_DIFFICULTY


def test_topic_words_shift_difficulty():
    assert estimate_difficulty("Математика", "Введение в анализ") == 2
    assert estimate_difficulty("Математика", "Теоремы и доказательства") == 5  # clamped to 5
    assert estimate_difficulty("Литература", "Обзор эпохи") == 1


def test_case_and_empty_are_safe():
    assert estimate_difficulty("ФИЗИКА", "ОПТИКА") == 4
    assert 1 <= estimate_difficulty("", "") <= 5


@pytest.mark.parametrize("exam,topic", [("Математика", "Теорема доказательство интеграл"),
                                         ("Физкультура", "Введение основы обзор")])
def test_always_in_range(exam, topic):
    assert 1 <= estimate_difficulty(exam, topic) <= 5


def make():
    p = Planner()
    p.add_exam("Математика", TODAY + timedelta(days=10), TODAY)
    return p


@pytest.mark.parametrize("value", ["авто", "АВТО", "", None])
def test_planner_auto_difficulty(value):
    p = make()
    topic = p.add_topic("Математика", "Введение в анализ", value)
    assert topic.difficulty == 2


def test_manual_difficulty_still_works_and_can_be_changed():
    p = make()
    p.add_topic("Математика", "Ряды", 5)
    assert p.topics[("Математика", "Ряды")].difficulty == 5
    p.set_difficulty("Математика", "Ряды", "2")
    assert p.topics[("Математика", "Ряды")].difficulty == 2
    p.set_difficulty("Математика", "Ряды", "авто")
    assert p.topics[("Математика", "Ряды")].difficulty == 5
    with pytest.raises(ValidationError):
        p.set_difficulty("Математика", "Ряды", "9")
    with pytest.raises(ValidationError):
        p.set_difficulty("Математика", "Нет такой", "3")
