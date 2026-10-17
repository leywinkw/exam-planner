from planner.catalog import CATALOG, subjects, topics_for
from planner.estimator import estimate_difficulty


def test_catalog_is_sane():
    for subject, topics in CATALOG.items():
        assert len(topics) >= 5 and len(set(topics)) == len(topics)
        for topic in topics:
            assert 1 <= estimate_difficulty(subject, topic) <= 5


def test_known_subjects_get_their_own_base():
    assert estimate_difficulty("Математика", "Пределы") >= estimate_difficulty("Литература", "Поэзия")
    assert estimate_difficulty("Обществознание", "Политика") == 3


def test_subjects_hides_taken():
    assert "Физика" not in subjects(taken=["Физика"])
    assert "Математика" in subjects(taken=["Физика"])


def test_topics_for_matching():
    assert "Пределы" in topics_for("Математика")
    assert "Пределы" in topics_for("математика (1 курс)")
    assert "Пределы" not in topics_for("Математика", taken=["Пределы"])
    assert topics_for("Что-то своё") == []
    assert topics_for("") == []
