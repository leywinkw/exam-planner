from datetime import date, timedelta

from planner.errors import ValidationError
from planner.estimator import estimate_difficulty
from planner.models import (CONTROL, CONTROL_PREFIX, DONE, EXAM, TODO, Exam, Topic,
                            parse_difficulty)

AUTO = "авто"  # если сложность «авто», её считает программа
DEFAULT_DAILY_LIMIT = 4  # часов в день по умолчанию
DEFAULT_MAX_CHUNK = 2  # сколько часов одной темы можно ставить в один день
REVISION_HOURS = {EXAM: 2, CONTROL: 1}  # повторение накануне, 2 часа перед экзаменом и 1 перед контрольной
REVISION = "Повторение"  # так в плане называется повторение


class Planner:
    # хранит экзамены, темы и план по дням
    # exams это словарь {название: Exam}, topics это {(событие, тема): Topic}
    # plan это словарь {дата: [(событие, тема, часы)]}, по нему рисуются календарь и диаграмма

    def __init__(self, daily_limit=DEFAULT_DAILY_LIMIT, max_chunk=DEFAULT_MAX_CHUNK):
        self.exams = {}
        self.topics = {}
        self.plan = {}
        self.set_daily_limit(daily_limit)
        self.set_max_chunk(max_chunk)

    # --- изменение данных ---
    def set_daily_limit(self, value):
        # лимит часов в день, целое число от 1 до 16
        try:
            limit = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Лимит часов в день должен быть целым числом") from None
        if not 1 <= limit <= 16:
            raise ValidationError("Лимит часов в день: от 1 до 16")
        self.daily_limit = limit

    def set_max_chunk(self, value):
        # сколько часов одной темы в день, целое число от 1 до 8
        try:
            chunk = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Часов на тему в день должно быть целым числом") from None
        if not 1 <= chunk <= 8:
            raise ValidationError("Часов на одну тему в день: от 1 до 8")
        self.max_chunk = chunk

    def add_exam(self, name, exam_date, today=None, kind=EXAM):
        # добавляет экзамен или контрольную, дата в будущем и название не должно повторяться
        today = today or date.today()
        name = str(name).strip()
        # к названию контрольной добавляем префикс
        if kind == CONTROL and name and not name.startswith(CONTROL_PREFIX):
            name = CONTROL_PREFIX + name
        exam = Exam(name, exam_date, kind)
        if exam.date <= today:
            raise ValidationError("Дата должна быть в будущем")
        if exam.name in self.exams:
            raise ValidationError("Такое событие уже есть")
        self.exams[exam.name] = exam
        return exam

    def remove_exam(self, name):
        if name not in self.exams:
            raise ValidationError("Экзамен не найден")
        del self.exams[name]
        # вместе с событием удаляем его темы
        self.topics = {k: t for k, t in self.topics.items() if t.exam != name}

    def add_topic(self, exam_name, name, difficulty):
        # добавляет тему, сложность «авто» считает estimator
        if exam_name not in self.exams:
            raise ValidationError("Сначала добавьте экзамен")
        # если «авто», считаем сложность по названиям
        if self._is_auto(difficulty):
            difficulty = estimate_difficulty(exam_name, name)
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

    def set_difficulty(self, exam_name, name, difficulty):
        # меняет сложность темы, «авто» считает её заново
        topic = self.topics.get((exam_name, name))
        if topic is None:
            raise ValidationError("Тема не найдена")
        if self._is_auto(difficulty):
            difficulty = estimate_difficulty(exam_name, name)
        topic.difficulty = parse_difficulty(difficulty)
        return topic

    @staticmethod
    def _is_auto(value):
        # true, если сложность не задана руками
        return value is None or str(value).strip().lower() in ("", AUTO)

    def set_status(self, exam_name, name, status):
        # отмечает тему выполненной или возвращает в план
        topic = self.topics.get((exam_name, name))
        if topic is None:
            raise ValidationError("Тема не найдена")
        if status not in (TODO, DONE):
            raise ValidationError("Некорректный статус темы")
        topic.status = status

    # --- построение плана ---
    def build_plan(self, today=None):
        # строит план заново от сегодняшнего дня, возвращает темы, которые не успели
        # часы события делим поровну на все учебные дни до него, сложные темы идут первыми
        # за день до события только повторение, в день события занятий нет
        today = today or date.today()
        plan = {}  # сам план, {дата: [(событие, тема, часы)]}
        load = {}  # сколько часов уже занято в каждый день

        def add(day, exam, topic, hours):
            # добавляем часы в план и считаем, сколько занято в этот день
            items = plan.setdefault(day, [])
            for index, (e, t, h) in enumerate(items):
                if (e, t) == (exam, topic):  # если эта тема уже есть в этот день, просто прибавляем часы
                    items[index] = (e, t, h + hours)
                    break
            else:
                items.append((exam, topic, hours))
            load[day] = load.get(day, 0) + hours
            # запоминаем первый день темы, нужно для пересчёта
            known = self.topics.get((exam, topic))
            if known is not None and known.planned_day is None:
                known.planned_day = day

        # будущие события по дате, ближайшее первым
        upcoming = sorted((e for e in self.exams.values() if e.date > today),
                          key=lambda e: e.date)
        # в дни событий и накануне не учимся
        blocked = {d for e in upcoming for d in (e.date, e.date - timedelta(days=1))}
        # сначала ставим повторение на день перед событием
        for exam in upcoming:
            eve = exam.date - timedelta(days=1)
            if eve >= today:
                add(eve, exam.name, REVISION, min(REVISION_HOURS[exam.kind], self.daily_limit))

        at_risk = []  # темы, которые не успеваем
        for exam in upcoming:
            last_study_day = exam.date - timedelta(days=2)  # последний день учёбы, накануне повторение
            todo = [t for t in self.topics.values()
                    if t.exam == exam.name and t.status == TODO]
            # сложные темы первыми, при одинаковой сложности по алфавиту
            todo.sort(key=lambda t: (-t.difficulty, t.name))
            left = {t.key: t.hours for t in todo}  # сколько часов каждой темы ещё надо поставить
            total = sum(left.values())
            # учебные дни до срока, где есть свободное время
            days = []
            day = today
            while day <= last_study_day:
                if day not in blocked and self.daily_limit - load.get(day, 0) > 0:
                    days.append(day)
                day += timedelta(days=1)
            if total and days:
                # k-й час ставим на день номер floor((k + 0.5) * дней / часов),
                # так часы расходятся по всему сроку, а не лежат в первых днях
                allot = [0] * len(days)
                for k in range(total):
                    allot[int((k + 0.5) * len(days) / total)] += 1
                carry = 0  # часы, которые не влезли в прошлые дни
                for day, planned in zip(days, allot):
                    budget = min(planned + carry, self.daily_limit - load.get(day, 0))
                    carry = planned + carry - budget
                    for topic in todo:  # по порядку, сложные первыми
                        chunk = min(left[topic.key], budget, self.max_chunk)
                        if chunk > 0:
                            add(day, exam.name, topic.name, chunk)
                            left[topic.key] -= chunk
                            budget -= chunk
                    carry += budget  # что не использовали из-за лимита на тему, переносим дальше
            # если часы остались, ставим их в самые свободные дни
            for topic in todo:
                for day in sorted(days, key=lambda d: (load.get(d, 0), d)):
                    if left[topic.key] <= 0:
                        break
                    already = sum(h for e, t, h in plan.get(day, []) if (e, t) == (exam.name, topic.name))
                    chunk = min(left[topic.key], self.daily_limit - load.get(day, 0), self.max_chunk - already)
                    if chunk > 0:
                        add(day, exam.name, topic.name, chunk)
                        left[topic.key] -= chunk
            # если и так не влезло, тема не успевает
            at_risk += [t for t in todo if left[t.key] > 0]
        self.plan = plan
        return at_risk

    def replan(self, today=None):
        # пересчитывает план и возвращает (moved, at_risk)
        # moved это невыполненные темы с прошедшим днём, их ставим заново с сегодня
        # at_risk это темы, которые не успеваем
        today = today or date.today()
        # пропущенная тема, не выполнена, а её день уже прошёл
        moved = [t for t in self.topics.values()
                 if t.status == TODO and t.planned_day is not None and t.planned_day < today]
        for topic in moved:
            topic.planned_day = None  # сбрасываем день, чтобы build_plan поставил тему заново
        at_risk = self.build_plan(today)
        return moved, at_risk

    def day_load(self, day):
        # сумма часов за день, по ней красится календарь
        return sum(hours for _, _, hours in self.plan.get(day, []))
