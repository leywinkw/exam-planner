"""Guess topic difficulty (1-5, hours = difficulty) from the exam and topic names.

Everything is plain dicts of lower-case word stems, so it is easy to extend:
a stem matches when it occurs inside the lower-cased name.
"""

DEFAULT_DIFFICULTY = 3

# exam (subject) stem -> base difficulty
SUBJECT_BASE = {
    "математ": 4, "алгебр": 4, "геометр": 3, "анализ": 4, "статистик": 3,
    "физик": 4, "хими": 4, "биолог": 3, "информат": 3, "программ": 3,
    "python": 3, "питон": 3, "алгоритм": 4, "баз": 3,
    "истори": 3, "географ": 2, "литератур": 2, "русск": 2, "английск": 2,
    "язык": 2, "философ": 3, "социолог": 2, "психолог": 3,
    "эконом": 3, "право": 3, "юрис": 3, "менеджмент": 2, "маркетинг": 2,
    "физкультур": 1, "обж": 1,
}

# topic stem -> change of difficulty
TOPIC_SHIFT = {
    "введени": -2, "обзор": -1, "основ": -1, "базов": -1, "общ": -1, "истори": -1,
    "понят": -1, "определен": -1,
    "теорем": 1, "доказательств": 1, "интеграл": 1, "производн": 1, "дифференц": 1,
    "уравнен": 1, "матриц": 1, "ряд": 1, "предел": 1, "вероятност": 1,
    "термодинам": 1, "квант": 1, "органическ": 1, "расширенн": 1, "продвинут": 1,
    "сложн": 1, "углублен": 1, "оптимизац": 1, "комплекс": 1,
}


def estimate_difficulty(exam_name, topic_name):
    """Return difficulty 1-5: subject base (default 3) plus topic-word shifts."""
    exam = str(exam_name).lower()
    topic = str(topic_name).lower()
    level = DEFAULT_DIFFICULTY
    for stem, base in SUBJECT_BASE.items():
        if stem in exam:
            level = base
            break
    # each stem counts once, so repeated words cannot run away
    level += sum(shift for stem, shift in TOPIC_SHIFT.items() if stem in topic)
    return max(1, min(5, level))
