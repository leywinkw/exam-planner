from datetime import date, timedelta

from planner.errors import ValidationError
from planner.estimator import estimate_difficulty
from planner.models import (CONTROL, CONTROL_PREFIX, DONE, EXAM, TODO, Exam, Topic,
                            parse_difficulty)

AUTO = "авто"  # значение сложности, при котором её подбирает программа
DEFAULT_DAILY_LIMIT = 4  # часов учёбы в день по умолчанию
DEFAULT_MAX_CHUNK = 2  # больше стольки часов одной темы за день не ставим: тема растягивается на несколько дней
REVISION_HOURS = {EXAM: 2, CONTROL: 1}  # повторение накануне: 2 часа перед экзаменом, 1 перед контрольной
REVISION = "Повторение"  # так называется «тема» повторения в плане


class Planner:
    """Хранит экзамены и темы и строит план по дням.

    exams  - словарь {название: Exam}, topics - словарь {(событие, тема): Topic};
    plan   - словарь {дата: [(событие, тема, часы), ...]}, его рисуют календарь и диаграмма.
    """

    def __init__(self, daily_limit=DEFAULT_DAILY_LIMIT, max_chunk=DEFAULT_MAX_CHUNK):
        self.exams = {}
        self.topics = {}
        self.plan = {}
        self.set_daily_limit(daily_limit)
        self.set_max_chunk(max_chunk)

    # --- ввод и изменение данных ---------------------------------------
    def set_daily_limit(self, value):
        """Лимит часов учёбы в день: целое число от 1 до 16."""
        try:
            limit = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Лимит часов в день должен быть целым числом") from None
        if not 1 <= limit <= 16:
            raise ValidationError("Лимит часов в день: от 1 до 16")
        self.daily_limit = limit

    def set_max_chunk(self, value):
        """Сколько часов одной темы можно ставить в один день: целое число от 1 до 8."""
        try:
            chunk = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Часов на тему в день должно быть целым числом") from None
        if not 1 <= chunk <= 8:
            raise ValidationError("Часов на одну тему в день: от 1 до 8")
        self.max_chunk = chunk

    def add_exam(self, name, exam_date, today=None, kind=EXAM):
        """Добавляет экзамен или контрольную; дата должна быть в будущем, название уникальным."""
        today = today or date.today()
        name = str(name).strip()
        # у контрольной название получает префикс, чтобы не совпасть с экзаменом по тому же предмету
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
        # вместе с событием удаляем все его темы (собираем словарь без них)
        self.topics = {k: t for k, t in self.topics.items() if t.exam != name}

    def add_topic(self, exam_name, name, difficulty):
        """Добавляет тему к событию; сложность «авто» подбирается по названиям."""
        if exam_name not in self.exams:
            raise ValidationError("Сначала добавьте экзамен")
        # «авто»: сложность подбирает estimator по названию экзамена и темы
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
        """Меняет сложность (а значит, и часы) темы; «авто» подбирает её заново по названиям."""
        topic = self.topics.get((exam_name, name))
        if topic is None:
            raise ValidationError("Тема не найдена")
        if self._is_auto(difficulty):
            difficulty = estimate_difficulty(exam_name, name)
        topic.difficulty = parse_difficulty(difficulty)
        return topic

    @staticmethod
    def _is_auto(value):
        """True, если сложность не задана вручную: пусто или слово «авто»."""
        return value is None or str(value).strip().lower() in ("", AUTO)

    def set_status(self, exam_name, name, status):
        """Отмечает тему выполненной (done) или возвращает её в план (todo)."""
        topic = self.topics.get((exam_name, name))
        if topic is None:
            raise ValidationError("Тема не найдена")
        if status not in (TODO, DONE):
            raise ValidationError("Некорректный статус темы")
        topic.status = status

    # --- построение плана ----------------------------------------------
    def build_plan(self, today=None):
        """Строит self.plan заново, начиная с сегодняшнего дня; возвращает темы, которые не поместились.

        Сначала идут самые сложные темы ближайшего события. День перед событием отдан
        под повторение, в день самого события занятий нет.
        """
        today = today or date.today()
        plan = {}  # итог: {дата: [(событие, тема, часы)]}
        load = {}  # сколько часов уже занято в каждый день: {дата: часы}

        def add(day, exam, topic, hours):
            # кладём порцию часов в план и учитываем, сколько времени в этот день уже занято
            plan.setdefault(day, []).append((exam, topic, hours))
            load[day] = load.get(day, 0) + hours
            # запоминаем первый день, на который поставили тему (нужно для пересчёта)
            known = self.topics.get((exam, topic))
            if known is not None and known.planned_day is None:
                known.planned_day = day

        # будущие события по возрастанию даты: ближайшее планируем первым
        upcoming = sorted((e for e in self.exams.values() if e.date > today),
                          key=lambda e: e.date)
        # дни событий и дни перед ними закрыты для учёбы (там экзамен или повторение)
        blocked = {d for e in upcoming for d in (e.date, e.date - timedelta(days=1))}
        # сначала ставим повторение на день перед каждым событием
        for exam in upcoming:
            eve = exam.date - timedelta(days=1)
            if eve >= today:
                add(eve, exam.name, REVISION, min(REVISION_HOURS[exam.kind], self.daily_limit))

        at_risk = []  # темы, которые не успеваем разместить до срока
        for exam in upcoming:
            last_study_day = exam.date - timedelta(days=2)  # за день до события идёт повторение
            todo = [t for t in self.topics.values()
                    if t.exam == exam.name and t.status == TODO]
            # самые сложные темы первыми, при равной сложности по алфавиту
            todo.sort(key=lambda t: (-t.difficulty, t.name))
            for topic in todo:
                # за день ставим не больше max_chunk часов одной темы, остаток переходит на следующие дни
                left = topic.hours
                day = today
                while left > 0 and day <= last_study_day:
                    free = self.daily_limit - load.get(day, 0)  # свободно часов в этот день
                    if day not in blocked and free > 0:
                        chunk = min(free, left, self.max_chunk)
                        add(day, exam.name, topic.name, chunk)
                        left -= chunk
                    day += timedelta(days=1)
                if left > 0:  # дни кончились, а часы остались: тема не помещается
                    at_risk.append(topic)
        self.plan = plan
        return at_risk

    def replan(self, today=None):
        """Пересчитывает план и сообщает, что изменилось.

        Возвращает (moved, at_risk): moved - невыполненные темы, день которых уже прошёл
        (пропущенные), они планируются заново с сегодняшнего дня; at_risk - темы, не успевающие в срок.
        """
        today = today or date.today()
        # пропущенная тема: не выполнена, а день, на который её ставили, уже позади
        moved = [t for t in self.topics.values()
                 if t.status == TODO and t.planned_day is not None and t.planned_day < today]
        for topic in moved:
            topic.planned_day = None  # сбрасываем день, чтобы build_plan поставил тему заново
        at_risk = self.build_plan(today)
        return moved, at_risk

    def day_load(self, day):
        """Сумма часов за день: от неё зависит цвет клетки календаря."""
        return sum(hours for _, _, hours in self.plan.get(day, []))
