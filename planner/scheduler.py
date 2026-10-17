from datetime import date, timedelta

from planner.errors import ValidationError
from planner.models import DONE, TODO, Exam, Topic

DEFAULT_DAILY_LIMIT = 4
REVISION_HOURS = 2
REVISION = "Повторение"


class Planner:
    """Holds exams and topics and builds a day-by-day plan.

    plan is a dict: {date: [(exam_name, topic_name, hours), ...]}.
    """

    def __init__(self, daily_limit=DEFAULT_DAILY_LIMIT):
        self.exams = {}
        self.topics = {}
        self.plan = {}
        self.set_daily_limit(daily_limit)

    # --- editing -------------------------------------------------------
    def set_daily_limit(self, value):
        try:
            limit = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Лимит часов в день должен быть целым числом") from None
        if not 1 <= limit <= 16:
            raise ValidationError("Лимит часов в день: от 1 до 16")
        self.daily_limit = limit

    def add_exam(self, name, exam_date, today=None):
        today = today or date.today()
        exam = Exam(name, exam_date)
        if exam.date <= today:
            raise ValidationError("Дата экзамена должна быть в будущем")
        if exam.name in self.exams:
            raise ValidationError("Такой экзамен уже есть")
        self.exams[exam.name] = exam
        return exam

    def remove_exam(self, name):
        if name not in self.exams:
            raise ValidationError("Экзамен не найден")
        del self.exams[name]
        self.topics = {k: t for k, t in self.topics.items() if t.exam != name}

    def add_topic(self, exam_name, name, difficulty):
        if exam_name not in self.exams:
            raise ValidationError("Сначала добавьте экзамен")
        topic = Topic(exam_name, name, difficulty)
        if topic.key in self.topics:
            raise ValidationError("Такая тема уже есть в этом экзамене")
        self.topics[topic.key] = topic
        return topic

    def remove_topic(self, exam_name, name):
        try:
            del self.topics[(exam_name, name)]
        except KeyError:
            raise ValidationError("Тема не найдена") from None

    def set_status(self, exam_name, name, status):
        topic = self.topics.get((exam_name, name))
        if topic is None:
            raise ValidationError("Тема не найдена")
        if status not in (TODO, DONE):
            raise ValidationError("Некорректный статус темы")
        topic.status = status

    # --- planning ------------------------------------------------------
    def build_plan(self, today=None):
        """Rebuild self.plan from today; return topics that do not fit.

        Hardest topics of the earliest exam go first. The day before an exam
        is revision. Nothing is planned on or after the exam date.
        """
        today = today or date.today()
        plan = {}
        load = {}

        def add(day, exam, topic, hours):
            plan.setdefault(day, []).append((exam, topic, hours))
            load[day] = load.get(day, 0) + hours
            known = self.topics.get((exam, topic))
            if known is not None and known.planned_day is None:
                known.planned_day = day

        upcoming = sorted((e for e in self.exams.values() if e.date > today),
                          key=lambda e: e.date)
        # exam days and the day before each exam are closed for studying
        blocked = {d for e in upcoming for d in (e.date, e.date - timedelta(days=1))}
        for exam in upcoming:
            eve = exam.date - timedelta(days=1)
            if eve >= today:
                add(eve, exam.name, REVISION, min(REVISION_HOURS, self.daily_limit))

        at_risk = []
        for exam in upcoming:
            last_study_day = exam.date - timedelta(days=2)
            todo = [t for t in self.topics.values()
                    if t.exam == exam.name and t.status == TODO]
            todo.sort(key=lambda t: (-t.difficulty, t.name))
            day = today
            for topic in todo:
                left = topic.hours
                while left > 0 and day <= last_study_day:
                    free = self.daily_limit - load.get(day, 0)
                    if day in blocked or free <= 0:
                        day += timedelta(days=1)
                        continue
                    chunk = min(free, left)
                    add(day, exam.name, topic.name, chunk)
                    left -= chunk
                if left > 0:
                    at_risk.append(topic)
        self.plan = plan
        return at_risk

    def replan(self, today=None):
        """Rebuild the plan and report what changed.

        Returns (moved, at_risk): moved are todo topics whose planned day is
        already in the past (missed); they are planned again from today.
        """
        today = today or date.today()
        moved = [t for t in self.topics.values()
                 if t.status == TODO and t.planned_day is not None and t.planned_day < today]
        for topic in moved:
            topic.planned_day = None
        at_risk = self.build_plan(today)
        return moved, at_risk

    def day_load(self, day):
        return sum(hours for _, _, hours in self.plan.get(day, []))
